"""What kmctl adds to APM's Antigravity install, and the commands its package ships (ADR 0020).

APM 0.33.0 writes kmctl's skills, rules, SessionStart hook and okf's MCP
server for Antigravity from the package's ``apm/antigravity/`` sub-package
(spike:apm-hands-back/1, /2). Two things it cannot do yet, and kmctl does:

- Agents: APM writes none for Antigravity (APM issue #2990). kmctl
  translates its own and okf's Claude Code agents into ``.agents/plugins/kmctl/``,
  a folder it alone owns, which Antigravity loads from a trusted workspace.
- okf's Stop hook: APM writes it into ``.agents/hooks.json`` with a path from
  the repository root, but agy runs hooks in ``.agents/``, so it fails at
  the end of every turn. kmctl takes that handler out; the package's own
  Stop wrapper (``STOP_COMMAND``) runs okf's check instead (ADR 0018).

Every function here prints nothing. ``plugin_files`` says what the folder
holds, ``write_plugin`` replaces the folder with it, and ``compare_plugin``
and ``plugin_problems`` report how a folder on disk differs: ``kmctl doctor``
uses that comparison, and any other check can call it.
"""

import json
import shutil
from importlib.resources import files
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError

from kmctl.plugin import HOOK_TIMEOUT, MCP_NAME, PluginError, okf_server_current

#: Where the folder sits, relative to the repository.
PLUGIN_PATH = Path(".agents") / "plugins" / "kmctl"
PLUGIN_NAME = "kmctl"
#: Where APM puts okf-skills' Claude-format agents, relative to the repository.
OKF_AGENTS = Path("apm_modules") / "scaccogatto" / "okf-skills" / "agents"
#: The command of the package's Antigravity SessionStart hook. Antigravity fails a hook whose stdout is not
#: JSON, so it prints ``{}`` and exits 0 when kmctl is missing or fails (I1).
HOOK_COMMAND = (
    "command -v kmctl >/dev/null 2>&1 || { echo '{}'; exit 0; }; "
    "out=$(kmctl briefing --format antigravity 2>/dev/null) "
    "&& printf '%s\\n' \"$out\" || echo '{}'; exit 0"
)
#: The command of the package's Antigravity PostToolUse hook: the summary nudge
#: after every tool call (ADR 0028). agy hands the model the injectSteps it
#: prints there, though its docs say PostToolUse expects ``{}``
#: (spike:okf-summary-nudge-agy-opencode/1). KMCTL_PINNED=1 for the reason
#: ``kmctl.plugin.NUDGE_COMMAND`` gives; a missing kmctl or a failing verb
#: prints ``{}`` and exits 0 (I1).
NUDGE_COMMAND = (
    "command -v kmctl >/dev/null 2>&1 || { echo '{}'; exit 0; }; "
    "out=$(KMCTL_PINNED=1 kmctl summary nudge --format antigravity 2>/dev/null) "
    "&& printf '%s\\n' \"$out\" || echo '{}'; exit 0"
)
#: okf's Stop hook script as APM deploys it for Antigravity, relative to the
#: repository.
OKF_STOP_SCRIPT = ".agents/hooks/okf-skills/hooks/okf-stop-check.sh"
#: Where APM merges hooks for Antigravity, relative to the repository.
APM_HOOKS = Path(".agents") / "hooks.json"
#: okf's own Stop handler as APM 0.33.0 writes it for Antigravity: a path from
#: the repository root, which fails because agy runs hooks in ``.agents/``.
APM_OKF_STOP = f'bash "{OKF_STOP_SCRIPT}"'
#: The command of the package's Antigravity Stop hook, which runs okf's check
#: in its place. agy runs it in ``.agents/``, one level below the repository
#: (spike:apm-hands-back/3), and blocks a stop only on ``"decision": "continue"``,
#: where okf prints Claude Code's ``"block"``. It continues only on the first
#: stop of a turn (agy counts ``executionNum`` from 0, per turn;
#: spike:antigravity-okf-stop-hook/3), as okf's own ``stop_hook_active``
#: guard does in Claude Code, and prints ``{}`` and exits 0 otherwise (I1).
STOP_COMMAND = (
    "in=$(cat); printf '%s' \"$in\" "
    "| grep -Eq '\"executionNum\"[[:space:]]*:[[:space:]]*0([^0-9]|$)' "
    "|| { echo '{}'; exit 0; }; "
    f"cd .. 2>/dev/null && [ -f {OKF_STOP_SCRIPT} ] || {{ echo '{{}}'; exit 0; }}; "
    f"out=$(printf '{{}}' | bash {OKF_STOP_SCRIPT} 2>/dev/null); "
    'case "$out" in *\'"decision":"block"\'*) printf \'%s\\n\' "$out" '
    '| sed \'s/"decision":"block"/"decision":"continue"/\';; '
    "*) echo '{}';; esac; exit 0"
)
#: Each Claude Code tool and the Antigravity tools that do its job.
TOOLS: dict[str, tuple[str, ...]] = {
    "Read": ("view_file",),
    "Grep": ("grep_search",),
    "Glob": ("find_by_name", "list_dir"),
    "Write": ("write_to_file",),
    "Edit": ("replace_file_content",),
    "Bash": ("run_command",),
}
FIX = "run kmctl plugin patch"
#: The fix for a piece APM writes from kmctl's package.
APM_FIX = (
    "run apm install --target antigravity (kmctl's package must be in apm.yml), "
    "then kmctl plugin patch"
)


