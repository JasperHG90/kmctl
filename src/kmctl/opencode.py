"""What kmctl adds to APM's OpenCode install (ADR 0024).

APM 0.33.0 writes kmctl's and okf's skills into ``.agents/skills/``, copies
the agents into ``.opencode/agents/`` unchanged, and writes okf's MCP server
into ``opencode.json``. It writes no rules or hooks for OpenCode, and the
agents it copies keep Claude Code's front matter, which OpenCode drops
without a word (spike:opencode-harness/1). kmctl adds the rest:

- Agents: it rewrites kmctl's and okf's three agents in ``.opencode/agents/``
  into OpenCode's format. ``apm install`` writes APM's copies back, so patch
  runs after every install (spike:opencode-harness/4, /7).
- Rules: OpenCode has no rules folder; it loads the files the
  ``instructions`` list of ``opencode.json`` names. kmctl writes its four
  rules to ``.opencode/rules/`` and adds ``.opencode/rules/*.md`` to that
  list. Every rule loads in every session.
- The briefing and the summary nudge: a plugin, ``.opencode/plugins/kmctl.js``,
  that runs ``kmctl briefing`` once and adds its text to the system prompt
  (spike:opencode-harness/2), and runs ``kmctl summary nudge`` after each
  tool call and adds its text to that tool's result
  (spike:okf-summary-nudge-agy-opencode/2, ADR 0028).

Every function here prints nothing. ``files`` says what kmctl writes,
``write`` writes it, ``undo`` deletes it, and the ``*_problems`` functions
report how what is on disk differs, for ``kmctl doctor``.
"""

import json
from importlib.resources import files as package_files
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError

from kmctl.antigravity import OKF_AGENTS, agents_dir
from kmctl.plugin import (
    HOOK_TIMEOUT,
    MCP_NAME,
    PluginError,
    okf_mcp_launcher,
    read_json,
)

AGENTS = Path(".opencode") / "agents"
RULES = Path(".opencode") / "rules"
PLUGIN = Path(".opencode") / "plugins" / "kmctl.js"
CONFIG = Path("opencode.json")
#: The entry kmctl adds to opencode.json's ``instructions``. OpenCode globs it
#: from the start folder up to the git root (spike:opencode-harness/1).
INSTRUCTIONS = ".opencode/rules/*.md"
#: Each Claude Code tool and the OpenCode 2.x permission that covers it. Its
#: write and patch tools ask as ``edit``, and its Bash is ``shell``.
TOOLS: dict[str, str] = {
    "Read": "read",
    "Grep": "grep",
    "Glob": "glob",
    "Write": "edit",
    "Edit": "edit",
    "Bash": "shell",
}
FIX = "run kmctl plugin patch"
APM_FIX = (
    "run apm install --target opencode (kmctl's package must be in apm.yml), "
    "then kmctl plugin patch"
)
#: The marker ``nudge_problems`` looks for: the plugin's after-tool hook.
NUDGE_HOOK = 'ctx.tool.hook("execute.after"'
#: The plugin OpenCode 2.x loads from ``.opencode/plugins/``: a default export
#: ``{id, setup}`` (spike:opencode-harness/2). setup starts ``kmctl briefing``
#: once without waiting for it, and the ``context`` hook adds its text before
#: each request. The ``execute.after`` hook runs ``kmctl summary nudge
#: --format opencode`` after each tool call and adds its text to that tool's
#: result, which the model reads once (spike:okf-summary-nudge-agy-opencode/2).
#: It closes the child's stdin, which ``execFile`` would leave open, and sets
#: KMCTL_PINNED=1 for the reason ``kmctl.plugin.NUDGE_COMMAND`` gives.
#: OpenCode catches nothing a plugin throws, so every step swallows its
#: errors: with kmctl missing or failing it adds nothing (I1).
PLUGIN_SOURCE = f"""\
// Written by kmctl plugin patch; it rewrites this file. kmctl plugin patch
// --undo deletes it. It adds kmctl's knowledge briefing to each session and
// its summary nudge to a tool's result, and never fails either: without a
// working kmctl it adds nothing.
import {{ execFile, spawn }} from "node:child_process"

const briefing = (cwd) =>
  new Promise((resolve) => {{
    try {{
      execFile(
        "kmctl",
        ["briefing", "--path", cwd],
        {{ cwd, timeout: {HOOK_TIMEOUT * 1000}, windowsHide: true }},
        (error, stdout) => resolve(error ? "" : String(stdout).trim()),
      )
    }} catch {{
      resolve("")
    }}
  }})

const nudge = (cwd) =>
  new Promise((resolve) => {{
    try {{
      const child = spawn(
        "kmctl",
        ["summary", "nudge", "--format", "opencode", "--path", cwd],
        {{
          cwd,
          env: {{ ...process.env, KMCTL_PINNED: "1" }},
          stdio: ["ignore", "pipe", "ignore"],
          timeout: {HOOK_TIMEOUT * 1000},
          windowsHide: true,
        }},
      )
      let out = ""
      child.stdout.on("data", (chunk) => {{
        out += chunk
      }})
      child.on("error", () => resolve(""))
      child.on("close", (code) => resolve(code === 0 ? out.trim() : ""))
    }} catch {{
      resolve("")
    }}
  }})

const said = async (text) => {{
  try {{
    return await text
  }} catch {{
    return ""
  }}
}}

export default {{
  id: "kmctl",
  setup: async (ctx) => {{
    const where = ctx?.location
    const cwd = where?.project?.directory ?? where?.directory ?? process.cwd()
    try {{
      const text = briefing(cwd)
      await ctx.session.hook("context", async (event) => {{
        try {{
          const out = await said(text)
          if (out) event.system.push({{ type: "text", text: out }})
        }} catch {{}}
      }})
    }} catch {{}}
    try {{
      await {NUDGE_HOOK}, async (event) => {{
        try {{
          const content = event?.result?.content
          if (!Array.isArray(content)) return
          const out = await nudge(cwd)
          if (out) content.push({{ type: "text", text: out }})
        }} catch {{}}
      }})
    }} catch {{}}
  }},
}}
"""


