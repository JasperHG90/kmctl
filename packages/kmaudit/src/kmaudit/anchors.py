"""What a claim names and where it is in the repository, found with no model.

Every backticked span in a claim is an anchor, resolved against the repository:

- a path: tracked now, gone (in git history only), or never tracked;
- a command of the repository's CLIs (pyproject scripts, walked through
  ``--help``; argparse scripts, read from their source), with its flags and
  defaults;
- a flag (``--x``), on the commands the claim names, else on any command;
- any other name: defined (Python ``ast``, and keys of YAML, TOML and JSON
  files), mentioned in code, mentioned only in tests, or absent.

``kmaudit checks todo`` hands an agent the anchors and the lines around
them, so a check writer sees the code it is about.
"""

import ast
import hashlib
import json
import os
import re
import subprocess
import tomllib
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, field
from typing import Any

import yaml

from kmaudit.steps import Repository, is_test, python_definitions

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
        self.dirs = {
            "/".join(f.split("/")[:i])
            for f in tracked
            for i in range(1, f.count("/") + 1)
        }
        log = subprocess.run(
            ["git", "-C", str(repo.root), "log", "--all", "--name-only", "--format="],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        self.history = set(log.split()) - tracked
        self.basenames = {f.rsplit("/", 1)[-1]: f for f in tracked}
        self.top = {f.split("/")[0] for f in tracked if "/" in f}
        self.tracked = tracked
        self.code = {
            f: repo.text(f)
            for f in sorted(self.files)
            if not f.endswith(".md") and self._is_text(f)
        }
        self.definitions = self._definitions()
        self.commands = {
            c.path: c
            for c in [
                *self._typer_commands(cache, walk_help),
                *self._argparse_commands(),
            ]
        }

    def _is_text(self, path: str) -> bool:
        """Whether the file reads as text: no NUL byte in its first 8 KiB."""
        try:
            return b"\0" not in (self.repo.root / path).read_bytes()[:8192]
        except OSError:
            return False

    def _definitions(self) -> dict[str, list[str]]:
        """Each defined name (Python function, class or assignment; YAML, TOML or JSON key) with the files that define it."""
        found: dict[str, list[str]] = {}
        for path, text in self.code.items():
            for name in _defined_names(path, text):
                found.setdefault(name, []).append(path)
        return found

    def _typer_commands(
        self,
        cache: tuple[Callable[[str], Any], Callable[[str, Any], None]] | None,
        walk_help: bool,
    ) -> list[Command]:
        """Walk each pyproject script's ``--help``, reading only its Commands and Options panels, or read the cache.

        The walk is slow (one process per command), so its result is kept under a key of pyproject.toml and the code
        of every package the scripts run: it is walked again only after one of those changes.
        """
        scripts = self.repo.scripts()
        if not walk_help or not scripts:
            return []
        packages = {entry.split(":")[0].split(".")[0] for entry in scripts.values()}
        depends = [
            "pyproject.toml",
            *(f for f in sorted(self.files) if packages & set(f.split("/")[:-1])),
        ]
        key = (
            "cli-commands:"
            + hashlib.sha256(
                json.dumps([(f, self.repo.sha(f)) for f in depends]).encode()
            ).hexdigest()
        )
        if cache is not None and (kept := cache[0](key)) is not None:
            return [Command(**c) for c in kept]
        env = {**os.environ, "COLUMNS": "400", "NO_COLOR": "1", "TERM": "dumb"}
        commands: list[Command] = []
        for cli in scripts:
            queue: list[list[str]] = [[]]
            try:
                base = self.repo.command_line([cli])
            except ValueError:
                continue  # not installed: its commands are not known
            while queue:
                words = queue.pop()
                help_text = subprocess.run(
                    [*base, *words, "--help"],
                    cwd=self.repo.root,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=120,
                    check=False,  # a command whose help fails just shows no flags
                ).stdout
                command, subcommands = _parse_rich_help(
                    " ".join([cli, *words]), help_text
                )
                commands.append(command)
                if len(words) < HELP_DEPTH:
                    queue += [[*words, sub] for sub in subcommands]
        if cache is not None:
            cache[1](key, [asdict(c) for c in commands])
        return commands

    def _argparse_commands(self) -> Iterator[Command]:
        """Read argparse parsers from the source of each tracked Python script that builds one."""
        for path, text in self.code.items():
            if (
                not path.endswith(".py")
                or "ArgumentParser(" not in text
                or is_test(path)
            ):
                continue
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            parsers: dict[str, Command] = {}
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Assign)
                    and isinstance(node.value, ast.Call)
                    and len(node.targets) == 1
                ):
                    target, call = node.targets[0], node.value
                    if not isinstance(target, ast.Name) or not isinstance(
                        call.func, ast.Attribute | ast.Name
                    ):
                        continue
                    name = (
                        call.func.attr
                        if isinstance(call.func, ast.Attribute)
                        else call.func.id
                    )
                    if name == "ArgumentParser":
                        parsers[target.id] = Command(path)
                    elif (
                        name == "add_parser"
                        and call.args
                        and isinstance(call.args[0], ast.Constant)
                    ):
                        parsers[target.id] = Command(f"{path} {call.args[0].value!s}")
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "add_argument"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in parsers
                ):
                    default = next(
                        (k.value for k in node.keywords if k.arg == "default"), None
                    )
                    shown = (
                        str(default.value)
                        if isinstance(default, ast.Constant)
                        else None
                    )
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and str(arg.value).startswith(
                            "--"
                        ):
                            parsers[node.func.value.id].flags[str(arg.value)] = shown
            yield from parsers.values()

    def mentions(self, word: str) -> tuple[list[str], list[str]]:
        """Return the code files and the test files that hold the word whole."""
        pattern = re.compile(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])")
        hits = [p for p, text in self.code.items() if pattern.search(text)]
        return [p for p in hits if not is_test(p)], [p for p in hits if is_test(p)]


