"""The steps a check is made of, and the model-free runner.

An agent writes a check once; it is data, never code. Each step reads the
repository's tracked files, never the knowledge itself (``.okf/``,
``docs/``, READMEs, agent notes), and holds or fails. A help step runs
``--help`` of a pyproject script, or of a tracked script that builds an
argparse parser; nothing else runs. A check holds when every step holds.

Code steps need ast-grep-py and query steps jmespath, both in the
``kmaudit`` extra and imported only when such a step runs. Without
them those steps report skipped, never failed.
"""

import ast
import fnmatch
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import tomllib
from functools import cached_property
from pathlib import Path, PurePath
from types import ModuleType
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from kmaudit import AuditError

MAX_HITS = 30
#: The most matched spans a step keeps, so a broad pattern cannot bloat the store.
MAX_SPANS = 200
INSTALL = "uv tool install --force 'kmaudit @ git+https://github.com/JasperHG90/kmctl#subdirectory=packages/kmaudit'"
SKIPPED = "skipped: needs ast-grep-py or jmespath"
TEST_DIRS = {
    "tests",
    "test",
    "__tests__",
    "spec",
    "specs",
    "testdata",
    "fixtures",
    "evals",
}
TEST_FILE = re.compile(r"^(test_.*|.*_test\.\w+|.*\.(test|spec)\.\w+|conftest\.py)$")

#: What a check may read: tracked files with these extensions, outside these
#: folders and file names. The knowledge itself is left out, since a check that
#: read a claim's own words would prove nothing.
INCLUDE_EXTENSIONS = (
    ".py", ".toml", ".yaml", ".yml", ".jinja", ".sh", ".bash", ".json", ".md",
    ".hcl", ".tf", ".nomad", ".tpl", ".j2", ".go", ".js", ".mjs", ".ts", ".tsx",
    ".rs", ".java", ".rb", ".ini", ".cfg", ".conf", ".lua", ".sql",
)  # fmt: skip
EXCLUDE_DIRS = frozenset(
    {".loop", ".claude", ".vscode", ".okf", "docs", ".kmctl", ".kmaudit"}
)
EXCLUDE_PATTERNS = (
    "*.pyc",
    "*.lock",
    "*.min.js",
    "README.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "AGENTS.md",
)

LANGUAGES = {
    ".py": "python",
    ".sh": "bash",
    ".bash": "bash",
    ".js": "javascript",
    ".mjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
}
WILDCARD = re.compile(r"\$\$\$[A-Z0-9_]*|\$[A-Z][A-Z0-9_]*")
TRAILING_REST = re.compile(r",\s*\$\$\$[A-Z0-9_]*\s*\)")
SINGLE = re.compile(r"(?<!\$)\$[A-Z][A-Z0-9_]*")
LITERAL_DOLLAR = {"bash", "ruby"}


class MissingExtra(Exception):
    """A step needs a package of the ``kmaudit`` extra that is not installed."""


def extra(module: str) -> ModuleType:
    """Import ``module`` from the ``kmaudit`` extra.

    Raises
    ------
    MissingExtra
        When it is not installed.
    """
    try:
        return importlib.import_module(module)
    except ImportError as error:
        raise MissingExtra(f"{module} is not installed; {INSTALL}") from error


def is_test(path: str) -> bool:
    """Whether the path is a test, fixture or eval: a name there may assert that a thing is gone."""
    parts = path.split("/")
    return bool(TEST_DIRS & set(parts[:-1])) or bool(TEST_FILE.match(parts[-1]))


class _Step(BaseModel):
    """Base of every step: unknown keys are refused, so a typo is not silently ignored."""

    model_config = ConfigDict(extra="forbid")


class FileStep(_Step):
    """A tracked file or folder exists, or does not."""

    op: Literal["file"]
    path: str = Field(
        description="A path relative to the repository root, or a glob like action/*.sh."
    )
    exists: bool = Field(
        default=True,
        description="True: at least one tracked file matches. False: none does.",
    )


