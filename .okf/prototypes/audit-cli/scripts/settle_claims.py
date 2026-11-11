"""Pilot: settle stored claims without a model, from git, the repository's CLIs and tree-sitter definitions.

Every backticked span in a claim is an anchor, resolved against the repository:

- a path: tracked now, gone (tracked in git history only), or never tracked;
- a command of the repository's CLIs (pyproject scripts, walked through ``--help``; argparse scripts, read from
  their source), with its flags and defaults;
- a flag (``--x``), on the commands the claim names, else on any command;
- any other name: defined (tree-sitter), mentioned in code, mentioned only in tests, or absent.

Markdown files and ``.okf/`` are never searched: they are where claims come from, so finding a claim's words there
proves nothing. A claim gets a verdict only when its words, with the anchors taken out, match a shape whose truth
the anchors decide (it no longer exists, the default of a flag, a file has a tool or flag, a file imports a module).
Every other claim is left to a model, with what the anchors resolved to.

Run from the audit-cli folder:

    uv run python scripts/settle_claims.py --repo ../../.. [--db PATH]

Writes results/settle/claims.jsonl (one line per claim) and results/settle/summary.json, and prints the summary.
"""

import argparse
import ast
import json
import os
import pathlib as plb
import re
import sqlite3
import subprocess
import tomllib
from collections import Counter
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from typing import Any

from platformdirs import user_data_dir
from tree_sitter import Node
from tree_sitter_language_pack import get_parser

HERE = plb.Path(__file__).resolve().parent.parent
OUT = HERE / "results" / "settle"
LANGUAGES = {".py": "python", ".yml": "yaml", ".yaml": "yaml", ".toml": "toml", ".sh": "bash", ".json": "json"}
TEST_DIRS = {"tests", "test", "__tests__", "spec", "specs", "testdata", "fixtures", "evals"}
TEST_FILE = re.compile(r"^(test_.*|.*_test\.\w+|.*\.(test|spec)\.\w+|conftest\.py)$")
SPAN = re.compile(r"`([^`]+)`")
WORD = re.compile(r"[a-z][\w-]*")


def is_test(path: str) -> bool:
    """Whether the path is a test, fixture or eval: a name there may assert that a thing is gone."""
    parts = path.split("/")
    return bool(TEST_DIRS & set(parts[:-1])) or bool(TEST_FILE.match(parts[-1]))


def git(repo: plb.Path, *args: str) -> str:
    """Return a git command's output in the repository."""
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


@dataclass
class Command:
    """One command of a repository CLI, with its flags and their defaults (None when it has none or none is shown)."""

    path: str
    flags: dict[str, str | None] = field(default_factory=dict)


class Repo:
    """The repository's evidence: tracked files, git history, CLI commands, definitions and code text.

    Parameters
    ----------
    root :
        The repository root.
    exclude :
        Folder prefixes left out: copies and records of other files (``.loop/`` holds spike copies of scripts).
    """

    def __init__(self, root: plb.Path, exclude: tuple[str, ...] = ()) -> None:
        self.root = root
        tracked = set(git(root, "ls-files", "-z").split("\0")) - {""}
        self.files = {f for f in tracked if not f.startswith(exclude)}
        self.dirs = {"/".join(f.split("/")[:i]) for f in self.files for i in range(1, f.count("/") + 1)}
        self.history = set(git(root, "log", "--all", "--name-only", "--format=").split()) - tracked
        self.basenames = {f.rsplit("/", 1)[-1]: f for f in self.files}
        self.top = {f.split("/")[0] for f in self.files if "/" in f}
        self.code = {
            f: (root / f).read_text(errors="replace")
            for f in sorted(self.files)
            if not f.endswith(".md") and not f.startswith(".okf/") and (root / f).is_file() and self._is_text(root / f)
        }
        self.definitions = self._definitions()
        self.commands = {c.path: c for c in [*self._typer_commands(), *self._argparse_commands()]}

    @staticmethod
    def _is_text(path: plb.Path) -> bool:
        """Whether the file reads as text: no NUL byte in its first 8 KiB."""
        return b"\0" not in path.read_bytes()[:8192]

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

    def _typer_commands(self) -> Iterator[Command]:
        """Walk each pyproject script's ``--help``, reading only the names in its Commands and Options panels."""
        try:
            scripts = tomllib.loads((self.root / "pyproject.toml").read_text()).get("project", {}).get("scripts", {})
        except (OSError, tomllib.TOMLDecodeError):
            return
        env = {**os.environ, "COLUMNS": "400", "NO_COLOR": "1", "TERM": "dumb"}
        for cli in scripts:
            queue: list[list[str]] = [[]]
            while queue:
                words = queue.pop()
                help_text = subprocess.run(
                    ["uv", "run", cli, *words, "--help"],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    env=env,
                    check=False,  # a command whose help fails just shows no flags
                ).stdout
                command, subcommands = _parse_rich_help(" ".join([cli, *words]), help_text)
                yield command
                if len(words) < 3:
                    queue += [[*words, sub] for sub in subcommands]

    def _argparse_commands(self) -> Iterator[Command]:
        """Read argparse parsers from the source of each tracked Python script that builds one."""
        for path, text in self.code.items():
            if not path.endswith(".py") or "ArgumentParser(" not in text or is_test(path):
                continue
            parsers: dict[str, Command] = {}
            for node in ast.walk(ast.parse(text)):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and len(node.targets) == 1:
                    target, call = node.targets[0], node.value
                    if not isinstance(target, ast.Name) or not isinstance(call.func, ast.Attribute | ast.Name):
                        continue
                    name = call.func.attr if isinstance(call.func, ast.Attribute) else call.func.id
                    if name == "ArgumentParser":
                        parsers[target.id] = Command(path)
                    elif name == "add_parser" and call.args and isinstance(call.args[0], ast.Constant):
                        parsers[target.id] = Command(f"{path} {call.args[0].value!s}")
            for node in ast.walk(ast.parse(text)):
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