def plugin_dir(cwd: Path) -> Path:
    """The folder kmctl owns in the repository at ``cwd``."""
    return cwd / PLUGIN_PATH


def agents_dir() -> Path:
    """kmctl's Claude-format agents: package data in a wheel, the repository in a checkout."""
    package = Path(str(files("kmctl")))
    if (package / "_agents").is_dir():
        return package / "_agents"
    return Path(__file__).resolve().parents[2] / "apm" / ".apm" / "agents"


class _ClaudeAgent(BaseModel):
    """A Claude Code agent's front matter, with the fields the translation keeps."""

    name: str = Field(description="The agent's name.")
    description: str = Field(description="When to dispatch it.")
    tools: str | list[str] | None = Field(
        default=None, description="Its tools: a comma string or a list."
    )


def _claude_tools(agent: _ClaudeAgent, source: str) -> list[str]:
    """The tool names in a Claude agent's ``tools:``, a comma string or a list."""
    if agent.tools is None:
        raise PluginError(
            f"the agent {source} names no tools, so kmctl cannot tell which "
            "Antigravity tools to give it; give it a tools: list"
        )
    names = agent.tools.split(",") if isinstance(agent.tools, str) else agent.tools
    return [n.strip() for n in names if n.strip()]


def translate_agent(text: str, source: str) -> str:
    """Turn a Claude Code agent file into an Antigravity one.

    The front matter keeps ``name`` and ``description``, maps ``tools`` through
    ``TOOLS`` to a YAML list, and adds ``mainAgent: false``, ``subagent: true``
    and ``model: inherit``, plus ``commandExecutionPolicy: "off"`` when the
    agent has no Bash. Every other key (``color``, ``effort``, a named
    ``model``) is dropped. The body is copied unchanged.

    Parameters
    ----------
    text :
        The Claude agent file.
    source :
        Where it came from, for error messages.

    Raises
    ------
    PluginError
        When the file has no front matter or no tools, or names a tool
        ``TOOLS`` lacks, naming that tool.
    """
    end = text.find("\n---\n", 4)
    if not text.startswith("---\n") or end == -1:
        raise PluginError(f"the agent {source} has no front matter")
    try:
        agent = _ClaudeAgent.model_validate(yaml.safe_load(text[4:end]))
    except (yaml.YAMLError, ValidationError) as error:
        raise PluginError(
            f"the agent {source} has front matter kmctl cannot read ({error}); "
            "it needs a name, a description and tools"
        ) from error
    tools: list[str] = []
    for name in _claude_tools(agent, source):
        if name not in TOOLS:
            raise PluginError(
                f"the agent {source} uses the Claude tool {name!r}, which kmctl "
                "has no Antigravity tool for; upgrade kmctl, or report it at "
                "https://github.com/JasperHG90/kmctl/issues"
            )
        tools += [t for t in TOOLS[name] if t not in tools]
    out: dict[str, object] = {
        "name": agent.name,
        "description": agent.description,
        "tools": tools,
        "mainAgent": False,
        "subagent": True,
        "model": "inherit",
    }
    if "run_command" not in tools:
        out["commandExecutionPolicy"] = "off"
    head = yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=1_000_000)
    return f"---\n{head}---\n{text[end + 5 :]}"