def rules_dir() -> Path:
    """kmctl's rules in Claude Code's form: package data in a wheel, the repository in a checkout."""
    package = Path(str(package_files("kmctl")))
    if (package / "_rules").is_dir():
        return package / "_rules"
    return (
        Path(__file__).resolve().parents[2] / "apm" / "claude" / ".apm" / "instructions"
    )


def _split(text: str, source: str) -> tuple[object, str]:
    """A markdown file's parsed front matter and its body.

    Raises
    ------
    PluginError
        When the file has no front matter, or it is not YAML.
    """
    end = text.find("\n---\n", 4)
    if not text.startswith("---\n") or end == -1:
        raise PluginError(f"{source} has no front matter")
    try:
        return yaml.safe_load(text[4:end]), text[end + 5 :]
    except yaml.YAMLError as error:
        raise PluginError(
            f"{source} has front matter kmctl cannot read ({error})"
        ) from error


class _ClaudeAgent(BaseModel):
    """A Claude Code agent's front matter, with the fields the translation reads."""

    description: str = Field(description="When to dispatch it.")
    tools: str | list[str] = Field(description="Its tools: a comma string or a list.")


def translate_agent(text: str, source: str) -> str:
    """Turn a Claude Code agent file into an OpenCode one.

    The front matter keeps ``description``, adds ``mode: subagent`` and writes
    ``permission``: ``"*": deny`` first, then ``allow`` for each tool mapped
    through ``TOOLS`` (the last matching rule wins). Every other key goes:
    ``name`` (OpenCode takes it from the file name), ``color``, ``effort``,
    ``model``; OpenCode would send an unknown key to the model provider.
    The body is copied unchanged.

    Parameters
    ----------
    text :
        The Claude agent file.
    source :
        Where it came from, for error messages.

    Raises
    ------
    PluginError
        When the file has no front matter, no description or no tools, or
        names a tool ``TOOLS`` lacks, naming that tool.
    """
    meta, body = _split(text, f"the agent {source}")
    try:
        agent = _ClaudeAgent.model_validate(meta)
    except ValidationError as error:
        raise PluginError(
            f"the agent {source} has front matter kmctl cannot read ({error}); "
            "it needs a description and tools"
        ) from error
    names = agent.tools.split(",") if isinstance(agent.tools, str) else agent.tools
    permission: dict[str, str] = {"*": "deny"}
    for name in (n.strip() for n in names if n.strip()):
        if name not in TOOLS:
            raise PluginError(
                f"the agent {source} uses the Claude tool {name!r}, which kmctl "
                "has no OpenCode permission for; upgrade kmctl, or report it at "
                "https://github.com/JasperHG90/kmctl/issues"
            )
        permission[TOOLS[name]] = "allow"
    out = {
        "description": agent.description,
        "mode": "subagent",
        "permission": permission,
    }
    head = yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=1_000_000)
    return f"---\n{head}---\n{body}"


