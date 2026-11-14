"""Mutation testing for checks: does a check that holds notice when the code it is about changes?

A check can hold without testing its claim: a grep for a comment that restates the claim holds whatever the code does.
To find out, small changes are made, one at a time and only in memory, to the code lines a check's steps matched and
the lines around them, and the check is run on each changed copy. A check that notices none of them is weak.

The changes are the ones a real edit would make: flip a boolean, change a number or a string, swap == and !=, negate
a condition, delete a statement, rename a defined name, change a YAML value or delete a YAML key, delete a file a file step found. Comments,
docstrings and other string-only lines are never changed: a check pinned to one is exactly what this should expose.
A change that no longer parses is dropped, so a check is never "killed" by a syntax error.
"""

import ast
import json
import re
import tomllib
from dataclasses import dataclass, field
from typing import Any

import yaml

from kmaudit.steps import (
    AnyStep,
    CodeStep,
    DefinitionStep,
    FileStep,
    GrepStep,
    ImportStep,
    QueryStep,
    Repository,
    run_check,
)

VERSION = "4"  # part of each stored score's key: a new version of the changes made measures every check again
MAX_MUTANTS = 24  # per check
AROUND = 2  # lines either side of a matched line that are changed too
LOCATION = re.compile(r"([\w./-]+\.\w+):(\d+):")
NUMBER = re.compile(r"(?<![\w.])(\d+)(?![\w.])")
STRING = re.compile(r"""(["'])([^"'\n]+)\1""")
YAML_VALUE = re.compile(
    r"^(\s*(?:-\s+)?[\w.\"'-]+\s*:\s+)([^\s#|>&*!\[{][^#]*?)(\s+#.*)?\s*$"
)
YAML_KEY = r"^\s*(?:-\s+)?[\"']?{}[\"']?\s*:"
#: A YAML mapping key at the start of a line, so a check on key names can notice it renamed.
YAML_KEY_NAME = re.compile(r"^(\s*(?:-\s+)?)([A-Za-z_][\w.-]*)(?=\s*:(?:\s|$))")
JMESPATH_WORDS = {
    "contains",
    "starts_with",
    "ends_with",
    "length",
    "not_null",
    "to_string",
    "to_array",
    "keys",
    "values",
    "join",
    "sort",
    "type",
    "max",
    "min",
    "sum",
    "abs",
    "null",
    "true",
    "false",
}


@dataclass
class Mutant:
    """One change to the code: the file, the line (0 for a whole file), what changed, and the new text (None: deleted)."""

    path: str
    line: int
    change: str
    text: str | None


@dataclass
class Quality:
    """How a check fared against the mutants of its code."""

    mutants: int = 0
    killed: int = 0
    survived: list[str] = field(default_factory=list)
    killed_by: list[str] = field(
        default_factory=list
    )  # the kind of each change noticed

    @property
    def weak(self) -> bool:
        """Whether the check is weak: it matched only text, or noticed none of the mutants it was tried on."""
        return TEXT_ONLY in self.survived or (self.mutants > 0 and self.killed == 0)

    @property
    def meaningful(self) -> int:
        """Changes noticed to a value or condition: a deletion breaks any check that matches the line or the file,
        so noticing one says nothing about what the check tests."""
        return sum(1 for change in self.killed_by if change not in DELETIONS)

    @property
    def score(self) -> float | None:
        """The share of mutants the check noticed, or None when there were none to try."""
        return self.killed / self.mutants if self.mutants else None


def _parses(path: str, text: str) -> bool:
    """Whether a changed file still parses in its own language (files of other languages always count)."""
    try:
        if path.endswith(".py"):
            ast.parse(text)
        elif path.endswith((".yml", ".yaml")):
            yaml.safe_load(text)
        elif path.endswith(".json"):
            json.loads(text)
        elif path.endswith(".toml"):
            tomllib.loads(text)
    except (SyntaxError, ValueError, yaml.YAMLError, tomllib.TOMLDecodeError):
        return False
    return True


def _text_lines(path: str, text: str) -> set[int]:
    """Return the 1-based lines that are only text, never code: blank lines, comments, and in Python the lines of a
    string that stands alone (a docstring) or spans lines. A line that starts with a quote is code elsewhere: a JSON
    key, a quoted YAML value, a dict entry."""
    lines = text.splitlines()
    if path.endswith(".md"):
        comment: tuple[str, ...] = (
            "<!--",
        )  # in a prompt or skill, every other line is what it says
    elif path.endswith((".py", ".yml", ".yaml", ".toml", ".sh", ".bash", ".rb")):
        comment = ("#",)
    else:
        comment = ("//", "/*", "*")
    out = {
        n
        for n, line in enumerate(lines, 1)
        if not line.strip() or line.strip().startswith(comment)
    }
    if path.endswith(".py"):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return out
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                out |= set(
                    range(node.lineno, (node.end_lineno or node.lineno) + 1)
                )  # a docstring or a bare string
            elif (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.end_lineno is not None
                and node.end_lineno > node.lineno
            ):
                out |= set(
                    range(node.lineno + 1, node.end_lineno + 1)
                )  # the inside of a multi-line string
    return out