@dataclass
class Anchor:
    """One backticked span and what it resolved to."""

    text: str
    kind: str
    status: str
    where: list[str] = field(default_factory=list)


def resolve(repo: Repo, text: str, claim_commands: list[str]) -> Anchor:
    """Resolve one span: as a command, a flag, a path, then a name."""
    clis = {c.split()[0] for c in repo.commands}
    words = text.split()
    if len(words) > 1 and words[0] in clis:
        verbs = [words[0]]
        for word in words[1:]:
            if not WORD.fullmatch(word):
                break
            verbs.append(word)
        while len(verbs) > 1 and " ".join(verbs) not in repo.commands:
            verbs.pop()
        command = repo.commands.get(" ".join(verbs))
        flags = [w.split("=")[0] for w in words if w.startswith("--")]
        if command is None or len(verbs) < min(len(words), 2) and not flags:
            return Anchor(text, "command", "missing")
        missing = [f for f in flags if f not in command.flags and f != "--help"]
        return Anchor(text, "command", "missing" if missing else "found", [command.path])
    if text.startswith("--"):
        flag = text.split()[0].split("=")[0]
        named = [c for c in repo.commands.values() if any(c.path.startswith(n) for n in claim_commands)]
        scope = named or list(repo.commands.values())
        on = [c.path for c in scope if flag in c.flags]
        return Anchor(text, "flag", "found" if on else "missing", on)
    candidate = text.rstrip("/")
    if candidate in repo.basenames:
        return Anchor(text, "path", "present", [repo.basenames[candidate]])
    in_repo = candidate.split("/")[0] in repo.top or candidate in repo.files or candidate in repo.history
    if in_repo:
        if "*" in candidate:
            pattern = re.compile(re.escape(candidate).replace(r"\*", "[^/]*"))
            found = [f for f in repo.files if pattern.fullmatch(f)]
            return Anchor(text, "path", "present" if found else "never", found[:5])
        if candidate in repo.files or candidate in repo.dirs:
            return Anchor(text, "path", "present", [candidate])
        if candidate in repo.history:
            return Anchor(text, "path", "gone")
        return Anchor(text, "path", "never")
    parts = text.split(".")
    if len(parts) > 1 and all(WORD.fullmatch(x.lower()) for x in parts):
        files = [{p for p in repo.definitions.get(x, []) if not is_test(p)} for x in parts]
        shared = set.intersection(*files)
        if shared:
            return Anchor(text, "name", "defined", sorted(shared)[:5])
    defined = [p for p in repo.definitions.get(text, []) if not is_test(p)]
    if defined:
        return Anchor(text, "name", "defined", sorted(set(defined))[:5])
    code, tests = repo.mentions(text)
    if code:
        return Anchor(text, "name", "mentioned", code[:5])
    old = sorted(f for f in repo.history if text in f.split("/"))
    if old:
        return Anchor(text, "name", "gone", old[:5])
    if tests:
        return Anchor(text, "name", "tests only", tests[:5])
    return Anchor(text, "name", "absent")


def claim_commands(repo: Repo, spans: list[str]) -> list[str]:
    """Return the commands a claim names: a command span, or a script path whose file is a CLI."""
    found = []
    for span in spans:
        words = span.split()
        for n in range(len(words), 0, -1):
            if " ".join(words[:n]) in repo.commands:
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


