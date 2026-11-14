"""kmctl audit judge against a fake decision endpoint (respx): shapes, cache, limits, retries and refusals."""

import asyncio
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
import tenacity
from fixtures.audit_repo import git, make_repo, store_claims
from typer.testing import CliRunner

from kmctl import app, tracing
from kmctl.claims import check_verbs
from kmctl.judge import FAILURE, JUDGE, LINK

F = Callable[..., Any]
URL = "https://gateway.example/v1/decisions"
KEY = "sk-test-0123456789"
CONFIG = f"""
[decisions]
max_calls = {{max_calls}}

[decisions.providers.clef]
base_url = "{URL}"
api_key_env = "CLEF_TEST_KEY"

[decisions.failure]
enabled = true
provider = "clef"
model = "jev-latest"

[decisions.claim]
enabled = true
provider = "clef"
model = "jev-latest"

[decisions.link]
enabled = {{link}}
provider = "clef"
model = "jev-latest"
"""
FAILURE_REPLY = {
    "answers": {
        "claim_false": {"noul": 0.82},
        "cause": {
            "probabilities": {"claim_false": 0.7, "check_wrong": 0.2, "unclear": 0.1}
        },
    }
}
JUDGE_REPLY = {
    "answers": {
        "shown_true": {"value": 0.9},
        "verdict": {"probabilities": {"true": 0.8, "false": 0.1, "not_shown": 0.1}},
    }
}
LINK_REPLY = {
    "answers": {"link": {"probabilities": {"0": 0.1, "1": 0.1, "2": 0.2, "3": 0.6}}}
}
LINK_LEVELS_SHOWN = {"unrelated": 0.1, "keyword": 0.1, "nearby": 0.2, "the claim": 0.6}


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = make_repo(tmp_path / "repo")
    monkeypatch.chdir(root)
    monkeypatch.setenv("CLEF_TEST_KEY", KEY)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("KMCTL_AUDIT_CONFIG", raising=False)
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.setattr(
        tenacity, "wait_exponential_jitter", lambda **_: tenacity.wait_none()
    )
    _config(tmp_path, max_calls=4, link="true")
    return root


def _config(tmp_path: Path, max_calls: int, link: str) -> None:
    path = tmp_path / "xdg" / "kmctl" / "audit.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(CONFIG.format(max_calls=max_calls, link=link))


@pytest.fixture
def ids(repo: Path) -> dict[str, str]:
    found = store_claims(
        repo,
        {
            "tool#parts": [
                (1, "point", "The CLI exits 1 when given more than one argument."),
                (2, "point", "The CLI writes out.txt."),
            ],
            "decisions/0001-use-sqlite#decision": [
                (1, "point", "The store is SQLite.")
            ],
        },
    )
    exits, writes, sqlite = found.values()
    answers = [
        {"claim": exits, "steps": [{"op": "code", "pattern": "if len(sys.argv) > 2: $$$B", "paths": "src/tool.py"}],
         "strength": "exact", "why": "w"},
        {"claim": writes, "steps": [{"op": "code", "pattern": "open(\"out.txt\", $$$A)", "paths": "src/tool.py"}],
         "strength": "exact", "why": "w"},
        {"claim": sqlite, "steps": [{"op": "imports", "path": "src/tool.py", "module": "sqlite3"}],
         "strength": "exact", "why": "w", "drift": "Nothing imports sqlite3."},
    ]  # fmt: skip
    result = check_verbs.submit(repo, json.dumps(answers))
    assert not result.refused, result.refused
    return {"exits": exits, "writes": writes, "sqlite": sqlite}


def judge(*args: str, stdin: str | None = None) -> tuple[int, str, str]:
    result = CliRunner().invoke(app, ["audit", "judge", *args], input=stdin)
    assert KEY not in result.stdout + result.stderr
    return result.exit_code, result.stdout, result.stderr


def test_failure_shape_and_answer(repo: Path, ids: dict[str, str]) -> None:
    with respx.mock:
        route = respx.post(URL).mock(
            return_value=httpx.Response(200, json=FAILURE_REPLY)
        )
        code, out, err = judge("failure", ids["sqlite"], "--json")

    assert code == 0, err
    body = json.loads(route.calls[0].request.content)
    assert body["model"] == "jev-latest"
    assert body["questions"] == FAILURE
    assert body["state"]["claim"] == "The store is SQLite."
    assert body["state"]["holds"] is False
    assert route.calls[0].request.headers["Authorization"] == f"Bearer {KEY}"
    assert json.loads(out) == [
        {"question": "failure", "id": ids["sqlite"], "model": "jev-latest", "cached": False,
         "chance": 0.82, "cause": "claim_false"}
    ]  # fmt: skip


