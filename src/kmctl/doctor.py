"""Check that kmctl's tools, its installed package and the ``kmctl init`` files are in place.

``run_doctor`` returns one ``Check`` per thing it looked at and prints
nothing, so the CLI, the tests and the CI action can all call it. It reads
files and runs one command, APM's ``--version`` at the pinned release from
uv's cache (``uv tool run --offline``), which opens no connection and writes
nothing (spike:kmctl-doctor/4). It never runs ``claude plugin list``: that
command goes online and writes ``.claude.json``, so the old claude plugin is
read from ``enabledPlugins`` in the settings files instead. Only with
``online`` does it fetch okf's MCP script URL.

It finds the harnesses installed here from what an install leaves, never
from what is missing: the targets in apm.yml, the paths apm.lock.yaml lists
for the kmctl package, the kmctl hook or an old kmctl plugin in
settings.json, and ``.agents/plugins/kmctl/``. Any one marks the harness, so
a deleted piece is reported by name instead of hiding the harness.
"""

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from kmctl import antigravity
from kmctl.plugin import (
    APM_CLI,
    HARNESSES,
    MCP_NAME,
    OLD_PLUGIN,
    PACKAGE_PATH,
    Lock,
    LockDependency,
    PluginError,
    Scope,
    apm_dir,
    apm_entries,
    apm_root,
    cli_version,
    hook_entry,
    kmctl_hooks,
    kmctl_package,
    okf_mcp_server,
    okf_mcp_url,
    other_okf_server,
    package_ref,
    read_json,
    read_lock,
    read_manifest,
    settings_path,
    shown_path,
    user_mcp_file,
)

#: The command doctor runs to see that APM runs at the pinned release without the network.
APM_VERSION_ARGS = ("tool", "run", "--offline", "--from", APM_CLI, "apm", "--version")
#: The claude plugins the install route before ADR 0014 enabled.
OLD_PLUGINS = (OLD_PLUGIN, "okf@scaccogatto")
#: Where APM's lock names okf's skills package.
OKF_REPO = "scaccogatto/okf-skills"
#: The folder each harness's files go in, relative to the repository.
FOLDERS = {"claude": ".claude", "antigravity": ".agents"}
#: The agy CLI settings file under HOME that lists the trusted folders.
AGY_SETTINGS = Path(".gemini") / "antigravity-cli" / "settings.json"
TRUST_FIX = "open this folder in Antigravity and trust it"
UV_FIX = "install uv (https://docs.astral.sh/uv/)"
#: The most problems one check line names before it counts the rest.
SHOWN_PROBLEMS = 5
#: Seconds the offline APM run and the --online fetch may take.
TIMEOUT = 60


@dataclass(frozen=True)
class Check:
    """One thing doctor looked at and what it found.

    Attributes
    ----------
    id : str
        A stable dotted name, such as ``dep.uv`` or ``claude.hook``.
    harness : str | None
        The harness the check belongs to, or None for one that serves all.
    ok : bool
        Whether the check passed.
    detail : str
        What doctor found; for a failure, what is wrong.
    fix : str | None
        For a failure, the instruction that fixes it, usually ``run kmctl
        ...``; None when the check passed.
    """

    id: str
    harness: str | None
    ok: bool
    detail: str
    fix: str | None = None


@dataclass(frozen=True)
class DoctorResult:
    """Every check doctor ran, in the order it prints them.

    Attributes
    ----------
    ok : bool
        Whether every check passed.
    checks : list[Check]
        The checks.
    """

    ok: bool
    checks: list[Check]


def _pass(cid: str, harness: str | None, detail: str) -> Check:
    """A passed check."""
    return Check(cid, harness, True, detail)


def _fail(cid: str, harness: str | None, detail: str, fix: str) -> Check:
    """A failed check with its fix."""
    return Check(cid, harness, False, detail, fix)


def _suffix(scope: Scope) -> str:
    """The flag a fix adds so it acts at ``scope``."""
    return " --scope user" if scope == "user" else ""


def _install_fix(harness: str, scope: Scope) -> str:
    """The install command that puts back a missing piece of ``harness``."""
    return f"run kmctl plugin install --harness {harness}{_suffix(scope)}"


