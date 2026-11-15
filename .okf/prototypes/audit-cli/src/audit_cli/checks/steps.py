"""The steps a check is made of, and the code that runs them.

A model writes a check once; it is data, never code. Each step reads the repository's tracked files (never the
knowledge itself: ``.okf/``, ``docs/``, READMEs, as the ``[files]`` settings say) and holds or fails. One step runs a
program: a help step runs ``--help`` of a pyproject script, or of a tracked script that builds an argparse parser
(which stops at ``--help``), with the subcommand words the model wrote; nothing else runs. A check holds when every
step holds.
"""

import ast
import fnmatch
import hashlib
import json
import os
import pathlib as plb
import re
import subprocess
import tomllib
from functools import cached_property
from typing import Annotated, Any, Literal

import jmespath
import yaml
from ast_grep_py import SgNode, SgRoot
from jmespath.exceptions import JMESPathError
from pydantic import BaseModel, Field

from audit_cli.config import FilesConfig

MAX_HITS = 30
TEST_DIRS = {"tests", "test", "__tests__", "spec", "specs", "testdata", "fixtures", "evals"}
TEST_FILE = re.compile(r"^(test_.*|.*_test\.\w+|.*\.(test|spec)\.\w+|conftest\.py)$")


def is_test(path: str) -> bool:
    """Whether the path is a test, fixture or eval: a name there may assert that a thing is gone."""
    parts = path.split("/")
    return bool(TEST_DIRS & set(parts[:-1])) or bool(TEST_FILE.match(parts[-1]))


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
LITERAL_DOLLAR = {"bash", "ruby"}  # where $NAME is a variable of the language, not a wildcard


class FileStep(BaseModel):
    """A tracked file or folder exists, or does not."""

    op: Literal["file"]
    path: str = Field(description="A path relative to the repository root, or a glob like action/*.sh.")
    exists: bool = Field(default=True, description="True: at least one tracked file matches. False: none does.")


class GrepStep(BaseModel):
    """A Python regular expression matches a line in the matching files, or matches none."""

    op: Literal["grep"]
    pattern: str = Field(description="A Python regular expression, matched against each line.")
    paths: str = Field(
        description="A glob of tracked files to search, like action/agent.py or .github/workflows/*.yml."
    )
    present: bool = Field(default=True, description="True: some line matches. False: no line matches.")


class QueryStep(BaseModel):
    """A JMESPath query over YAML, TOML or JSON files gives the expected value."""

    op: Literal["query"]
    paths: str = Field(description="A glob of YAML, TOML or JSON files; the query runs on each and the results join.")
    query: str = Field(description="A JMESPath query, such as jobs.*.steps[?starts_with(uses, 'x')].with.k[].")
    expect: Literal["equals", "every", "contains", "not_empty", "empty"] = Field(
        description="equals: the joined result equals value. every: the result is a non-empty list whose items all "
        "equal value. contains: value is in the result. not_empty / empty: the result has something / nothing."
    )
    value: Any = Field(default=None, description="The value to compare with, for equals, every and contains.")


class CodeStep(BaseModel):
    """Code of a given shape appears in the matching files (an ast-grep pattern).

    It tests presence only. A pattern can be valid and still never match what was meant (``timeout=120`` is an
    assignment in Python, not a keyword argument), so "matches nothing" would pass for a broken pattern; absence is
    tested with grep, definition or imports instead.
    """

    op: Literal["code"]
    pattern: str = Field(
        description="Code as written in the files' language, with $NAME for any one expression and $$$NAME for any "
        "run of arguments or statements: subprocess.run($$$A, timeout=120), if not $X: $$$B, sys.exit(1). It matches "
        "code only, never comments or strings, and ignores formatting. It must be a whole expression or statement. "
        "In shell and Ruby files $NAME is the variable of that name, matched as written; only $$$NAME is a wildcard. "
        "In shell a command with more arguments after the pattern still matches: use grep for an exact command line. "
        "Lowercase Ruby globals such as $stderr never match."
    )
    paths: str = Field(description="A glob of source files: Python, shell, JavaScript, TypeScript, Rust, Java, Ruby.")
    present: bool = Field(
        default=True, description="Must be true: the step only tests that code is there. Test absence with grep."
    )


