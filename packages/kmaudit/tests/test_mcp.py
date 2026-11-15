"""kmaudit mcp, driven through the MCP SDK's stdio client as a harness drives it."""

import asyncio
import json
import re
import sys
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pytest
from kmaudit.cli import app
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from typer.testing import CliRunner

from .fixtures.audit_repo import make_repo

PACKAGE = Path(__file__).resolve().parents[1]
KMAUDIT = str(Path(sys.executable).with_name("kmaudit"))
TOOLS = {
    "namespaces",
    "claims_todo",
    "claims_submit",
    "claims_list",
    "checks_todo",
    "checks_try",
    "checks_submit",
    "checks_run",
    "checks_list",
    "coverage",
    "judge",
}
HARNESSES = ["Claude Code", "Codex", "Antigravity", "LangGraph"]
#: The commands the slim CLI keeps, each documented in commands.md and the README.
KEPT = ["mcp", "ui", "namespaces", "briefing", "claims list", "checks list"]


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = make_repo(tmp_path / "repo")
    monkeypatch.chdir(root)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("KMCTL_AUDIT_CONFIG", raising=False)
    return root


@asynccontextmanager
async def connect(root: Path) -> AsyncIterator[ClientSession]:
    """Start ``kmaudit mcp`` in ``root`` over stdio, as a harness does, and open a session."""
    params = StdioServerParameters(
        command=KMAUDIT,
        args=["mcp"],
        cwd=root,
        env={"XDG_CONFIG_HOME": str(root.parent / "xdg")},
    )
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        yield session


def drive(root: Path, steps: Callable[[ClientSession], Awaitable[Any]]) -> Any:
    """Run ``steps`` against a fresh server in ``root`` and return what they return."""

    async def main() -> Any:
        async with connect(root) as session:
            return await steps(session)

    return asyncio.run(main())


async def call(session: ClientSession, tool: str, **arguments: Any) -> tuple[bool, str]:
    """Call ``tool`` and return whether it is an error and its text."""
    result = await session.call_tool(tool, arguments)
    return bool(result.is_error), "".join(c.text for c in result.content)


async def ok(session: ClientSession, tool: str, **arguments: Any) -> Any:
    """Call ``tool``, insist it succeeded, and return its JSON."""
    error, text = await call(session, tool, **arguments)
    assert not error, text
    return json.loads(text)


def cli(*args: str) -> Any:
    """Run ``kmaudit ARGS --json`` in-process and return its JSON."""
    result = CliRunner().invoke(app, [*args, "--json"])
    assert result.exit_code == 0, result.stderr
    return json.loads(result.stdout)


def answer(section: dict, key: str | None = None) -> dict:
    """A valid answer for ``section``: one point claim per sentence."""
    return {
        "section": section["id"],
        "key": key or section["key"],
        "sentences": [
            {
                "n": s["n"],
                "how_to_check": "open the file",
                "reason": "names a file",
                "kind": "point",
                "claims": [{"claim": f"{section['id']} claim {s['n']}"}],
            }
            for s in section["sentences"]
        ],
    }


def test_lists_every_tool_each_taking_folder(repo: Path) -> None:
    async def steps(session: ClientSession) -> Any:
        listed = (await session.list_tools()).tools
        off = await call(session, "judge", folder=".okf", question="link", ids=["x"])
        return {t.name: t.input_schema for t in listed}, off

    schemas, (error, text) = drive(repo, steps)

    assert set(schemas) == TOOLS
    for name, schema in schemas.items():
        assert "folder" in schema["properties"], name
        if name != "namespaces":
            assert "folder" in schema.get("required", []), name
    assert {"folder", "question", "ids", "lines"} <= set(schemas["judge"]["properties"])
    # The judge tool refuses an off question with a line naming the tool and the fix.
    assert error and "tool judge: refused:" in text and "[decisions.link]" in text


