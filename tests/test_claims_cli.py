"""kmctl audit claims todo, submit and list, driven as an agent would drive them."""

import json
import socket
from pathlib import Path

import pytest
from fixtures.audit_repo import git, make_repo
from typer.testing import CliRunner

from kmctl import app


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = make_repo(tmp_path / "repo")
    monkeypatch.chdir(root)
    return root


def run(*args: str, stdin: str | None = None) -> tuple[int, str, str]:
    result = CliRunner().invoke(app, list(args), input=stdin)
    return result.exit_code, result.stdout, result.stderr


def todo(*args: str) -> dict:
    code, out, err = run("audit", "claims", "todo", *args, "--json")
    assert code == 0, err
    return json.loads(out)


def answer(section: dict, kind: str = "point") -> dict:
    """A valid answer for ``section``: one claim per sentence, or none."""
    return {
        "section": section["id"],
        "key": section["key"],
        "sentences": [
            {
                "n": s["n"],
                "how_to_check": "open the file" if kind != "none" else "",
                "reason": "names a file",
                "kind": kind,
                "claims": [
                    {"claim": f"{section['id']} claim {s['n']}", "quantifier": "exists"}
                ]
                if kind != "none"
                else [],
            }
            for s in section["sentences"]
        ],
    }


def submit_all() -> None:
    sections = todo()["sections"]
    code, _, err = run(
        "audit",
        "claims",
        "submit",
        "-",
        stdin=json.dumps([answer(s) for s in sections]),
    )
    assert code == 0, err


def test_todo_first_run_lists_every_section_with_key_and_instructions(
    repo: Path,
) -> None:
    result = todo()

    assert [s["id"] for s in result["sections"]] == [
        "decisions/0001-use-sqlite#decision",
        "decisions/0001-use-sqlite#correction-2026-01-02",
        "tool#parts",
        "tool#values",
    ]
    assert (
        "kind" in result["instructions"]
        and "kmctl audit claims submit" in result["instructions"]
    )
    assert all(s["key"] and s["sentences"][0]["n"] == 1 for s in result["sections"])
    assert result["counts"]["pending"] == 4


def test_todo_lists_nothing_after_submit(repo: Path) -> None:
    submit_all()

    result = todo()

    assert result["sections"] == []
    assert result["counts"]["up_to_date"] == 4


def test_todo_after_an_edit_lists_only_that_section_and_drops_its_claims(
    repo: Path,
) -> None:
    submit_all()
    path = repo / ".okf" / "tool.md"
    path.write_text(path.read_text().replace("Plain words", "Short words"))

    result = todo()

    assert [s["id"] for s in result["sections"]] == ["tool#values"]
    assert result["counts"]["changed"] == 1
    _, out, _ = run("audit", "claims", "list", "--claims", "--json")
    assert all(c["section"] != "tool#values" for c in json.loads(out)["claims"])


def test_todo_drops_a_removed_concepts_claims(repo: Path) -> None:
    submit_all()
    (repo / ".okf" / "tool.md").unlink()

    result = todo()

    assert result["counts"]["removed"] == 2
    _, out, _ = run("audit", "claims", "list", "--claims", "--json")
    assert {c["concept"] for c in json.loads(out)["claims"]} == {
        "decisions/0001-use-sqlite"
    }


def test_todo_on_one_concept_leaves_the_others(repo: Path) -> None:
    submit_all()

    result = todo(".okf/tool.md")

    assert result["counts"] == {
        "up_to_date": 2,
        "pending": 0,
        "new": 0,
        "changed": 0,
        "removed": 0,
    }


def test_todo_limit_and_counts_for_people(repo: Path) -> None:
    assert len(todo("--limit", "1")["sections"]) == 1
    code, out, _ = run("audit", "claims", "todo")
    assert code == 0
    assert "to extract" in out and out.strip().splitlines()[-1].startswith("Next: ")
    assert "kmctl audit claims submit" in out
    assert "pending .okf/tool.md  (2 sections)" in out
    assert todo()["concepts"][1] == {
        "concept": "tool",
        "path": ".okf/tool.md",
        "sections": 2,
    }


def test_submit_stores_a_valid_answer(repo: Path) -> None:
    section = todo()["sections"][2]

    code, out, err = run(
        "audit", "claims", "submit", "-", "--json", stdin=json.dumps(answer(section))
    )

    assert code == 0, err
    assert json.loads(out) == {
        "stored": [{"section": "tool#parts", "claims": 3}],
        "refused": [],
    }


def test_submit_from_a_file(repo: Path, tmp_path: Path) -> None:
    section = todo()["sections"][2]
    file = tmp_path / "answers.json"
    file.write_text(json.dumps([answer(section, "none")]))

    code, out, _ = run("audit", "claims", "submit", str(file))

    assert code == 0
    assert "stored tool#parts (0 claims)" in out


def _refusal(stdin: str) -> tuple[int, str, str]:
    code, out, err = run("audit", "claims", "submit", "-", stdin=stdin)
    return code, out, err


def test_submit_refuses_a_stale_key(repo: Path) -> None:
    section = todo()["sections"][2]
    stale = answer(section) | {"key": "0000"}

    code, _, err = _refusal(json.dumps(stale))

    assert code == 1
    assert len(err.strip().splitlines()) == 1
    assert "stale key" in err and "kmctl audit claims todo" in err


def test_submit_refuses_a_missing_sentence_verdict(repo: Path) -> None:
    section = todo()["sections"][2]
    short = answer(section)
    short["sentences"] = short["sentences"][:1]

    code, _, err = _refusal(json.dumps(short))

    assert code == 1
    assert len(err.strip().splitlines()) == 1
    assert "no verdict for sentences [2, 3]" in err