class DefinitionStep(BaseModel):
    """A Python function, class or assigned name is defined in the matching files, or is not."""

    op: Literal["definition"]
    name: str = Field(description="The name: a function, class, method or module-level assignment.")
    paths: str = Field(description="A glob of Python files.")
    defined: bool = Field(default=True)


class ImportStep(BaseModel):
    """A Python file imports a module, or does not."""

    op: Literal["imports"]
    path: str = Field(description="A Python file, or a glob of them: imported holds when any of them imports it.")
    module: str = Field(description="The top-level module name, like kmctl or os.")
    imported: bool = Field(default=True)


class HelpStep(BaseModel):
    """A repository CLI's --help output for one command matches a pattern, or does not."""

    op: Literal["help"]
    command: str = Field(
        description="The command, starting with a CLI the repository installs or a tracked script: "
        "`kmctl verify` or `action/agent.py publish`."
    )
    pattern: str = Field(description="A Python regular expression searched in the help text.")
    present: bool = Field(default=True)


AnyStep = FileStep | GrepStep | CodeStep | QueryStep | DefinitionStep | ImportStep | HelpStep
Step = Annotated[AnyStep, Field(discriminator="op")]


class StepResult(BaseModel):
    """Whether one step held, and what it saw."""

    holds: bool
    detail: str


