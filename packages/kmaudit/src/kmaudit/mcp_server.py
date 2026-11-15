"""``kmaudit mcp``: kmaudit's verbs as the tools of a stdio MCP server.

Any harness that speaks MCP (Claude Code, Codex, Antigravity, a LangGraph
agent) starts ``kmaudit mcp`` and calls these tools; they are the only way an
agent drives the audit, since the CLI keeps only ``mcp``, ``ui``,
``namespaces``, ``briefing`` and the two list commands. Each tool takes
``folder``, the namespace: absolute, or relative to the directory the harness
starts the server in. Each returns JSON. A refusal of the whole call is a
tool error, ``Error executing tool TOOL: refused: REASON``, naming the fix; a submit that refuses
some answers and stores others is a result whose ``refused`` list names each
one.

stdin and stdout carry the MCP messages, so the verbs run in a worker thread
(except ``judge``, which awaits its model calls on the event loop) and every
subprocess they start gets ``stdin=DEVNULL``.
"""

import json
import sqlite3
from collections.abc import Callable
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Any, Literal

import anyio.to_thread
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, TextContent
from pydantic import Field, TypeAdapter

from kmaudit import AuditError
from kmaudit.check_verbs import Status
from kmaudit.models import KINDS

INSTRUCTIONS = """\
kmaudit audits what a folder of markdown docs claims about its repository. \
Every tool takes folder: the audited folder (its namespace), absolute or \
relative to the server's working directory; an absolute path is safest.

Claims: claims_todo hands out sections and the instructions for answering \
them; answer each section and pass the list to claims_submit; claims_list \
reads them back. Checks: checks_todo hands out claims with the lines they \
are about; test a draft with checks_try, store it with checks_submit; \
checks_run reruns what changed and checks_list shows each claim's status. \
coverage says how much code the checks match; namespaces lists the audited \
folders; judge asks the optional decision model.

The todo tools hand out 5 items by default; pass brief=true after the first \
round to leave out the instructions you already have. Where a result's next \
names a tool and a folder (claims_submit with folder docs), call that tool \
with that namespace as folder. A refused call is a tool error naming the fix; a submit that stores some \
answers lists the rest under refused, each with its fix."""

server = MCPServer(
    name="kmaudit",
    instructions=INSTRUCTIONS,
    version=version("kmaudit"),
    log_level="WARNING",
)

Folder = Annotated[
    str,
    Field(
        description=(
            "The folder of markdown docs to audit (its namespace), or a folder or page inside "
            "one to narrow the scope; absolute, or relative to the server's working directory. "
            "The repository root holding .okf/ means .okf."
        )
    ),
]
Answers = Annotated[
    list[dict[str, Any]] | str,
    Field(
        description=(
            "The answers: a list of answer objects in the shape the matching todo tool's "
            "instructions give, or the JSON text of that list."
        )
    ),
]
Limit = Annotated[
    int,
    Field(
        ge=1,
        description="Hand out at most this many; the counts still cover all. Default: 5.",
    ),
]
Brief = Annotated[
    bool,
    Field(
        description="Leave out the instructions (and answer schema) you already have from an earlier round."
    ),
]
By = Annotated[
    str, Field(description="Who wrote the answers, recorded with each. Default: agent.")
]


async def _run(work: Callable[[], str]) -> CallToolResult:
    """Run ``work`` in a worker thread and return its JSON, or refuse the call.

    Raises
    ------
    ToolError
        With ``refused: REASON`` when the verb refuses the call; the SDK puts
        the tool's name in front.
    """
    try:
        text = await anyio.to_thread.run_sync(work)
    except (AuditError, sqlite3.Error) as error:
        raise ToolError(f"refused: {error}") from error
    return CallToolResult(content=[TextContent(type="text", text=text)])


def _text(answers: list[dict[str, Any]] | str) -> str:
    """The answers as the JSON text the verbs read."""
    return answers if isinstance(answers, str) else json.dumps(answers)


@server.tool()
async def namespaces(
    folder: Annotated[
        str,
        Field(
            description="A path in the repository whose namespaces to list. Default: the working directory."
        ),
    ] = ".",
) -> CallToolResult:
    """List the repository's namespaces: each audited folder with its sections, claims and checks."""
    from kmaudit.namespaces import listing

    return await _run(
        lambda: json.dumps({"namespaces": [asdict(r) for r in listing(Path(folder))]}),
    )


@server.tool()
async def claims_todo(
    folder: Folder, limit: Limit = 5, brief: Brief = False
) -> CallToolResult:
    """List the sections with no claims extracted for their current text, with the instructions for answering them.

    Answer each section per the instructions and pass the answers to claims_submit.
    """
    from kmaudit.verbs import todo

    return await _run(
        lambda: todo(Path(folder), limit, brief).model_dump_json(exclude_none=brief),
    )


