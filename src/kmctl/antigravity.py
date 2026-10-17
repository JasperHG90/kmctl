"""The Antigravity plugin folder kmctl writes beside APM's install (ADR 0015).

APM 0.33.0 installs skills for Antigravity into ``.agents/``, but no agents
and no MCP server Antigravity reads, and rules agy cannot use: a YAML list of
globs, which agy refuses, and globs relative to the repository, which agy
matches against absolute paths. kmctl writes the agents, the rules, the MCP
server and the SessionStart hook into one folder it alone owns,
``.agents/plugins/kmctl/``, which Antigravity loads from a trusted workspace
(spike:antigravity-harness/3, spike:antigravity-rules/3), and deletes APM's
copies of its rules.

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

from kmctl.plugin import HOOK_TIMEOUT, PluginError, okf_mcp_launcher

#: Where the folder sits, relative to the repository.
PLUGIN_PATH = Path(".agents") / "plugins" / "kmctl"
PLUGIN_NAME = "kmctl"
#: The hook's name in hooks.json, which maps names to hooks.
HOOK_NAME = "kmctl-briefing"
#: The name Antigravity shows for okf's MCP server.
MCP_NAME = "bundle"
#: Where APM puts okf-skills' Claude-format agents, relative to the repository.
OKF_AGENTS = Path("apm_modules") / "scaccogatto" / "okf-skills" / "agents"
#: Where APM writes rules for Antigravity, relative to the repository.
APM_RULES = ".agents/rules/"
#: The prefix agy needs on a glob: it matches a glob holding a ``/`` against
#: the file's absolute path (spike:antigravity-rules/3).
ANY_FOLDER = "**/"
#: The command the hook runs. Antigravity fails a hook whose stdout is not
#: JSON, so it prints ``{}`` and exits 0 when kmctl is missing or fails (I1).
HOOK_COMMAND = (
    "command -v kmctl >/dev/null 2>&1 || { echo '{}'; exit 0; }; "
    "out=$(kmctl briefing --format antigravity 2>/dev/null) "
    "&& printf '%s\\n' \"$out\" || echo '{}'; exit 0"
)
#: Where the MCP launcher starts looking for ``.okf/``: the repository the
#: plugin folder sits in, when Antigravity sets PLUGIN_ROOT, then the working
#: folder.
MCP_STARTS = ('"${PLUGIN_ROOT:+$PLUGIN_ROOT/../../..}"', '"$PWD"')
#: Each Claude Code tool and the Antigravity tools that do its job.
TOOLS: dict[str, tuple[str, ...]] = {
    "Read": ("view_file",),
    "Grep": ("grep_search",),
    "Glob": ("find_by_name", "list_dir"),
    "Write": ("write_to_file",),
    "Edit": ("replace_file_content",),
    "Bash": ("run_command",),
}
FIX = "run kmctl plugin install --harness antigravity"


def plugin_dir(cwd: Path) -> Path:
    """The folder kmctl owns in the repository at ``cwd``."""
    return cwd / PLUGIN_PATH


def agents_dir() -> Path:
    """kmctl's Claude-format agents: package data in a wheel, the repository in a checkout."""
    package = Path(str(files("kmctl")))
    if (package / "_agents").is_dir():
        return package / "_agents"
    return Path(__file__).resolve().parents[2] / "apm" / ".apm" / "agents"


def instructions_dir() -> Path:
    """kmctl's APM instructions: package data in a wheel, the repository in a checkout."""
    package = Path(str(files("kmctl")))
    if (package / "_instructions").is_dir():
        return package / "_instructions"
    return Path(__file__).resolve().parents[2] / "apm" / ".apm" / "instructions"


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
                "https://github.com/JasperHG90/Knowledge-management/issues"
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


class _Instruction(BaseModel):
    """An APM instruction's front matter: the globs it applies to, if any."""

    apply_to: str | list[str] | None = Field(
        default=None,
        alias="applyTo",
        description="A comma-separated string or a list of globs, relative to the repository.",
    )


def _globs(apply_to: str | list[str] | None) -> list[str]:
    """The globs of an ``applyTo`` value, each with the ``**/`` prefix agy needs."""
    items = apply_to.split(",") if isinstance(apply_to, str) else apply_to or []
    globs = [g.strip() for g in items if g.strip()]
    return [g if g.startswith(ANY_FOLDER) else ANY_FOLDER + g for g in globs]