def test_lists_judge_tool_awaiting_run_judge(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import kmaudit.judge as judging
    from kmaudit.mcp_server import server

    seen: list[tuple] = []

    async def fake(
        folder: Path, question: str, ids: list[str], lines: str = "", config=None
    ) -> judging.JudgeResult:
        seen.append((Path(folder), question, ids, lines))
        return judging.JudgeResult(
            entries=[
                judging.JudgeEntry(
                    id=i,
                    judgement=judging.Judgement(
                        question=question, id=i, model="m", cached=True, score=1.0
                    ),
                )
                for i in ids
            ]
        )

    monkeypatch.setattr(judging, "run_judge", fake)

    result = asyncio.run(
        server.call_tool(
            "judge", {"folder": ".okf", "question": "link", "ids": ["a", "b"]}
        )
    )

    assert seen == [(Path(".okf"), "link", ["a", "b"], "")]
    entries = json.loads(result.content[0].text)["entries"]
    assert [e["id"] for e in entries] == ["a", "b"]


def test_round_trip_todo_submit_list_matches_the_list_command(repo: Path) -> None:
    async def steps(session: ClientSession) -> Any:
        first = await ok(session, "claims_todo", folder=".okf")
        stored = await ok(
            session,
            "claims_submit",
            folder=".okf",
            answers=[answer(s) for s in first["sections"]],
        )
        again = await ok(session, "claims_todo", folder=".okf", limit=15)
        listed = await ok(session, "claims_list", folder=".okf")
        each = await ok(session, "claims_list", folder=".okf", claims=True)
        return first, stored, again, listed, each

    first, stored, again, listed, each = drive(repo, steps)

    assert first["sections"] and first["namespace"] == ".okf"
    assert [s["section"] for s in stored["stored"]] == [
        s["id"] for s in first["sections"]
    ]
    assert stored["refused"] == []
    assert sum(s["claims"] for s in stored["stored"]) > 0
    assert again["sections"] == [] and again["counts"]["up_to_date"] == len(
        first["sections"]
    )
    assert listed == cli("claims", "list", ".okf")
    assert each == cli("claims", "list", ".okf", "--claims")
    assert {c["section"] for c in each["claims"]} == {
        s["id"] for s in first["sections"]
    }


def test_refusal_is_a_tool_error_and_mixed_batch_lists_refused(repo: Path) -> None:
    async def steps(session: ClientSession) -> Any:
        unknown = await call(session, "claims_todo", folder="no-such-folder")
        garbled = await call(session, "claims_submit", folder=".okf", answers="{not")
        sections = (await ok(session, "claims_todo", folder=".okf"))["sections"]
        mixed = await ok(
            session,
            "claims_submit",
            folder=".okf",
            answers=[answer(sections[0]), answer(sections[1], key="0" * 16)],
        )
        stale = await ok(
            session,
            "claims_submit",
            folder=".okf",
            answers=[answer(sections[2], key="0" * 16)],
        )
        alive = await ok(session, "claims_list", folder=".okf")
        return unknown, garbled, sections, mixed, stale, alive

    unknown, garbled, sections, mixed, stale, alive = drive(repo, steps)

    error, text = unknown
    assert error
    assert "tool claims_todo: refused:" in text
    assert "does not exist; give a folder of markdown docs" in text
    error, text = garbled
    assert error
    assert "tool claims_submit: refused: the answer is not JSON" in text
    assert [s["section"] for s in mixed["stored"]] == [sections[0]["id"]]
    [refused] = mixed["refused"]
    assert refused["section"] == sections[1]["id"]
    assert "stale key" in refused["reason"]
    assert "call claims_todo" in refused["reason"]
    assert stale["stored"] == [] and len(stale["refused"]) == 1
    assert alive["totals"]


def _big_repo(root: Path) -> Path:
    """The fixture repository plus docs/, 20 pages of 10 sections each."""
    make_repo(root)
    for page in range(20):
        body = "\n\n".join(
            f"## Part {n}\n\nThe tool writes file {page}-{n}.txt. It reads it back."
            for n in range(10)
        )
        path = root / "docs" / f"page{page}.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"# Page {page}\n\n{body}\n", encoding="utf-8")
    return root


def test_paging_default_limit_stays_small_and_brief_drops_instructions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _big_repo(tmp_path / "repo")
    monkeypatch.chdir(root)

    async def steps(session: ClientSession) -> Any:
        error, text = await call(session, "claims_todo", folder="docs")
        assert not error, text
        brief = await ok(session, "claims_todo", folder="docs", brief=True)
        return text, brief

    text, brief = drive(root, steps)
    full = json.loads(text)

    assert full["counts"]["pending"] >= 200
    assert len(full["sections"]) == 5
    assert len(text.encode()) < 100_000
    assert full["instructions"]
    assert "instructions" not in brief and len(brief["sections"]) == 5


def test_documented_every_tool_and_harness_and_absolute_folder(repo: Path) -> None:
    async def steps(session: ClientSession) -> Any:
        names = [t.name for t in (await session.list_tools()).tools]
        relative = await ok(session, "claims_list", folder=".okf")
        absolute = await ok(session, "claims_list", folder=str(repo / ".okf"))
        return names, relative, absolute

    names, relative, absolute = drive(repo, steps)
    commands = (PACKAGE / "docs" / "commands.md").read_text(encoding="utf-8")
    readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
    headings = re.findall(r"^#{2,4} (.+)$", readme, flags=re.MULTILINE)

    for name in names:
        assert f"`{name}`" in commands, name
    for command in KEPT:
        assert f"## `kmaudit {command}`" in commands, command
        assert f"`kmaudit {command}" in readme, command
    for harness in HARNESSES:
        assert any(harness in h for h in headings), harness
    assert absolute == relative