@server.tool()
async def claims_submit(
    folder: Folder, answers: Answers, by: By = "agent"
) -> CallToolResult:
    """Store an agent's verdicts and claims for sections claims_todo handed out.

    Returns stored (section, claims) and refused (section, reason with the fix); a stale key
    or a bad answer is refused on its own while the good answers are stored.
    """
    from kmaudit.verbs import submit

    return await _run(
        lambda: submit(Path(folder), _text(answers), by).model_dump_json(),
    )


@server.tool()
async def claims_list(
    folder: Folder,
    kind: Annotated[
        Literal[KINDS] | None,
        Field(description="Only claims of this kind."),
    ] = None,
    claims: Annotated[
        bool,
        Field(
            description="List each claim with its sentence, kind, quantifier, how to check and reason."
        ),
    ] = False,
) -> CallToolResult:
    """Show the stored claims: counts per concept and kind, or each claim."""
    from kmaudit.verbs import list_claims

    return await _run(
        lambda: list_claims(Path(folder), kind, claims).model_dump_json(
            exclude_none=True
        ),
    )


@server.tool()
async def checks_todo(
    folder: Folder, limit: Limit = 5, brief: Brief = False
) -> CallToolResult:
    """List the stored claims with no check or current reason, with the lines they are about, the instructions and the answer schema.

    Draft each answer, test it with checks_try, then store it with checks_submit.
    """
    from kmaudit.check_verbs import todo

    return await _run(
        lambda: todo(Path(folder), limit, brief).model_dump_json(exclude_none=brief),
    )


@server.tool()
async def checks_try(folder: Folder, answers: Answers) -> CallToolResult:
    """Run draft checks and say whether each holds and which changes to the code it would miss. It stores nothing."""
    from kmaudit.check_verbs import Tried, try_answers

    return await _run(
        lambda: (
            TypeAdapter(list[Tried])
            .dump_json(try_answers(Path(folder), _text(answers)))
            .decode()
        ),
    )


@server.tool()
async def checks_submit(
    folder: Folder, answers: Answers, by: By = "agent"
) -> CallToolResult:
    """Store checks and reasons for claims, refusing weak and failing checks.

    Returns stored and refused (claim, reason with the fix); the good answers are stored.
    """
    from kmaudit.check_verbs import submit

    return await _run(
        lambda: submit(Path(folder), _text(answers), by).model_dump_json(),
    )


@server.tool()
async def checks_run(
    folder: Folder,
    all: Annotated[
        bool,
        Field(
            description="Rerun every stored check, not only those whose files changed."
        ),
    ] = False,
) -> CallToolResult:
    """Rerun the stored checks whose files changed, with no model, and report each claim's status. It can take minutes; the audit page's Rerun stale checks button does the same."""
    from kmaudit.check_verbs import run

    return await _run(lambda: run(Path(folder), all).model_dump_json())


@server.tool()
async def checks_list(
    folder: Folder,
    status: Annotated[
        Status | None, Field(description="Only claims with this status.")
    ] = None,
) -> CallToolResult:
    """Show each claim's check status, strength and why, as the last checks_run or checks_submit left it."""
    from kmaudit.check_verbs import list_checks

    return await _run(
        lambda: list_checks(Path(folder), status).model_dump_json(exclude_none=True),
    )


@server.tool()
async def coverage(folder: Folder) -> CallToolResult:
    """Show how much of the repository's code the checks match, line by line."""
    from kmaudit.coverage import coverage as measure

    return await _run(lambda: measure(Path(folder)).model_dump_json())


@server.tool()
async def judge(
    folder: Folder,
    question: Annotated[
        Literal["failure", "claim", "link"],
        Field(
            description=(
                "failure: does a failed check show its claim false? claim: do the lines show "
                "the claim true? link: does a check test its claim?"
            )
        ),
    ],
    ids: Annotated[
        list[str],
        Field(
            description="Check ids (failure, link) from checks_list, or one claim id (claim) from claims_list."
        ),
    ],
    lines: Annotated[
        str, Field(description="claim only: the lines to judge the claim on.")
    ] = "",
) -> CallToolResult:
    """Ask the configured decision model one question about stored checks or a claim.

    Off unless the question is switched on in the user's audit.toml. Returns one entry per
    id: its judgement, or the error that stopped it.
    """
    from kmaudit.judge import run_judge

    try:
        result = await run_judge(Path(folder), question, ids, lines)
    except (AuditError, sqlite3.Error) as error:
        raise ToolError(f"refused: {error}") from error
    return CallToolResult(
        content=[
            TextContent(type="text", text=result.model_dump_json(exclude_none=True))
        ]
    )