def test_claim_shape_takes_lines_on_stdin(repo: Path, ids: dict[str, str]) -> None:
    with respx.mock:
        route = respx.post(URL).mock(return_value=httpx.Response(200, json=JUDGE_REPLY))
        code, out, _ = judge(
            "claim", ids["writes"], "--json", stdin="3: open('out.txt', 'w')\n"
        )

    assert code == 0
    body = json.loads(route.calls[0].request.content)
    assert body["questions"] == JUDGE
    assert body["state"]["lines"] == "3: open('out.txt', 'w')\n"
    assert json.loads(out)[0] | {} == {
        "question": "claim", "id": ids["writes"], "model": "jev-latest", "cached": False,
        "chance": 0.9, "verdict": "true",
    }  # fmt: skip


def test_link_score_from_level_probabilities(repo: Path, ids: dict[str, str]) -> None:
    with respx.mock:
        route = respx.post(URL).mock(return_value=httpx.Response(200, json=LINK_REPLY))
        _, out, _ = judge("link", ids["exits"], "--json")

    assert json.loads(route.calls[0].request.content)["questions"] == LINK
    answer = json.loads(out)[0]
    assert (answer["score"], answer["level"]) == (0.767, "the claim")
    assert answer["levels"] == LINK_LEVELS_SHOWN


@pytest.mark.parametrize(
    "levels",
    [{"2": 0.4, "3": 0.3, "4": 0.3}, {"-1": 0.9, "0": 0.1}],
    ids=["above-3", "negative"],
)
def test_link_levels_outside_0_to_3_are_refused(
    repo: Path, ids: dict[str, str], levels: dict[str, float]
) -> None:
    reply = {"answers": {"link": {"probabilities": levels}}}
    with respx.mock:
        respx.post(URL).mock(return_value=httpx.Response(200, json=reply))
        code, _, err = judge("link", ids["exits"])

    assert code == 1
    assert "the levels are 0 to 3" in err


def test_cache_a_repeat_sends_no_request(repo: Path, ids: dict[str, str]) -> None:
    with respx.mock:
        route = respx.post(URL).mock(return_value=httpx.Response(200, json=LINK_REPLY))
        judge("link", ids["exits"])
        code, out, _ = judge("link", ids["exits"])

    assert code == 0
    assert route.call_count == 1
    assert "[cached]" in out


def test_cache_a_changed_check_result_asks_again(
    repo: Path, ids: dict[str, str]
) -> None:
    with respx.mock:
        route = respx.post(URL).mock(return_value=httpx.Response(200, json=LINK_REPLY))
        judge("link", ids["exits"])
        tool = repo / "src" / "tool.py"
        tool.write_text("# moved down\n" + tool.read_text())
        check_verbs.run(repo)
        judge("link", ids["exits"])

    assert route.call_count == 2


def test_limit_keeps_max_calls_in_flight(
    repo: Path, ids: dict[str, str], tmp_path: Path
) -> None:
    _config(tmp_path, max_calls=1, link="true")
    in_flight = 0
    most = 0

    async def answer(request: httpx.Request) -> httpx.Response:
        nonlocal in_flight, most
        in_flight += 1
        most = max(most, in_flight)
        await asyncio.sleep(0.05)
        in_flight -= 1
        return httpx.Response(200, json=LINK_REPLY)

    with respx.mock:
        route = respx.post(URL).mock(side_effect=answer)
        code, _, _ = judge("link", ids["exits"], ids["writes"])

    assert code == 0
    assert route.call_count == 2
    assert most == 1


def test_retry_a_503_then_200(repo: Path, ids: dict[str, str]) -> None:
    with respx.mock:
        route = respx.post(URL).mock(
            side_effect=[httpx.Response(503), httpx.Response(200, json=LINK_REPLY)]
        )
        code, _, err = judge("link", ids["exits"])

    assert code == 0, err
    assert route.call_count == 2


@pytest.mark.parametrize(
    ("response", "words"),
    [
        (
            httpx.Response(401, text=f"bad key {KEY}"),
            "decisions.providers.clef.api_key_env",
        ),
        (
            httpx.Response(200, json={"answers": {"claim_false": {"noul": 0.5}}}),
            "left out ['cause']",
        ),
    ],
    ids=["401", "missing-question"],
)
def test_error_is_one_stderr_line(
    repo: Path, ids: dict[str, str], response: httpx.Response, words: str
) -> None:
    with respx.mock:
        respx.post(URL).mock(return_value=response)
        code, _, err = judge("failure", ids["sqlite"])

    assert code == 1
    assert len(err.strip().splitlines()) == 1
    assert words in err


def test_off_question_refuses_naming_its_table(
    repo: Path, ids: dict[str, str], tmp_path: Path
) -> None:
    _config(tmp_path, max_calls=4, link="false")

    with respx.mock:
        route = respx.post(URL)
        code, _, err = judge("link", ids["exits"])

    assert code == 1
    assert "[decisions.link]" in err
    assert route.call_count == 0


def test_failure_refuses_a_check_that_holds(repo: Path, ids: dict[str, str]) -> None:
    code, _, err = judge("failure", ids["exits"])

    assert code == 1 and "holds" in err