def translate_rule(text: str, source: str) -> str:
    """Turn a rule in APM's instructions form into an OpenCode one: the body, under a notice.

    OpenCode loads every file ``instructions`` names in every session, so the
    ``applyTo`` front matter, which it would not read, goes.

    Raises
    ------
    PluginError
        When the file has no front matter.
    """
    _, body = _split(text, f"the rule {source}")
    notice = (
        "<!-- Written by kmctl plugin patch from kmctl's package; it rewrites "
        "this file. OpenCode loads it in every session. -->\n"
    )
    return notice + body.lstrip("\n")


def agent_paths(cwd: Path) -> frozenset[str]:
    """The agents patch rewrites in ``.opencode/agents/``, by path from the repository.

    kmctl's always; okf's when APM put okf-skills in ``cwd``.
    """
    folders = [agents_dir(), cwd / OKF_AGENTS]
    return frozenset(
        (AGENTS / p.name).as_posix() for folder in folders for p in folder.glob("*.md")
    )


def agent_files(cwd: Path) -> dict[str, str]:
    """Each agent kmctl writes into ``.opencode/agents/``, by its path from the repository.

    kmctl's come with the CLI, okf's from where APM put okf-skills in ``cwd``.

    Raises
    ------
    PluginError
        When ``apm_modules/`` holds no okf agents, which happens before
        ``apm install`` runs, or an agent cannot be translated.
    """
    okf = cwd / OKF_AGENTS
    if not okf.is_dir():
        raise PluginError(f"apm_modules/ is missing; {APM_FIX}")
    out = {}
    for folder in (agents_dir(), okf):
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            out[(AGENTS / path.name).as_posix()] = translate_agent(text, str(path))
    return out


def rule_files() -> dict[str, str]:
    """Each rule kmctl writes into ``.opencode/rules/``, by its path from the repository."""
    out = {}
    for path in sorted(rules_dir().glob("*.instructions.md")):
        name = path.name.removesuffix(".instructions.md") + ".md"
        text = path.read_text(encoding="utf-8")
        out[(RULES / name).as_posix()] = translate_rule(text, str(path))
    return out


def files(cwd: Path) -> dict[str, str]:
    """Every file kmctl writes for OpenCode in ``cwd``, by its path from the repository, as this kmctl writes it.

    Raises
    ------
    PluginError
        As ``agent_files`` does.
    """
    return {**agent_files(cwd), **rule_files(), PLUGIN.as_posix(): PLUGIN_SOURCE}


def _config(cwd: Path) -> dict[str, object]:
    """opencode.json in ``cwd``, parsed; empty when it is missing.

    Raises
    ------
    PluginError
        When the file is not a JSON object, naming it.
    """
    return read_json(cwd / CONFIG)


def _write_config(cwd: Path, data: dict[str, object]) -> None:
    """Write opencode.json as APM 0.33.0 does: two-space indent, no final newline.

    APM rewrites the file on every install, so matching its bytes keeps an
    install and a patch from changing it back and forth.
    """
    (cwd / CONFIG).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _instructions(data: dict[str, object]) -> list[object]:
    """opencode.json's ``instructions`` list, empty when the key is missing.

    Raises
    ------
    PluginError
        When the key is there but is not a list.
    """
    listed = data.get("instructions", [])
    if not isinstance(listed, list):
        raise PluginError(
            f"{CONFIG.as_posix()} has an instructions key that is not a list; fix "
            "it, then run the command again"
        )
    return listed


def add_instructions(cwd: Path) -> bool:
    """Add ``INSTRUCTIONS`` to opencode.json's ``instructions`` once, keeping every other key; return whether the file changed.

    It creates the file when it is missing.

    Raises
    ------
    PluginError
        When opencode.json is not a JSON object, or its ``instructions`` is
        not a list; the file is left as it was.
    """
    data = _config(cwd)
    listed = _instructions(data)
    data["instructions"] = listed
    if INSTRUCTIONS in listed:
        return False
    listed.append(INSTRUCTIONS)
    _write_config(cwd, data)
    return True


def write(cwd: Path) -> list[str]:
    """Write ``files`` into ``cwd`` and add the instructions entry; return the paths that changed.

    A file that already holds what kmctl writes is left alone, so a second run
    changes nothing.

    Raises
    ------
    PluginError
        As ``files`` and ``add_instructions`` do; nothing is written then.
    """
    want = files(cwd)
    _instructions(_config(cwd))  # refuse an unusable opencode.json before writing
    changed = []
    for rel, text in want.items():
        path = cwd / rel
        if path.is_file() and path.read_bytes() == text.encode("utf-8"):
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        changed.append(rel)
    if add_instructions(cwd):
        changed.append(CONFIG.as_posix())
    return changed


