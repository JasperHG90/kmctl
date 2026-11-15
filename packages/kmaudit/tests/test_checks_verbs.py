"""The checks verbs (todo, try, submit, run and list) driven as a check-writing agent drives them through the MCP tools, and kmaudit checks list."""

import json
import socket
import sys
from pathlib import Path

import pytest
from kmaudit import AuditError, check_verbs, verbs
from kmaudit.cli import app
from typer.testing import CliRunner

from .fixtures.audit_repo import git, make_repo, store_claims

GREP_COMMENT = {"op": "grep", "pattern": "retries stop", "paths": "src/tool.py"}
CODE = {"op": "code", "pattern": "if len(sys.argv) > 2: $$$B", "paths": "src/tool.py"}
FAILING = {"op": "code", "pattern": "sys.exit(3)", "paths": "src/tool.py"}


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = make_repo(tmp_path / "repo")
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def ids(repo: Path) -> dict[str, str]:
    found = store_claims(
        repo,
        {
            "tool#parts": [
                (1, "point", "The CLI exits 1 when given more than one argument."),
                (2, "point", "The CLI reads `config.toml` on start."),
            ]
        },
    )
    exits, reads_config = found.values()
    return {"exits": exits, "config": reads_config}


def run(*args: str, stdin: str | None = None) -> tuple[int, str, str]:
    result = CliRunner().invoke(app, list(args), input=stdin)
    return result.exit_code, result.stdout, result.stderr


def check(claim: str, *steps: dict, drift: str | None = None) -> dict:
    answer = {"claim": claim, "steps": list(steps), "strength": "exact", "why": "w"}
    if drift is not None:
        answer["drift"] = drift
    return answer


def todo(limit: int | None = None, brief: bool = False) -> dict:
    """What the checks_todo tool returns, parsed."""
    found = check_verbs.todo(Path("."), limit, brief)
    return json.loads(found.model_dump_json(exclude_none=brief))


def submit(*answers: dict) -> dict:
    """What the checks_submit tool returns for ``answers``, parsed."""
    return json.loads(
        check_verbs.submit(Path("."), json.dumps(list(answers))).model_dump_json()
    )


def try_answers(answers: list[dict]) -> list[dict]:
    """What the checks_try tool returns for ``answers``, parsed."""
    return [
        t.model_dump() for t in check_verbs.try_answers(Path("."), json.dumps(answers))
    ]


def rerun(everything: bool = False) -> dict:
    """What the checks_run tool (and the page's Rerun stale checks) returns, parsed."""
    return json.loads(check_verbs.run(Path("."), everything).model_dump_json())


def test_flow_from_no_checks_to_stored_checks(repo: Path, ids: dict[str, str]) -> None:
    handed = todo()
    assert {c["id"] for c in handed["claims"]} == set(ids.values())
    assert "checks_try" in handed["instructions"]
    assert (
        handed["next"]
        == "checks_try with folder .okf, then checks_submit with folder .okf"
    )
    assert handed["answer_schema"]["anyOf"]
    exits = next(c for c in handed["claims"] if c["id"] == ids["exits"])
    assert "sys.exit(1)" in exits["lines"]["text"]

    [refused] = submit(check(ids["exits"], GREP_COMMENT))["refused"]
    assert "matched only comments or docstrings" in refused["reason"]

    stored = submit(
        check(ids["exits"], CODE),
        {"claim": ids["config"], "reason": "Nothing in the code reads config.toml."},
    )
    assert stored["refused"] == []
    assert [s["status"] for s in stored["stored"]] == ["holds", "reason"]

    assert todo()["claims"] == []

    assert rerun()["rerun"] == 0

    tool = repo / "src" / "tool.py"
    tool.write_text(tool.read_text().replace('"hi"', '"hello"'))
    result = rerun()
    assert [r["claim"] for r in result["claims"] if r["rerun"]] == [ids["exits"]]
    assert result["counts"] == {"holds": 1, "reason": 1}


