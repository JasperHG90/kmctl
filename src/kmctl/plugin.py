"""What kmctl adds to an APM install of its package, and the pieces doctor and the CLI share (ADR 0014, ADR 0020, ADR 0021).

APM installs kmctl's package from a repository's apm.yml: the skills, the
audit agent, the rules, the SessionStart hooks and okf's MCP server.
``patch``, run after ``apm install``, adds only what APM cannot install yet:
for Antigravity, the plugin folder of agents ``kmctl.antigravity`` builds and
the removal of APM's broken okf Stop handler; for Claude Code, it moves older
installs over (the hook and MCP entry an older kmctl wrote itself, and the
claude plugin ``kmctl@kmctl``, ADR 0003). It never runs APM.

Each step is its own function and prints nothing, so ``kmctl doctor`` and the
Antigravity harness can reuse the hook entry, the MCP entry and its launcher.
"""

import json
import os
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

import yaml
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

Scope = Literal["project", "user"]
#: The harnesses kmctl's package installs for, in the order doctor lists them.
HARNESSES = ("claude", "antigravity")
#: The APM release kmctl's docs and doctor name, run through uvx.
APM_CLI = "apm-cli==0.33.0"
#: kmctl's GitHub repository.
REPO = "JasperHG90/kmctl"
#: The repository's name until it was renamed; installs made then still carry it.
OLD_REPO = "JasperHG90/Knowledge-management"
#: Where kmctl's package comes from: the git URL of the apm.yml entry it suggests.
DEFAULT_SOURCE = f"https://github.com/{REPO}.git"
#: The package's folder inside the source repository.
PACKAGE_PATH = "apm"
#: How an apm.yml written by hand (ADR 0013) names the package.
OLD_PACKAGE = f"{OLD_REPO}/apm"
#: The claude plugin and marketplace the install route before ADR 0014 added.
OLD_PLUGIN = "kmctl@kmctl"
OLD_MARKETPLACE = "kmctl"
#: The okf-skills commit apm/apm.yml pins; a test keeps the two equal.
OKF_COMMIT = "a8b96420de90d102c43cda1693d01ec4f925f2ab"
#: The name kmctl gives okf's MCP server; it replaces only a server of this name.
MCP_NAME = "okf-bundle"
#: What marks an MCP server as okf's, under whatever name it was added.
OKF_MCP_SCRIPT = "okf_mcp.py"
#: The text that marks a settings.json hook as kmctl's.
HOOK_MARK = "kmctl briefing"
HOOK_COMMAND = (
    "command -v kmctl >/dev/null 2>&1 || { echo '[kmctl] kmctl is not installed, "
    "so there is no knowledge briefing. Install it with: uv tool install "
    f"git+https://github.com/{REPO}'; exit 0; }}; "
    "kmctl briefing || echo '[kmctl] kmctl briefing failed; run kmctl briefing in "
    "a terminal to see why, or upgrade with uv tool install --force "
    f"git+https://github.com/{REPO}.'; exit 0"
)
HOOK_DESCRIPTION = (
    "kmctl: print the knowledge briefing (where knowledge lives, what is due, "
    "the rules). Never blocks."
)
HOOK_TIMEOUT = 10
#: The most characters of a tool's output a PluginError carries.
CAUSE_CAP = 400


class PluginError(Exception):
    """An install step that failed; the message names the fix."""


class _ClaudePlugin(BaseModel):
    """One entry of ``claude plugin list --json``."""

    id: str = Field(description="The plugin id, NAME@MARKETPLACE.")
    scope: str | None = Field(default=None, description="user, project or local.")
    project_path: str | None = Field(
        default=None,
        alias="projectPath",
        description="The repository a project or local install belongs to.",
    )


_CLAUDE_PLUGINS = TypeAdapter(list[_ClaudePlugin])


