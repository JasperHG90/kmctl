"""The check step DSL and its model-free runner, on a real fixture repository."""

import sys
from pathlib import Path

import pytest
from fixtures.audit_repo import git, make_repo
from pydantic import TypeAdapter

from kmctl.claims.steps import (
    SKIPPED,
    AnyStep,
    Repository,
    Step,
    reads,
    reads_key,
    run_check,
    run_step,
)

STEP = TypeAdapter(Step)


@pytest.fixture
def repo(tmp_path: Path) -> Repository:
    return Repository(make_repo(tmp_path / "repo"))


def _holds(repo: Repository, step: dict) -> bool:
    result = run_step(repo, STEP.validate_python(step))
    assert not result.detail.startswith("could not run"), result.detail
    return result.holds


@pytest.mark.parametrize(
    ("step", "holds"),
    [
        ({"op": "file", "path": "src/tool.py"}, True),
        ({"op": "file", "path": "src/*.rs"}, False),
        ({"op": "file", "path": "src/gone.py", "exists": False}, True),
        ({"op": "grep", "pattern": r"sys\.exit\(1\)", "paths": "src/*.py"}, True),
        ({"op": "grep", "pattern": "subprocess", "paths": "src/*.py", "present": False}, True),
        ({"op": "grep", "pattern": "subprocess", "paths": "src/*.py"}, False),
        ({"op": "code", "pattern": "sys.exit(1)", "paths": "src/tool.py"}, True),
        ({"op": "code", "pattern": "sys.exit(2)", "paths": "src/tool.py"}, False),
        ({"op": "query", "paths": "ci/audit.yml", "query": "jobs.audit.\"runs-on\"", "expect": "equals", "value": "ubuntu-latest"}, True),
        ({"op": "query", "paths": "ci/audit.yml", "query": "jobs.audit.\"timeout-minutes\"", "expect": "equals", "value": 20}, False),
        ({"op": "definition", "name": "MAX_RETRIES", "paths": "src/*.py"}, True),
        ({"op": "definition", "name": "MIN_RETRIES", "paths": "src/*.py"}, False),
        ({"op": "imports", "path": "src/tool.py", "module": "json"}, True),
        ({"op": "imports", "path": "src/tool.py", "module": "httpx"}, False),
    ],
)  # fmt: skip
def test_each_step_holds_and_fails(repo: Repository, step: dict, holds: bool) -> None:
    assert _holds(repo, step) is holds


def test_help_step_runs_an_argparse_script(repo: Repository) -> None:
    assert _holds(
        repo, {"op": "help", "command": "scripts/release.py", "pattern": "--fast"}
    )
    assert not _holds(
        repo, {"op": "help", "command": "scripts/release.py", "pattern": "--slow"}
    )


def test_help_step_refuses_a_command_that_is_not_a_cli(repo: Repository) -> None:
    result = run_step(
        repo,
        STEP.validate_python({"op": "help", "command": "src/tool.py", "pattern": "x"}),
    )

    assert not result.holds and "not a CLI of this repository" in result.detail


@pytest.mark.parametrize("glob", ["**/*.md", ".okf/*.md", "README.md", "CHANGELOG.md"])
def test_markdown_and_okf_are_never_read(repo: Repository, glob: str) -> None:
    result = run_step(
        repo, STEP.validate_python({"op": "grep", "pattern": "out.txt", "paths": glob})
    )

    assert not result.holds
    assert "no readable tracked file" in result.detail or "never read" in result.detail


def test_untracked_files_are_never_read(repo: Repository) -> None:
    (repo.root / "src" / "new.py").write_text("SECRET = 1\n")

    assert not _holds(repo, {"op": "definition", "name": "SECRET", "paths": "src/*.py"})


def test_a_code_step_tests_presence_only() -> None:
    with pytest.raises(ValueError, match="present"):
        STEP.validate_python(
            {"op": "code", "pattern": "x()", "paths": "a.py", "present": False}
        )