def _changes(path: str, line: str) -> list[tuple[str, str]]:
    """Return each changed version of one code line, with a word on what changed."""
    out: list[tuple[str, str]] = []
    yaml_file = path.endswith((".yml", ".yaml"))
    for old, new in (
        ("True", "False"),
        ("False", "True"),
        ("true", "false"),
        ("false", "true"),
    ):
        if re.search(rf"\b{old}\b", line):
            out.append((re.sub(rf"\b{old}\b", new, line, count=1), f"{old} to {new}"))
            break
    if (number := NUMBER.search(line)) is not None:
        out.append(
            (
                line[: number.start()]
                + str(int(number.group(1)) + 1)
                + line[number.end() :],
                "a number + 1",
            )
        )
    if (string := STRING.search(line)) is not None:
        changed = (
            string.group(1) + "mutated" + string.group(1)
        )  # a whole new value: an append keeps substrings
        out.append(
            (
                line[: string.start()] + changed + line[string.end() :],
                "a string replaced",
            )
        )
    if " == " in line:
        out.append((line.replace(" == ", " != ", 1), "== to !="))
    elif " != " in line:
        out.append((line.replace(" != ", " == ", 1), "!= to =="))
    if path.endswith(".py") and (
        named := re.match(
            r"^(\s*(?:async\s+)?(?:def|class)\s+)(\w+)|^(\s*)(\w+)(\s*[:=])", line
        )
    ):
        if named.group(2):
            out.append(
                (
                    named.group(1) + named.group(2) + "_mutated" + line[named.end() :],
                    "a name renamed",
                )
            )
        elif named.group(4) and named.group(4) not in {
            "return",
            "pass",
            "else",
            "try",
            "finally",
        }:
            out.append(
                (
                    named.group(3) + named.group(4) + "_mutated" + line[named.end(4) :],
                    "a name renamed",
                )
            )
    if path.endswith(".py") and (
        cond := re.match(r"^(\s*)(if|elif|while) (.+):\s*$", line)
    ):
        out.append(
            (
                f"{cond.group(1)}{cond.group(2)} not ({cond.group(3)}):",
                "condition negated",
            )
        )
    if yaml_file and (key := YAML_KEY_NAME.match(line)):
        out.append(
            (
                key.group(1) + key.group(2) + "_mutated" + line[key.end(2) :],
                "a YAML key renamed",
            )
        )
    if yaml_file and (value := YAML_VALUE.match(line)) and not STRING.search(line):
        out.append(
            (
                value.group(1) + "mutated" + (value.group(3) or ""),
                "a YAML value replaced",
            )
        )
    if path.endswith(".py") and line.strip() and not line.rstrip().endswith(":"):
        indent = line[: len(line) - len(line.lstrip())]
        out.append((indent + "pass", "statement deleted"))
    if yaml_file and YAML_VALUE.match(line):
        out.append(("", "YAML key deleted"))
    return out


def _scalars(detail: str) -> list[str]:
    """Return the text of each string or number a query step returned, read from its result detail, longest first."""
    try:
        value = json.loads(detail.split(": ", 1)[1])
    except (IndexError, json.JSONDecodeError):
        return []
    found: list[str] = []
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, list):
            stack += item
        elif isinstance(item, dict):
            stack += list(item.values())
        elif (
            isinstance(item, str | int | float)
            and not isinstance(item, bool)
            and len(str(item)) > 1
        ):
            found.append(str(item))
    return sorted(set(found), key=len, reverse=True)[:10]


def _literals(query: str) -> list[str]:
    """Return the strings a query compares against, like 'okf-vs-code' or `"ubuntu-latest"`, longest first.

    A backtick literal is JSON and is read as such. Numbers, true, false and null are left out: they turn up on many
    lines that have nothing to do with the query.
    """
    found: list[str] = []
    for raw, literal in re.findall(r"'([^']{2,})'|`([^`]+)`", query):
        value: Any = raw
        if literal:
            try:
                value = json.loads(literal)
            except json.JSONDecodeError:
                value = literal
        if isinstance(value, str) and len(value.strip()) > 1:
            found.append(value)
    return sorted(set(found), key=len, reverse=True)