class LockDependency(BaseModel):
    """One package in apm.lock.yaml, with the fields kmctl reads."""

    repo_url: str | None = Field(
        default=None, description="Where the package came from, such as owner/repo."
    )
    host: str | None = Field(
        default=None, description="The git host, when it is not github.com."
    )
    port: int | None = Field(default=None, description="The git host's port, if any.")
    name: str | None = Field(default=None, description="The package's apm.yml name.")
    virtual_path: str | None = Field(
        default=None, description="The package's folder inside its repository."
    )
    resolved_ref: str | None = Field(
        default=None, description="The ref APM installed, such as v0.4.0."
    )
    deployed_files: list[str] = Field(
        default_factory=list, description="Files and folders APM wrote for it."
    )
    deployed_file_hashes: dict[str, str] = Field(
        default_factory=dict,
        description="Each deployed file's hash as APM recorded it, sha256:HEX.",
    )


class Lock(BaseModel):
    """apm.lock.yaml, with the fields kmctl reads."""

    dependencies: list[LockDependency] = Field(
        default_factory=list, description="The installed packages."
    )


def cli_version() -> str:
    """This kmctl's version, which names the package tag it installs."""
    return version("kmctl")


def package_ref() -> str:
    """The git tag of the package this CLI installs: ``v<cli version>`` (ADR 0001)."""
    return f"v{cli_version()}"


def okf_mcp_url() -> str:
    """The raw URL of okf's MCP server script at the pinned okf-skills commit."""
    return (
        f"https://raw.githubusercontent.com/scaccogatto/okf-skills/{OKF_COMMIT}"
        "/servers/okf_mcp.py"
    )


def skills_dir() -> Path:
    """The package's skills/ folder: package data in a wheel, the repository in a checkout."""
    package = Path(str(files("kmctl")))
    if (package / "_skills").is_dir():
        return package / "_skills"
    return Path(__file__).resolve().parents[2] / "apm" / ".apm" / "skills"


def claude_config_dir() -> Path:
    """The folder Claude Code reads user files from: $CLAUDE_CONFIG_DIR, by default ~/.claude."""
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(configured) if configured else Path.home() / ".claude"


def settings_path(cwd: Path, scope: Scope) -> Path:
    """The settings.json the hook goes in: the repository's, or the user's."""
    if scope == "user":
        return claude_config_dir() / "settings.json"
    return cwd / ".claude" / "settings.json"


def apm_dir(cwd: Path, scope: Scope) -> Path:
    """The folder holding apm.yml and apm.lock.yaml: the repository, or ~/.apm at user scope."""
    return Path.home() / ".apm" if scope == "user" else cwd


def apm_root(cwd: Path, scope: Scope) -> Path:
    """Where APM runs, which is also the root of the paths its lock records."""
    return Path.home() if scope == "user" else cwd


def user_mcp_file() -> Path:
    """The file claude keeps user-scope MCP servers in."""
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(configured) if configured else Path.home()) / ".claude.json"


