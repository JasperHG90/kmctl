"""Find lines to show for a claim the settle step found nothing for, with no model: the concept's area, then keywords.

Run from the audit-cli folder: uv run python scripts/pilots/dossier.py [--show N]

Where the settle step finds a claim's named things, the one call is shown the lines around them. Claims that name
nothing ("the CI audit's checkout keeps no credentials") get nothing and go to the searching agent. This builds lines
for them in three free steps:

1. Area: the files the claim's concept is about: its ``sources`` front matter (an OKF field) and every tracked file
   its text names in backticks, plus the files the settle step located for any claim of the concept.
2. Commands: for a command the claim names (``kmctl verify``), the code files that register its last word in quotes.
3. Keywords: the claim's and its sentence's words ranked by BM25 over 40-line windows of the area files (of every
   readable code and config file when the area is empty); the best windows are shown.

Prints, over the claims the agent would get (scripts/pilots/no_lines.py), how many now have lines and from which
step, and writes results/pilots/dossier.json.
"""

import argparse
import json
import math
import re
import sys
from collections import Counter
from functools import cache

import yaml

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common, no_lines  # the scripts folder is not a package on the path

WINDOW = 40
STEP = 20
TOP = 3
LIMIT = 6000
CODE = (".py", ".sh", ".yml", ".yaml", ".toml", ".json", ".js", ".ts", ".go", ".rs", ".rb", ".java", ".cfg", ".ini")
STOP = {
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


@cache
def readable() -> tuple[str, ...]:
    """Return the tracked code and config files a check may read, tests left out."""
    tracked = common.git_files()
    return tuple(
        f for f in tracked if f.endswith(CODE) and not f.startswith(common.LEFT_OUT) and "test" not in f.split("/")[0]
    )


@cache
def lines_of(path: str) -> tuple[str, ...]:
    """Return a file's lines."""
    return tuple((common.REPO / path).read_text(errors="replace").splitlines())


@cache
def windows() -> tuple[tuple[str, int, Counter[str]], ...]:
    """Return every 40-line window of every readable file, with its word counts."""
    out = []
    for path in readable():
        lines = lines_of(path)
        for start in range(0, max(len(lines) - STEP, 1), STEP):
            out.append((path, start, Counter(tokens("\n".join(lines[start : start + WINDOW])))))
    return tuple(out)


@cache
def idf() -> dict[str, float]:
    """Return each word's inverse document frequency over all windows."""
    df: Counter[str] = Counter()
    for _, _, counts in windows():
        df.update(counts.keys())
    n = len(windows())
    return {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}


def bm25(query: list[str], counts: Counter[str], length: int, mean: float) -> float:
    """Return a window's BM25 score for the query words."""
    k, b = 1.2, 0.75
    weights = idf()
    score = 0.0
    for t in set(query):
        f = counts.get(t, 0)
        if f:
            score += weights.get(t, 0.0) * f * (k + 1) / (f + k * (1 - b + b * length / mean))
    return score


@cache
def area(concept: str) -> tuple[str, ...]:
    """Return the readable files a concept is about: its sources, the files it names, those its claims located."""
    path = common.REPO / ".okf" / f"{concept}.md"
    text = path.read_text() if path.exists() else ""
    files: list[str] = []
    if text.startswith("---"):
        front = yaml.safe_load(text.split("---", 2)[1]) or {}
        files += [s.get("resource", "") for s in front.get("sources") or [] if isinstance(s, dict)]
    files += [m.strip().split()[0].rstrip("/") for m in BACKTICK.findall(text) if m.strip()]
    for claim in common.claims():
        if claim.concept == concept:
            files += common.located_files(claim)
    known = set(readable())
    return tuple(dict.fromkeys(f for f in files if f in known))


def command_files(claim: common.StoredClaim) -> list[str]:
    """Return the readable code files that register, in quotes, the last word of each command the claim names."""
    found: list[str] = []
    for anchor in claim.anchors:
        if anchor["kind"] != "command":
            continue
        verb = anchor["text"].split()[-1]
        found += [f for f in readable() if f.endswith(".py") and f'"{verb}"' in "\n".join(lines_of(f))]
    return list(dict.fromkeys(found))


def dossier(claim: common.StoredClaim) -> tuple[str, str]:
    """Return the lines to show for a claim and where its files came from: area, commands, or everywhere."""
    commands = command_files(claim)
    files = list(dict.fromkeys([*commands, *area(claim.concept)]))
    source = "commands" if commands else "area" if files else "everywhere"
    allowed = set(files) if files else set(readable())
    query = tokens(f"{claim.text} {claim.sentence}")
    pool = [w for w in windows() if w[0] in allowed]
    if not pool or not query:
        return "", source
    mean = sum(sum(c.values()) for _, _, c in pool) / len(pool)
    ranked = sorted(pool, key=lambda w: -bm25(query, w[2], sum(w[2].values()), mean))
    parts: list[str] = []
    used: set[tuple[str, int]] = set()
    for path, start, counts in ranked:
        if len(parts) == TOP or bm25(query, counts, sum(counts.values()), mean) == 0:
            break
        if any(path == p and abs(start - s) < WINDOW for p, s in used):
            continue
        used.add((path, start))
        lines = lines_of(path)
        end = min(start + WINDOW, len(lines))
        parts.append(f"--- {path}:{start + 1}-{end}\n" + "\n".join(f"{i + 1}: {lines[i]}" for i in range(start, end)))
    return "\n".join(parts)[:LIMIT], source


def main() -> None:
    """Count how many of the agent's claims get lines, by source, and save each dossier."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--show", type=int, default=0, help="Print the first N dossiers.")
    args = parser.parse_args()
    claims = no_lines.agent_share()
    out = {}
    for claim in claims:
        text, source = dossier(claim)
        out[claim.claim_id] = {
            "claim": claim.text,
            "source": source,
            "files": sorted(set(re.findall(r"--- (\S+):", text))),
            "lines": text,
        }
    summary = {
        "claims": len(claims),
        "with_lines": sum(bool(e["lines"]) for e in out.values()),
        "by_source": dict(Counter(e["source"] for e in out.values())),
    }
    (common.OUT / "dossier.json").write_text(json.dumps({"summary": summary, "claims": out}, indent=1))
    print(json.dumps(summary, indent=1))
    for e in list(out.values())[: args.show]:
        print("\n#", e["claim"], f"({e['source']})", e["files"])


if __name__ == "__main__":
    main()