def test_try_reports_holds_weak_and_misses_and_writes_nothing(
    repo: Path, ids: dict[str, str]
) -> None:
    before = (repo / ".kmaudit" / ".okf.sqlite").read_bytes()

    weak, good, failing = try_answers(
        [check(ids["exits"], GREP_COMMENT), check(ids["exits"], CODE), check(ids["exits"], FAILING)]
    )  # fmt: skip

    assert (weak["holds"], weak["weak"]) == (True, True)
    assert weak["missed"]
    assert (good["holds"], good["weak"]) == (True, False)
    assert good["killed"] > 0
    assert failing["holds"] is False
    assert (repo / ".kmaudit" / ".okf.sqlite").read_bytes() == before


def _one_refusal(answers: list[dict] | str) -> str:
    """The one reason a submit refuses ``answers`` for, the whole call's or its one answer's; nothing is stored."""
    text = answers if isinstance(answers, str) else json.dumps(answers)
    try:
        result = check_verbs.submit(Path("."), text)
    except AuditError as error:
        return str(error)
    assert result.stored == []
    [refused] = result.refused
    return refused.reason


def test_submit_refuses_a_weak_check_naming_what_it_missed(
    repo: Path, ids: dict[str, str]
) -> None:
    grep_name = {"op": "grep", "pattern": "def main", "paths": "src/tool.py"}

    err = _one_refusal([check(ids["exits"], grep_name)])

    assert "weak check" in err and "checks_try" in err


def test_submit_refuses_a_failing_check_without_drift(
    repo: Path, ids: dict[str, str]
) -> None:
    err = _one_refusal([check(ids["exits"], FAILING)])

    assert "the check fails" in err and "drift" in err


def test_submit_stores_a_failing_check_marked_drift(
    repo: Path, ids: dict[str, str]
) -> None:
    result = submit(check(ids["exits"], FAILING, drift="The CLI exits 1, not 3."))

    assert result["refused"] == []
    assert result["stored"][0]["status"] == "drift"


def test_submit_refuses_a_stale_claim_id(repo: Path, ids: dict[str, str]) -> None:
    err = _one_refusal([check("000000000000", CODE)])

    assert "call checks_todo" in err


@pytest.mark.parametrize(
    "bad",
    [
        "not json",
        json.dumps(
            {"claim": "x", "steps": [{"op": "nope"}], "strength": "exact", "why": "w"}
        ),
    ],
    ids=["not-json", "unknown-step"],
)
def test_submit_refuses_a_malformed_answer(
    repo: Path, ids: dict[str, str], bad: str
) -> None:
    err = _one_refusal(bad)

    assert "checks_todo" in err


def test_submit_refuses_a_code_step_without_the_extra(
    repo: Path, ids: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "ast_grep_py", None)

    err = _one_refusal([check(ids["exits"], CODE)])

    assert "kmaudit" in err and "uv tool install" in err


def test_submit_keeps_good_answers_in_a_mixed_file(
    repo: Path, ids: dict[str, str]
) -> None:
    result = submit(
        check(ids["exits"], FAILING),
        {"claim": ids["config"], "reason": "No code reads it."},
    )

    assert [r["claim"] for r in result["refused"]] == [ids["exits"]]
    assert [s["claim"] for s in result["stored"]] == [ids["config"]]


def test_run_reports_a_check_that_now_fails(repo: Path, ids: dict[str, str]) -> None:
    submit(check(ids["exits"], CODE))
    tool = repo / "src" / "tool.py"
    tool.write_text(tool.read_text().replace("> 2", ">= 2"))

    result = rerun()

    assert {r["claim"]: r["status"] for r in result["claims"]}[ids["exits"]] == "fails"


def test_list_shows_status_strength_and_quality(
    repo: Path, ids: dict[str, str]
) -> None:
    submit(
        check(ids["exits"], CODE),
        {"claim": ids["config"], "reason": "No code reads it."},
    )

    _, out, _ = run("checks", "list", "--json")
    rows = {r["claim"]: r for r in json.loads(out)["claims"]}

    assert rows[ids["exits"]]["status"] == "holds"
    assert rows[ids["exits"]]["strength"] == "exact"
    assert "/" in rows[ids["exits"]]["quality"]
    assert rows[ids["config"]]["reason"] == "No code reads it."
    _, out, _ = run("checks", "list", "--status", "reason", "--json")
    assert [r["claim"] for r in json.loads(out)["claims"]] == [ids["config"]]