def _update_fix(harness: str, scope: Scope) -> str:
    """The update command that brings ``harness`` to this kmctl's version."""
    return f"run kmctl plugin update --harness {harness}{_suffix(scope)}"


def _load(path: Path) -> tuple[dict[str, Any], str | None]:
    """The JSON object in ``path`` (empty when missing), and why it could not be read, if so."""
    try:
        return read_json(path), None
    except PluginError:
        return {}, "is not a JSON object"


# Which harnesses are here -------------------------------------------------------


def _harness_of(path: str) -> str | None:
    """The harness whose folder holds ``path``, a path apm.lock.yaml lists."""
    parts = PurePosixPath(path).parts
    for harness, folder in FOLDERS.items():
        if parts[:1] == (folder,):
            return harness
    return None


def _manifest_targets(cwd: Path, scope: Scope) -> list[str]:
    """The ``targets`` of the apm.yml that names kmctl's package, or none."""
    try:
        data = read_manifest(apm_dir(cwd, scope) / "apm.yml")
    except PluginError:
        return []
    names_kmctl = any(
        isinstance(e, dict) and e.get("path") == PACKAGE_PATH for e in apm_entries(data)
    )
    targets = data.get("targets") if names_kmctl else None
    if isinstance(targets, str):
        return [targets]
    return [str(t) for t in targets] if isinstance(targets, list) else []


def _settings_files(cwd: Path, scope: Scope) -> list[Path]:
    """The Claude Code settings files that can enable a plugin at ``scope``."""
    if scope == "user":
        return [settings_path(cwd, scope)]
    return [settings_path(cwd, scope), cwd / ".claude" / "settings.local.json"]


def _old_plugins(cwd: Path, scope: Scope) -> list[tuple[Path, str]]:
    """Each (settings file, plugin) where an old claude plugin is enabled."""
    found = []
    for path in _settings_files(cwd, scope):
        enabled = _load(path)[0].get("enabledPlugins")
        if isinstance(enabled, dict):
            found += [(path, p) for p in OLD_PLUGINS if enabled.get(p) is True]
    return found


def _kmctl_mark(cwd: Path, scope: Scope, harness: str) -> bool:
    """Whether a piece kmctl itself writes for ``harness`` is there: the hook, the old kmctl plugin, or the plugin folder."""
    if harness == "claude":
        old = any(name == OLD_PLUGIN for _, name in _old_plugins(cwd, scope))
        return bool(kmctl_hooks(settings_path(cwd, scope)) or old)
    return antigravity.plugin_dir(cwd).exists()


def harnesses_found(cwd: Path, scope: Scope = "project") -> list[str]:
    """The harnesses kmctl is installed for at ``scope``, from what an install leaves.

    Antigravity installs per repository only, so at user scope only
    ``claude`` can be found.
    """
    targets = _manifest_targets(cwd, scope)
    package = kmctl_package(read_lock(cwd, scope))
    deployed = {_harness_of(p) for p in package.deployed_files} if package else set()
    return [
        h
        for h in HARNESSES
        if not (h == "antigravity" and scope == "user")
        and (h in targets or h in deployed or _kmctl_mark(cwd, scope, h))
    ]


# Tools -------------------------------------------------------------------------


def _tool(cid: str, name: str, harness: str | None, fix: str) -> Check:
    """Whether ``name`` is on PATH."""
    found = shutil.which(name)
    if found is None:
        return _fail(cid, harness, f"{name} is not on PATH", fix)
    return _pass(cid, harness, found)


