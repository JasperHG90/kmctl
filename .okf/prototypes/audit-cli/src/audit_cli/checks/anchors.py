"""What a claim names, where it is in the repository, and the claims those findings settle with no model.

Every backticked span in a claim is an anchor, resolved against the repository:

- a path: tracked now, gone (in git history only), or never tracked;
- a command of the repository's CLIs (pyproject scripts, walked through ``--help``; argparse scripts, read from their
  source), with its flags and defaults;
- a flag (``--x``), on the commands the claim names, else on any command;
- any other name: defined (tree-sitter), mentioned in code, mentioned only in tests, or absent.

A claim gets a verdict only when its words, with the anchors taken out, match a shape whose truth the anchors decide:
it no longer exists, the default of a flag, a file has a tool or flag, a file imports a module, a command accepts an
argument and a flag. Every other claim goes on to a model, with the lines around its anchors.
"""

import ast
import hashlib
import json
import os
import pathlib as plb
import re
import subprocess
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, field
from typing import Any

from tree_sitter import Node
from tree_sitter_language_pack import get_parser

from audit_cli.checks.steps import Repository, is_test

LANGUAGES = {".py": "python", ".yml": "yaml", ".yaml": "yaml", ".toml": "toml", ".sh": "bash", ".json": "json"}
SPAN = re.compile(r"`([^`]+)`")
WORD = re.compile(r"[a-z][\w-]*")
HELP_DEPTH = 3  # how many subcommand levels of a CLI's --help are walked


@dataclass
class Command:
    """One command of a repository CLI, with its flags and their defaults (None when it has none or none is shown)."""

    path: str
    flags: dict[str, str | None] = field(default_factory=dict)


@dataclass
class Anchor:
    """One backticked span and what it resolved to: kind (path, command, flag, name), status and where it is."""

    text: str
    kind: str
    status: str
    where: list[str] = field(default_factory=list)


@dataclass
class Settled:
    """What the anchors say about a claim: a verdict (None when a model must decide), the rule that gave it."""

    verdict: bool | None
    rule: str
    anchors: list[Anchor]


class Evidence:
    """The repository's evidence for anchors: files, git history, CLI commands, definitions and code text.

    Parameters
    ----------
    repo :
        The files a check may read.
    cache :
        Reads and writes the walked CLI commands under a key of what they depend on; None walks every time.
    walk_help :
        Run each pyproject script's ``--help`` to find its commands; off in tests, where nothing is installed.
    """

    def __init__(
        self,
        repo: Repository,
        cache: tuple[Callable[[str], Any], Callable[[str, Any], None]] | None = None,
        walk_help: bool = True,
    ) -> None:
        self.repo = repo
        tracked = set(repo.tracked)
        self.files = set(repo.files)
        self.dirs = {"/".join(f.split("/")[:i]) for f in tracked for i in range(1, f.count("/") + 1)}
        log = subprocess.run(
            ["git", "-C", str(repo.root), "log", "--all", "--name-only", "--format="],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        self.history = set(log.split()) - tracked
        self.basenames = {f.rsplit("/", 1)[-1]: f for f in tracked}
        self.top = {f.split("/")[0] for f in tracked if "/" in f}
        self.tracked = tracked
        self.code = {f: repo.text(f) for f in sorted(self.files) if not f.endswith(".md") and self._is_text(f)}
        self.definitions = self._definitions()
        self.commands = {c.path: c for c in [*self._typer_commands(cache, walk_help), *self._argparse_commands()]}

    def _is_text(self, path: str) -> bool:
        """Whether the file reads as text: no NUL byte in its first 8 KiB."""
        try:
            return b"\0" not in (self.repo.root / path).read_bytes()[:8192]
        except OSError:
            return False

    def _definitions(self) -> dict[str, list[str]]:
        """Return each defined name (function, class, assignment, config key) with the files that define it."""
        keep = re.compile(r"definition|declaration|assignment|pair|table|block_mapping_pair")
        found: dict[str, list[str]] = {}
        for path, text in self.code.items():
            language = LANGUAGES.get(plb.PurePath(path).suffix)
            if language is None:
                continue
            for node in _walk(get_parser(language).parse(text.encode()).root_node):
                if not keep.search(node.type):
                    continue
                name = next(
                    (node.child_by_field_name(f) for f in ("name", "key", "left") if node.child_by_field_name(f)),
                    None,
                )
                if name is not None and name.text:
                    found.setdefault(name.text.decode(errors="replace").strip("\"' "), []).append(path)
        return found

    def _typer_commands(
        self, cache: tuple[Callable[[str], Any], Callable[[str, Any], None]] | None, walk_help: bool
    ) -> list[Command]:
        """Walk each pyproject script's ``--help``, reading only its Commands and Options panels, or read the cache.

        The walk is slow (one process per command), so its result is kept under a key of pyproject.toml and the code
        of every package the scripts run: it is walked again only after one of those changes.
        """
        scripts = self.repo.scripts()
        if not walk_help or not scripts:
            return []
        packages = {entry.split(":")[0].split(".")[0] for entry in scripts.values()}
        depends = ["pyproject.toml", *(f for f in sorted(self.files) if packages & set(f.split("/")[:-1]))]
        key = (
            "cli-commands:" + hashlib.sha256(json.dumps([(f, self.repo.sha(f)) for f in depends]).encode()).hexdigest()
        )
        if cache is not None and (kept := cache[0](key)) is not None:
            return [Command(**c) for c in kept]
        env = {**os.environ, "COLUMNS": "400", "NO_COLOR": "1", "TERM": "dumb"}
        commands: list[Command] = []
        for cli in scripts:
            queue: list[list[str]] = [[]]
            while queue:
                words = queue.pop()
                help_text = subprocess.run(
                    ["uv", "run", cli, *words, "--help"],
                    cwd=self.repo.root,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=120,
                    check=False,  # a command whose help fails just shows no flags
                ).stdout
                command, subcommands = _parse_rich_help(" ".join([cli, *words]), help_text)
                commands.append(command)
                if len(words) < HELP_DEPTH:
                    queue += [[*words, sub] for sub in subcommands]
        if cache is not None:
            cache[1](key, [asdict(c) for c in commands])
        return commands

    def _argparse_commands(self) -> Iterator[Command]:
        """Read argparse parsers from the source of each tracked Python script that builds one."""
        for path, text in self.code.items():
            if not path.endswith(".py") or "ArgumentParser(" not in text or is_test(path):
                continue
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            parsers: dict[str, Command] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and len(node.targets) == 1:
                    target, call = node.targets[0], node.value
                    if not isinstance(target, ast.Name) or not isinstance(call.func, ast.Attribute | ast.Name):
                        continue
                    name = call.func.attr if isinstance(call.func, ast.Attribute) else call.func.id
                    if name == "ArgumentParser":
                        parsers[target.id] = Command(path)
                    elif name == "add_parser" and call.args and isinstance(call.args[0], ast.Constant):
                        parsers[target.id] = Command(f"{path} {call.args[0].value!s}")
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "add_argument"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in parsers
                ):
                    default = next((k.value for k in node.keywords if k.arg == "default"), None)
                    shown = str(default.value) if isinstance(default, ast.Constant) else None
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and str(arg.value).startswith("--"):
                            parsers[node.func.value.id].flags[str(arg.value)] = shown
            yield from parsers.values()

    def mentions(self, word: str) -> tuple[list[str], list[str]]:
        """Return the code files and the test files that hold the word whole."""
        pattern = re.compile(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])")
        hits = [p for p, text in self.code.items() if pattern.search(text)]
        return [p for p in hits if not is_test(p)], [p for p in hits if is_test(p)]