def _cause(output: str) -> str:
    """The lines of ``output`` that say why a tool failed, joined with "; ".

    git's ``fatal:`` and ``error:`` lines and APM's ``[x]`` lines name the
    cause, but the tool may print them before a last line that does not. So
    keep those lines in order, then the last line, cut to CAUSE_CAP
    characters.
    """
    lines = [line.strip() for line in output.strip().splitlines() if line.strip()]
    if not lines:
        return "no output"
    kept = [line for line in lines if line.startswith(("fatal:", "error:", "[x]"))]
    if lines[-1] not in kept[-1:]:
        kept.append(lines[-1])
    cause = "; ".join(kept)
    return cause if len(cause) <= CAUSE_CAP else cause[: CAUSE_CAP - 1] + "…"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a command in ``cwd`` and capture its output."""
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


def _require(
    proc: subprocess.CompletedProcess[str],
    what: str,
    again: str = "kmctl plugin patch",
) -> None:
    """Raise when ``proc`` failed, naming the command ``what``, its cause and the verb ``again`` to rerun."""
    if proc.returncode != 0:
        output = f"{proc.stderr}\n{proc.stdout}"
        raise PluginError(
            f"{what} failed: {_cause(output)}; run it by hand to see why, then "
            f"{again} again"
        )


# Old installs ------------------------------------------------------------------


def remove_old_plugin(cwd: Path, scope: Scope) -> list[str]:
    """Remove the claude plugin ``kmctl@kmctl`` where it applies here, and say what happened.

    A project or local install counts when its project path is ``cwd``; a user
    install counts at user scope. For each, it runs ``claude plugin uninstall``,
    then ``claude plugin prune`` (so okf, installed only as kmctl's dependency,
    goes too, while an okf the user installed on purpose stays) and
    ``claude plugin marketplace remove kmctl``, at that scope
    (spike:apm-only-install/7).

    Returns
    -------
    list[str]
        Notes for the reader: what was removed, or why the step was skipped.

    Raises
    ------
    PluginError
        When an uninstall step fails.
    """
    if shutil.which("claude") is None:
        return [
            (
                "the claude CLI is not on PATH, so kmctl did not look for the old "
                f"{OLD_PLUGIN} plugin"
            )
        ]
    listed = _run(["claude", "plugin", "list", "--json"], cwd)
    if listed.returncode != 0:
        return [
            (
                f"claude plugin list failed ({_cause(listed.stderr + listed.stdout)}), "
                f"so kmctl did not look for the old {OLD_PLUGIN} plugin"
            )
        ]
    try:
        plugins = _CLAUDE_PLUGINS.validate_json(listed.stdout or "[]")
    except ValidationError as error:
        raise PluginError(
            f"claude plugin list --json printed a list kmctl cannot read ({error}); "
            "upgrade Claude Code, then run kmctl plugin patch again"
        ) from error
    here = cwd.resolve()
    scopes: list[str] = []
    for found in plugins:
        if found.id != OLD_PLUGIN or found.scope is None:
            continue
        if (
            scope == "user"
            and found.scope == "user"
            or (
                scope == "project"
                and found.scope in ("project", "local")
                and found.project_path
                and Path(found.project_path).resolve() == here
            )
        ):
            scopes.append(found.scope)
    notes = []
    for at in dict.fromkeys(scopes):
        for args in (
            ["plugin", "uninstall", OLD_PLUGIN, "--scope", at],
            ["plugin", "prune", "--scope", at, "--yes"],
            ["plugin", "marketplace", "remove", OLD_MARKETPLACE, "--scope", at],
        ):
            proc = _run(["claude", *args], cwd)
            # A marketplace that is already gone is what this step wants (claude 2.1.301).
            if args[1] == "marketplace" and "not found" in proc.stderr + proc.stdout:
                continue
            _require(proc, f"claude {' '.join(args)}")
        notes.append(
            f"removed the old claude plugin {OLD_PLUGIN} ({at} scope), the "
            f"dependencies only it needed, and the {OLD_MARKETPLACE} marketplace"
        )
    return notes


def _repo_of(text: str) -> str | None:
    """The kmctl repository ``text`` names, under its current or old name, or None."""
    lowered = text.lower()
    for repo in (REPO, OLD_REPO):
        if repo.lower() in lowered:
            return repo
    return None


def _old_layout(lock: Lock | None) -> str | None:
    """The repository of a kmctl v0.3.0-or-older package in the lock, whose hook APM installed from plugin/, or None."""
    for dep in lock.dependencies if lock else []:
        repo = _repo_of(dep.repo_url or "")
        if repo and dep.virtual_path == "plugin":
            return repo
    return None


def _names_old_package(entry: object, old_layout: str | None) -> bool:
    """Whether an apm.yml dependency entry is the hand-written form ADR 0013 users added.

    The string form (the only one ADR 0013's docs gave) always is. kmctl's own
    ``{git, path: apm}`` form is only when the lock shows the old layout
    installed, since that layout's hook needs ``apm uninstall``
    (spike:apm-only-install/6); otherwise ``write_manifest`` replaces it.
    """
    if isinstance(entry, str):
        repo = _repo_of(entry)
        return repo is not None and f"{repo}/apm".lower() in entry.lower()
    if isinstance(entry, dict):
        return (
            old_layout is not None
            and _repo_of(str(entry.get("git", ""))) is not None
            and entry.get("path") == PACKAGE_PATH
        )
    return False


def read_manifest(path: Path) -> Any:
    """The apm.yml at ``path``, parsed, or None when there is none or it is empty.

    Raises
    ------
    PluginError
        When the file is not a YAML mapping.
    """
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise PluginError(
            f"{path} is not valid YAML ({error}); fix it, then run the command again"
        ) from error
    if data is not None and not isinstance(data, dict):
        raise PluginError(
            f"{path} is not a YAML mapping; fix it, then run the command again"
        )
    return data


def apm_entries(data: Any) -> list[object]:
    """The ``dependencies.apm`` list of a parsed apm.yml, or an empty list."""
    deps = data.get("dependencies") if isinstance(data, dict) else None
    entries = deps.get("apm") if isinstance(deps, dict) else None
    return list(entries) if isinstance(entries, list) else []


# apm.yml and the APM install ---------------------------------------------------


def read_lock(cwd: Path, scope: Scope) -> Lock | None:
    """The apm.lock.yaml APM keeps for ``scope``, or None when there is none or it does not parse."""
    path = apm_dir(cwd, scope) / "apm.lock.yaml"
    if not path.is_file():
        return None
    try:
        return Lock.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (yaml.YAMLError, ValidationError):
        return None


def kmctl_package(lock: Lock | None) -> LockDependency | None:
    """The kmctl package's entry in the lock, or None."""
    for dep in lock.dependencies if lock else []:
        if dep.name == "kmctl" and dep.virtual_path == PACKAGE_PATH:
            return dep
    return None


def kmctl_files(lock: Lock | None) -> LockDependency | None:
    """kmctl's package with its sub-packages' deployed files folded in, or None.

    APM records ``apm/claude`` and ``apm/antigravity`` as entries of their
    own (named ``kmctl-claude`` and ``kmctl-antigravity``, from the same
    repository), and the rules and hooks are listed there, not under
    ``kmctl`` (ADR 0020).
    """
    package = kmctl_package(lock)
    if package is None or lock is None:
        return package
    files = list(package.deployed_files)
    hashes = dict(package.deployed_file_hashes)
    for dep in lock.dependencies:
        sub = (dep.virtual_path or "").startswith(PACKAGE_PATH + "/")
        if sub and dep.repo_url == package.repo_url:
            files += [f for f in dep.deployed_files if f not in files]
            hashes.update(dep.deployed_file_hashes)
    return package.model_copy(
        update={"deployed_files": files, "deployed_file_hashes": hashes}
    )


# The hook ----------------------------------------------------------------------


def hook_entry() -> dict[str, object]:
    """The one SessionStart hook kmctl writes: relay ``kmctl briefing``, never block (I1)."""
    return {
        "type": "command",
        "description": HOOK_DESCRIPTION,
        "command": HOOK_COMMAND,
        "timeout": HOOK_TIMEOUT,
    }


def read_json(path: Path) -> dict[str, Any]:
    """The JSON object in ``path``, or an empty one when the file is missing.

    Raises
    ------
    PluginError
        When the file is not a JSON object.
    """
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except ValueError as error:
        raise PluginError(
            f"{path} is not valid JSON ({error}); fix it, then run the command again"
        ) from error
    if not isinstance(data, dict):
        raise PluginError(
            f"{path} is not a JSON object; fix it, then run the command again"
        )
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    """Write ``data`` to ``path`` as indented JSON, creating its folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _is_kmctl_hook(hook: object) -> bool:
    """Whether a settings.json hook is kmctl's, which kmctl knows by its command."""
    return isinstance(hook, dict) and HOOK_MARK in str(hook.get("command", ""))


def kmctl_hooks(path: Path) -> list[dict[str, Any]]:
    """Every SessionStart hook in the settings.json at ``path`` that runs ``kmctl briefing``."""
    try:
        data = read_json(path)
    except PluginError:
        return []
    hooks = data.get("hooks")
    groups = hooks.get("SessionStart") if isinstance(hooks, dict) else None
    return [
        hook
        for group in (groups if isinstance(groups, list) else [])
        if isinstance(group, dict) and isinstance(group.get("hooks"), list)
        for hook in group["hooks"]
        if _is_kmctl_hook(hook)
    ]


# okf's MCP server --------------------------------------------------------------


def okf_mcp_launcher(starts: Sequence[str] = ('"$PWD"',)) -> str:
    """A POSIX sh script that starts okf's MCP server on the nearest ``.okf/`` folder.

    It walks up from each start folder in turn to the first folder holding
    ``.okf/`` and runs ``uv run <okf_mcp_url()> <that folder>/.okf``. When no
    start leads to one, it passes ``.okf``, so the server starts and its tools
    report that there is no bundle instead of the server failing to start.

    Parameters
    ----------
    starts :
        Shell words naming the folders to start from, tried in order; one
        that is empty or not a folder is skipped. The default is the working
        folder. The Antigravity plugin passes its own folder first.
    """
    url = okf_mcp_url()
    return (
        f"for d in {' '.join(starts)}; do "
        '[ -n "$d" ] || continue; '
        'd=$(cd "$d" 2>/dev/null && pwd -P) || continue; '
        "while :; do "
        f'if [ -d "$d/.okf" ]; then exec uv run {url} "$d/.okf"; fi; '
        '[ "$d" = / ] && break; d=$(dirname "$d"); '
        "done; done; "
        f"exec uv run {url} .okf"
    )


def okf_mcp_server() -> dict[str, object]:
    """The MCP server entry kmctl writes for okf: the launcher, run by ``sh -c``."""
    return {"type": "stdio", "command": "sh", "args": ["-c", okf_mcp_launcher()]}


def _is_okf_server(server: object) -> bool:
    """Whether an MCP server entry runs okf's server script."""
    if not isinstance(server, dict):
        return False
    args = server.get("args")
    words = [str(server.get("command", ""))]
    words += [str(a) for a in args] if isinstance(args, list) else []
    return any(OKF_MCP_SCRIPT in w for w in words)


def other_okf_server(servers: object) -> str | None:
    """The name of an okf MCP server in ``servers`` that is not kmctl's own, or None."""
    if not isinstance(servers, dict):
        return None
    for name, server in servers.items():
        if name != MCP_NAME and _is_okf_server(server):
            return str(name)
    return None


def _apm_recorded_groups(settings: Path) -> list[object]:
    """The SessionStart groups APM records in the ``apm-hooks.json`` beside ``settings``, without its marker."""
    try:
        data = read_json(settings.parent / "apm-hooks.json")
    except PluginError:
        return []
    groups = data.get("SessionStart")
    if not isinstance(groups, list):
        return []
    return [
        {k: v for k, v in group.items() if k != "_apm_source"}
        for group in groups
        if isinstance(group, dict)
    ]


def drop_old_hook(settings: Path) -> bool:
    """Take out the SessionStart hooks an older kmctl wrote into ``settings``; return whether any went.

    Since ADR 0020 APM writes kmctl's hook from the package and records each
    group it wrote in ``apm-hooks.json``. A group that runs ``kmctl briefing``
    and is not recorded there holds kmctl's own hook, from before; left in
    place, the briefing would print twice (spike:apm-hands-back/3, /5). Only
    kmctl's hooks leave such a group, which goes when nothing else is left in
    it. Every other key, group and hook stays; a missing file is left missing.
    """
    if not settings.is_file():
        return False
    data = read_json(settings)
    hooks = data.get("hooks")
    groups = hooks.get("SessionStart") if isinstance(hooks, dict) else None
    if not isinstance(groups, list):
        return False
    recorded = _apm_recorded_groups(settings)
    kept: list[object] = []
    dropped = False
    for group in groups:
        inner = group.get("hooks") if isinstance(group, dict) else None
        ours = isinstance(inner, list) and any(_is_kmctl_hook(h) for h in inner)
        if not ours or group in recorded:
            if ours:
                recorded.remove(group)
            kept.append(group)
            continue
        # An older kmctl put its hook in whatever group held one; keep the rest.
        assert isinstance(group, dict) and isinstance(inner, list)
        dropped = True
        rest = [h for h in inner if not _is_kmctl_hook(h)]
        if rest:
            kept.append({**group, "hooks": rest})
    if not dropped:
        return False
    assert isinstance(hooks, dict)
    if kept:
        hooks["SessionStart"] = kept
    else:
        del hooks["SessionStart"]
    if not hooks:
        del data["hooks"]
    _write_json(settings, data)
    return True


def okf_server_current(server: object) -> bool:
    """Whether an ``okf-bundle`` entry runs the command and args kmctl's package declares.

    Only those two count: APM adds keys such as ``type`` of its own.
    """
    want = okf_mcp_server()
    return isinstance(server, dict) and (server.get("command"), server.get("args")) == (
        want["command"],
        want["args"],
    )


def drop_old_mcp(cwd: Path, scope: Scope) -> tuple[bool, list[str]]:
    """Take out an ``okf-bundle`` entry an older kmctl wrote that differs from the package's.

    APM skips an MCP server that is already configured, so an entry at an
    older okf pin would stay; once it is gone, ``apm install`` writes the
    package's (spike:plugin-patch/1, spike:apm-hands-back/5). At user scope
    it uses ``claude mcp remove``. Every other server stays.

    Returns
    -------
    tuple[bool, list[str]]
        Whether it removed the entry, and a note when the claude CLI is
        missing and the entry stays.
    """
    if scope == "project":
        path = cwd / ".mcp.json"
        if not path.is_file():
            return False, []
        data = read_json(path)
        servers = data.get("mcpServers")
        if not (
            isinstance(servers, dict)
            and MCP_NAME in servers
            and not okf_server_current(servers[MCP_NAME])
        ):
            return False, []
        del servers[MCP_NAME]
        _write_json(path, data)
        return True, []
    try:
        servers = read_json(user_mcp_file()).get("mcpServers")
    except PluginError:
        servers = None
    if not (
        isinstance(servers, dict)
        and MCP_NAME in servers
        and not okf_server_current(servers[MCP_NAME])
    ):
        return False, []
    args = ["mcp", "remove", MCP_NAME, "--scope", "user"]
    if shutil.which("claude") is None:
        return False, [
            (
                f"the claude CLI is not on PATH, so kmctl left an older {MCP_NAME} "
                f"that APM will not replace; run claude {' '.join(args)}, then "
                "apm install -g and kmctl plugin patch --scope user again"
            )
        ]
    _require(_run(["claude", *args], cwd), f"claude {' '.join(args)}")
    return True, []


def shown_path(path: Path, cwd: Path) -> str:
    """``path`` as a reader finds it: relative to ``cwd`` when inside it, else in full."""
    try:
        return str(path.relative_to(cwd))
    except ValueError:
        return str(path)


# Patch -------------------------------------------------------------------------
#
# APM installs kmctl's package, hooks, rules and okf's MCP server (ADR 0020);
# ``kmctl plugin patch``, run after ``apm install``, adds only what APM cannot
# install yet and moves older kmctl installs over (ADR 0021).


@dataclass
class PatchResult:
    """What ``patch`` or ``unpatch`` did.

    Attributes
    ----------
    scope : str
        ``project`` or ``user``.
    harnesses : list[str]
        The harnesses APM installed kmctl's package for, which it patched.
    package_ref : str | None
        The ref the lock records for kmctl's package.
    notes : list[str]
        One line per thing a reader should know: what it removed or wrote,
        and when to run ``apm install`` again.
    """

    scope: str
    harnesses: list[str]
    package_ref: str | None
    notes: list[str]


def new_entry() -> dict[str, str]:
    """The apm.yml entry for this CLI's package: ``{git, path: apm, ref: v<cli version>}``."""
    return {"git": DEFAULT_SOURCE, "path": PACKAGE_PATH, "ref": package_ref()}


def _old_entry(cwd: Path, scope: Scope, lock: Lock | None) -> object | None:
    """An apm.yml entry naming kmctl's package in a form from before ADR 0014, or None."""
    manifest = read_manifest(apm_dir(cwd, scope) / "apm.yml")
    old_layout = _old_layout(lock)
    for entry in apm_entries(manifest):
        if _names_old_package(entry, old_layout):
            return entry
    if old_layout:
        return f"{old_layout}/{PACKAGE_PATH}"
    return None


def _harnesses_of(package: LockDependency) -> list[str]:
    """The harnesses whose folders hold files the lock lists for ``package``."""
    tops = {f.split("/", 1)[0] for f in package.deployed_files}
    return [
        h
        for h, top in (("claude", ".claude"), ("antigravity", ".agents"))
        if top in tops
    ]


def patch(cwd: Path, scope: Scope = "project") -> PatchResult:
    """Add what APM cannot install for kmctl's package yet, for the harnesses APM installed it for.

    It never runs APM. For Claude Code it removes what an older kmctl wrote
    that APM now writes (``drop_old_hook``, ``drop_old_mcp``) and the old
    claude plugin ``kmctl@kmctl``; for Antigravity it writes the plugin
    folder of translated agents and takes APM's broken okf Stop handler out
    of ``.agents/hooks.json`` (ADR 0020). Running it again changes nothing.

    Raises
    ------
    PluginError
        When apm.yml still names the package in a form from before ADR 0014
        (naming the ``apm uninstall`` and the entry to write), when the lock
        lists no kmctl package (naming ``apm install``), or a step fails.
    """
    # antigravity imports this module, so it is imported here, not at the top.
    from kmctl import antigravity

    g = " -g" if scope == "user" else ""
    lock = read_lock(cwd, scope)
    old = _old_entry(cwd, scope, lock)
    if old is not None:
        raise PluginError(
            f"apm.yml names kmctl's package the old way ({old}), whose hook only "
            f"apm uninstall removes; run apm uninstall{g} "
            f"{old.partition('#')[0] if isinstance(old, str) else uninstall_name(old)}, "
            f"add {json.dumps(new_entry())} to apm.yml's dependencies.apm, run "
            f"apm install{g}, then kmctl plugin patch again"
        )
    package = kmctl_files(lock)
    if package is None:
        raise PluginError(
            f"apm.lock.yaml lists no kmctl package; add {json.dumps(new_entry())} "
            f"to apm.yml's dependencies.apm and run apm install{g} (the README's "
            "install section), then kmctl plugin patch again"
        )
    harnesses = _harnesses_of(package)
    notes: list[str] = []
    if "claude" in harnesses:
        again = False
        if drop_old_hook(settings_path(cwd, scope)):
            notes.append("removed the SessionStart hook an older kmctl wrote itself")
        removed, more = drop_old_mcp(cwd, scope)
        notes += more
        if removed:
            notes.append(f"removed the {MCP_NAME} server an older kmctl wrote")
            again = True
        notes = remove_old_plugin(cwd, scope) + notes
        if again:
            notes.append(f"run apm install{g} again, so APM writes {MCP_NAME}")
    if "antigravity" in harnesses and scope == "project":
        folder = antigravity.write_plugin(cwd)
        notes.append(
            f"wrote {shown_path(folder, cwd)}/ (the agents, which APM does not "
            "install for Antigravity yet); Antigravity loads it once you trust "
            "this folder"
        )
        if antigravity.drop_apm_okf_stop(cwd):
            notes.append(
                "took APM's okf Stop handler out of .agents/hooks.json, where it "
                "cannot run; kmctl's package runs okf's check instead"
            )
    return PatchResult(scope, harnesses, package.resolved_ref, notes)


def unpatch(cwd: Path, scope: Scope = "project") -> PatchResult:
    """Delete what ``patch`` wrote: the Antigravity plugin folder in ``cwd``, and nothing else."""
    from kmctl import antigravity

    folder = antigravity.plugin_dir(cwd)
    notes = []
    if folder.exists():
        shutil.rmtree(folder)
        notes.append(f"deleted {shown_path(folder, cwd)}/")
    return PatchResult(scope, [], None, notes)


def uninstall_name(entry: object) -> str:
    """The name ``apm uninstall`` takes for an apm.yml entry of kmctl's package.

    A ``git:`` entry becomes ``HOST[:PORT]/OWNER/REPO/apm`` from its own URL,
    case kept: APM lowercases a GitHub repo_url in the lock, so the lock is
    not used (spike:plugin-remove/5, /3). An scp-style ``git@host:owner/repo``
    URL works the same way. A plain string entry is passed as written.
    """
    if not isinstance(entry, dict):
        return str(entry)
    url = str(entry.get("git", "")).strip()
    if "://" in url:
        parts = urlsplit(url)
        host = parts.hostname or ""
        host += f":{parts.port}" if parts.port else ""
        path = parts.path
    else:
        host, _, path = (
            url.partition("@")[2].partition(":") if "@" in url else ("", "", url)
        )
    path = path.strip("/").removesuffix(".git")
    return "/".join(p for p in (host, path, str(entry.get("path", PACKAGE_PATH))) if p)
