"""The lines of the repository shown to the model for each claim, found with no model.

A claim whose anchors resolved gets the lines around each one: a few lines either side of its first matches, or the
first lines of a file it names. A claim that names nothing ("the CI audit's checkout keeps no credentials") gets lines
in three steps:

1. Area: the files the claim's concept is about: its ``sources`` front matter (an OKF field), every readable file its
   text names in backticks, and the files the anchors of its concept's other claims were found in.
2. Commands: for a command the claim names, the code files that register its last word in quotes.
3. Keywords: the claim's and its sentence's words ranked by BM25 over 40-line windows of those files, or of every
   readable code file when the claim has no area; the best windows are shown.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import cached_property

import yaml

from audit_cli.checks.anchors import Anchor, located
from audit_cli.checks.steps import Repository

AROUND = 8  # lines either side of an anchor's match
FIRST_LINES = 40  # lines shown of a file the claim names
WINDOW = 40
STEP = 20
TOP = 3  # windows shown from keyword search
NOTHING = "(nothing found to show)"
STOP = {
    *[
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "by",
        "with",
        "as",
        "at",
        "is",
        "are",
        "be",
        "been",
        "was",
        "were",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "not",
        "no",
        "never",
        "only",
        "each",
        "every",
        "any",
        "all",
        "can",
        "could",
        "may",
        "might",
        "must",
        "should",
        "does",
        "do",
        "did",
        "has",
        "have",
        "had",
        "when",
        "while",
        "after",
        "before",
        "from",
        "into",
        "than",
        "then",
        "so",
        "such",
        "same",
        "also",
        "which",
        "who",
        "what",
        "where",
        "how",
        "why",
        "there",
        "their",
        "them",
        "they",
        "his",
        "her",
        "our",
        "your",
        "one",
        "two",
        "own",
        "just",
        "still",
        "per",
        "via",
    ]
}
BACKTICK = re.compile(r"`([^`\n]+)`")
WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+")


def tokens(text: str) -> list[str]:
    """Return a text's lower-case words, with snake_case and camelCase split into parts too, minus stop words."""
    out = []
    for word in WORD.findall(text):
        parts = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", word)
        for t in {word.lower(), *(p.lower() for p in parts)}:
            if len(t) > 2 and t not in STOP:
                out.append(t)
    return out


@dataclass
class ClaimLines:
    """The lines shown for one claim and where they came from: anchors, area, commands, everywhere or nothing."""

    text: str
    source: str
    files: list[str]


