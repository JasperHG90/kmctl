"""Code coverage by claims: which lines the stored checks matched and what counts as code, as the coverage MCP tool reports them."""

import json
from pathlib import Path

import pytest
from kmaudit import AuditError, check_verbs
from kmaudit.coverage import code_files, coverage
from kmaudit.steps import Repository

from .fixtures.audit_repo import git, make_repo, store_claims

EXITS = "The CLI exits 1 when given more than one argument."
RETRIES = "The tool retries at most MAX_RETRIES times."
CODE = {"op": "code", "pattern": "if len(sys.argv) > 2: $$$B", "paths": "src/tool.py"}
GREP = {"op": "grep", "pattern": "^MAX_RETRIES = 3$", "paths": "src/tool.py"}


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = make_repo(tmp_path / "repo")
    (root / "tests").mkdir()
    (root / "tests" / "test_tool.py").write_text("def test_x():\n    assert True\n")
    (root / "uv.lock").write_text("lock\n")
    (root / ".github" / "skills" / "okf").mkdir(parents=True)
    (root / ".github" / "skills" / "okf" / "SKILL.md").write_text("# installed\n")
    git(root, "add", ".")
    git(
        root,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.com",
        "commit",
        "-qm",
        "more",
    )
    monkeypatch.chdir(root)
    return root


def answer(root: Path, *answers: dict) -> None:
    result = check_verbs.submit(root, json.dumps(list(answers)))
    assert not result.refused, result.refused


@pytest.fixture
def ids(repo: Path) -> dict[str, str]:
    found = store_claims(
        repo, {"tool#parts": [(1, "point", EXITS), (2, "point", RETRIES)]}
    )
    return {"exits": found[EXITS], "retries": found[RETRIES]}


def test_code_leaves_out_tests_lock_files_installed_packages_and_knowledge(
    repo: Path,
) -> None:
    files = code_files(Repository(repo))

    assert "src/tool.py" in files
    assert not [
        f for f in files if f.startswith(("tests/", ".okf/", ".github/skills/"))
    ]
    assert "uv.lock" not in files


def test_a_line_counts_once_a_check_matched_it(repo: Path, ids: dict[str, str]) -> None:
    answer(
        repo,
        {"claim": ids["exits"], "steps": [CODE], "strength": "exact", "why": "w"},
        {"claim": ids["retries"], "steps": [GREP], "strength": "proxy", "why": "w"},
    )

    tool = next(f for f in coverage(repo).by_file if f.path == "src/tool.py")

    assert sorted(tool.hits) == [4, 10, 11]
    assert tool.hits[10].claims == [ids["exits"]]
    assert tool.lines == 9  # twelve lines, three of them blank
    assert tool.covered == 3
    assert set(tool.read_by) == {ids["exits"], ids["retries"]}


def test_a_check_that_shows_drift_marks_its_lines(
    repo: Path, ids: dict[str, str]
) -> None:
    gone = {"op": "code", "pattern": "sys.exit(3)", "paths": "src/tool.py"}
    answer(
        repo,
        {
            "claim": ids["exits"],
            "steps": [CODE, gone],
            "strength": "exact",
            "why": "w",
            "drift": "it exits 1",
        },
    )

    tool = next(f for f in coverage(repo).by_file if f.path == "src/tool.py")

    assert tool.hits[10].drift is True


def test_a_reason_covers_nothing(repo: Path, ids: dict[str, str]) -> None:
    answer(repo, {"claim": ids["exits"], "reason": "no step fits"})

    assert coverage(repo).covered == 0


def test_coverage_refuses_a_folder_with_no_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(AuditError, match="give a folder of markdown docs"):
        coverage(Path("."))


def test_a_run_on_files_that_changed_since_is_stale_and_not_counted(
    repo: Path, ids: dict[str, str]
) -> None:
    answer(
        repo, {"claim": ids["exits"], "steps": [CODE], "strength": "exact", "why": "w"}
    )
    tool = repo / "src" / "tool.py"
    tool.write_text("# moved\n# down\n" + tool.read_text())

    stale = coverage(repo)
    check_verbs.run(repo)
    fresh = coverage(repo)

    assert (stale.covered, stale.stale) == (0, 1)
    tool_cov = next(f for f in fresh.by_file if f.path == "src/tool.py")
    assert (fresh.stale, sorted(tool_cov.hits)) == (0, [12, 13])


def test_a_tracked_file_deleted_from_disk_is_left_out(
    repo: Path, ids: dict[str, str]
) -> None:
    answer(
        repo, {"claim": ids["exits"], "steps": [CODE], "strength": "exact", "why": "w"}
    )
    (repo / "src" / "tool.py").unlink()

    measured = coverage(repo)

    assert "src/tool.py" not in [f.path for f in measured.by_file]
    assert measured.stale == 1


def test_a_run_skipped_for_a_missing_extra_does_not_mark_lines_failing(
    repo: Path, ids: dict[str, str]
) -> None:
    from kmaudit.check_store import save_run
    from kmaudit.steps import SKIPPED, Span, StepResult
    from kmaudit.store import Store

    answer(
        repo, {"claim": ids["exits"], "steps": [CODE], "strength": "exact", "why": "w"}
    )
    with Store(repo) as store:
        from kmaudit.check_store import check

        stored = check(store, ids["exits"])
        assert stored is not None
        save_run(
            store,
            ids["exits"],
            stored.reads,
            stored.reads_key or "",
            False,
            [
                StepResult(
                    holds=False,
                    detail=SKIPPED,
                    skipped=True,
                    spans=[Span(path="src/tool.py", start=10, end=10)],
                )
            ],
        )

    tool = next(f for f in coverage(repo).by_file if f.path == "src/tool.py")

    assert tool.hits[10].drift is False