def test_no_verb_changes_the_tree(repo: Path, ids: dict[str, str]) -> None:
    todo()
    try_answers([check(ids["exits"], CODE)])
    submit(check(ids["exits"], CODE))
    rerun(everything=True)
    run("checks", "list")

    assert git(repo, "status", "--porcelain") == ""


def test_no_verb_opens_a_network_connection(
    repo: Path, ids: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("network connection opened")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)

    todo()
    assert submit(check(ids["exits"], CODE))["refused"] == []
    rerun(everything=True)
    code, _, err = run("checks", "list")
    assert code == 0, err


def test_help_walk_and_help_steps_leave_the_tree_and_ignored_files_alone(
    repo: Path, ids: dict[str, str]
) -> None:
    """todo walks the pyproject CLI's help and try runs help steps; neither may create .venv or uv.lock."""
    help_steps = [
        check(ids["exits"], {"op": "help", "command": "tool", "pattern": "x"}),
        check(
            ids["exits"],
            {"op": "help", "command": "scripts/release.py", "pattern": "--fast"},
        ),
    ]

    todo()
    not_installed, script = try_answers(help_steps)

    assert "not installed" in not_installed["steps"][0]["detail"]
    assert script["holds"] is True
    assert git(repo, "status", "--porcelain", "--ignored") == "!! .kmaudit/\n"


def test_editing_a_section_keeps_the_checks_of_claims_that_come_back(
    repo: Path, ids: dict[str, str]
) -> None:
    submit(check(ids["exits"], CODE))
    path = repo / ".okf" / "tool.md"
    path.write_text(path.read_text().replace("on start", "at start"))
    verbs.todo(Path("."))
    todo()  # between dropping and re-extracting

    again = store_claims(
        repo,
        {
            "tool#parts": [
                (1, "point", "The CLI exits 1 when given more than one argument."),
                (2, "point", "The CLI reads `config.toml` at start."),
            ]
        },
    )

    assert again["The CLI exits 1 when given more than one argument."] == ids["exits"]
    _, out, _ = run("checks", "list", "--json")
    rows = {r["claim"]: r["status"] for r in json.loads(out)["claims"]}
    assert rows[ids["exits"]] == "holds"
    assert ids["config"] not in rows  # its text changed, so its id did too


def test_submit_refuses_drift_on_a_step_that_could_not_run(
    repo: Path, ids: dict[str, str]
) -> None:
    broken = {"op": "grep", "pattern": "(", "paths": "src/*.py"}

    err = _one_refusal([check(ids["exits"], broken, drift="The docs are wrong.")])

    assert "cannot show drift" in err


def test_a_check_with_nothing_to_change_is_not_measured(
    repo: Path, ids: dict[str, str]
) -> None:
    absent = {"op": "grep", "pattern": "zzqqxx", "paths": "src/*.py", "present": False}

    result = submit(check(ids["exits"], absent))

    assert result["refused"] == []
    assert result["stored"][0]["status"] == "not measured"
    assert rerun()["counts"]["not measured"] == 1


def test_a_skipped_check_reruns_once_the_extra_is_back(
    repo: Path, ids: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    submit(check(ids["exits"], CODE))
    tool = repo / "src" / "tool.py"
    tool.write_text(tool.read_text() + "\n")
    with monkeypatch.context() as hidden:
        hidden.setitem(sys.modules, "ast_grep_py", None)
        assert [
            r["status"] for r in rerun()["claims"] if r["claim"] == ids["exits"]
        ] == ["skipped"]

    assert [r["status"] for r in rerun()["claims"] if r["claim"] == ids["exits"]] == [
        "holds"
    ]


def test_outside_git_refuses_in_one_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "plain" / ".okf").mkdir(parents=True)
    (tmp_path / "plain" / ".okf" / "index.md").write_text(
        '---\nokf_version: "0.2"\n---\n'
    )
    monkeypatch.chdir(tmp_path / "plain")

    code, _, err = run("checks", "list")

    assert code == 1
    assert len(err.strip().splitlines()) == 1
    assert "not a git repository" in err