class LineFinder:
    """Finds lines for claims in one repository; the keyword index is built once, on first use.

    Parameters
    ----------
    repo :
        The files a check may read.
    limit :
        The most characters shown for one claim.
    """

    def __init__(self, repo: Repository, limit: int = 6000) -> None:
        self.repo = repo
        self.limit = limit
        self.code = [f for f in repo.files if not f.endswith(".md") and not f.split("/")[0].startswith("test")]

    def _lines(self, path: str) -> list[str]:
        """Return a file's lines."""
        return self.repo.text(path).splitlines()

    @cached_property
    def windows(self) -> list[tuple[str, int, Counter[str]]]:
        """Every 40-line window of every readable code and prompt file, with its word counts."""
        out = []
        for path in self.repo.files:
            lines = self._lines(path)
            for start in range(0, max(len(lines) - STEP, 1), STEP):
                out.append((path, start, Counter(tokens("\n".join(lines[start : start + WINDOW])))))
        return out

    @cached_property
    def idf(self) -> dict[str, float]:
        """Each word's inverse document frequency over all windows."""
        df: Counter[str] = Counter()
        for _, _, counts in self.windows:
            df.update(counts.keys())
        n = len(self.windows) or 1
        return {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def _bm25(self, query: list[str], counts: Counter[str], mean: float) -> float:
        """Return a window's BM25 score for the query words."""
        k, b = 1.2, 0.75
        length = sum(counts.values())
        score = 0.0
        for t in set(query):
            f = counts.get(t, 0)
            if f:
                score += self.idf.get(t, 0.0) * f * (k + 1) / (f + k * (1 - b + b * length / (mean or 1)))
        return score

    def area(self, concept_text: str, sibling_files: list[str]) -> list[str]:
        """Return the readable files a concept is about: its sources, the files it names, those its claims located."""
        files: list[str] = []
        if concept_text.startswith("---"):
            try:
                front = yaml.safe_load(concept_text.split("---", 2)[1]) or {}
            except yaml.YAMLError:
                front = {}
            sources = front.get("sources") if isinstance(front, dict) else None
            for source in sources or []:
                if isinstance(source, dict) and isinstance(source.get("resource"), str):
                    files.append(source["resource"])
                elif isinstance(source, str):
                    files.append(source)
        files += [m.strip().split()[0].rstrip("/") for m in BACKTICK.findall(concept_text) if m.strip()]
        files += sibling_files
        known = set(self.repo.files)
        return list(dict.fromkeys(f for f in files if f in known))

    def command_files(self, anchors: list[Anchor]) -> list[str]:
        """Return the code files that register, in quotes, the last word of each command the claim names."""
        found: list[str] = []
        for anchor in anchors:
            if anchor.kind == "command":
                verb = anchor.text.split()[-1]
                found += [f for f in self.code if f.endswith(".py") and f'"{verb}"' in self.repo.text(f)]
        return list(dict.fromkeys(found))

    def around(self, anchors: list[Anchor]) -> str:
        """Return the lines around each anchor in the files it was found in."""
        parts: list[str] = []
        for anchor in anchors:
            needle = anchor.text.split()[-1].lstrip("-") if anchor.kind == "command" else anchor.text
            for where in anchor.where[:3]:
                path = where.split()[0]
                if path not in self.repo.files:
                    continue
                lines = self._lines(path)
                if anchor.kind == "path" and path == anchor.text.rstrip("/"):
                    shown = "\n".join(f"{i}: {line}" for i, line in enumerate(lines[:FIRST_LINES], 1))
                    parts.append(f"--- {path} (first lines)\n{shown}")
                    continue
                for i in [i for i, line in enumerate(lines) if needle in line][:3]:
                    lo, hi = max(i - AROUND, 0), min(i + AROUND + 1, len(lines))
                    parts.append(
                        f"--- {path}:{lo + 1}-{hi}\n" + "\n".join(f"{j + 1}: {lines[j]}" for j in range(lo, hi))
                    )
        return "\n".join(dict.fromkeys(parts))[: self.limit]

    def search(self, query: list[str], files: list[str]) -> str:
        """Return the best keyword windows among ``files``, or among every readable code file when none are given."""
        allowed = set(files) if files else set(self.code)
        pool = [w for w in self.windows if w[0] in allowed]
        if not pool or not query:
            return ""
        mean = sum(sum(c.values()) for _, _, c in pool) / len(pool)
        scored = sorted(((self._bm25(query, c, mean), p, s) for p, s, c in pool), key=lambda x: -x[0])
        parts: list[str] = []
        used: list[tuple[str, int]] = []
        for score, path, start in scored:
            if len(parts) == TOP or score == 0:
                break
            if any(path == p and abs(start - s) < WINDOW for p, s in used):
                continue
            used.append((path, start))
            lines = self._lines(path)
            end = min(start + WINDOW, len(lines))
            parts.append(
                f"--- {path}:{start + 1}-{end}\n" + "\n".join(f"{i + 1}: {lines[i]}" for i in range(start, end))
            )
        return "\n".join(parts)[: self.limit]

    def find(
        self, claim: str, sentence: str, anchors: list[Anchor], concept_text: str, sibling_files: list[str]
    ) -> ClaimLines:
        """Return the lines for one claim: around its anchors, else from its area, commands or everywhere."""
        near = self.around(anchors)
        if near:
            return ClaimLines(near, "anchors", located(anchors, self.repo))
        commands = self.command_files(anchors)
        files = list(dict.fromkeys([*commands, *self.area(concept_text, sibling_files)]))
        source = "commands" if commands else "area" if files else "everywhere"
        text = self.search(tokens(f"{claim} {sentence}"), files)
        if not text:
            return ClaimLines(NOTHING, "nothing", [])
        return ClaimLines(text, source, list(dict.fromkeys(re.findall(r"^--- (\S+?)[: ]", text, re.MULTILINE))))