def _apm(cwd: Path) -> Check:
    """Whether APM at the pinned release runs from uv's cache, without the network."""
    pinned = APM_CLI.split("==")[1]
    fetch = f"run uvx --from {APM_CLI} apm --version, which downloads it once"
    uv = shutil.which("uv")
    if uv is None:
        return _fail("dep.apm", None, "uv is not on PATH, so APM cannot run", UV_FIX)
    try:
        proc = subprocess.run(
            [uv, *APM_VERSION_ARGS],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return _fail("dep.apm", None, f"APM {pinned} did not run ({error})", fetch)
    if proc.returncode != 0:
        return _fail("dep.apm", None, f"APM {pinned} is not in uv's cache", fetch)
    said = (proc.stdout.strip().splitlines() or [pinned])[0]
    return _pass("dep.apm", None, f"APM runs from uv's cache: {said}")


def _dependencies(cwd: Path, found: list[str]) -> list[Check]:
    """uv, git and APM always; claude and agy for the harnesses found."""
    checks = [
        _tool("dep.uv", "uv", None, UV_FIX),
        _tool("dep.git", "git", None, "install git (https://git-scm.com/downloads)"),
        _apm(cwd),
    ]
    if "claude" in found:
        checks.append(
            _tool(
                "dep.claude",
                "claude",
                "claude",
                "install Claude Code (https://code.claude.com/docs/en/setup)",
            )
        )
    if "antigravity" in found:
        checks.append(
            _tool(
                "dep.agy",
                "agy",
                "antigravity",
                "install the Antigravity CLI so agy is on PATH",
            )
        )
    return checks


# kmctl init --------------------------------------------------------------------


def _init(cwd: Path) -> list[Check]:
    """Whether ``kmctl init`` has set the repository up."""
    checks = []
    for cid, rel in (("init.okf", ".okf/index.md"), ("init.docs", "docs/README.md")):
        if (cwd / rel).is_file():
            checks.append(_pass(cid, None, f"{rel} exists"))
        else:
            checks.append(_fail(cid, None, f"{rel} is missing", "run kmctl init"))
    return checks


# The lock and the files APM deployed ----------------------------------------------


def _lock(cwd: Path, scope: Scope, harness: str) -> tuple[Check, Lock | None]:
    """The ``HARNESS.lock`` check, and the parsed lock when it names kmctl's package."""
    cid = f"{harness}.lock"
    path = apm_dir(cwd, scope) / "apm.lock.yaml"
    shown = shown_path(path, cwd)
    install = _install_fix(harness, scope)
    if not path.is_file():
        return _fail(cid, harness, f"{shown} is missing", install), None
    lock = read_lock(cwd, scope)
    if lock is None:
        return _fail(cid, harness, f"{shown} does not parse", install), None
    package = kmctl_package(lock)
    if package is None:
        detail = f"{shown} does not name kmctl's package"
        return _fail(cid, harness, detail, install), None
    if package.resolved_ref != package_ref():
        detail = (
            f"{shown} has kmctl's package at {package.resolved_ref}, this kmctl "
            f"is {cli_version()}"
        )
        return _fail(cid, harness, detail, _update_fix(harness, scope)), lock
    return _pass(cid, harness, f"{shown} has kmctl's package at {package_ref()}"), lock


def _sha256(path: Path) -> str:
    """``path``'s hash in apm.lock.yaml's form, sha256:HEX."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _deployed(
    cwd: Path,
    scope: Scope,
    harness: str,
    cid: str,
    what: str,
    package: LockDependency | None,
) -> Check:
    """Whether every file the lock lists for ``package`` under ``harness``'s folder is there unchanged."""
    install = _install_fix(harness, scope)
    folder = FOLDERS[harness]
    if package is None:
        return _fail(cid, harness, f"apm.lock.yaml does not list {what}", install)
    root = apm_root(cwd, scope)
    paths = [p for p in package.deployed_files if _harness_of(p) == harness]
    if not paths:
        detail = f"apm.lock.yaml lists no {what} files under {folder}/"
        return _fail(cid, harness, detail, install)
    wrong = []
    for rel in paths:
        target = root / rel
        if not target.exists():
            wrong.append(f"{rel} is missing")
        elif (
            rel in package.deployed_file_hashes
            and target.is_file()
            and _sha256(target) != package.deployed_file_hashes[rel]
        ):
            wrong.append(f"{rel} differs from apm.lock.yaml")
    if wrong:
        shown = wrong[:SHOWN_PROBLEMS]
        if len(wrong) > SHOWN_PROBLEMS:
            shown.append(f"and {len(wrong) - SHOWN_PROBLEMS} more")
        return _fail(cid, harness, ", ".join(shown), install)
    return _pass(cid, harness, f"{len(paths)} {what} paths match apm.lock.yaml")


def _okf_package(lock: Lock | None) -> LockDependency | None:
    """okf-skills' entry in the lock, or None."""
    for dep in lock.dependencies if lock else []:
        if dep.repo_url == OKF_REPO:
            return dep
    return None


# Claude Code -------------------------------------------------------------------


def _claude_hook(cwd: Path, scope: Scope) -> Check:
    """Whether settings.json holds exactly the SessionStart hook this kmctl writes."""
    path = settings_path(cwd, scope)
    shown = shown_path(path, cwd)
    install = _install_fix("claude", scope)
    _, broken = _load(path)
    if broken:
        return _fail("claude.hook", "claude", f"{shown} {broken}", f"fix {shown}")
    hooks = kmctl_hooks(path)
    if hooks == [hook_entry()]:
        detail = f"{shown} holds the SessionStart hook this kmctl writes"
        return _pass("claude.hook", "claude", detail)
    if not hooks:
        detail = f"the kmctl SessionStart hook is missing from {shown}"
        return _fail("claude.hook", "claude", detail, install)
    detail = f"the kmctl SessionStart hook in {shown} is not the one this kmctl writes"
    return _fail("claude.hook", "claude", detail, _update_fix("claude", scope))


def _claude_mcp(cwd: Path, scope: Scope) -> Check:
    """Whether okf's MCP server is declared for Claude Code: kmctl's okf-bundle, or another okf server."""
    path = cwd / ".mcp.json" if scope == "project" else user_mcp_file()
    shown = shown_path(path, cwd)
    data, broken = _load(path)
    if broken:
        return _fail("claude.okf-mcp", "claude", f"{shown} {broken}", f"fix {shown}")
    servers = data.get("mcpServers")
    own = servers.get(MCP_NAME) if isinstance(servers, dict) else None
    if own == okf_mcp_server():
        detail = f"{shown} declares okf's MCP server {MCP_NAME}"
        return _pass("claude.okf-mcp", "claude", detail)
    other = other_okf_server(servers)
    if other is not None:
        detail = f"{shown} declares okf's MCP server as {other!r}"
        return _pass("claude.okf-mcp", "claude", detail)
    if own is not None:
        detail = (
            f"okf's MCP server {MCP_NAME} in {shown} is not the one this kmctl writes"
        )
        return _fail("claude.okf-mcp", "claude", detail, _update_fix("claude", scope))
    detail = f"okf's MCP server {MCP_NAME} is missing from {shown}"
    return _fail("claude.okf-mcp", "claude", detail, _install_fix("claude", scope))


def _claude_old_plugin(cwd: Path, scope: Scope) -> Check:
    """Whether a settings file still enables the claude plugin route before ADR 0014."""
    found = _old_plugins(cwd, scope)
    if not found:
        detail = f"no settings file enables {' or '.join(OLD_PLUGINS)}"
        return _pass("claude.old-plugin", "claude", detail)
    named = ", ".join(f"{name} in {shown_path(path, cwd)}" for path, name in found)
    if any(name == OLD_PLUGIN for _, name in found):
        fix = _install_fix("claude", scope)
    else:
        # The install removes okf only as kmctl@kmctl's dependency; on its own it
        # needs its own uninstall, at the scope of the file that enables it.
        path, name = found[0]
        at = (
            "user"
            if scope == "user"
            else "local"
            if path.name == "settings.local.json"
            else "project"
        )
        fix = f"run claude plugin uninstall {name} --scope {at}"
    return _fail(
        "claude.old-plugin",
        "claude",
        f"the old claude plugin is enabled: {named}",
        fix,
    )


# Antigravity -------------------------------------------------------------------


def _antigravity_plugin(cwd: Path) -> Check:
    """Whether every file under .agents/plugins/kmctl/ is the one this kmctl writes."""
    cid = "antigravity.plugin"
    shown = antigravity.PLUGIN_PATH.as_posix()
    try:
        problems = antigravity.plugin_problems(cwd)
    except PluginError as error:
        detail, _, fix = str(error).rpartition("; ")
        if not detail:
            detail, fix = fix, antigravity.FIX
        return _fail(cid, "antigravity", detail, fix)
    if not antigravity.plugin_dir(cwd).is_dir():
        return _fail(cid, "antigravity", f"{shown}/ is missing", antigravity.FIX)
    if problems:
        shown_problems = problems[:SHOWN_PROBLEMS]
        if len(problems) > SHOWN_PROBLEMS:
            shown_problems.append(f"and {len(problems) - SHOWN_PROBLEMS} more")
        return _fail(cid, "antigravity", ", ".join(shown_problems), antigravity.FIX)
    return _pass(cid, "antigravity", f"{shown}/ holds what this kmctl writes")


def _antigravity_hook(cwd: Path) -> Check:
    """Whether the plugin folder's hooks.json is the hook this kmctl writes."""
    shown = (antigravity.PLUGIN_PATH / "hooks.json").as_posix()
    if antigravity.hook_present(cwd):
        detail = f"{shown} holds the SessionStart hook this kmctl writes"
        return _pass("antigravity.hook", "antigravity", detail)
    detail = f"{shown} is missing or is not the hook this kmctl writes"
    return _fail("antigravity.hook", "antigravity", detail, antigravity.FIX)


def _antigravity_mcp(cwd: Path) -> Check:
    """Whether the plugin folder's mcp_config.json declares okf's MCP server as this kmctl writes it."""
    path = antigravity.plugin_dir(cwd) / "mcp_config.json"
    shown = (antigravity.PLUGIN_PATH / "mcp_config.json").as_posix()
    data, _ = _load(path)
    if data == antigravity.mcp_config():
        detail = f"{shown} declares okf's MCP server {antigravity.MCP_NAME}"
        return _pass("antigravity.okf-mcp", "antigravity", detail)
    detail = f"{shown} is missing or is not the MCP server this kmctl writes"
    return _fail("antigravity.okf-mcp", "antigravity", detail, antigravity.FIX)


def _antigravity_trust(cwd: Path) -> Check | None:
    """Whether agy trusts this repository; None when agy is not on PATH, which dep.agy reports."""
    if shutil.which("agy") is None:
        return None
    path = Path.home() / AGY_SETTINGS
    trusted = _load(path)[0].get("trustedWorkspaces")
    here = cwd.resolve()
    if isinstance(trusted, list) and any(
        isinstance(t, str) and Path(t).resolve() == here for t in trusted
    ):
        detail = f"{here} is in trustedWorkspaces of ~/{AGY_SETTINGS.as_posix()}"
        return _pass("antigravity.trust", "antigravity", detail)
    detail = (
        f"{here} is not in trustedWorkspaces of ~/{AGY_SETTINGS.as_posix()}, so "
        "Antigravity does not load .agents/"
    )
    return _fail("antigravity.trust", "antigravity", detail, TRUST_FIX)


def _antigravity_fetch() -> Check:
    """Whether okf's MCP script, which the plugin runs with ``uv run``, can be fetched."""
    import httpx  # only --online needs it

    url = okf_mcp_url()
    again = "check the network and proxy settings, then run kmctl doctor --online again"
    try:
        with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
            response = client.head(url)
    except httpx.HTTPError as error:
        detail = f"could not fetch {url} ({error})"
        return _fail("antigravity.okf-mcp-url", "antigravity", detail, again)
    if response.status_code != 200:
        detail = f"{url} answered HTTP {response.status_code}"
        return _fail("antigravity.okf-mcp-url", "antigravity", detail, again)
    return _pass("antigravity.okf-mcp-url", "antigravity", f"{url} can be fetched")


# One harness, and all of it ------------------------------------------------------


def _harness(cwd: Path, scope: Scope, harness: str, online: bool) -> list[Check]:
    """Every check of one harness installed at ``scope``."""
    lock_check, lock = _lock(cwd, scope, harness)
    checks = [
        lock_check,
        _deployed(
            cwd, scope, harness, f"{harness}.files", "kmctl", kmctl_package(lock)
        ),
        _deployed(
            cwd,
            scope,
            harness,
            f"{harness}.okf-skills",
            "okf-skills",
            _okf_package(lock),
        ),
    ]
    if harness == "claude":
        checks += [
            _claude_hook(cwd, scope),
            _claude_mcp(cwd, scope),
            _claude_old_plugin(cwd, scope),
        ]
        return checks
    checks += [_antigravity_plugin(cwd), _antigravity_hook(cwd), _antigravity_mcp(cwd)]
    trust = _antigravity_trust(cwd)
    if trust is not None:
        checks.append(trust)
    if online:
        checks.append(_antigravity_fetch())
    return checks


def _where(cwd: Path, scope: Scope, found: list[str]) -> list[Check]:
    """Which harnesses are installed, or that none is and how to install one.

    At project scope with no Claude Code install here but one at user scope,
    ``claude.scope`` passes and points at ``kmctl doctor --scope user``
    rather than suggesting a second install.
    """
    checks = []
    if found:
        at = " at user scope" if scope == "user" else ""
        checks.append(
            _pass("kmctl.harness", None, f"installed for {', '.join(found)}{at}")
        )
    if (
        scope == "project"
        and "claude" not in found
        and "claude" in harnesses_found(cwd, "user")
    ):
        detail = "installed at user scope; run kmctl doctor --scope user"
        checks.append(_pass("claude.scope", "claude", detail))
    if not checks:
        where = "at user scope" if scope == "user" else "in this repository"
        checks.append(
            _fail(
                "kmctl.harness",
                None,
                f"no kmctl harness {where}",
                _install_fix("claude", scope),
            )
        )
    return checks


def run_doctor(
    cwd: Path, scope: Scope = "project", online: bool = False
) -> DoctorResult:
    """Run every check for the repository at ``cwd``, or for the user-scope install.

    In order: this kmctl's version (``kmctl.version``); the tools
    (``dep.uv``, ``dep.git``, ``dep.apm``, and ``dep.claude`` or ``dep.agy``
    for each harness found); at project scope, the ``kmctl init`` files
    (``init.okf``, ``init.docs``); which harnesses are installed
    (``kmctl.harness``, or ``claude.scope`` when only a user-scope install
    exists); then each harness's checks: ``HARNESS.lock``, ``.files``,
    ``.okf-skills``, ``.okf-mcp``, and for claude ``claude.hook`` and
    ``claude.old-plugin``, for antigravity ``antigravity.plugin``,
    ``antigravity.hook``, ``antigravity.trust`` (when agy is on PATH) and,
    with ``online``, ``antigravity.okf-mcp-url``.

    Parameters
    ----------
    cwd :
        The repository.
    scope :
        ``project`` checks the install in ``cwd``; ``user`` checks the one in
        ``~/.apm/`` and Claude Code's user folder.
    online :
        Also fetch okf's MCP script URL, the one check that uses the network.

    Returns
    -------
    DoctorResult
        Every check, and whether all passed.
    """
    cwd = cwd.resolve()
    found = harnesses_found(cwd, scope)
    checks = [_pass("kmctl.version", None, f"kmctl {cli_version()}")]
    checks += _dependencies(cwd, found)
    if scope == "project":
        checks += _init(cwd)
    checks += _where(cwd, scope, found)
    for harness in found:
        checks += _harness(cwd, scope, harness, online)
    return DoctorResult(all(c.ok for c in checks), checks)


def as_json(result: DoctorResult) -> str:
    """``result`` as one JSON object: ok, and checks with id, harness, ok, detail and fix."""
    return json.dumps(
        {
            "ok": result.ok,
            "checks": [
                {
                    "id": c.id,
                    "harness": c.harness,
                    "ok": c.ok,
                    "detail": c.detail,
                    "fix": c.fix,
                }
                for c in result.checks
            ],
        }
    )


def render(result: DoctorResult) -> str:
    """One line per check: ``ok   ID: DETAIL`` or ``fail ID: DETAIL; FIX``."""
    return "\n".join(
        f"ok   {c.id}: {c.detail}" if c.ok else f"fail {c.id}: {c.detail}; {c.fix}"
        for c in result.checks
    )