class GrepStep(_Step):
    """A Python regular expression matches a line in the matching files, or matches none."""

    op: Literal["grep"]
    pattern: str = Field(
        description="A Python regular expression, matched against each line."
    )
    paths: str = Field(
        description="A glob of tracked files to search, like src/pkg/cli.py or .github/workflows/*.yml."
    )
    present: bool = Field(
        default=True, description="True: some line matches. False: no line matches."
    )


class QueryStep(_Step):
    """A JMESPath query over YAML, TOML or JSON files gives the expected value (needs kmaudit)."""

    op: Literal["query"]
    paths: str = Field(
        description="A glob of YAML, TOML or JSON files; the query runs on each and the results join."
    )
    query: str = Field(
        description="A JMESPath query, such as jobs.*.steps[?starts_with(uses, 'x')].with.k[]."
    )
    expect: Literal["equals", "every", "contains", "not_empty", "empty"] = Field(
        description="equals: the joined result equals value. every: the result is a non-empty list whose items all "
        "equal value. contains: value is in the result. not_empty / empty: the result has something / nothing."
    )
    value: Any = Field(
        default=None,
        description="The value to compare with, for equals, every and contains.",
    )


class CodeStep(_Step):
    """Code of a given shape appears in the matching files, an ast-grep pattern (needs kmaudit).

    It tests presence only: a valid pattern can still never match what was
    meant, so "matches nothing" would pass for a broken pattern.
    """

    op: Literal["code"]
    pattern: str = Field(
        description="Code as written in the files' language, with $NAME for any one expression and $$$NAME for any "
        "run of arguments or statements: subprocess.run($$$A, timeout=120), if not $X: $$$B, sys.exit(1). It matches "
        "code only, never comments or strings, and ignores formatting. It must be a whole expression or statement. "
        "In shell and Ruby files $NAME is the variable of that name; only $$$NAME is a wildcard."
    )
    paths: str = Field(
        description="A glob of source files: Python, shell, JavaScript, TypeScript, Rust, Java, Ruby."
    )
    present: Literal[True] = Field(
        default=True,
        description="Always true: the step only tests that code is there. Test absence with grep.",
    )


class DefinitionStep(_Step):
    """A Python function, class or assigned name is defined in the matching files, or is not."""

    op: Literal["definition"]
    name: str = Field(
        description="The name: a function, class, method or module-level assignment."
    )
    paths: str = Field(description="A glob of Python files.")
    defined: bool = Field(
        default=True, description="True: some file defines it. False: none does."
    )


class ImportStep(_Step):
    """A Python file imports a module, or does not."""

    op: Literal["imports"]
    path: str = Field(
        description="A Python file, or a glob of them: imported holds when any of them imports it."
    )
    module: str = Field(description="The top-level module name, like httpx or os.")
    imported: bool = Field(
        default=True, description="True: some file imports it. False: none does."
    )


class HelpStep(_Step):
    """A repository CLI's --help output for one command matches a pattern, or does not."""

    op: Literal["help"]
    command: str = Field(
        description="The command, starting with a CLI the repository installs or a tracked argparse script: "
        "`mytool verify` or `scripts/release.py`."
    )
    pattern: str = Field(
        description="A Python regular expression searched in the help text."
    )
    present: bool = Field(
        default=True, description="True: the pattern is found. False: it is not."
    )


AnyStep = (
    FileStep | GrepStep | CodeStep | QueryStep | DefinitionStep | ImportStep | HelpStep
)
Step = Annotated[AnyStep, Field(discriminator="op")]
NEEDS_EXTRA: tuple[type[_Step], ...] = (CodeStep, QueryStep)


class Span(BaseModel):
    """Lines of one file a step matched, 1-based and inclusive."""

    path: str
    start: int
    end: int