def package_hooks(harness: str) -> dict[str, object]:
    """The hooks.json kmctl's ``apm/HARNESS/`` sub-package ships, in Claude Code's format APM reads.

    Claude Code gets the briefing's SessionStart hook and the summary
    nudge's PostToolUse hook; Antigravity gets ``HOOK_COMMAND`` at
    SessionStart, ``NUDGE_COMMAND`` at PostToolUse after every tool and
    ``STOP_COMMAND`` at Stop. The files in the package must equal these (the
    tests check it).
    """
    from kmctl.plugin import NUDGE_MATCHER, hook_entry, nudge_hook_entry

    def group(
        handler: dict[str, object], matcher: str = "*"
    ) -> list[dict[str, object]]:
        return [{"matcher": matcher, "hooks": [handler]}]

    if harness == "claude":
        return {
            "hooks": {
                "SessionStart": group(hook_entry()),
                "PostToolUse": group(nudge_hook_entry(), NUDGE_MATCHER),
            }
        }
    start = {"type": "command", "command": HOOK_COMMAND, "timeout": HOOK_TIMEOUT}
    nudge = {"type": "command", "command": NUDGE_COMMAND, "timeout": HOOK_TIMEOUT}
    stop = {"type": "command", "command": STOP_COMMAND, "timeout": HOOK_TIMEOUT}
    return {
        "hooks": {
            "SessionStart": group(start),
            "PostToolUse": group(nudge),
            "Stop": group(stop),
        }
    }


def _runs_okf_stop(handler: object) -> bool:
    """Whether a hooks.json handler is okf's own Stop handler as APM writes it, not kmctl's wrapper."""
    return isinstance(handler, dict) and str(handler.get("command", "")).strip() == (
        APM_OKF_STOP
    )


def _apm_hooks_data(cwd: Path) -> dict[str, object] | None:
    """APM's hooks.json in ``cwd``, parsed; None when the file is missing.

    Raises
    ------
    PluginError
        When the file is not a JSON object.
    """
    path = cwd / APM_HOOKS
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        data = None
    if not isinstance(data, dict):
        raise PluginError(f"{APM_HOOKS.as_posix()} is not a JSON object")
    return data


def _okf_handlers(data: dict[str, object]) -> bool:
    """Whether any handler in a parsed hooks.json runs okf's Stop check script."""
    return any(
        _runs_okf_stop(handler)
        for events in data.values()
        if isinstance(events, dict)
        for handlers in events.values()
        if isinstance(handlers, list)
        for handler in handlers
    )


def apm_okf_stop_present(cwd: Path) -> bool:
    """Whether APM's hooks.json in ``cwd`` still runs okf's Stop check, which never works there.

    It reads the file as ``drop_apm_okf_stop`` does, so only a handler whose
    command runs the script counts.

    Raises
    ------
    PluginError
        When the file is not a JSON object, which install leaves alone and
        agy cannot load either.
    """
    data = _apm_hooks_data(cwd)
    return data is not None and _okf_handlers(data)


def drop_apm_okf_stop(cwd: Path) -> bool:
    """Take okf's Stop handlers out of APM's hooks.json in ``cwd``; return whether any went.

    APM writes okf's handler with a path from the repository root, but agy
    runs it in ``.agents/``, so it fails at the end of every turn; the
    package's Stop wrapper, which names the script too, stays and runs it
    instead. A named hook
    left with no handlers is dropped; every other hook and key stays. A
    file that is missing or not a JSON object is left alone.
    """
    path = cwd / APM_HOOKS
    try:
        data = _apm_hooks_data(cwd)
    except PluginError:
        return False
    if data is None:
        return False
    changed = False
    for name, events in list(data.items()):
        if not isinstance(events, dict):
            continue
        dropped = False
        for event, handlers in list(events.items()):
            if not isinstance(handlers, list):
                continue
            kept = [h for h in handlers if not _runs_okf_stop(h)]
            if len(kept) != len(handlers):
                dropped = True
                if kept:
                    events[event] = kept
                else:
                    del events[event]
        if dropped and not events:
            del data[name]
        changed = changed or dropped
    if changed:
        path.write_text(_json(data), encoding="utf-8")
    return changed


def _json(data: dict[str, object]) -> str:
    return json.dumps(data, indent=2) + "\n"


