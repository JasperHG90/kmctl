"""People's feedback on claims and checks: stored, handed back to agents with the work, and taken in by their next answer."""

import json
from pathlib import Path
from typing import Any, Literal

import pytest
from kmaudit import check_verbs, verbs
from kmaudit.feedback import FeedbackIn, latest, record
from kmaudit.store import Store
from pydantic import ValidationError

from .fixtures.audit_repo import make_repo, store_claims

CODE = {"op": "code", "pattern": "if len(sys.argv) > 2: $$$B", "paths": "src/tool.py"}
EXITS = "The CLI exits 1 when given more than one argument."
CONFIG = "The CLI reads `config.toml` on start."


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = make_repo(tmp_path / "repo")
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def ids(repo: Path) -> dict[str, str]:
    """Two claims of tool#parts: one with a check that holds, one with a reason."""
    found = store_claims(
        repo, {"tool#parts": [(1, "point", EXITS), (2, "point", CONFIG)]}
    )
    result = check_verbs.submit(
        repo,
        json.dumps(
            [
                {
                    "claim": found[EXITS],
                    "steps": [CODE],
                    "strength": "exact",
                    "why": "w",
                },
                {"claim": found[CONFIG], "reason": "Nothing reads config.toml."},
            ]
        ),
    )
    assert not result.refused, result.refused
    return {"exits": found[EXITS], "config": found[CONFIG]}


def give(
    repo: Path, claim: str, target: Literal["claim", "check"], **given: Any
) -> None:
    with Store(repo) as store:
        record(store, FeedbackIn(claim=claim, target=target, **given), "human:test")


def todo_ids(repo: Path) -> list[str]:
    return [c.id for c in check_verbs.todo(repo).claims]


def test_a_verdict_goes_on_the_check_not_the_claim() -> None:
    with pytest.raises(ValidationError, match="verdict goes on the check"):
        FeedbackIn(claim="abc", target="claim", verdict="false")


def test_feedback_on_an_unknown_claim_is_refused(
    repo: Path, ids: dict[str, str]
) -> None:
    from kmaudit import AuditError

    with Store(repo) as store, pytest.raises(AuditError, match="no stored claim"):
        record(store, FeedbackIn(claim="nope", target="claim"), "human:test")


def test_the_latest_judgment_wins_and_history_stays(
    repo: Path, ids: dict[str, str]
) -> None:
    give(repo, ids["exits"], "check", vote="up")
    give(repo, ids["exits"], "check", vote="down", note="tests the wrong line")

    with Store(repo) as store:
        now = latest(store)[(ids["exits"], "check")]
        rows = store.db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]

    assert (now.vote, now.note, now.by) == (
        "down",
        "tests the wrong line",
        "human:test",
    )
    assert now.answer is not None and now.answer["steps"] == [{**CODE, "present": True}]
    assert rows == 2


def test_a_thumbs_down_on_a_check_hands_the_claim_out_again_with_the_note(
    repo: Path, ids: dict[str, str]
) -> None:
    assert todo_ids(repo) == []

    give(repo, ids["exits"], "check", vote="down", note="pin the exit code")
    todo = check_verbs.todo(repo)

    assert [c.id for c in todo.claims] == [ids["exits"]]
    said = todo.claims[0].feedback[0]
    assert (said.on, said.vote, said.note) == ("check", "down", "pin the exit code")
    assert said.answer is not None and said.answer["kind"] == "check"
    assert (
        todo.feedback_instructions
        and "outranks your reading" in todo.feedback_instructions
    )


def test_the_next_answer_takes_the_feedback_in(repo: Path, ids: dict[str, str]) -> None:
    give(repo, ids["exits"], "check", vote="down", note="pin the exit code")

    check_verbs.submit(
        repo,
        json.dumps(
            [
                {
                    "claim": ids["exits"],
                    "steps": [CODE],
                    "strength": "exact",
                    "why": "again",
                }
            ]
        ),
    )

    assert todo_ids(repo) == []
    with Store(repo) as store:
        assert latest(store)[(ids["exits"], "check")].answered_at is not None