def _defined_names(path: str, text: str) -> set[str]:
    """The names a file defines: Python definitions, or the keys of a YAML, TOML or JSON file at any depth."""
    try:
        if path.endswith(".py"):
            return python_definitions(text)
        if path.endswith((".yml", ".yaml")):
            data: Any = yaml.safe_load(text)
        elif path.endswith(".toml"):
            data = tomllib.loads(text)
        elif path.endswith(".json"):
            data = json.loads(text)
        else:
            return set()
    except (SyntaxError, ValueError, yaml.YAMLError):
        return set()
    names: set[str] = set()
    stack = [data]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            names |= {str(k) for k in item}
            stack += list(item.values())
        elif isinstance(item, list):
            stack += item
    return names


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
        return Anchor(
            text, "command", "missing" if missing else "found", [command.path]
        )
    if text.startswith("--"):
        flag = text.split()[0].split("=")[0]
        named = [
            c
            for c in evidence.commands.values()
            if any(c.path.startswith(n) for n in claim_commands)
        ]
        scope = named or list(evidence.commands.values())
        on = [c.path for c in scope if flag in c.flags]
        return Anchor(text, "flag", "found" if on else "missing", on)
    candidate = text.rstrip("/")
    if candidate in evidence.basenames:
        return Anchor(text, "path", "present", [evidence.basenames[candidate]])
    if (
        candidate.split("/")[0] in evidence.top
        or candidate in evidence.tracked
        or candidate in evidence.history
    ):
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
        files = [
            {p for p in evidence.definitions.get(x, []) if not is_test(p)}
            for x in parts
        ]
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


def located(anchors: list[Anchor], repo: Repository) -> list[str]:
    """Return the readable files the anchors were found in, in order: paths, definitions, mentions, scripts."""
    files: list[str] = []
    for anchor in anchors:
        for where in anchor.where:
            path = where.split()[
                0
            ]  # "action/agent.py publish" is a command of that script
            if path in repo.files and path not in files:
                files.append(path)
    return files