def undo_paths(cwd: Path) -> list[str]:
    """What ``undo`` would delete or change in ``cwd``, by path from the repository; it changes nothing.

    The agents that are still kmctl's translation, the rules and the plugin
    that are there, and opencode.json when its ``instructions`` lists
    ``INSTRUCTIONS``.
    """
    try:
        agents = agent_files(cwd)
    except PluginError:
        agents = {}
    found = [
        rel
        for rel, text in agents.items()
        if (cwd / rel).is_file() and (cwd / rel).read_bytes() == text.encode("utf-8")
    ]
    found += [
        rel for rel in [*rule_files(), PLUGIN.as_posix()] if (cwd / rel).is_file()
    ]
    try:
        listed = _config(cwd).get("instructions")
    except PluginError:
        return found
    if isinstance(listed, list) and INSTRUCTIONS in listed:
        found.append(CONFIG.as_posix())
    return found


def undo(cwd: Path) -> list[str]:
    """Delete what ``write`` wrote in ``cwd``; return the paths it deleted or changed, as ``undo_paths`` names them.

    The rules and the plugin go. An agent goes only when it is still
    kmctl's translation, so ``apm uninstall`` can then remove APM's own
    files (spike:opencode-harness/7). The instructions entry goes from
    opencode.json, and the file goes once nothing is left in it. Folders
    left empty go. An unreadable opencode.json is left alone.
    """
    done = undo_paths(cwd)
    for rel in done:
        if rel != CONFIG.as_posix():
            (cwd / rel).unlink()
    for folder in (RULES, PLUGIN.parent):
        if (cwd / folder).is_dir() and not any((cwd / folder).iterdir()):
            (cwd / folder).rmdir()
    if CONFIG.as_posix() in done:
        data = _config(cwd)
        listed = _instructions(data)
        listed.remove(INSTRUCTIONS)
        if not listed:
            del data["instructions"]
        if data:
            _write_config(cwd, data)
        else:
            (cwd / CONFIG).unlink()
    return done


_SAID = {"missing": "is missing", "differs": "differs from what this kmctl writes"}


def _problems(cwd: Path, want: dict[str, str]) -> list[str]:
    """One line per file in ``want`` that is missing in ``cwd`` or differs."""
    found = []
    for rel, text in want.items():
        path = cwd / rel
        if not path.is_file():
            found.append(f"{rel} {_SAID['missing']}")
        elif path.read_bytes() != text.encode("utf-8"):
            found.append(f"{rel} {_SAID['differs']}")
    return found


def agent_problems(cwd: Path) -> list[str]:
    """How each agent in ``.opencode/agents/`` differs from kmctl's translation, such as after a bare ``apm install``.

    Raises
    ------
    PluginError
        As ``agent_files`` does.
    """
    return _problems(cwd, agent_files(cwd))


def rule_problems(cwd: Path) -> list[str]:
    """How the rules and opencode.json's instructions entry differ from what this kmctl writes."""
    found = _problems(cwd, rule_files())
    try:
        listed = _config(cwd).get("instructions")
    except PluginError:
        return [*found, f"{CONFIG.as_posix()} is not a JSON object"]
    if not (isinstance(listed, list) and INSTRUCTIONS in listed):
        found.append(f"{CONFIG.as_posix()}'s instructions lacks {INSTRUCTIONS}")
    return found


def hook_problems(cwd: Path) -> list[str]:
    """How the briefing plugin differs from what this kmctl writes."""
    return _problems(cwd, {PLUGIN.as_posix(): PLUGIN_SOURCE})


def nudge_problems(cwd: Path) -> list[str]:
    """Why the plugin in ``cwd`` runs no summary nudge after a tool call: it is missing or lacks ``NUDGE_HOOK``."""
    path = cwd / PLUGIN
    shown = PLUGIN.as_posix()
    if not path.is_file():
        return [f"{shown} {_SAID['missing']}"]
    if NUDGE_HOOK not in path.read_text(encoding="utf-8", errors="replace"):
        return [f"{shown} lacks the execute.after hook that runs kmctl summary nudge"]
    return []


def mcp_present(cwd: Path) -> bool:
    """Whether opencode.json declares okf's server as APM writes it from kmctl's package (spike:opencode-harness/6)."""
    try:
        servers = _config(cwd).get("mcp")
    except PluginError:
        return False
    server = servers.get(MCP_NAME) if isinstance(servers, dict) else None
    command = ["sh", "-c", okf_mcp_launcher()]
    return (
        isinstance(server, dict)
        and server.get("type") == "local"
        and server.get("enabled", True) is True
        and server.get("command") == command
    )