@pytest.mark.parametrize(
    "bad",
    ["not json", json.dumps({"section": "tool#parts", "sentences": "x"})],
    ids=["not-json", "wrong-shape"],
)
def test_submit_refuses_a_malformed_answer(repo: Path, bad: str) -> None:
    todo()

    code, _, err = _refusal(bad)

    assert code == 1
    assert len(err.strip().splitlines()) == 1
    assert "submit again" in err or "pipe a list" in err


def test_submit_keeps_good_sections_of_a_mixed_file(repo: Path) -> None:
    sections = todo()["sections"]
    good = answer(sections[2])
    bad = answer(sections[3]) | {"key": "0000"}

    code, out, err = run(
        "audit", "claims", "submit", "-", "--json", stdin=json.dumps([good, bad])
    )

    assert code == 1
    assert len(err.strip().splitlines()) == 1
    assert [s["section"] for s in json.loads(out)["stored"]] == ["tool#parts"]
    assert [s["id"] for s in todo()["sections"]] == [
        "decisions/0001-use-sqlite#decision",
        "decisions/0001-use-sqlite#correction-2026-01-02",
        "tool#values",
    ]


def test_list_counts_per_kind(repo: Path) -> None:
    sections = todo()["sections"]
    answers = [
        answer(sections[2]),
        answer(sections[3], "none"),
        answer(sections[0], "external"),
    ]
    run("audit", "claims", "submit", "-", stdin=json.dumps(answers))

    code, out, _ = run("audit", "claims", "list", "--json")

    assert code == 0
    data = json.loads(out)
    assert data["totals"] == {"point": 3, "external": 2}
    tool = next(d for d in data["documents"] if d["concept"] == "tool")
    assert tool == {
        "concept": "tool",
        "sections": 2,
        "extracted": 2,
        "claims": {"point": 3},
    }


def test_list_one_concept_and_kind(repo: Path) -> None:
    sections = todo()["sections"]
    run(
        "audit",
        "claims",
        "submit",
        "-",
        stdin=json.dumps([answer(sections[2]), answer(sections[0], "external")]),
    )

    _, out, _ = run("audit", "claims", "list", ".okf/tool.md", "--claims", "--json")
    claims = json.loads(out)["claims"]
    assert {c["concept"] for c in claims} == {"tool"}
    assert set(claims[0]) == {
        "id", "section", "concept", "n", "sentence", "kind", "claim",
        "quantifier", "how_to_check", "reason", "refers_to",
    }  # fmt: skip

    _, out, _ = run(
        "audit", "claims", "list", "--kind", "external", "--claims", "--json"
    )
    assert {c["kind"] for c in json.loads(out)["claims"]} == {"external"}


def test_list_refuses_an_unknown_kind(repo: Path) -> None:
    code, _, err = run("audit", "claims", "list", "--kind", "pointy")

    assert code == 1
    assert "point, structural" in err


def test_refers_to_labels_resolve_to_section_ids(repo: Path) -> None:
    values = todo()["sections"][3]
    reply = answer(values)
    reply["sentences"][0]["claims"][0]["refers_to"] = ["1.2", 1, "9.9"]

    run("audit", "claims", "submit", "-", stdin=json.dumps(reply))

    _, out, _ = run("audit", "claims", "list", "--claims", "--json")
    assert json.loads(out)["claims"][0]["refers_to"] == ["tool#parts|2"]


def test_no_verb_changes_the_tree(repo: Path) -> None:
    submit_all()
    run("audit", "claims", "list")
    run("audit", "claims", "list", "--claims", "--json")

    assert git(repo, "status", "--porcelain") == ""


def test_no_verb_opens_a_network_connection(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("network connection opened")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)

    submit_all()
    code, _, err = run("audit", "claims", "list")
    assert code == 0, err


def test_todo_after_editing_a_first_section_lists_the_later_ones(repo: Path) -> None:
    """Earlier sections are in a section's key, since a claim may cite them."""
    submit_all()
    path = repo / ".okf" / "tool.md"
    path.write_text(path.read_text().replace("on start", "at start"))

    assert [s["id"] for s in todo()["sections"]] == ["tool#parts", "tool#values"]


@pytest.mark.parametrize(
    ("change", "words"),
    [
        ("none-with-claims", "kind none but lists claims"),
        ("empty", "answer list is empty"),
    ],
)
def test_submit_refuses_claims_under_none_and_an_empty_list(
    repo: Path, change: str, words: str
) -> None:
    section = todo()["sections"][2]
    none_with_claims = answer(section, "none")
    none_with_claims["sentences"][0]["claims"] = [{"claim": "x"}]
    reply = none_with_claims if change == "none-with-claims" else []

    code, _, err = _refusal(json.dumps(reply))

    assert code == 1
    assert len(err.strip().splitlines()) == 1
    assert words in err


def test_submit_counts_one_claim_for_a_repeated_text(repo: Path) -> None:
    section = todo()["sections"][2]
    reply = answer(section)
    for verdict in reply["sentences"]:
        verdict["claims"] = [{"claim": "The same claim."}]

    _, out, _ = run("audit", "claims", "submit", "-", "--json", stdin=json.dumps(reply))

    assert json.loads(out)["stored"] == [{"section": "tool#parts", "claims": 1}]


def test_todo_refuses_a_skipped_file(repo: Path) -> None:
    code, _, err = run("audit", "claims", "todo", ".okf/prototypes/spike/README.md")

    assert code == 1
    assert "not a concept kmctl audits" in err


def test_list_claims_json_holds_only_claims(repo: Path) -> None:
    submit_all()

    _, out, _ = run("audit", "claims", "list", "--claims", "--json")

    assert list(json.loads(out)) == ["claims"]