def test_todo_brief_leaves_out_the_instructions_and_schema(
    repo: Path, ids: dict[str, str]
) -> None:
    data = todo(limit=1, brief=True)

    assert "instructions" not in data and "answer_schema" not in data
    assert len(data["claims"]) == 1


def test_a_reason_found_by_keyword_search_does_not_go_stale_on_code_edits(
    repo: Path, ids: dict[str, str]
) -> None:
    """Only files the claim's anchors name make a reason stale, not keyword-search windows (ADR 0040)."""
    submit({"claim": ids["config"], "reason": "No code reads config.toml."})
    tool = repo / "src" / "tool.py"
    tool.write_text(tool.read_text() + "\n# touched\n")

    _, out, _ = run("checks", "list", "--json")

    assert {r["claim"]: r["status"] for r in json.loads(out)["claims"]}[
        ids["config"]
    ] == "reason"


def test_a_reason_goes_stale_when_a_file_its_anchors_name_changes(
    repo: Path, ids: dict[str, str]
) -> None:
    submit(
        {"claim": ids["exits"], "reason": "The exit is not what the sentence names."}
    )
    tool = repo / "src" / "tool.py"
    tool.write_text(tool.read_text() + "\n# touched\n")

    _, out, _ = run("checks", "list", "--json")

    assert {r["claim"]: r["status"] for r in json.loads(out)["claims"]}[
        ids["exits"]
    ] == "stale reason"


def test_a_claim_from_a_long_table_gets_only_its_rows(repo: Path) -> None:
    """A table is one sentence; a claim from it sees the rows it is about, not the whole table."""
    rows = "".join(f"| `file{i}.txt` | holds note {i} |\n" for i in range(40))
    table = (
        "| File | What |\n|---|---|\n"
        + rows
        + "| `config.toml` | the CLI reads it on start |\n"
    )
    tool = repo / ".okf" / "tool.md"
    tool.write_text(tool.read_text() + "\n## Files\n\n" + table)
    found = store_claims(
        repo, {"tool#files": [(1, "point", "The CLI reads its config on start.")]}
    )

    claim = next(c for c in todo(brief=True)["claims"] if c["id"] in found.values())
    assert "config.toml" in claim["sentence"]
    assert "file7.txt" not in claim["sentence"]
    assert [a["text"] for a in claim["anchors"]] == ["config.toml"]


@pytest.mark.parametrize(
    ("sentence", "claim", "kept", "dropped"),
    [
        # one long line is not a table: nothing to cut it at, so it comes back whole
        ("The CLI " + "reads config " * 80 + "on start.", "The CLI reads config.", None, None),
        # no line shares a word with the claim: the first SENTENCE_SHOWN characters
        ("| A | B |\n|---|---|\n" + "| x | y |\n" * 200, "Retries stop early.", "| A | B |", " ..."),
        # many rows tie: header, separator and at most three of them
        ("| Verb | Does |\n|---|---|\n" + "| `kmctl run` | writes nothing |\n" * 50,
         "kmctl writes nothing", "| Verb | Does |", None),
    ],
    ids=["one long line", "no shared word", "tied rows"],
)  # fmt: skip
def test_focus_cuts_only_long_sentences(
    sentence: str, claim: str, kept: str | None, dropped: str | None
) -> None:
    from kmaudit.check_verbs import SENTENCE_SHOWN, _focus
    from kmaudit.models import Claim

    found = _focus(
        Claim(
            id="x", section="s", concept="c", n=1, sentence=sentence, kind="point",
            claim=claim, quantifier="exists", how_to_check="", reason="", refers_to=[],
        )
    )  # fmt: skip

    if kept is None:
        assert found == sentence
    elif dropped:
        assert found.startswith(kept) and found.endswith(dropped)
        assert len(found) == SENTENCE_SHOWN + len(dropped)
    else:
        assert found.startswith(kept)
        assert len(found.splitlines()) <= 5
