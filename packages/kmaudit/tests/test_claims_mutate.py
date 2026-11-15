"""Mutation testing: a check that notices no change to the code it matched is weak."""

from pathlib import Path

import pytest
from kmaudit.mutate import TEXT_ONLY, _parses, measure, mutants
from kmaudit.steps import Repository, Step, run_check
from pydantic import TypeAdapter

from .fixtures.audit_repo import git, make_repo

STEPS = TypeAdapter(list[Step])


@pytest.fixture
def repo(tmp_path: Path) -> Repository:
    return Repository(make_repo(tmp_path / "repo"))


def _measure(repo: Repository, raw: list[dict]):
    steps = STEPS.validate_python(raw)
    holds, results = run_check(repo, steps)
    assert holds, results
    return measure(repo, steps, [r.detail for r in results])


def test_a_grep_on_a_comment_is_weak(repo: Repository) -> None:
    quality = _measure(
        repo, [{"op": "grep", "pattern": "retries stop", "paths": "src/tool.py"}]
    )

    assert quality.weak
    assert TEXT_ONLY in quality.survived


def test_a_code_step_on_the_condition_kills_its_mutants(repo: Repository) -> None:
    quality = _measure(
        repo,
        [
            {
                "op": "code",
                "pattern": "if len(sys.argv) > 2: $$$B",
                "paths": "src/tool.py",
            }
        ],
    )

    assert not quality.weak
    assert quality.killed > 0


def test_unparsable_mutants_are_dropped(repo: Repository) -> None:
    steps = STEPS.validate_python(
        [{"op": "code", "pattern": "sys.exit(1)", "paths": "src/tool.py"}]
    )
    _, results = run_check(repo, steps)

    found = mutants(repo, steps, [r.detail for r in results])

    assert found
    assert all(_parses(m.path, m.text) for m in found if m.text is not None)
    assert not _parses("a.py", "if x\n")


def test_measuring_writes_nothing_to_disk(repo: Repository) -> None:
    before = (repo.root / "src" / "tool.py").read_text()

    _measure(repo, [{"op": "code", "pattern": "sys.exit(1)", "paths": "src/tool.py"}])

    assert (repo.root / "src" / "tool.py").read_text() == before
    assert git(repo.root, "status", "--porcelain") == ""


def test_a_check_on_yaml_key_names_notices_a_renamed_key(repo: Repository) -> None:
    """A check that the job's keys exist is not weak: renaming a key is a change it notices (ADR 0040)."""
    quality = _measure(
        repo,
        [{"op": "grep", "pattern": r"^\s+timeout-minutes:", "paths": "ci/audit.yml"}],
    )

    assert not quality.weak
    assert "a YAML key renamed" in quality.killed_by