def _region(
    repo: Repository, steps: list[AnyStep], details: list[str]
) -> dict[str, set[int]]:
    """Return, per file, the lines the check is about: lines its steps matched or named, before widening."""
    region: dict[str, set[int]] = {}
    for step, detail in zip(steps, details, strict=False):
        if isinstance(step, GrepStep | CodeStep) and step.present:
            for path, line in LOCATION.findall(detail):
                region.setdefault(path, set()).add(int(line))
        elif isinstance(step, DefinitionStep) and step.defined:
            pattern = re.compile(
                rf"^\s*(?:async\s+)?(?:def|class)\s+{re.escape(step.name)}\b|^\s*{re.escape(step.name)}\s*[:=]"
            )
            for path in repo.match(step.paths):
                hits = [
                    n
                    for n, line in enumerate(repo.text(path).splitlines(), 1)
                    if pattern.search(line)
                ]
                region.setdefault(path, set()).update(hits)
        elif isinstance(step, ImportStep) and step.imported:
            pattern = re.compile(rf"^\s*(?:import|from)\s+{re.escape(step.module)}\b")
            for path in repo.match(step.path):
                hits = [
                    n
                    for n, line in enumerate(repo.text(path).splitlines(), 1)
                    if pattern.search(line)
                ]
                region.setdefault(path, set()).update(hits)
        elif isinstance(step, QueryStep):
            values = _scalars(detail) or _literals(
                step.query
            )  # what it returned, or for a yes/no what it compares to
            keys = {
                k
                for k in re.findall(r"[A-Za-z_][\w-]*", step.query)
                if k not in JMESPATH_WORDS
            }
            for path in repo.match(step.paths):
                lines = repo.text(path).splitlines()
                held = {
                    n for n, line in enumerate(lines, 1) for v in values if v in line
                }
                if held:  # the lines that hold what the query returned, or the values it compares to
                    region.setdefault(path, set()).update(held)
                    continue
                words = re.findall(
                    r"[A-Za-z_][\w-]*", step.query
                )  # a yes/no or nothing: the last key it names
                key = next((k for k in reversed(words) if k in keys), "")
                if key:
                    key_line = re.compile(YAML_KEY.format(re.escape(key)))
                    region.setdefault(path, set()).update(
                        n for n, line in enumerate(lines, 1) if key_line.search(line)
                    )
    return {p: lines for p, lines in region.items() if lines and p in repo.files}


def mutants(repo: Repository, steps: list[AnyStep], details: list[str]) -> list[Mutant]:
    """Return up to MAX_MUTANTS changes to the code a check is about, spread over its lines, each still parsing."""
    out: list[Mutant] = []
    if steps and all(
        isinstance(step, FileStep) for step in steps
    ):  # a deleted file fails any step that reads it
        for step in steps:
            if isinstance(step, FileStep) and step.exists:
                for path in repo.match(step.path, among=repo.tracked)[:2]:
                    out.append(Mutant(path, 0, "file deleted", None))
    matched_lines: list[list[Mutant]] = []
    neighbours: list[list[Mutant]] = []
    for path, matched in sorted(_region(repo, steps, details).items()):
        text = repo.text(path)
        lines = text.splitlines()
        skip = _text_lines(path, text)
        near = {
            n
            for m in matched
            for n in range(m - AROUND, m + AROUND + 1)
            if 1 <= n <= len(lines)
        }
        for n in sorted(near - skip):
            options = []
            for new_line, change in _changes(path, lines[n - 1]):
                new_lines = (
                    lines[: n - 1] + ([new_line] if new_line else []) + lines[n:]
                )
                new_text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
                if new_text != text and _parses(path, new_text):
                    options.append(Mutant(path, n, change, new_text))
            if options:
                (matched_lines if n in matched else neighbours).append(options)
    for group in (
        matched_lines,
        neighbours,
    ):  # every change to matched lines before any to their neighbours
        depth = 0
        while len(out) < MAX_MUTANTS and any(depth < len(o) for o in group):
            out += [o[depth] for o in group if depth < len(o)][: MAX_MUTANTS - len(out)]
            depth += 1
    return out


TEXT_ONLY = "every line it matched is a comment or docstring"
DELETIONS = {"statement deleted", "YAML key deleted", "file deleted"}


def matched_only_text(
    repo: Repository, steps: list[AnyStep], details: list[str]
) -> bool:
    """Whether the check's steps matched lines and every one of them is text, not code (a comment, a docstring)."""
    region = _region(repo, steps, details)
    matched = [(path, n) for path, lines in region.items() for n in lines]
    return bool(matched) and all(
        n in _text_lines(path, repo.text(path)) for path, n in matched
    )


def measure(repo: Repository, steps: list[AnyStep], details: list[str]) -> Quality:
    """Run a holding check on each mutant of its code; return how many it noticed and which it did not.

    A mutant counts as noticed only when a step fails on what it read, not when a step could not run at all. A check
    whose matched lines are all comments or docstrings has no code to change; its survived list says so, which marks
    it weak.
    """
    quality = Quality()
    if matched_only_text(repo, steps, details):
        quality.survived.append(TEXT_ONLY)
    for mutant in mutants(repo, steps, details):
        holds, results = run_check(repo.changed({mutant.path: mutant.text}), steps)
        noticed = not holds and any(
            not r.holds and not r.detail.startswith("could not run") for r in results
        )
        quality.mutants += 1
        if noticed:
            quality.killed += 1
            quality.killed_by.append(mutant.change)
        else:
            where = f"{mutant.path}:{mutant.line}" if mutant.line else mutant.path
            quality.survived.append(f"{where}: {mutant.change}")
    return quality