def plugin_files(cwd: Path) -> dict[str, str]:
    """Every file the plugin folder holds, by its path inside the folder, as this kmctl writes it.

    It holds ``plugin.json`` and the agents, translated from Claude Code's
    format: kmctl's come with the CLI, okf's from where APM put okf-skills in
    ``cwd``.

    Raises
    ------
    PluginError
        When ``apm_modules/`` holds no okf agents, which happens before
        ``apm install`` runs or in a fresh clone, or an agent cannot be
        translated.
    """
    okf = cwd / OKF_AGENTS
    if not okf.is_dir():
        raise PluginError(f"apm_modules/ is missing; {APM_FIX}")
    out = {"plugin.json": _json({"name": PLUGIN_NAME})}
    for folder in (agents_dir(), okf):
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            out[f"agents/{path.name}"] = translate_agent(text, str(path))
    return out


def write_plugin(cwd: Path) -> Path:
    """Replace the plugin folder in ``cwd`` with ``plugin_files``, and return the folder.

    Raises
    ------
    PluginError
        As ``plugin_files`` does; the folder is then left as it was.
    """
    want = plugin_files(cwd)
    folder = plugin_dir(cwd)
    if folder.exists():
        shutil.rmtree(folder)
    for rel, text in want.items():
        path = folder / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return folder


def compare_plugin(folder: Path, want: dict[str, str]) -> list[tuple[str, str]]:
    """How ``folder`` differs from ``want``: (path inside it, ``missing``, ``differs`` or ``extra``), sorted."""
    have = {
        p.relative_to(folder).as_posix(): p
        for p in folder.rglob("*")
        if p.is_file() or p.is_symlink()
    }
    found = []
    for rel in sorted(want.keys() | have.keys()):
        if rel not in have:
            found.append((rel, "missing"))
        elif rel not in want:
            found.append((rel, "extra"))
        elif have[rel].read_bytes() != want[rel].encode("utf-8"):
            found.append((rel, "differs"))
    return found


_SAID = {
    "missing": "is missing",
    "differs": "differs from what this kmctl writes",
    "extra": "is not one kmctl writes",
}


def plugin_problems(cwd: Path) -> list[str]:
    """One line per file under the plugin folder in ``cwd`` that differs from what this kmctl writes.

    Each line names the file and how it differs; the fix for every one is
    ``FIX``.

    Raises
    ------
    PluginError
        As ``plugin_files`` does, such as when ``apm_modules/`` is missing.
    """
    want = plugin_files(cwd)
    shown = PLUGIN_PATH.as_posix()
    return [
        f"{shown}/{rel} {_SAID[kind]}"
        for rel, kind in compare_plugin(plugin_dir(cwd), want)
    ]


def _commands(data: dict[str, object], event: str) -> list[str]:
    """The commands of every ``event`` handler in a parsed Antigravity hooks.json.

    APM 0.33.0 writes SessionStart and Stop handlers flat, and PreToolUse and
    PostToolUse ones nested in ``{matcher, hooks}`` groups; both forms count.
    """
    handlers = [
        item
        for events in data.values()
        if isinstance(events, dict)
        for item in events.get(event, [])
        if isinstance(item, dict)
    ]
    for group in [h for h in handlers if isinstance(h.get("hooks"), list)]:
        handlers += [h for h in group["hooks"] if isinstance(h, dict)]
    return [str(h.get("command", "")) for h in handlers if "hooks" not in h]


def _hooks_data(cwd: Path) -> dict[str, object]:
    """APM's hooks.json in ``cwd``, parsed; empty when it is missing or not a JSON object."""
    try:
        return _apm_hooks_data(cwd) or {}
    except PluginError:
        return {}


def hook_present(cwd: Path) -> bool:
    """Whether APM's ``.agents/hooks.json`` in ``cwd`` holds the package's SessionStart and Stop hooks."""
    data = _hooks_data(cwd)
    return HOOK_COMMAND in _commands(data, "SessionStart") and (
        STOP_COMMAND in _commands(data, "Stop")
    )


def nudge_hook_present(cwd: Path) -> bool:
    """Whether APM's ``.agents/hooks.json`` in ``cwd`` holds the package's PostToolUse summary nudge."""
    return NUDGE_COMMAND in _commands(_hooks_data(cwd), "PostToolUse")


def mcp_present(cwd: Path) -> bool:
    """Whether ``.agents/mcp_config.json`` in ``cwd`` declares okf's server as kmctl's package does."""
    path = cwd / ".agents" / "mcp_config.json"
    try:
        servers = json.loads(path.read_text(encoding="utf-8")).get("mcpServers")
    except (OSError, ValueError, AttributeError):
        return False
    return isinstance(servers, dict) and okf_server_current(servers.get(MCP_NAME))