def test_code_and_query_steps_skip_without_the_extra(
    repo: Repository, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "ast_grep_py", None)
    monkeypatch.setitem(sys.modules, "jmespath", None)

    for step in (
        {"op": "code", "pattern": "sys.exit(1)", "paths": "src/tool.py"},
        {
            "op": "query",
            "paths": "ci/audit.yml",
            "query": "jobs",
            "expect": "not_empty",
        },
    ):
        result = run_step(repo, STEP.validate_python(step))
        assert (result.holds, result.skipped, result.detail) == (False, True, SKIPPED)
    assert _holds(repo, {"op": "grep", "pattern": "MAX_RETRIES", "paths": "src/*.py"})
    assert _holds(repo, {"op": "definition", "name": "main", "paths": "src/*.py"})
    assert _holds(repo, {"op": "imports", "path": "src/tool.py", "module": "sys"})
    assert _holds(repo, {"op": "file", "path": "ci/audit.yml"})


def _steps(*raw: dict) -> list[AnyStep]:
    return [STEP.validate_python(s) for s in raw]


def test_a_check_holds_only_when_every_step_does(repo: Repository) -> None:
    good = {"op": "file", "path": "src/tool.py"}
    bad = {"op": "file", "path": "nope.py"}

    assert run_check(repo, _steps(good, good))[0]
    assert not run_check(repo, _steps(good, bad))[0]
    assert not run_check(repo, [])[0]


def test_reads_key_moves_with_content_and_new_glob_matches(repo: Repository) -> None:
    steps = _steps({"op": "grep", "pattern": "x", "paths": "src/*.py"})
    before = reads_key(reads(repo, steps))

    assert reads_key(reads(Repository(repo.root), steps)) == before
    (repo.root / "src" / "tool.py").write_text("x = 2\n")
    assert reads_key(reads(Repository(repo.root), steps)) != before
    edited = reads_key(reads(Repository(repo.root), steps))
    (repo.root / "src" / "more.py").write_text("y = 1\n")
    git(repo.root, "add", "src/more.py")
    assert reads_key(reads(Repository(repo.root), steps)) != edited


def test_an_excluded_file_says_checks_never_read_it(repo: Repository) -> None:
    result = run_step(
        repo,
        STEP.validate_python({"op": "grep", "pattern": "x", "paths": "CHANGELOG.md"}),
    )

    assert "never read" in result.detail and "restate the knowledge" in result.detail


def test_markdown_outside_the_knowledge_is_read(repo: Repository) -> None:
    """A skill or prompt is what the code runs, so a check may read it (ADR 0040)."""
    skill = repo.root / "skills" / "tidy" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: tidy\n---\n\nRun `tool tidy --all`.\n")
    git(repo.root, "add", "skills")

    assert _holds(
        Repository(repo.root),
        {"op": "grep", "pattern": "tool tidy --all", "paths": "skills/**/SKILL.md"},
    )


@pytest.mark.parametrize(
    ("step", "spans"),
    [
        (
            {"op": "grep", "pattern": "MAX_RETRIES", "paths": "src/tool.py"},
            [(4, 4), (9, 9)],
        ),
        (
            {
                "op": "code",
                "pattern": "if len(sys.argv) > 2: $$$B",
                "paths": "src/tool.py",
            },
            [(10, 11)],
        ),
        ({"op": "definition", "name": "main", "paths": "src/tool.py"}, [(7, 12)]),
        ({"op": "imports", "path": "src/tool.py", "module": "sys"}, [(2, 2)]),
        ({"op": "file", "path": "src/tool.py"}, []),
    ],
    ids=["grep lines", "code node", "definition", "import", "file has none"],
)
def test_each_step_records_the_lines_it_matched(
    repo: Repository, step: dict, spans: list[tuple[int, int]]
) -> None:
    result = run_step(repo, STEP.validate_python(step))

    assert result.holds, result.detail
    assert [(s.path, s.start, s.end) for s in result.spans] == [
        ("src/tool.py", a, b) for a, b in spans
    ]
