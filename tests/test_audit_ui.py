"""kmctl audit ui: the page's data, the local server's calls and who it answers, and second opinions."""

import json
import threading
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
import respx
from fixtures.audit_repo import make_repo, store_claims
from typer.testing import CliRunner

from kmctl import app
from kmctl.claims import AuditError, check_verbs
from kmctl.claims.ui import AuditServer, build, second_opinion

CODE = {"op": "code", "pattern": "if len(sys.argv) > 2: $$$B", "paths": "src/tool.py"}
EXITS = "The CLI exits 1 when given more than one argument."
CONFIG = "The CLI reads `config.toml` on start."
URL = "https://gateway.example/v1/decisions"
SETTINGS = f"""
[decisions.providers.clef]
base_url = "{URL}"
api_key_env = "CLEF_TEST_KEY"

[decisions.link]
enabled = true
provider = "clef"
model = "jev-latest"
"""
LINK_REPLY = {
    "answers": {"link": {"probabilities": {"0": 0.0, "1": 0.1, "2": 0.1, "3": 0.8}}}
}


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = make_repo(tmp_path / "repo")
    monkeypatch.chdir(root)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("KMCTL_AUDIT_CONFIG", raising=False)
    return root


@pytest.fixture
def ids(repo: Path) -> dict[str, str]:
    """A claim with a check that holds, and one with a reason."""
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
    assert not result.refused
    return {"exits": found[EXITS], "config": found[CONFIG]}


@pytest.fixture
def server(repo: Path, ids: dict[str, str]) -> Iterator[AuditServer]:
    running = AuditServer(repo, 0, "human:test")
    thread = threading.Thread(target=running.serve_forever, daemon=True)
    thread.start()
    yield running
    running.shutdown()
    running.server_close()


@pytest.fixture
def client(server: AuditServer) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=server.url, timeout=10.0) as c:
        yield c


def claim_in(view: dict, claim_id: str) -> dict:
    return next(
        c
        for d in view["concepts"]
        for sec in d["sections"]
        for s in sec["sentences"]
        for c in s["claims"]
        if c["id"] == claim_id
    )


def test_the_page_shows_each_claim_with_its_check_and_coverage(
    repo: Path, ids: dict[str, str]
) -> None:
    view = build(repo).model_dump()
    exits, config = claim_in(view, ids["exits"]), claim_in(view, ids["config"])

    assert (exits["status"], exits["coverage"], exits["ask"]) == (
        "holds",
        "checked",
        "link",
    )
    assert exits["check"]["steps"][0]["op"] == "code"
    assert (config["coverage"], config["ask"]) == ("reason", "claim")
    assert view["questions"] == []


def test_the_page_and_its_data_are_served(
    client: httpx.Client, ids: dict[str, str]
) -> None:
    page = client.get("/")
    data = client.get("/api/data")

    assert page.status_code == 200 and 'fetch("/api/data"' in page.text
    assert (
        data.status_code == 200
        and claim_in(data.json(), ids["exits"])["status"] == "holds"
    )


def test_a_verdict_from_the_page_is_stored_and_wins_over_the_check(
    client: httpx.Client, ids: dict[str, str]
) -> None:
    sent = {
        "claim": ids["exits"],
        "target": "check",
        "vote": "down",
        "verdict": "false",
        "note": "no",
    }

    res = client.post("/api/feedback", json=sent)

    view = res.json()
    assert res.status_code == 200, res.text
    assert (view["coverage"], view["human"], view["disagrees"]) == (
        "drift",
        "false",
        True,
    )
    assert view["feedback"]["check"] | {"at": ""} == {
        "vote": "down", "verdict": "false", "note": "no", "by": "human:test", "at": "", "answered": False
    }  # fmt: skip
    assert ids["exits"] in [c.id for c in check_verbs.todo(Path(".")).claims]


@pytest.mark.parametrize(
    ("headers", "status"),
    [
        ({"Origin": "https://evil.example"}, 403),
        ({"Host": "evil.example"}, 403),
        ({"Content-Type": "text/plain"}, 415),
    ],
    ids=["foreign origin", "rebound host", "not json"],
)
def test_writes_from_anywhere_but_the_page_are_refused(
    client: httpx.Client, ids: dict[str, str], headers: dict[str, str], status: int
) -> None:
    body = json.dumps({"claim": ids["exits"], "target": "claim", "vote": "down"})
    res = client.post(
        "/api/feedback",
        content=body,
        headers={"Content-Type": "application/json", **headers},
    )

    assert res.status_code == status
    assert check_verbs.todo(Path(".")).claims == []


def test_bad_feedback_is_refused_with_the_field(
    client: httpx.Client, ids: dict[str, str]
) -> None:
    res = client.post(
        "/api/feedback",
        json={"claim": ids["exits"], "target": "claim", "vote": "maybe"},
    )

    assert res.status_code == 400
    assert res.json()["error"].startswith("vote:")


def test_a_second_opinion_is_refused_while_its_question_is_off(
    repo: Path, ids: dict[str, str]
) -> None:
    with pytest.raises(
        AuditError,
        match=r"the link question is off; switch it on under \[decisions.link\]",
    ):
        second_opinion(repo, ids["exits"])


def test_a_second_opinion_asks_the_model_once_and_shows_on_the_page(
    repo: Path, ids: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = tmp_path / "audit.toml"
    settings.write_text(SETTINGS, encoding="utf-8")
    monkeypatch.setenv("CLEF_TEST_KEY", "sk-test")

    with respx.mock:
        route = respx.post(URL).mock(return_value=httpx.Response(200, json=LINK_REPLY))
        first = second_opinion(repo, ids["exits"], settings)
        again = second_opinion(repo, ids["exits"], settings)
    shown = claim_in(build(repo, config=settings).model_dump(), ids["exits"])

    assert route.call_count == 1
    assert first.opinion is not None and first.opinion.level == "the claim"
    assert again.opinion == first.opinion
    assert shown["opinion"]["level"] == "the claim"


def test_ui_refuses_a_folder_with_no_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["audit", "ui", "--no-open", "--port", "0"])

    assert result.exit_code == 1
    assert result.stderr.startswith("kmctl audit ui: refused:")


def test_feedback_keeps_the_second_opinion_read_from_the_given_settings(
    repo: Path, ids: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from kmctl.claims.feedback import FeedbackIn
    from kmctl.claims.ui import give_feedback

    settings = tmp_path / "audit.toml"
    settings.write_text(SETTINGS, encoding="utf-8")
    monkeypatch.setenv("CLEF_TEST_KEY", "sk-test")
    with respx.mock:
        respx.post(URL).mock(return_value=httpx.Response(200, json=LINK_REPLY))
        second_opinion(repo, ids["exits"], settings)

    view = give_feedback(
        repo,
        FeedbackIn(claim=ids["exits"], target="check", vote="up"),
        "human:test",
        settings,
    )

    assert view.opinion is not None and view.opinion.level == "the claim"


@pytest.mark.parametrize("length", ["abc", "-1"])
def test_a_bad_content_length_is_refused_not_dropped(
    server: AuditServer, length: str
) -> None:
    import http.client  # httpx will not send a malformed Content-Length

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=10)
    conn.putrequest("POST", "/api/feedback")
    conn.putheader("Content-Type", "application/json")
    conn.putheader("Content-Length", length)
    conn.endheaders()
    res = conn.getresponse()

    assert res.status == 411
    assert "Content-Length" in json.loads(res.read())["error"]
    conn.close()