def translate_rule(text: str, source: str) -> str:
    """An APM instruction file rewritten as an Antigravity rule.

    ``applyTo`` becomes ``trigger: glob`` and ``globs:`` as one
    comma-separated string, the only form agy reads, with each glob given a
    leading ``**/``. An instruction without ``applyTo`` becomes
    ``trigger: always_on``. The body is copied unchanged.

    Parameters
    ----------
    text :
        The instruction file.
    source :
        Where it came from, for error messages.

    Raises
    ------
    PluginError
        When the front matter is not YAML or ``applyTo`` is not a string or
        a list of strings.
    """
    body = text
    meta: object = {}
    end = text.find("\n---\n", 4)
    if text.startswith("---\n") and end != -1:
        body = text[end + 5 :]
        try:
            meta = yaml.safe_load(text[4:end]) or {}
        except yaml.YAMLError as error:
            raise PluginError(
                f"the instruction {source} has front matter that is not YAML ({error})"
            ) from error
    try:
        instruction = _Instruction.model_validate(meta)
    except ValidationError as error:
        raise PluginError(
            f"the instruction {source} has an applyTo kmctl cannot read ({error}); "
            "it must be a comma-separated string of globs"
        ) from error
    globs = _globs(instruction.apply_to)
    if not globs:
        return f"---\ntrigger: always_on\n---\n{body}"
    return f"---\ntrigger: glob\nglobs: {json.dumps(', '.join(globs))}\n---\n{body}"


def drop_apm_rules(cwd: Path, deployed: list[str]) -> list[str]:
    """Delete the rule files APM wrote for kmctl's package in ``cwd``, and return their paths.

    ``deployed`` is the lock's ``deployed_files`` for kmctl's package; only
    those under ``APM_RULES`` go, so every other package's rules stay.
    """
    gone = []
    for rel in deployed:
        path = cwd / rel
        if rel.startswith(APM_RULES) and path.is_file():
            path.unlink()
            gone.append(rel)
    return gone


def hooks() -> dict[str, object]:
    """hooks.json: one named hook with one SessionStart handler."""
    handler = {"type": "command", "command": HOOK_COMMAND, "timeout": HOOK_TIMEOUT}
    return {HOOK_NAME: {"SessionStart": [handler]}}


def mcp_config() -> dict[str, object]:
    """mcp_config.json: okf's MCP server, run by the launcher Claude Code's entry uses."""
    launcher = okf_mcp_launcher(starts=MCP_STARTS)
    return {"mcpServers": {MCP_NAME: {"command": "sh", "args": ["-c", launcher]}}}


def _json(data: dict[str, object]) -> str:
    return json.dumps(data, indent=2) + "\n"


def plugin_files(cwd: Path) -> dict[str, str]:
    """Every file the plugin folder holds, by its path inside the folder, as this kmctl writes it.

    kmctl's agents and rules come with the CLI; okf's agents come from where
    APM put okf-skills in ``cwd``.

    Raises
    ------
    PluginError
        When ``apm_modules/`` holds no okf agents, which happens before
        ``apm install`` runs or in a fresh clone, or an agent cannot be
        translated.
    """
    okf = cwd / OKF_AGENTS
    if not okf.is_dir():
        raise PluginError(f"apm_modules/ is missing; {FIX}")
    out = {
        "plugin.json": _json({"name": PLUGIN_NAME}),
        "hooks.json": _json(hooks()),
        "mcp_config.json": _json(mcp_config()),
    }
    for folder in (agents_dir(), okf):
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            out[f"agents/{path.name}"] = translate_agent(text, str(path))
    for path in sorted(instructions_dir().glob("*.instructions.md")):
        name = path.name.removesuffix(".instructions.md")
        text = path.read_text(encoding="utf-8")
        out[f"rules/{name}.md"] = translate_rule(text, str(path))
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


def hook_present(cwd: Path) -> bool:
    """Whether the plugin folder's hooks.json is exactly the one this kmctl writes."""
    path = plugin_dir(cwd) / "hooks.json"
    return path.is_file() and path.read_text(encoding="utf-8") == _json(hooks())