def _walk(node: Node) -> Iterator[Node]:
    """Yield every node under ``node``."""
    stack = [node]
    while stack:
        current = stack.pop()
        stack.extend(current.children)
        yield current


def _parse_rich_help(path: str, text: str) -> tuple[Command, list[str]]:
    """Read a Typer help page: the first word of each Commands row, and each Options row's flag and default."""
    command, subcommands, panel = Command(path), [], ""
    for line in text.splitlines():
        if line.startswith("╭─"):
            panel = line.strip("╭─ ").split(" ")[0]
            continue
        if not line.startswith("│"):
            continue
        row = line.strip("│").rstrip()
        if panel == "Commands" and re.match(r"^ [a-z][\w-]*\s", row):
            subcommands.append(row.split()[0])
        elif panel == "Options" and re.match(r"^\s+(\*\s+)?--[\w-]+", row):
            flag = re.search(r"--[\w-]+", row)
            default = re.search(r"\[default: ([^\]]+)\]", row)
            if flag:
                command.flags[flag.group(0)] = default.group(1) if default else None
    return command, subcommands


def resolve(evidence: Evidence, text: str, claim_commands: list[str]) -> Anchor:
    """Resolve one span: as a command, a flag, a path, then a name."""
    clis = {c.split()[0] for c in evidence.commands}
    words = text.split()
    if len(words) > 1 and words[0] in clis:
        verbs = [words[0]]
        for word in words[1:]:
            if not WORD.fullmatch(word):
                break
            verbs.append(word)
        while len(verbs) > 1 and " ".join(verbs) not in evidence.commands:
            verbs.pop()
        command = evidence.commands.get(" ".join(verbs))
        flags = [w.split("=")[0] for w in words if w.startswith("--")]
        if command is None or len(verbs) < min(len(words), 2) and not flags:
            return Anchor(text, "command", "missing")
        missing = [f for f in flags if f not in command.flags and f != "--help"]
        return Anchor(text, "command", "missing" if missing else "found", [command.path])
    if text.startswith("--"):
        flag = text.split()[0].split("=")[0]
        named = [c for c in evidence.commands.values() if any(c.path.startswith(n) for n in claim_commands)]
        scope = named or list(evidence.commands.values())
        on = [c.path for c in scope if flag in c.flags]
        return Anchor(text, "flag", "found" if on else "missing", on)
    candidate = text.rstrip("/")
    if candidate in evidence.basenames:
        return Anchor(text, "path", "present", [evidence.basenames[candidate]])
    if candidate.split("/")[0] in evidence.top or candidate in evidence.tracked or candidate in evidence.history:
        if "*" in candidate:
            pattern = re.compile(re.escape(candidate).replace(r"\*", "[^/]*"))
            found = [f for f in sorted(evidence.tracked) if pattern.fullmatch(f)]
            return Anchor(text, "path", "present" if found else "never", found[:5])
        if candidate in evidence.tracked or candidate in evidence.dirs:
            return Anchor(text, "path", "present", [candidate])
        if candidate in evidence.history:
            return Anchor(text, "path", "gone")
        return Anchor(text, "path", "never")
    parts = text.split(".")
    if len(parts) > 1 and all(WORD.fullmatch(x.lower()) for x in parts):
        files = [{p for p in evidence.definitions.get(x, []) if not is_test(p)} for x in parts]
        shared = set.intersection(*files)
        if shared:
            return Anchor(text, "name", "defined", sorted(shared)[:5])
    defined = [p for p in evidence.definitions.get(text, []) if not is_test(p)]
    if defined:
        return Anchor(text, "name", "defined", sorted(set(defined))[:5])
    code, tests = evidence.mentions(text)
    if code:
        return Anchor(text, "name", "mentioned", code[:5])
    old = sorted(f for f in evidence.history if text in f.split("/"))
    if old:
        return Anchor(text, "name", "gone", old[:5])
    if tests:
        return Anchor(text, "name", "tests only", tests[:5])
    return Anchor(text, "name", "absent")