def settle(repo: Repo, claim: str) -> dict[str, Any]:
    """Return the claim's verdict (true, false or None for a model), the shape that decided it, and its anchors."""
    spans = SPAN.findall(claim)
    commands = claim_commands(repo, spans)
    anchors = [resolve(repo, s, commands) for s in spans]
    shape = SPAN.sub("a", claim).strip().rstrip(".").lower()
    verdict: bool | None = None
    rule = ""
    if anchors and ABSENT.match(shape):
        rule, verdict = "absent", all(gone(a) for a in anchors)
    elif len(anchors) == 2 and DEFAULT.match(shape) and anchors[0].kind == "flag":
        defaults = {repo.commands[c].flags.get(anchors[0].text) for c in anchors[0].where if c in repo.commands}
        if len(defaults) == 1 and None not in defaults:
            rule, verdict = "default", defaults.pop() == anchors[1].text
    elif len(anchors) == 2 and HAS.match(shape) and anchors[0].kind == "path":
        owner, thing = spans
        if anchors[1].kind == "flag":
            rule, verdict = "has flag", any(c.split()[0] == owner for c in anchors[1].where)
        elif owner in repo.code:
            defined_here = owner in repo.definitions.get(thing, [])
            rule, verdict = "has", defined_here or owner in repo.mentions(thing)[0]
    elif len(anchors) == 1 and (match := IMPORT.match(shape)) and spans[0] in repo.code:
        tree = ast.parse(repo.code[spans[0]])
        modules = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        modules |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        rule, verdict = "import", match.group(1) not in modules
    elif len(anchors) == 3 and ACCEPTS.match(shape) and anchors[0].kind == "command":
        command = repo.commands.get(anchors[0].where[0]) if anchors[0].where else None
        if command is not None:
            rule, verdict = "accepts", anchors[2].text in command.flags
    return {"verdict": verdict, "rule": rule, "anchors": [asdict(a) for a in anchors]}


# Wrong versions of settled claims, each with the verdict the rules must give: a pilot that only says true proves
# nothing. Written for kmctl's repository.
MUTANTS = [
    ("`action/agent.py` no longer exists in the repository.", False),
    ("`action/knowledge-audit.sh` no longer exists in the repository.", True),
    ("The default `--min-severity` is `low`.", False),
    ("The default `--min-severity` is `high`.", True),
    ("`action/agent.py` has a `run_bash` tool.", False),
    ("`action/agent.py` has a `run_shell` tool.", True),
    ("No import of json exists in `action/agent.py`.", False),
    ("No import of kmctl exists in `action/agent.py`.", True),
    ("`kmctl verify` accepts an `ID` argument and a `--by` flag.", True),
    ("`kmctl verify` accepts an `ID` argument and a `--who` flag.", False),
]


def main() -> None:
    """Settle every stored claim and write the results."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo", type=plb.Path, required=True, help="The repository the claims describe.")
    default_db = plb.Path(user_data_dir("audit-cli")) / "projects" / "kmctl-f62c60167c76" / "audit.sqlite"
    parser.add_argument("--db", type=plb.Path, default=default_db, help="The audit-cli database holding the claims.")
    parser.add_argument(
        "--exclude", action="append", default=[".loop/"], help="A folder prefix to leave out; repeatable."
    )
    args = parser.parse_args()
    repo = Repo(args.repo.resolve(), tuple(args.exclude))
    db = sqlite3.connect(args.db)
    rows = db.execute(
        "SELECT claim_id, chunk_id, sentence_n, claim_type, claim FROM claims ORDER BY chunk_id"
    ).fetchall()
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for claim_id, chunk_id, n, kind, claim in rows:
        results.append(
            {"claim_id": claim_id, "chunk": chunk_id, "n": n, "kind": kind, "claim": claim} | settle(repo, claim)
        )
    (OUT / "claims.jsonl").write_text("".join(json.dumps(r) + "\n" for r in results))
    anchored = [r for r in results if r["anchors"]]
    summary = {
        "claims": len(results),
        "settled": Counter(str(r["verdict"]).lower() for r in results if r["verdict"] is not None),
        "settled_by_rule": Counter(r["rule"] for r in results if r["verdict"] is not None),
        "with_anchors": len(anchored),
        "every_anchor_located": sum(all(not gone(a) for a in [Anchor(**x) for x in r["anchors"]]) for r in anchored),
        "an_anchor_missing": sum(any(gone(Anchor(**x)) for x in r["anchors"]) for r in anchored),
        "anchors_by_status": Counter(f"{a['kind']}: {a['status']}" for r in results for a in r["anchors"]),
        "commands_found": len(repo.commands),
    }
    mutants = [(claim, want, settle(repo, claim)["verdict"]) for claim, want in MUTANTS]
    summary["mutants_right"] = f"{sum(want == got for _, want, got in mutants)} of {len(mutants)}"
    summary["mutants_wrong"] = [f"{claim} -> {got}" for claim, want, got in mutants if want != got]
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