@pytest.mark.parametrize(
    ("verdict", "handed_out", "disagrees"),
    [("false", True, True), ("holds", False, False)],
)
def test_a_verdict_the_check_disagrees_with_sends_it_back(
    repo: Path, ids: dict[str, str], verdict: str, handed_out: bool, disagrees: bool
) -> None:
    give(repo, ids["exits"], "check", verdict=verdict)

    row = next(
        r for r in check_verbs.list_checks(repo).claims if r.claim == ids["exits"]
    )

    assert (ids["exits"] in todo_ids(repo)) is handed_out
    assert (row.status, row.human, row.disagrees) == ("holds", verdict, disagrees)


def test_a_verdict_stops_counting_when_the_files_it_was_given_on_change(
    repo: Path, ids: dict[str, str]
) -> None:
    give(repo, ids["exits"], "check", verdict="false")
    tool = repo / "src" / "tool.py"
    tool.write_text(tool.read_text().replace('"hi"', '"hello"'))

    row = next(
        r for r in check_verbs.list_checks(repo).claims if r.claim == ids["exits"]
    )

    assert (row.human, row.disagrees) == (None, False)


def test_a_thumbs_down_on_a_reason_hands_it_out_again(
    repo: Path, ids: dict[str, str]
) -> None:
    give(
        repo,
        ids["config"],
        "check",
        vote="down",
        note="a grep for config.toml settles it",
    )

    assert todo_ids(repo) == [ids["config"]]


def test_a_thumbs_down_on_a_claim_hands_its_section_out_again(
    repo: Path, ids: dict[str, str]
) -> None:
    assert (
        verbs.todo(repo, limit=None).counts.pending == 3
    )  # the fixture extracted one section

    give(repo, ids["exits"], "claim", vote="down", note="two claims in one")
    todo = verbs.todo(repo)

    assert todo.sections[0].id == "tool#parts"
    said = todo.sections[0].feedback
    assert [(f.on, f.claim, f.note) for f in said] == [
        ("claim", EXITS, "two claims in one")
    ]
    assert todo.counts.pending == 4
    assert todo.feedback_instructions is not None


def test_extracting_the_section_again_takes_the_claim_feedback_in(
    repo: Path, ids: dict[str, str]
) -> None:
    give(repo, ids["exits"], "claim", vote="down")

    store_claims(
        repo,
        {"tool#parts": [(1, "point", "The CLI exits 1 on two or more arguments.")]},
    )

    assert "tool#parts" not in [s.id for s in verbs.todo(repo).sections]


def test_answers_people_liked_are_shown_as_examples(
    repo: Path, ids: dict[str, str]
) -> None:
    give(repo, ids["exits"], "check", vote="up", note="pins the exit, not a word")
    give(repo, ids["config"], "claim", vote="up")
    give(
        repo, ids["exits"], "claim", vote="down"
    )  # a later down replaces nothing on another claim

    checks = check_verbs.todo(repo)
    claims = verbs.todo(repo)

    assert [(e.on, e.note) for e in checks.examples] == [
        ("check", "pins the exit, not a word")
    ]
    assert [(e.on, e.claim) for e in claims.examples] == [("claim", CONFIG)]


def test_feedback_follows_its_claim_when_re_extraction_rewords_it(
    repo: Path, ids: dict[str, str]
) -> None:
    give(repo, ids["exits"], "check", vote="up", note="good")
    reworded = "The CLI exits 1 when it gets more than one argument."

    new = store_claims(
        repo, {"tool#parts": [(1, "point", reworded), (2, "point", CONFIG)]}
    )
    check_verbs.todo(repo)  # prunes, carrying the answer and its feedback

    with Store(repo) as store:
        said = latest(store)
    assert (new[reworded], "check") in said
    assert (ids["exits"], "check") not in said