def claim_commands(evidence: Evidence, spans: list[str]) -> list[str]:
    """Return the commands a claim names: a command span, or a script path whose file is a CLI."""
    found = []
    for span in spans:
        words = span.split()
        for n in range(len(words), 0, -1):
            if " ".join(words[:n]) in evidence.commands:
                found.append(" ".join(words[:n]))
                break
    return found


ABSENT = re.compile(
    r"^(the )?a((,| and|, and) (the )?a)*( \w+ plugin| file| script)?"
    r" (no longer exists?|does not exist|do not exist|is gone|are gone)( in .*)?$"
)
DEFAULT = re.compile(r"^the default a is a$")
HAS = re.compile(r"^a has an? a (tool|option|flag|argument|input|job|command|function|class)$")
IMPORT = re.compile(r"^no import of ([\w.]+) exists in a$")
ACCEPTS = re.compile(r"^a accepts an? a argument and an? a flag$")


def gone(anchor: Anchor) -> bool:
    """Whether the anchor names nothing in the repository: an untracked path, an absent name, a missing command.

    A name held only by tests counts as gone: a test that lists it often asserts that it stays gone.
    """
    return anchor.status in {"gone", "never", "absent", "missing", "tests only"}


def settle(evidence: Evidence, claim: str) -> Settled:
    """Resolve a claim's anchors and return its verdict when one of the shapes decides it, else None."""
    spans = SPAN.findall(claim)
    commands = claim_commands(evidence, spans)
    anchors = [resolve(evidence, s, commands) for s in spans]
    shape = SPAN.sub("a", claim).strip().rstrip(".").lower()
    verdict: bool | None = None
    rule = ""
    if anchors and ABSENT.match(shape):
        rule, verdict = "absent", all(gone(a) for a in anchors)
    elif len(anchors) == 2 and DEFAULT.match(shape) and anchors[0].kind == "flag":
        defaults = {evidence.commands[c].flags.get(anchors[0].text) for c in anchors[0].where if c in evidence.commands}
        if len(defaults) == 1 and None not in defaults:
            rule, verdict = "default", defaults.pop() == anchors[1].text
    elif len(anchors) == 2 and HAS.match(shape) and anchors[0].kind == "path":
        owner, thing = spans
        if anchors[1].kind == "flag":
            rule, verdict = "has flag", any(c.split()[0] == owner for c in anchors[1].where)
        elif owner in evidence.code:
            defined_here = owner in evidence.definitions.get(thing, [])
            rule, verdict = "has", defined_here or owner in evidence.mentions(thing)[0]
    elif len(anchors) == 1 and (match := IMPORT.match(shape)) and spans[0] in evidence.code:
        try:
            tree = ast.parse(evidence.code[spans[0]])
        except SyntaxError:
            return Settled(None, "", anchors)
        modules = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        modules |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        rule, verdict = "import", match.group(1) not in modules
    elif len(anchors) == 3 and ACCEPTS.match(shape) and anchors[0].kind == "command":
        command = evidence.commands.get(anchors[0].where[0]) if anchors[0].where else None
        if command is not None:
            rule, verdict = "accepts", anchors[2].text in command.flags
    return Settled(verdict, rule, anchors)


def located(anchors: list[Anchor], repo: Repository) -> list[str]:
    """Return the readable files the anchors were found in, in order: paths, definitions, mentions, scripts."""
    files: list[str] = []
    for anchor in anchors:
        for where in anchor.where:
            path = where.split()[0]  # "action/agent.py publish" is a command of that script
            if path in repo.files and path not in files:
                files.append(path)
    return files