class Repository:
    """The files a check may read: tracked by git and allowed by the ``[files]`` settings.

    The settings leave out the knowledge itself (``.okf/``, ``docs/``, READMEs and agent notes), since a check that
    read a claim's own words would prove nothing; prompt and config files in markdown stay readable. A file step sees
    every tracked file outside the left-out folders: that one exists says nothing the claims restate.

    Parameters
    ----------
    root :
        The repository root.
    files :
        Which files are read; the defaults when None.
    """

    def __init__(self, root: plb.Path, files: FilesConfig | None = None) -> None:
        self.root = root
        settings = files or FilesConfig()
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, text=True, check=True)
        skipped = set(settings.skipped_dirs)
        self.tracked = sorted(f for f in out.stdout.split("\0") if f and not skipped & set(f.split("/")[:-1]))
        extensions = tuple(settings.include_extensions)
        patterns = settings.skipped_patterns
        self.files = [
            f
            for f in self.tracked
            if f.endswith(extensions) and not any(fnmatch.fnmatchcase(f.rsplit("/", 1)[-1], p) for p in patterns)
        ]
        self._help: dict[str, str] = {}
        self._hashes: dict[str, str] = {}
        self._changed: dict[str, str] = {}  # path: text, for a copy made by changed()

    def changed(self, edits: dict[str, str | None]) -> "Repository":
        """Return a copy that reads ``edits`` in place of the files on disk: new text, or None for a deleted file.

        Nothing is written; it is how a mutant of the code is run. A help step in the copy still sees the files on
        disk, so it cannot notice an edit.
        """
        _ = self.clis  # the help allow-list comes from the real files, never from an edited copy
        copy = object.__new__(Repository)
        copy.__dict__.update(self.__dict__)
        gone = {p for p, text in edits.items() if text is None}
        copy.tracked = [f for f in self.tracked if f not in gone]
        copy.files = [f for f in self.files if f not in gone]
        copy._changed = {**self._changed, **{p: t for p, t in edits.items() if t is not None}}
        copy._hashes = {}  # help output is shared: edits in memory never reach a CLI, which runs from disk
        return copy

    def match(self, pattern: str, among: list[str] | None = None) -> list[str]:
        """Return the readable files matching a path or glob; a folder path matches the files under it.

        ``**/`` also matches no folder, as in most globs: ``src/**/*.py`` matches ``src/cli.py``. ``among`` is the
        list to match in; the readable files (no markdown) by default.
        """
        pattern = pattern.strip().strip("/")
        patterns = {pattern, pattern.replace("**/", "")}
        return [
            f
            for f in (self.files if among is None else among)
            if any(fnmatch.fnmatchcase(f, p) for p in patterns) or f.startswith(pattern + "/")
        ]

    def text(self, path: str) -> str:
        """Return a file's text: the edited text in a copy made by changed(), else the file on disk."""
        if path in self._changed:
            return self._changed[path]
        return (self.root / path).read_text(errors="replace")

    def sha(self, path: str) -> str:
        """Return a hash of a file's content as it is in the working tree, or "missing" when it is not there."""
        if path not in self._hashes and path in self._changed:
            self._hashes[path] = hashlib.sha256(self._changed[path].encode()).hexdigest()[:16]
        if path not in self._hashes:
            try:
                self._hashes[path] = hashlib.sha256((self.root / path).read_bytes()).hexdigest()[:16]
            except OSError:
                self._hashes[path] = "missing"
        return self._hashes[path]

    def scripts(self) -> dict[str, str]:
        """Return the pyproject scripts: each command name with its entry point, like ``pkg.cli:main``."""
        try:
            data = tomllib.loads((self.root / "pyproject.toml").read_text())
        except (OSError, tomllib.TOMLDecodeError):
            return {}
        return dict(data.get("project", {}).get("scripts", {}))

    @cached_property
    def clis(self) -> set[str]:
        """The commands a help step may run: pyproject scripts, and tracked Python scripts that build an argparse parser.

        A script that builds a parser stops at ``--help`` before it does anything else; any other script might run
        in full, so it is never offered.
        """
        return set(self.scripts()) | {
            f for f in self.files if f.endswith(".py") and not is_test(f) and "ArgumentParser(" in self.text(f)
        }

    def help(self, command: str) -> str:
        """Return a repository command's --help text, run once and kept."""
        if command not in self._help:
            words = command.split()
            if not words or words[0] not in self.clis:
                raise ValueError(f"{words[0] if words else command!r} is not a CLI of this repository")
            run = ["uv", "run", "--script", *words] if words[0].endswith(".py") else ["uv", "run", *words]
            env = {**os.environ, "COLUMNS": "400", "NO_COLOR": "1", "TERM": "dumb"}
            done = subprocess.run(
                [*run, "--help"], cwd=self.root, capture_output=True, text=True, env=env, timeout=120, check=False
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


def _definitions(source: str) -> set[str]:
    """Return the names a Python file defines: functions, classes, methods and assigned names."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names |= {t.id for t in targets if isinstance(t, ast.Name)}
    return names


def find_code(repo: Repository, pattern: str, files: list[str]) -> list[str]:
    """Return where code matching an ast-grep pattern sits in ``files``, as ``path:line: text``.

    A trailing ``, $$$`` run also matches no arguments, as ast-grep alone does not. Files in a language the pattern
    does not parse in are skipped (``exit 1`` is shell, not Python); a pattern that parses in none of the files'
    languages raises. In shell and Ruby, ast-grep would read ``$TOKEN`` as a wildcard; a match counts only if each
    such variable captured exactly itself, so ``$TOKEN`` never stands for ``$OTHER`` or ``$TOKEN_OLD``.
    """
    by_language: dict[str, list[str]] = {}
    for f in files:
        if (language := LANGUAGES.get(plb.PurePath(f).suffix)) is not None:
            by_language.setdefault(language, []).append(f)
    if not by_language:
        raise ValueError(f"no source file in a known language among {files[:5]}")
    patterns = {pattern, TRAILING_REST.sub(")", pattern)}
    shell_variables = SINGLE.findall(pattern)
    hits: dict[str, None] = {}
    parses = {
        language: paths
        for language, paths in by_language.items()
        if SgRoot(WILDCARD.sub("_x", pattern), language).root().find(kind="ERROR") is None
    }
    if not parses:
        raise ValueError(f"the pattern does not parse as {' or '.join(sorted(by_language))}")
    for language, paths in parses.items():
        for path in paths:
            root = SgRoot(repo.text(path), language).root()
            for variant in patterns:
                for node in root.find_all(pattern=variant):
                    if language in LITERAL_DOLLAR and not all(
                        (m := node.get_match(v[1:])) is not None and m.text() == v for v in shell_variables
                    ):
                        continue
                    first = node.text().splitlines()[0].strip()[:120] if node.text() else ""
                    hits[f"{path}:{node.range().start.line + 1}: {first}"] = None
    return list(hits)


TS_KINDS = (
    "function_declaration",
    "class_declaration",
    "abstract_class_declaration",
    "method_definition",
    "abstract_method_signature",
    "interface_declaration",
    "enum_declaration",
    "type_alias_declaration",
    "variable_declarator",
)
OUTLINE_KINDS = {
    "python": ("function_definition", "class_definition"),
    "javascript": ("function_declaration", "class_declaration", "method_definition", "variable_declarator"),
    "typescript": TS_KINDS,
    "tsx": TS_KINDS,
    "rust": ("function_item", "struct_item", "enum_item", "impl_item", "trait_item", "mod_item"),
    "java": ("class_declaration", "interface_declaration", "method_declaration"),
    "ruby": ("class", "module", "method", "singleton_method"),
    "bash": ("function_definition",),
}
OUTLINE_YAML_DEPTH = 4


def outline(repo: Repository, path: str) -> list[str]:
    """Return a source file's functions and classes, or a YAML file's keys, each as ``start-end: first line``.

    A YAML key whose value fits on its line shows the value too.

    Nesting is shown by indentation: a method under its class, a workflow step's keys under its job. YAML keys go
    four levels deep. Other files have no outline and raise.
    """
    suffix = plb.PurePath(path).suffix
    text = repo.text(path)
    if suffix in {".yml", ".yaml"}:
        root = SgRoot(text, "yaml").root()
        rows = []
        for node in root.find_all(kind="block_mapping_pair"):
            depth = sum(a.kind() == "block_mapping_pair" for a in node.ancestors())
            if depth < OUTLINE_YAML_DEPTH and (key := node.field("key")) is not None:
                span = f"{node.range().start.line + 1}-{node.range().end.line + 1}"
                value = node.field("value")
                inline = value is not None and value.range().start.line == node.range().start.line
                short = f": {value.text()[:80]}" if inline and value is not None and "\n" not in value.text() else ""
                rows.append(f"{'  ' * depth}{span}: {key.text()}{short}")
        return rows
    language = LANGUAGES.get(suffix)
    if language is None:
        raise ValueError(f"no outline for {path}: read it instead")
    kinds = OUTLINE_KINDS[language]
    root = SgRoot(text, language).root()
    nodes = sorted(
        (
            n
            for kind in kinds
            for n in root.find_all(kind=kind)
            if kind != "variable_declarator" or _is_arrow(n)  # const f = (x) => x is a function; other consts are not
        ),
        key=lambda n: (n.range().start.line, n.range().start.column),
    )

    def place(n: SgNode) -> tuple[int, int, int, int]:
        """Return where a node sits, to tell the kept nodes from the left-out ones."""
        r = n.range()
        return r.start.line, r.start.column, r.end.line, r.end.column

    kept = {place(n) for n in nodes}
    rows = []
    for node in nodes:
        # only listed parents indent: a plain const is left out, and a class body spans the same place as its class
        depth = sum(a.kind() in kinds and place(a) in kept for a in node.ancestors())
        first = node.text().splitlines()[0].strip()[:120]
        parent = node.parent()
        start = parent if parent is not None and parent.kind() == "decorated_definition" else node  # decorators too
        rows.append(f"{'  ' * depth}{start.range().start.line + 1}-{node.range().end.line + 1}: {first}")
    return rows


def _is_arrow(node: SgNode) -> bool:
    """Whether a JavaScript or TypeScript variable is assigned an arrow function or a function expression."""
    value = node.field("value")
    return value is not None and value.kind() in {"arrow_function", "function_expression", "function"}


def run_step(repo: Repository, step: AnyStep) -> StepResult:
    """Run one step; a step that cannot run (a bad pattern, no matching file) fails with the reason."""
    try:
        return _run(repo, step)
    except (
        re.error,
        JMESPathError,
        ValueError,
        SyntaxError,
        RuntimeError,
        OSError,
        yaml.YAMLError,
        subprocess.TimeoutExpired,
    ) as error:
        return StepResult(holds=False, detail=f"could not run: {type(error).__name__}: {error}")


def _run(repo: Repository, step: AnyStep) -> StepResult:
    """Run one step, raising when it cannot run."""
    if isinstance(step, FileStep):
        found = repo.match(step.path, among=repo.tracked)  # that a markdown file exists is not its content
        return StepResult(holds=bool(found) == step.exists, detail=f"{len(found)} matching: {found[:5]}")
    if isinstance(step, HelpStep):
        found_help = re.search(step.pattern, repo.help(step.command), re.MULTILINE)
        return StepResult(
            holds=bool(found_help) == step.present, detail=found_help.group(0) if found_help else "no match"
        )
    files = repo.match(step.path if isinstance(step, ImportStep) else step.paths)
    if not files:
        raise ValueError(
            f"no readable tracked file matches {step.path if isinstance(step, ImportStep) else step.paths!r}"
        )
    if isinstance(step, GrepStep):
        pattern = re.compile(step.pattern)
        hits = [
            f"{f}:{n}: {line.strip()[:120]}"
            for f in files
            for n, line in enumerate(repo.text(f).splitlines(), 1)
            if pattern.search(line)
        ]
        return StepResult(holds=bool(hits) == step.present, detail=f"{len(hits)} lines: {hits[:5]}")
    if isinstance(step, CodeStep):
        if not step.present:
            raise ValueError("a code step tests only that code is there; test absence with grep")
        found_code = find_code(repo, step.pattern, files)
        return StepResult(holds=bool(found_code) == step.present, detail=f"{len(found_code)} matches: {found_code[:5]}")
    if isinstance(step, QueryStep):
        result = _join([jmespath.search(step.query, _load(repo, f)) for f in files])
        holds = _expected(step, result)
        return StepResult(
            holds=holds, detail=f"result over {len(files)} files: {json.dumps(result, default=str)[:300]}"
        )
    if isinstance(step, DefinitionStep):
        where = [f for f in files if f.endswith(".py") and step.name in _definitions(repo.text(f))]
        return StepResult(holds=bool(where) == step.defined, detail=f"defined in {where[:5]}")
    importing = []
    for path in (f for f in files if f.endswith(".py")):
        tree = ast.parse(repo.text(path))
        modules = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        modules |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        if step.module in modules:
            importing.append(path)
    return StepResult(
        holds=bool(importing) == step.imported, detail=f"imported by {importing[:5]} of {len(files)} files"
    )


def _expected(step: QueryStep, result: Any) -> bool:
    """Whether a query's joined result is what the step expects; every needs a non-empty list."""
    if step.expect == "equals":
        return bool(result == step.value)
    if step.expect == "every":
        return isinstance(result, list) and bool(result) and all(r == step.value for r in result)
    if step.expect == "contains":
        return isinstance(result, list | str | dict) and step.value in result
    return bool(result) if step.expect == "not_empty" else not result


def reads(repo: Repository, steps: list[Step]) -> dict[str, str]:
    """Return the files a check's steps read now, each with its content hash.

    A glob is matched again each time, so a file that starts or stops matching changes the answer. A help step reads
    the script it runs, or for an installed command pyproject.toml and the files of the package its entry point names.
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
                paths += ["pyproject.toml", *(f for f in repo.files if package in f.split("/")[:-1])]
        else:
            paths += repo.match(step.paths)
    return {p: repo.sha(p) for p in sorted(set(paths))}


def reads_key(files: dict[str, str]) -> str:
    """Return one hash of a set of files and their content hashes."""
    return hashlib.sha256(json.dumps(sorted(files.items())).encode()).hexdigest()[:16]


def run_check(repo: Repository, steps: list[Step]) -> tuple[bool, list[StepResult]]:
    """Run every step; the check holds when each one does. A check with no steps does not hold."""
    results = [run_step(repo, step) for step in steps]
    return bool(results) and all(r.holds for r in results), results