def test_a_stale_verdict_sends_nothing_back(repo: Path, ids: dict[str, str]) -> None:
    """A verdict that agreed when given must not push a correct failing check to hide drift later."""
    give(repo, ids["exits"], "check", verdict="holds")
    tool = repo / "src" / "tool.py"
    tool.write_text(
        tool.read_text()
        .replace("sys.exit(1)", "sys.exit(2)")
        .replace("if len(sys.argv) > 2:", "if len(sys.argv) > 3:")
    )
    check_verbs.run(repo)

    row = next(
        r for r in check_verbs.list_checks(repo).claims if r.claim == ids["exits"]
    )

    assert row.status == "fails"
    assert (row.human, row.disagrees) == (None, False)
    assert ids["exits"] not in todo_ids(repo)


def test_false_on_a_claim_with_no_check_reaches_the_agent_before_it_is_taken_in(
    repo: Path,
) -> None:
    found = store_claims(repo, {"tool#parts": [(1, "point", EXITS)]})
    claim = found[EXITS]
    give(repo, claim, "check", verdict="false", note="it exits 2 actually")

    listed = next(c for c in check_verbs.todo(repo).claims if c.id == claim)

    assert [(f.verdict, f.note) for f in listed.feedback] == [
        ("false", "it exits 2 actually")
    ]


def test_false_on_a_reason_sends_the_claim_back(
    repo: Path, ids: dict[str, str]
) -> None:
    give(repo, ids["config"], "check", verdict="false")

    assert todo_ids(repo) == [ids["config"]]


def test_a_note_alone_sends_nothing_back_but_rides_along_when_handed_out(
    repo: Path, ids: dict[str, str]
) -> None:
    give(repo, ids["exits"], "check", note="fine, but pin the exit code too")
    assert todo_ids(repo) == []

    give(
        repo, ids["exits"], "check", vote="down", note="fine, but pin the exit code too"
    )
    listed = check_verbs.todo(repo).claims[0]

    assert listed.feedback[0].note == "fine, but pin the exit code too"


def test_a_note_on_a_claim_rides_along_when_its_section_is_handed_out(
    repo: Path, ids: dict[str, str]
) -> None:
    give(repo, ids["exits"], "claim", note="say which argument count")
    concept = repo / ".okf" / "tool.md"
    concept.write_text(concept.read_text().replace("on start.", "when it starts."))

    section = next(s for s in verbs.todo(repo).sections if s.id == "tool#parts")

    assert [f.note for f in section.feedback] == ["say which argument count"]


def test_a_verdict_on_a_claim_whose_answer_read_nothing_goes_stale_on_its_lines(
    repo: Path, ids: dict[str, str]
) -> None:
    from kmaudit.ui import give_feedback

    give_feedback(
        repo,
        FeedbackIn(claim=ids["config"], target="check", verdict="false"),
        "human:test",
    )
    before = next(
        r for r in check_verbs.list_checks(repo).claims if r.claim == ids["config"]
    )
    shown = repo / "pyproject.toml"  # the file the claim's lines come from, by keyword
    shown.write_text(shown.read_text() + '\n[tool.app]\nconfig = "config.toml"\n')

    after = next(
        r for r in check_verbs.list_checks(repo).claims if r.claim == ids["config"]
    )

    assert before.human == "false"
    assert after.human is None


def test_extracting_the_section_again_marks_the_claim_feedback_answered(
    repo: Path, ids: dict[str, str]
) -> None:
    give(repo, ids["exits"], "claim", vote="down")

    store_claims(
        repo,
        {"tool#parts": [(1, "point", "The CLI exits 1 on two or more arguments.")]},
    )

    with Store(repo) as store:
        assert latest(store)[(ids["exits"], "claim")].answered_at is not None


def test_feedback_on_an_unanswered_claim_follows_it_when_reworded(repo: Path) -> None:
    found = store_claims(repo, {"tool#parts": [(1, "point", EXITS)]})
    give(repo, found[EXITS], "claim", vote="up", note="clear")
    reworded = "The CLI exits 1 when it gets more than one argument."

    new = store_claims(repo, {"tool#parts": [(1, "point", reworded)]})
    check_verbs.todo(repo)

    with Store(repo) as store:
        assert latest(store)[(new[reworded], "claim")].note == "clear"