class StepResult(BaseModel):
    """Whether one step held, and what it saw."""

    holds: bool = Field(description="Whether the step held.")
    detail: str = Field(
        description="What it matched or printed, or why it could not run."
    )
    skipped: bool = Field(
        default=False,
        description="True when it needs kmaudit, which is not installed.",
    )
    spans: list[Span] = Field(
        default_factory=list,
        description="The lines it matched: grep lines, code nodes, definitions and imports; "
        "empty for steps that test whole files.",
    )


class Repository:
    """The files a check may read: tracked by git, outside the knowledge folders and the audited one.

    Parameters
    ----------
    root :
        The repository root.
    audited :
        The folder being audited, whose pages restate the claims; a check
        never reads a file in it. None leaves only the fixed folders out.
    """

    def __init__(self, root: Path, audited: Path | None = None) -> None:
        self.root = root
        inside = (
            None
            if audited is None or audited.resolve() == root.resolve()
            else audited.resolve().relative_to(root.resolve()).as_posix() + "/"
        )
        try:
            out = subprocess.run(
                ["git", "-C", str(root), "ls-files", "-z"],
                capture_output=True,
                text=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as error:
            raise AuditError(
                f"{root} is not a git repository; checks read only git-tracked files, so run git init and commit first"
            ) from error

        self.tracked = sorted(
            f
            for f in out.stdout.split("\0")
            if f
            and not EXCLUDE_DIRS & set(f.split("/")[:-1])
            and not (inside and f.startswith(inside))
        )
        self.files = [
            f
            for f in self.tracked
            if f.endswith(INCLUDE_EXTENSIONS)
            and not any(
                fnmatch.fnmatchcase(f.rsplit("/", 1)[-1], p) for p in EXCLUDE_PATTERNS
            )
        ]
        self._help: dict[str, str] = {}
        self._hashes: dict[str, str] = {}
        self._changed: dict[str, str] = {}

    def changed(self, edits: dict[str, str | None]) -> "Repository":
        """A copy that reads ``edits`` in place of the files on disk: new text, or None for a deleted file.

        Nothing is written; it is how a mutant is run. A help step in the copy
        still sees the files on disk, so it cannot notice an edit.
        """
        _ = self.clis
        copy = object.__new__(Repository)
        copy.__dict__.update(self.__dict__)
        gone = {p for p, text in edits.items() if text is None}
        copy.tracked = [f for f in self.tracked if f not in gone]
        copy.files = [f for f in self.files if f not in gone]
        copy._changed = {
            **self._changed,
            **{p: t for p, t in edits.items() if t is not None},
        }
        copy._hashes = {}
        return copy

    def match(self, pattern: str, among: list[str] | None = None) -> list[str]:
        """The readable files matching a path or glob; a folder path matches the files under it.

        ``**/`` also matches no folder: ``src/**/*.py`` matches ``src/cli.py``.
        ``among`` is the list to match in; the readable files by default.
        """
        pattern = pattern.strip().strip("/")
        patterns = {pattern, pattern.replace("**/", "")}
        return [
            f
            for f in (self.files if among is None else among)
            if any(fnmatch.fnmatchcase(f, p) for p in patterns)
            or f.startswith(pattern + "/")
        ]

    def text(self, path: str) -> str:
        """A file's text: the edited text in a copy made by ``changed``, else the file on disk."""
        if path in self._changed:
            return self._changed[path]
        return (self.root / path).read_text(errors="replace")

    def sha(self, path: str) -> str:
        """A hash of a file's content in the working tree, or "missing" when it is not there."""
        if path not in self._hashes and path in self._changed:
            self._hashes[path] = hashlib.sha256(
                self._changed[path].encode()
            ).hexdigest()[:16]
        if path not in self._hashes:
            try:
                self._hashes[path] = hashlib.sha256(
                    (self.root / path).read_bytes()
                ).hexdigest()[:16]
            except OSError:
                self._hashes[path] = "missing"
        return self._hashes[path]

    def scripts(self) -> dict[str, str]:
        """The pyproject scripts: each command name with its entry point, like ``pkg.cli:main``."""
        try:
            data = tomllib.loads((self.root / "pyproject.toml").read_text())
        except (OSError, tomllib.TOMLDecodeError):
            return {}
        return dict(data.get("project", {}).get("scripts", {}))

    @cached_property
    def clis(self) -> set[str]:
        """The commands a help step may run: pyproject scripts, and tracked Python scripts that build an argparse parser.

        A script that builds a parser stops at ``--help`` before it does
        anything else; any other script might run in full, so it is never run.
        """
        return set(self.scripts()) | {
            f
            for f in self.files
            if f.endswith(".py")
            and not is_test(f)
            and "ArgumentParser(" in self.text(f)
        }

    def command_line(self, words: list[str]) -> list[str]:
        """How to run a repository command without installing or syncing anything.

        A tracked script runs through ``uv run --no-project --offline
        --script``. A pyproject script runs from the repository's ``.venv``
        or from PATH, never through ``uv run``, which would create ``.venv``
        or rewrite ``uv.lock``.

        Raises
        ------
        ValueError
            When a pyproject script is not installed in ``.venv`` or on PATH.
        """
        if words[0].endswith(".py"):
            return ["uv", "run", "--no-project", "--offline", "--script", *words]
        local = self.root / ".venv" / "bin" / words[0]
        found = str(local) if local.is_file() else shutil.which(words[0])
        if found is None:
            raise ValueError(
                f"{words[0]} is not installed in .venv or on PATH, so its --help cannot run; install it first"
            )
        return [found, *words[1:]]

    def help(self, command: str) -> str:
        """A repository command's --help text, run once and kept.

        Raises
        ------
        ValueError
            When the command is not a CLI of this repository.
        """
        if command not in self._help:
            words = command.split()
            if not words or words[0] not in self.clis:
                raise ValueError(
                    f"{words[0] if words else command!r} is not a CLI of this repository"
                )
            run = self.command_line(words)
            env = {**os.environ, "COLUMNS": "400", "NO_COLOR": "1", "TERM": "dumb"}
            done = subprocess.run(
                [*run, "--help"],
                cwd=self.root,
                capture_output=True,
                text=True,
                env=env,
                timeout=120,
                check=False,
            )
            self._help[command] = done.stdout
        return self._help[command]


def _load(repo: Repository, path: str) -> Any:
    """Parse a YAML, TOML or JSON file."""
    text = repo.text(path)
    if path.endswith(".toml"):
        return tomllib.loads(text)
    if path.endswith(".json"):
        return json.loads(text)
    return yaml.safe_load(text)


def _join(results: list[Any]) -> Any:
    """Join per-file query results: lists are concatenated, a single file's value is kept as it is."""
    if len(results) == 1:
        return results[0]
    joined: list[Any] = []
    for result in results:
        joined += result if isinstance(result, list) else [result]
    return joined


def python_definitions(source: str) -> set[str]:
    """The names a Python file defines: functions, classes, methods and assigned names."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names |= {t.id for t in targets if isinstance(t, ast.Name)}
    return names


def python_definition_lines(source: str, name: str) -> list[tuple[int, int]]:
    """The first and last line of each function, class or assignment in a Python file that defines ``name``."""
    found: list[tuple[int, int]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            hit = node.name == name
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            hit = any(isinstance(t, ast.Name) and t.id == name for t in targets)
        else:
            continue
        if hit:
            found.append((node.lineno, node.end_lineno or node.lineno))
    return sorted(found)


def python_import_lines(source: str, module: str) -> list[tuple[int, int]]:
    """The lines of each import statement in a Python file that imports top-level ``module``."""
    found: list[tuple[int, int]] = []
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Import)
            and any(a.name.split(".")[0] == module for a in node.names)
            or (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.split(".")[0] == module
            )
        ):
            found.append((node.lineno, node.end_lineno or node.lineno))
    return sorted(found)


def find_code(repo: Repository, pattern: str, files: list[str]) -> dict[str, Span]:
    """Where code matching an ast-grep pattern sits in ``files``: each ``path:line: text`` with the lines its node spans.

    A trailing ``, $$$`` run also matches no arguments. Files in a language
    the pattern does not parse in are skipped. In shell and Ruby, a match
    counts only if each ``$NAME`` captured exactly itself.

    Raises
    ------
    MissingExtra
        When ast-grep-py is not installed.
    ValueError
        When no file is in a known language, or the pattern parses in none of them.
    """
    sg = extra("ast_grep_py")
    by_language: dict[str, list[str]] = {}
    for f in files:
        if (language := LANGUAGES.get(PurePath(f).suffix)) is not None:
            by_language.setdefault(language, []).append(f)
    if not by_language:
        raise ValueError(f"no source file in a known language among {files[:5]}")
    patterns = {pattern, TRAILING_REST.sub(")", pattern)}
    shell_variables = SINGLE.findall(pattern)
    hits: dict[str, Span] = {}
    parses = {
        language: paths
        for language, paths in by_language.items()
        if sg.SgRoot(WILDCARD.sub("_x", pattern), language).root().find(kind="ERROR")
        is None
    }
    if not parses:
        raise ValueError(
            f"the pattern does not parse as {' or '.join(sorted(by_language))}"
        )
    for language, paths in parses.items():
        for path in paths:
            root = sg.SgRoot(repo.text(path), language).root()
            for variant in patterns:
                for node in root.find_all(pattern=variant):
                    if language in LITERAL_DOLLAR and not all(
                        (m := node.get_match(v[1:])) is not None and m.text() == v
                        for v in shell_variables
                    ):
                        continue
                    first = (
                        node.text().splitlines()[0].strip()[:120] if node.text() else ""
                    )
                    where = node.range()
                    hits[f"{path}:{where.start.line + 1}: {first}"] = Span(
                        path=path, start=where.start.line + 1, end=where.end.line + 1
                    )
    return hits


def run_step(repo: Repository, step: AnyStep) -> StepResult:
    """Run one step; a step that cannot run fails with the reason, and one that needs the extra is skipped."""
    try:
        return _run(repo, step)
    except MissingExtra:
        return StepResult(holds=False, detail=SKIPPED, skipped=True)
    except Exception as error:  # noqa: BLE001  # any library error is the step failing to run, reported as such
        return StepResult(
            holds=False, detail=f"could not run: {type(error).__name__}: {error}"
        )


def _run(repo: Repository, step: AnyStep) -> StepResult:
    """Run one step, raising when it cannot run."""
    if isinstance(step, FileStep):
        found = repo.match(step.path, among=repo.tracked)
        return StepResult(
            holds=bool(found) == step.exists,
            detail=f"{len(found)} matching: {found[:5]}",
        )
    if isinstance(step, HelpStep):
        found_help = re.search(step.pattern, repo.help(step.command), re.MULTILINE)
        return StepResult(
            holds=bool(found_help) == step.present,
            detail=found_help.group(0) if found_help else "no match",
        )
    if isinstance(step, CodeStep):
        extra("ast_grep_py")
    if isinstance(step, QueryStep):
        extra("jmespath")
    glob = step.path if isinstance(step, ImportStep) else step.paths
    files = repo.match(glob)
    if not files:
        if repo.match(glob, among=repo.tracked):
            raise ValueError(
                f"{glob!r} matches only files checks never read: READMEs, CLAUDE.md, "
                "AGENTS.md and CHANGELOG.md restate the knowledge; test the code instead, "
                "or give a reason"
            )
        raise ValueError(f"no readable tracked file matches {glob!r}")
    if isinstance(step, GrepStep):
        pattern = re.compile(step.pattern)
        matched = [
            (f, n, line)
            for f in files
            for n, line in enumerate(repo.text(f).splitlines(), 1)
            if pattern.search(line)
        ]
        hits = [f"{f}:{n}: {line.strip()[:120]}" for f, n, line in matched]
        return StepResult(
            holds=bool(hits) == step.present,
            detail=f"{len(hits)} lines: {hits[:MAX_HITS]}",
            spans=[Span(path=f, start=n, end=n) for f, n, _ in matched[:MAX_SPANS]],
        )
    if isinstance(step, CodeStep):
        found_code = find_code(repo, step.pattern, files)
        return StepResult(
            holds=bool(found_code),
            detail=f"{len(found_code)} matches: {list(found_code)[:MAX_HITS]}",
            spans=list(found_code.values())[:MAX_SPANS],
        )
    if isinstance(step, QueryStep):
        jmespath = extra("jmespath")
        result = _join([jmespath.search(step.query, _load(repo, f)) for f in files])
        return StepResult(
            holds=_expected(step, result),
            detail=f"result over {len(files)} files: {json.dumps(result, default=str)[:300]}",
        )
    if isinstance(step, DefinitionStep):
        where = [
            f
            for f in files
            if f.endswith(".py") and step.name in python_definitions(repo.text(f))
        ]
        return StepResult(
            holds=bool(where) == step.defined,
            detail=f"defined in {where[:5]}",
            spans=[
                Span(path=f, start=a, end=b)
                for f in where
                for a, b in python_definition_lines(repo.text(f), step.name)
            ][:MAX_SPANS],
        )
    importing = [
        f
        for f in files
        if f.endswith(".py") and step.module in python_imports(repo.text(f))
    ]
    return StepResult(
        holds=bool(importing) == step.imported,
        detail=f"imported by {importing[:5]} of {len(files)} files",
        spans=[
            Span(path=f, start=a, end=b)
            for f in importing
            for a, b in python_import_lines(repo.text(f), step.module)
        ][:MAX_SPANS],
    )


def python_imports(source: str) -> set[str]:
    """The top-level modules a Python file imports."""
    tree = ast.parse(source)
    modules = {
        a.name.split(".")[0]
        for n in ast.walk(tree)
        if isinstance(n, ast.Import)
        for a in n.names
    }
    modules |= {
        n.module.split(".")[0]
        for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.module
    }
    return modules


def _expected(step: QueryStep, result: Any) -> bool:
    """Whether a query's joined result is what the step expects; every needs a non-empty list."""
    if step.expect == "equals":
        return bool(result == step.value)
    if step.expect == "every":
        return (
            isinstance(result, list)
            and bool(result)
            and all(r == step.value for r in result)
        )
    if step.expect == "contains":
        return isinstance(result, list | str | dict) and step.value in result
    return bool(result) if step.expect == "not_empty" else not result


def reads(repo: Repository, steps: list[AnyStep]) -> dict[str, str]:
    """The files a check's steps read now, each with its content hash.

    A glob is matched again each time, so a file that starts or stops
    matching changes the answer. A help step reads the script it runs, or for
    an installed command pyproject.toml and the files of its package.
    """
    paths: list[str] = []
    for step in steps:
        if isinstance(step, FileStep):
            paths += repo.match(step.path, among=repo.tracked)
        elif isinstance(step, ImportStep):
            paths += repo.match(step.path)
        elif isinstance(step, HelpStep):
            words = step.command.split()
            if words and words[0].endswith(".py"):
                paths.append(words[0])
            elif words and words[0] in (scripts := repo.scripts()):
                package = scripts[words[0]].split(":")[0].split(".")[0]
                paths += [
                    "pyproject.toml",
                    *(f for f in repo.files if package in f.split("/")[:-1]),
                ]
        else:
            paths += repo.match(step.paths)
    return {p: repo.sha(p) for p in sorted(set(paths))}


def reads_key(files: dict[str, str]) -> str:
    """One hash of a set of files and their content hashes."""
    return hashlib.sha256(json.dumps(sorted(files.items())).encode()).hexdigest()[:16]


def run_check(repo: Repository, steps: list[AnyStep]) -> tuple[bool, list[StepResult]]:
    """Run every step; the check holds when each one does. A check with no steps does not hold."""
    results = [run_step(repo, step) for step in steps]
    return bool(results) and all(r.holds for r in results), results
