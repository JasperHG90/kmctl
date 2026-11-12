"""The check store: schema steps, rerunning only on change, reusing scores, and reading a check back by id."""

import json
import sqlite3
from pathlib import Path

import pytest
from fixtures.audit_repo import git, make_repo, store_claims

from kmctl.claims import check_verbs
from kmctl.claims.check_store import check
from kmctl.claims.sections import cut, resolve_target
from kmctl.claims.store import STEPS, Store
from kmctl.claims.verbs import submit, todo

CHECK = {"op": "code", "pattern": "if len(sys.argv) > 2: $$$B", "paths": "src/tool.py"}
GLOB_CHECK = {"op": "grep", "pattern": "^MAX_RETRIES = ", "paths": "src/*.py"}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return make_repo(tmp_path / "repo")


@pytest.fixture
def ids(repo: Path) -> dict[str, str]:
    return store_claims(
        repo,
        {
            "tool#parts": [
                (1, "point", "The CLI exits 1 when given more than one argument."),
                (2, "point", "Retries stop after MAX_RETRIES."),
            ]
        },
    )


def _submit(repo: Path, answers: list[dict]) -> check_verbs.SubmitChecks:
    result = check_verbs.submit(repo, json.dumps(answers))
    assert not result.refused, result.refused
    return result


@pytest.fixture
def stored(repo: Path, ids: dict[str, str]) -> dict[str, str]:
    exits, retries = ids.values()
    _submit(
        repo,
        [
            {
                "claim": exits,
                "steps": [CHECK],
                "strength": "exact",
                "why": "the condition",
            },
            {
                "claim": retries,
                "steps": [GLOB_CHECK],
                "strength": "proxy",
                "why": "the constant",
            },
        ],
    )
    return {"exits": exits, "retries": retries}


def test_new_steps_open_a_fresh_and_a_claims_only_database(tmp_path: Path) -> None:
    (tmp_path / ".kmctl").mkdir()
    db = sqlite3.connect(tmp_path / ".kmctl" / "audit.sqlite")
    for statement in STEPS[0].split(";"):
        if statement.strip():
            db.execute(statement)
    db.execute("PRAGMA user_version = 1")
    db.commit()
    db.close()

    with Store(tmp_path) as store:
        assert store.version == len(STEPS) >= 2
        tables = {r[0] for r in store.db.execute("SELECT name FROM sqlite_master")}
    assert {"checks", "check_reads", "check_runs", "check_quality", "cache"} <= tables
    with Store(tmp_path / "fresh") as store:
        assert store.version == len(STEPS)


def _reran(repo: Path) -> dict[str, bool]:
    return {
        r.claim: r.rerun
        for r in check_verbs.run(repo).claims
        if r.status not in ("no check", "reason")
    }


def test_an_unchanged_repository_reruns_nothing(
    repo: Path, stored: dict[str, str]
) -> None:
    assert _reran(repo) == {stored["exits"]: False, stored["retries"]: False}


def test_an_edited_read_file_reruns_only_its_check(
    repo: Path, stored: dict[str, str]
) -> None:
    path = repo / "ci" / "audit.yml"
    path.write_text(path.read_text() + "# touched\n")
    assert _reran(repo) == {stored["exits"]: False, stored["retries"]: False}

    tool = repo / "src" / "tool.py"
    tool.write_text(tool.read_text().replace('"hi"', '"hello"'))
    assert _reran(repo) == {stored["exits"]: True, stored["retries"]: True}


def test_a_newly_matching_glob_file_reruns_only_that_check(
    repo: Path, stored: dict[str, str]
) -> None:
    (repo / "src" / "extra.py").write_text("x = 1\n")
    git(repo, "add", "src/extra.py")

    assert _reran(repo) == {stored["exits"]: False, stored["retries"]: True}


def test_a_reworded_claim_keeps_its_check_and_reruns(
    repo: Path, stored: dict[str, str]
) -> None:
    """Re-extraction rewords a claim; its answer follows to the claim of the same sentence (ADR 0040)."""
    again = store_claims(
        repo,
        {
            "tool#parts": [
                (1, "point", "The CLI exits 1 when given two or more arguments."),
                (2, "point", "Retries stop after MAX_RETRIES."),
            ]
        },
    )
    reworded = again["The CLI exits 1 when given two or more arguments."]

    result = check_verbs.run(repo)
    rows = {r.claim: r for r in result.claims}

    assert stored["exits"] not in rows
    assert (rows[reworded].status, rows[reworded].rerun) == ("holds", True)
    assert rows[stored["retries"]].rerun is False


def test_an_answer_is_dropped_when_two_claims_share_its_sentence(
    repo: Path, stored: dict[str, str]
) -> None:
    store_claims(
        repo,
        {
            "tool#parts": [
                (1, "point", "The CLI exits 1 on two arguments."),
                (2, "point", "Retries stop after MAX_RETRIES."),
            ]
        },
    )
    # A second claim from sentence 1 makes the carry ambiguous.
    todo(repo)
    section = next(s for s in cut(resolve_target(repo)) if s.id == "tool#parts")

    verdicts = [
        {"n": 1, "kind": "point", "claims": [{"claim": "The CLI exits 1 on two arguments."},
                                             {"claim": "The CLI checks its argument count."}]},
        {"n": 2, "kind": "point", "claims": [{"claim": "Retries stop after MAX_RETRIES."}]},
        {"n": 3, "kind": "none", "claims": []},
    ]  # fmt: skip
    assert not submit(
        repo,
        json.dumps({"section": section.id, "key": section.key, "sentences": verdicts}),
    ).refused

    rows = {r.claim: r.status for r in check_verbs.run(repo).claims}

    assert list(rows.values()).count("no check") == 2


def test_a_mutation_score_is_reused_until_its_key_moves(
    repo: Path, stored: dict[str, str]
) -> None:
    assert check_verbs.run(repo).measured == 0
    assert check_verbs.run(repo, everything=True).measured == 0

    tool = repo / "src" / "tool.py"
    tool.write_text(tool.read_text() + "\n# end\n")
    assert check_verbs.run(repo).measured == 2


def test_a_check_reads_back_by_id(repo: Path, stored: dict[str, str]) -> None:
    with Store(repo) as store:
        found = check(store, stored["exits"])

    assert found is not None
    assert found.kind == "check" and found.holds is True
    assert found.steps[0].op == "code"
    assert "src/tool.py:10: if len(sys.argv) > 2:" in found.results[0].detail
    assert found.quality is not None and found.quality.killed > 0
    assert list(found.reads) == ["src/tool.py"]
