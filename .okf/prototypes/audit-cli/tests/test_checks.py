"""Tests for check steps, run against a real git repository."""

import pathlib as plb
import subprocess

import pytest
from pydantic import TypeAdapter

from audit_cli.checks.steps import Repository, Step, run_check

WORKFLOW = """
jobs:
  build:
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: false
  release:
    steps:
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: {cache}
"""


@pytest.fixture
def checked(tmp_path: plb.Path) -> plb.Path:
    """A repository with a script, a workflow, a pyproject and a concept file that repeats a claim."""
    root = tmp_path / "checked"
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".okf").mkdir()
    (root / "action").mkdir()
    (root / "action" / "agent.py").write_text(
        'import os\nimport argparse\n\n\ndef run_shell(cmd):\n    """Run a command."""\n\n\nSEVERITY = "high"\n'
    )
    (root / ".github" / "workflows" / "ci.yml").write_text(WORKFLOW.format(cache="false"))
    (root / "pyproject.toml").write_text('[project]\nname = "x"\n[project.scripts]\nx = "x:main"\n')
    (root / ".okf" / "claim.md").write_text("run_bash exists\n")
    (root / "README.md").write_text("def run_bash(): pass\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    return root


def check(repo: plb.Path, *steps: dict[str, object]) -> bool:
    """Run steps given as the model would write them, as JSON-like dicts."""
    parsed = TypeAdapter(list[Step]).validate_python(list(steps))
    holds, _ = run_check(Repository(repo), parsed)
    return holds


@pytest.mark.parametrize(
    ("step", "holds"),
    [
        ({"op": "file", "path": "action/agent.py"}, True),
        ({"op": "file", "path": "action/knowledge-audit.sh", "exists": False}, True),
        ({"op": "file", "path": "action/*.py", "exists": False}, False),
        ({"op": "file", "path": "action"}, True),
        ({"op": "file", "path": "README.md"}, True),
        ({"op": "grep", "pattern": "run_shell", "paths": "action/**/*.py"}, True),
        ({"op": "definition", "name": "run_shell", "paths": "**/*.py"}, True),
        ({"op": "grep", "pattern": r"def run_shell\(", "paths": "action/*.py"}, True),
        ({"op": "grep", "pattern": r"def run_bash", "paths": "action/*.py"}, False),
        ({"op": "definition", "name": "run_shell", "paths": "action/agent.py"}, True),
        ({"op": "definition", "name": "SEVERITY", "paths": "action/agent.py"}, True),
        ({"op": "definition", "name": "run_bash", "paths": "**", "defined": False}, True),
        ({"op": "imports", "path": "action/agent.py", "module": "kmctl", "imported": False}, True),
        ({"op": "imports", "path": "action/agent.py", "module": "os"}, True),
    ],
)
def test_each_step_holds_or_fails(checked: plb.Path, step: dict[str, object], holds: bool) -> None:
    """Each kind of step decides from the repository's tracked files."""
    assert check(checked, step) is holds


def test_markdown_and_okf_are_never_read(checked: plb.Path) -> None:
    """A claim's own words in a concept or README prove nothing, so a check never finds them there."""
    assert check(checked, {"op": "grep", "pattern": "run_bash", "paths": "*", "present": False})


def test_every_needs_a_match_and_all_items_equal(checked: plb.Path) -> None:
    """Every setup-uv step sets enable-cache false: holds when all do, fails when one does not or none exist."""
    every = {
        "op": "query",
        "paths": ".github/workflows/*.yml",
        "query": "jobs.*.steps[] | [?starts_with(uses, 'astral-sh/setup-uv')].with.\"enable-cache\"",
        "expect": "every",
        "value": False,
    }
    assert check(checked, every)
    (checked / ".github" / "workflows" / "ci.yml").write_text(WORKFLOW.format(cache="true"))
    assert not check(checked, every)
    assert not check(checked, every | {"query": "jobs.*.steps[] | [?starts_with(uses, 'nothing')].with.x"})


def test_a_step_that_cannot_run_fails_with_the_reason(checked: plb.Path) -> None:
    """A broken pattern, a broken query or a glob matching nothing fails the check rather than crashing."""
    repo = Repository(checked)
    steps = TypeAdapter(list[Step]).validate_python(
        [
            {"op": "grep", "pattern": "(", "paths": "action/agent.py"},
            {"op": "query", "paths": "pyproject.toml", "query": "project[", "expect": "not_empty"},
            {"op": "grep", "pattern": "x", "paths": "nowhere/*.py"},
        ]
    )
    holds, results = run_check(repo, steps)
    assert not holds
    assert [r.detail.split(":")[0] for r in results] == ["could not run"] * 3


def test_help_refuses_a_command_the_repository_does_not_install(checked: plb.Path) -> None:
    """Only the repository's own CLIs run, so a check cannot run any other program."""
    assert not check(checked, {"op": "help", "command": "rm -rf /", "pattern": "x"})


def test_a_check_with_no_steps_does_not_hold(checked: plb.Path) -> None:
    """An empty check proves nothing."""
    assert run_check(Repository(checked), []) == (False, [])


def test_a_guarded_query_skips_steps_without_the_key(checked: plb.Path) -> None:
    """The prompt's advice holds: uses && starts_with(...) runs past a run: step, the bare form cannot run."""
    workflow = checked / ".github" / "workflows" / "ci.yml"
    workflow.write_text(workflow.read_text().replace("    steps:\n", "    steps:\n      - run: echo hi\n", 1))
    query: dict[str, object] = {"op": "query", "paths": ".github/workflows/ci.yml", "expect": "not_empty"}
    guarded = "jobs.*.steps[] | [?uses && starts_with(uses, 'actions/checkout')]"
    assert check(checked, query | {"query": guarded})
    assert not check(checked, query | {"query": "jobs.*.steps[] | [?starts_with(uses, 'actions/checkout')]"})


CODE = {
    "action/run.py": (
        "import subprocess\nimport sys\n\n\ndef shell(cmd):\n    # subprocess.run(cmd, timeout=999)\n"
        "    return subprocess.run(\n        cmd,\n        timeout=120,\n    )\n\n\ndef main(ok):\n"
        "    if not ok:\n        sys.exit(1)\n    shell(['ls'], )\n"
    ),
    "action/run.sh": (
        'if [ -z "$TOKEN" ]; then\n  exit 1\nfi\ncurl -sS "$URL"\ncurl -sS "$TOKEN_OLD" x\ncurl -H "$TOKEN" "$URL"\n'
        'if [ -z "$OTHER" ]; then\n  echo "$TOKEN"\n  exit 1\nfi\n'
    ),
    "action/log.rb": 'logger.puts("hi")\n$stderr.puts("x")\n',
}


@pytest.fixture
def coded(checked: plb.Path) -> plb.Path:
    """The checked repository with a Python and a shell file to match code in."""
    for path, text in CODE.items():
        (checked / path).write_text(text)
    subprocess.run(["git", "-C", str(checked), "add", "."], check=True)
    return checked


@pytest.mark.parametrize(
    ("pattern", "paths", "present", "holds"),
    [
        ("subprocess.run($$$A, timeout=120)", "action/*.py", True, True),
        ("subprocess.run($$$A, timeout=120, $$$B)", "action/*.py", True, True),
        ("subprocess.run($$$A, timeout=999)", "action/*.py", True, False),
        ("if not $X: $$$B", "action/run.py", True, True),
        ("sys.exit(1)", "action/**/*.py", True, True),
        ("def shell($$$P): $$$B", "action/run.py", True, True),
        ("exit 1", "action/run.sh", True, True),
        ('curl $$$A "$URL"', "action/run.sh", True, True),
        ("exit 2", "action/*", True, False),
        ('curl $$$A "$NOPE"', "action/run.sh", True, False),
        ('curl -sS "$TOKEN" $$$A', "action/run.sh", True, False),
        ('curl -H "$URL" "$TOKEN"', "action/run.sh", True, False),
        ('curl -H "$TOKEN" "$URL"', "action/run.sh", True, True),
        ('if [ -z "$OTHER" ]; then\n  $$$B\nfi', "action/run.sh", True, True),
        ('if [ -z "$NOBODY" ]; then\n  $$$B\nfi', "action/run.sh", True, False),
        ("$STDOUT.puts($A)", "action/log.rb", True, False),
        ("subprocess.run($$$A, timeout=120 $$$B)", "action/*", True, False),
    ],
)
def test_code_matches_by_shape_not_by_text(
    coded: plb.Path, pattern: str, paths: str, present: bool, holds: bool
) -> None:
    """A code step matches code over line breaks, skips comments, reads shell as well as Python, and takes a shell
    variable as written rather than as a wildcard."""
    assert check(coded, {"op": "code", "pattern": pattern, "paths": paths, "present": present}) is holds


@pytest.mark.parametrize("pattern", ["def (", "subprocess.run(", ""])
def test_a_code_pattern_that_does_not_parse_cannot_run(coded: plb.Path, pattern: str) -> None:
    """A broken pattern says why it cannot run, rather than reporting no match."""
    holds, results = run_check(
        Repository(coded),
        TypeAdapter(list[Step]).validate_python([{"op": "code", "pattern": pattern, "paths": "action/run.py"}]),
    )
    assert not holds
    assert results[0].detail.startswith("could not run")


def test_every_mapped_language_parses() -> None:
    """Each language the code step maps a suffix to is one ast-grep knows, so no file can crash it."""
    from ast_grep_py import SgRoot

    from audit_cli.checks.steps import LANGUAGES

    for language in set(LANGUAGES.values()):
        assert SgRoot("x", language).root() is not None


@pytest.mark.parametrize(
    "pattern",
    ["timeout=120", "subprocess.run($$$A, timeout=120 $$$B)", "sys.exit(2)"],
)
def test_a_code_step_never_tests_absence(coded: plb.Path, pattern: str) -> None:
    """A valid pattern can still miss what was meant (timeout=120 is an assignment), so absence is refused."""
    step = {"op": "code", "pattern": pattern, "paths": "action/*", "present": False}
    holds, results = run_check(Repository(coded), TypeAdapter(list[Step]).validate_python([step]))
    assert not holds
    assert results[0].detail.startswith("could not run")


def test_a_tracked_file_missing_from_disk_fails_the_step(coded: plb.Path) -> None:
    """A file git tracks but the working tree lacks makes the step fail with the reason, not crash the run."""
    (coded / "action" / "run.py").unlink()
    holds, results = run_check(
        Repository(coded),
        TypeAdapter(list[Step]).validate_python([{"op": "code", "pattern": "sys.exit(1)", "paths": "action/run.py"}]),
    )
    assert not holds
    assert results[0].detail.startswith("could not run")


def test_outline_lists_definitions_nested_and_yaml_keys_with_short_values(coded: plb.Path) -> None:
    """A Python file's functions come with their lines; a workflow's keys come nested, short values shown."""
    from audit_cli.checks.steps import outline

    repo = Repository(coded)
    assert outline(repo, "action/run.py") == ["5-10: def shell(cmd):", "13-16: def main(ok):"]
    rows = outline(repo, ".github/workflows/ci.yml")
    assert rows[:3] == ["2-14: jobs", "  3-8: build", "    4-8: steps"]
    assert "      5-5: uses: actions/checkout@v4" in rows
    assert "      7-8: with" in rows  # a value on the next lines is not shown as the key's value
    with pytest.raises(ValueError, match="no outline"):
        outline(repo, "pyproject.toml")


OUTLINED = {
    "action/deco.py": "import functools\n\n\n@functools.cache\ndef cached(x):\n    return x\n\n\nclass A:\n    class B:\n"
    "        def m(self):\n            pass\n",
    "action/ui.ts": "const arrow = (x: number) => x;\nconst n = 1;\nenum E { A }\ntype Al = string;\n"
    "abstract class Ab {\n  abstract g(): void;\n}\nconst obj = {\n  m() {},\n};\n",
}


@pytest.mark.parametrize(
    ("path", "rows"),
    [
        ("action/deco.py", ["4-6: def cached(x):", "9-12: class A:", "  10-12: class B:", "    11-12: def m(self):"]),
        (
            "action/ui.ts",
            [
                "1-1: arrow = (x: number) => x",
                "3-3: enum E { A }",
                "4-4: type Al = string;",
                "5-7: abstract class Ab {",
                "  6-6: abstract g(): void",
                "9-9: m() {}",  # under a plain const, which is not listed, so not indented
            ],
        ),
    ],
)
def test_outline_keeps_decorators_nesting_and_typescript_forms(checked: plb.Path, path: str, rows: list[str]) -> None:
    """A decorated function's range starts at its decorator; nested classes nest; TS arrows, enums, aliases and
    abstract classes are listed, a plain const is not."""
    from audit_cli.checks.steps import outline

    for name, text in OUTLINED.items():
        (checked / name).write_text(text)
    subprocess.run(["git", "-C", str(checked), "add", "."], check=True)
    assert outline(Repository(checked), path) == rows


def test_prompt_markdown_is_read_but_the_knowledge_is_not(checked: plb.Path) -> None:
    """A prompt file in markdown is code a check may read; READMEs and .okf/ stay out."""
    (checked / ".github" / "prompts").mkdir(parents=True)
    (checked / ".github" / "prompts" / "triage.md").write_text("Write under 200 tokens.\n")
    subprocess.run(["git", "-C", str(checked), "add", "."], check=True)
    repo = Repository(checked)
    assert ".github/prompts/triage.md" in repo.files
    assert "README.md" not in repo.files and not any(f.startswith(".okf/") for f in repo.files)
    assert check(checked, {"op": "grep", "pattern": "200 tokens", "paths": ".github/prompts/*.md"})


def test_reads_follow_globs_and_content(checked: plb.Path) -> None:
    """A check's reads are the files its steps match now, with content hashes that change with the file."""
    from audit_cli.checks.steps import reads, reads_key

    steps = TypeAdapter(list[Step]).validate_python(
        [{"op": "grep", "pattern": "x", "paths": "action/*.py"}, {"op": "file", "path": "pyproject.toml"}]
    )
    before = reads(Repository(checked), steps)
    assert set(before) == {"action/agent.py", "pyproject.toml"}
    (checked / "action" / "agent.py").write_text("changed = 1\n")
    after = reads(Repository(checked), steps)
    assert after["pyproject.toml"] == before["pyproject.toml"] and after["action/agent.py"] != before["action/agent.py"]
    (checked / "action" / "new.py").write_text("y = 2\n")
    subprocess.run(["git", "-C", str(checked), "add", "."], check=True)
    assert "action/new.py" in reads(Repository(checked), steps)
    assert reads_key(before) != reads_key(after)


def test_a_help_step_reads_the_package_its_command_runs(checked: plb.Path) -> None:
    """A help step on an installed command depends on pyproject.toml and the package its entry point names."""
    from audit_cli.checks.steps import reads

    (checked / "x").mkdir()
    (checked / "x" / "cli.py").write_text("def main(): pass\n")
    subprocess.run(["git", "-C", str(checked), "add", "."], check=True)
    steps = TypeAdapter(list[Step]).validate_python([{"op": "help", "command": "x", "pattern": "y"}])
    assert set(reads(Repository(checked), steps)) == {"pyproject.toml", "x/cli.py"}


def test_a_help_step_never_runs_a_script_that_builds_no_parser(checked: plb.Path) -> None:
    """A tracked script with no argparse parser might do its work on --help, so a help step refuses to run it."""
    marker = checked / "ran.txt"
    (checked / "action" / "spend.py").write_text(f"open({str(marker)!r}, 'w').write('spent')\n")
    subprocess.run(["git", "-C", str(checked), "add", "."], check=True)
    holds, results = run_check(
        Repository(checked),
        TypeAdapter(list[Step]).validate_python([{"op": "help", "command": "action/spend.py", "pattern": "x"}]),
    )
    assert not holds and results[0].detail.startswith("could not run") and not marker.exists()


def test_an_imports_step_over_a_glob_reads_every_file(checked: plb.Path) -> None:
    """imported holds when any matched file imports the module, and not imported only when none does."""
    (checked / "action" / "b.py").write_text("import yaml\n")
    subprocess.run(["git", "-C", str(checked), "add", "."], check=True)
    assert check(checked, {"op": "imports", "path": "action/*.py", "module": "yaml"})
    assert not check(checked, {"op": "imports", "path": "action/*.py", "module": "yaml", "imported": False})
