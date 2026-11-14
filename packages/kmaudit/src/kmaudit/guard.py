"""The shell guard for the claims and checks agents: a Claude Code PreToolUse hook that lets through only ``kmaudit`` commands.

An agent's front matter runs ``kmaudit guard --allow claims`` (or
``checks``) before each Bash call. The command passes when it is one
``kmaudit GROUP ...`` command, optionally after ``cd DIR &&``, optionally
fed by one quoted heredoc whose body is data. Anything else, a pipe, a
redirect, a second command or a command substitution, is refused with exit
code 2, which blocks the call.
"""

import re

from pydantic import BaseModel, ConfigDict, Field, ValidationError

#: The groups an agent may be allowed.
GROUPS = ("claims", "checks")
#: Characters that would chain, redirect or substitute on the command line.
_SHELL = re.compile(r"[;&|<>`$()]")
_CD = re.compile(r"^cd\s+(?:'[^']*'|\"[^\"$`]*\"|[^\s;&|<>`$()]+)\s*&&\s*")
_HEREDOC = re.compile(r"\s*<<-?\s*'(\w+)'\s*$")


class _ToolInput(BaseModel):
    """The part of a Bash call the guard reads."""

    model_config = ConfigDict(extra="ignore")

    command: str = ""


class HookInput(BaseModel):
    """A Claude Code PreToolUse hook's JSON input, as the guard reads it."""

    model_config = ConfigDict(extra="ignore")

    tool_name: str = ""
    tool_input: _ToolInput = Field(default_factory=_ToolInput)


def refusal(text: str, allow: str) -> str | None:
    """Why the guard refuses a hook input, or None when the call may run.

    Parameters
    ----------
    text :
        The hook's JSON input.
    allow :
        The ``kmaudit`` group the agent may run: claims or checks.
    """
    try:
        call = HookInput.model_validate_json(text)
    except ValidationError:
        return "the hook input is not the JSON Claude Code sends; nothing runs"
    if call.tool_name != "Bash":
        return None
    lines = call.tool_input.command.strip().splitlines()
    if not lines:
        return "an empty command"
    first = _CD.sub("", lines[0].strip(), count=1)
    heredoc = _HEREDOC.search(first)
    if heredoc is not None:
        first = first[: heredoc.start()]
        ends = [n for n, line in enumerate(lines) if line.strip() == heredoc.group(1)]
        if len(lines) < 2 or ends != [len(lines) - 1]:
            return (
                "a heredoc must end with its own terminator line and nothing after it"
            )
    elif len(lines) > 1:
        return "one command per call; feed answers with a quoted heredoc (<<'ANSWERS')"
    if not first.startswith(f"kmaudit {allow} ") and first != f"kmaudit {allow}":
        return (
            f"only kmaudit {allow} commands may run here; read files with the Read tool"
        )
    if _SHELL.search(first):
        return "no pipes, redirects, chained commands or substitutions; run the kmaudit command alone"
    return None