def test_extra_missing_refuses_naming_the_install(
    repo: Path, ids: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "tenacity", None)

    code, _, err = judge("link", ids["exits"])

    assert code == 1
    assert "uv tool install" in err and "kmctl[audit]" in err


def test_key_never_printed_and_tree_unchanged(
    repo: Path, ids: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLEF_TEST_KEY")
    code, _, err = judge("link", ids["exits"])
    assert code == 1 and "CLEF_TEST_KEY" in err

    monkeypatch.setenv("CLEF_TEST_KEY", KEY)
    with respx.mock:
        respx.post(URL).mock(return_value=httpx.Response(200, json=LINK_REPLY))
        judge("link", ids["exits"], "--json")

    assert git(repo, "status", "--porcelain") == ""


def test_tracing_off_unless_the_variable_is_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fn() -> int:
        return 1

    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    assert tracing.traced(fn, "x") is fn
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    wrapped = tracing.traced(fn, "x")
    assert wrapped is not fn
    assert getattr(wrapped, "__wrapped__", None) is fn


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="<html>\n<body>gateway error</body>\n</html>"),
        httpx.Response(400, text=f"line one\nline two {KEY}\nline three"),
        httpx.Response(
            200, json={"answers": {"claim_false": {"noul": "abc"}, "cause": {}}}
        ),
        httpx.Response(
            200,
            json={
                "answers": {
                    "claim_false": {},
                    "cause": {"probabilities": {"unclear": 1.0}},
                }
            },
        ),
    ],
    ids=["html-200", "multi-line-400", "wrong-type", "no-probability"],
)
def test_error_from_a_malformed_reply_is_one_stderr_line(
    repo: Path, ids: dict[str, str], response: httpx.Response
) -> None:
    with respx.mock:
        respx.post(URL).mock(return_value=response)
        code, _, err = judge("failure", ids["sqlite"])

    assert code == 1
    assert len(err.strip().splitlines()) == 1, err


def test_retry_after_on_a_429_is_honoured() -> None:
    from types import SimpleNamespace

    from kmctl.judge import _RetryAfter

    def state(response: httpx.Response) -> SimpleNamespace:
        error = httpx.HTTPStatusError(
            "x", request=httpx.Request("POST", URL), response=response
        )
        return SimpleNamespace(outcome=SimpleNamespace(exception=lambda: error))

    wait = _RetryAfter(lambda _: 1.5)

    assert wait(state(httpx.Response(429, headers={"Retry-After": "7"}))) == 7.0
    assert wait(state(httpx.Response(429, headers={"Retry-After": "999"}))) == 60.0
    assert wait(state(httpx.Response(429))) == 1.5
    assert wait(state(httpx.Response(503, headers={"Retry-After": "7"}))) == 1.5


def test_cache_a_reworded_question_set_asks_again(
    repo: Path, ids: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from kmctl import judge as judge_module

    with respx.mock:
        route = respx.post(URL).mock(return_value=httpx.Response(200, json=LINK_REPLY))
        judge("link", ids["exits"])
        reworded = {"link": {**LINK["link"], "instructions": "Reworded."}}
        monkeypatch.setitem(judge_module.QUESTION_SETS, "link", reworded)
        judge("link", ids["exits"])

    assert route.call_count == 2


def test_tracing_wraps_the_call_when_on(
    repo: Path, ids: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import langsmith

    names: list[str] = []

    def fake_traceable(run_type: str, name: str) -> Callable[[F], F]:
        def wrap(fn: F) -> F:
            names.append(f"{run_type}:{name}")
            return fn

        return wrap

    monkeypatch.setattr(langsmith, "traceable", fake_traceable)
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    with respx.mock:
        respx.post(URL).mock(return_value=httpx.Response(200, json=LINK_REPLY))
        code, _, err = judge("link", ids["exits"])

    assert code == 0, err
    assert names == ["llm:decision model"]


def test_tracing_on_without_langsmith_refuses(
    repo: Path, ids: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setitem(sys.modules, "langsmith", None)

    code, _, err = judge("link", ids["exits"])

    assert code == 1
    assert len(err.strip().splitlines()) == 1 and "langsmith" in err


HELP_WITHOUT_EXTRA = """
import sys

BLOCKED = {"tenacity", "langsmith", "jmespath", "ast_grep_py"}


class Block:
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in BLOCKED:
            raise ImportError(name)
        return None


sys.meta_path.insert(0, Block())
from typer.testing import CliRunner

from kmctl import app

for words in (["--help"], ["audit", "judge", "--help"], ["audit", "checks", "--help"]):
    result = CliRunner().invoke(app, words)
    assert result.exit_code == 0, (words, result.output)
assert "kmctl.judge" not in sys.modules
print("ok")
"""


def test_help_loads_without_the_extra() -> None:
    import subprocess

    done = subprocess.run(
        [sys.executable, "-c", HELP_WITHOUT_EXTRA],
        capture_output=True,
        text=True,
        check=False,
    )

    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "ok"
