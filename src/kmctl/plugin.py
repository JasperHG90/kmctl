"""Install kmctl's APM package for an agent harness, and the pieces APM leaves out (ADR 0014).

``install`` writes the kmctl entry into the repository's apm.yml, runs
``apm install`` at the version pinned in ``APM_CLI``, and then writes what the
package cannot carry: for Claude Code, the SessionStart hook in settings.json
and okf's MCP server; for Antigravity, the plugin folder ``kmctl.antigravity``
builds (ADR 0015). Before that it moves two kinds of older install over:
the claude plugin ``kmctl@kmctl`` (ADR 0003) and an apm.yml entry naming the
package another way (ADR 0013).

Each step is its own function and prints nothing, so ``kmctl doctor`` and the
Antigravity harness can reuse the hook entry, the MCP entry and its launcher.
"""

import json
import os
import re
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.metadata import version
from importlib.resources import files
from io import StringIO
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from ruamel.yaml import YAML

Scope = Literal["project", "user"]
#: The harnesses ``--harness`` accepts, in the order help lists them.
HARNESSES = ("claude", "antigravity")
#: The APM release kmctl runs through uvx, so every install uses the same one.
APM_CLI = "apm-cli==0.33.0"
#: Where the kmctl package comes from unless ``--source`` names another git URL.
DEFAULT_SOURCE = "https://github.com/JasperHG90/Knowledge-management.git"
#: The package's folder inside the source repository.
PACKAGE_PATH = "apm"
#: How an apm.yml written by hand (ADR 0013) names the package.
OLD_PACKAGE = "JasperHG90/Knowledge-management/apm"
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
    "git+https://github.com/JasperHG90/Knowledge-management'; exit 0; }; "
    "kmctl briefing || echo '[kmctl] kmctl briefing failed; run kmctl briefing in "
    "a terminal to see why, or upgrade with uv tool install --force "
    "git+https://github.com/JasperHG90/Knowledge-management.'; exit 0"
)
HOOK_DESCRIPTION = (
    "kmctl: print the knowledge briefing (where knowledge lives, what is due, "
    "the rules). Never blocks."
)
HOOK_TIMEOUT = 10
#: The line APM 0.33.0 prints when it leaves a file it did not write in place.
SKIP_LINE = "skipped -- local files exist"
#: The most characters of a tool's output a PluginError carries.
CAUSE_CAP = 400


class PluginError(Exception):
    """An install step that failed; the message names the fix."""


@dataclass(frozen=True)
class InstallResult:
    """What ``install`` did besides the APM install.

    Attributes
    ----------
    scope : str
        ``project`` or ``user``.
    harnesses : list[str]
        The harnesses it installed for.
    package_ref : str | None
        The ref apm.lock.yaml records for the kmctl package afterwards, or
        None when the lock does not name it.
    notes : list[str]
        One line per thing a reader should know: an old install removed, a
        step skipped and why, an MCP server kept.
    """

    scope: str
    harnesses: list[str]
    package_ref: str | None
    notes: list[str]


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


def parse_harnesses(text: str) -> list[str]:
    """Split a comma list of harnesses, without repeats.

    Raises
    ------
    PluginError
        When the list is empty or a name is not one of ``HARNESSES``.
    """
    names = [n.strip() for n in text.split(",") if n.strip()]
    unknown = [n for n in names if n not in HARNESSES]
    if unknown or not names:
        refused = ", ".join(map(repr, unknown)) if unknown else repr(text)
        raise PluginError(
            f"no harness {refused}; give --harness one of: {', '.join(HARNESSES)}"
        )
    return list(dict.fromkeys(names))


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


def _require(proc: subprocess.CompletedProcess[str], what: str) -> None:
    """Raise when ``proc`` failed, naming the command ``what`` and its cause."""
    if proc.returncode != 0:
        output = f"{proc.stderr}\n{proc.stdout}"
        raise PluginError(
            f"{what} failed: {_cause(output)}; run it by hand to see why, then "
            "kmctl plugin install again"
        )


def _apm(args: list[str], cwd: Path) -> None:
    """Run APM at ``APM_CLI`` through uvx, raising when it fails.

    Raises
    ------
    PluginError
        When uvx is not on PATH or APM fails, with APM's cause.
    """
    _require(_apm_run(args, cwd), f"uvx --from {APM_CLI} apm {' '.join(args)}")


def _apm_run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run APM at ``APM_CLI`` through uvx and return what it did.

    Raises
    ------
    PluginError
        When uvx is not on PATH.
    """
    if shutil.which("uvx") is None:
        raise PluginError(
            "uvx is not on PATH, and kmctl runs APM through it; install uv "
            "(https://docs.astral.sh/uv/), then run kmctl plugin install again"
        )
    return _run(["uvx", "--from", APM_CLI, "apm", *args], cwd)


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
            "upgrade Claude Code, then run kmctl plugin install again"
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


def _old_layout(lock: Lock | None) -> bool:
    """Whether the lock holds kmctl v0.3.0 or older, whose hook APM installed from plugin/."""
    return any(
        "jasperhg90/knowledge-management" in (dep.repo_url or "").lower()
        and dep.virtual_path == "plugin"
        for dep in (lock.dependencies if lock else [])
    )


def _names_old_package(entry: object, old_layout: bool) -> bool:
    """Whether an apm.yml dependency entry is the hand-written form ADR 0013 users added.

    The string form (the only one ADR 0013's docs gave) always is. kmctl's own
    ``{git, path: apm}`` form is only when the lock shows the old layout
    installed, since that layout's hook needs ``apm uninstall``
    (spike:apm-only-install/6); otherwise ``write_manifest`` replaces it.
    """
    if isinstance(entry, str):
        return OLD_PACKAGE.lower() in entry.lower()
    if isinstance(entry, dict):
        repo = str(entry.get("git", "")).lower()
        return (
            old_layout
            and "jasperhg90/knowledge-management" in repo
            and entry.get("path") == PACKAGE_PATH
        )
    return False


def _bare_url(url: str) -> str:
    """``url`` without scheme, user, ``.git`` suffix or trailing slash, in lower case."""
    url = re.sub(r"^[a-z][a-z0-9+.-]*://", "", url.strip().lower())
    url = re.sub(r"^[^@/]+@", "", url).rstrip("/")
    return url.removesuffix(".git")


def _locked_kmctl_urls(lock: Lock | None) -> set[str]:
    """Where the lock says kmctl's package came from, as ``_bare_url`` gives them.

    APM 0.33.0 splits a git source over ``host``, ``port`` and ``repo_url``
    (owner/repo), so this joins them again (spikes apm-only-install/4 to /6).
    """
    urls = set()
    for dep in lock.dependencies if lock else []:
        if dep.name == "kmctl" and dep.virtual_path == PACKAGE_PATH and dep.repo_url:
            host = (dep.host or "github.com") + (f":{dep.port}" if dep.port else "")
            urls.add(_bare_url(f"{host}/{dep.repo_url}"))
    return urls


def _is_kmctl_entry(entry: object, source: str, locked: set[str] | None = None) -> bool:
    """Whether an apm.yml dependency entry is kmctl's package, from ``source`` or another.

    It is a ``path: apm`` mapping whose git URL is ``source``, names
    kmctl's repository, or is where the lock (``locked``) says kmctl came from.
    """
    if not isinstance(entry, dict) or entry.get("path") != PACKAGE_PATH:
        return False
    git = str(entry.get("git", ""))
    return (
        git == source
        or "jasperhg90/knowledge-management" in git.lower()
        or _bare_url(git) in (locked or set())
    )


def _entry_label(entry: object) -> str:
    """A one-line form of an apm.yml dependency entry, for a note."""
    if isinstance(entry, dict):
        return json.dumps({str(k): str(v) for k, v in entry.items()})
    return str(entry)


def _roundtrip() -> YAML:
    """A YAML reader and writer that keeps comments and layout, set up as APM's is."""
    rt = YAML(typ="rt")
    rt.preserve_quotes = True
    rt.indent(mapping=2, sequence=4, offset=2)
    return rt


def read_manifest(path: Path) -> Any:
    """The apm.yml at ``path`` as round-trip YAML, or None when there is none or it is empty.

    Raises
    ------
    PluginError
        When the file is not a YAML mapping.
    """
    if not path.is_file():
        return None
    try:
        data = _roundtrip().load(path.read_text(encoding="utf-8"))
    except Exception as error:  # ruamel raises error types with no common base
        raise PluginError(
            f"{path} is not valid YAML ({error}); fix it, then run kmctl plugin "
            "install again"
        ) from error
    if data is not None and not isinstance(data, dict):
        raise PluginError(
            f"{path} is not a YAML mapping; fix it, then run kmctl plugin install again"
        )
    return data


def apm_entries(data: Any) -> list[object]:
    """The ``dependencies.apm`` list of a parsed apm.yml, or an empty list."""
    deps = data.get("dependencies") if isinstance(data, dict) else None
    entries = deps.get("apm") if isinstance(deps, dict) else None
    return list(entries) if isinstance(entries, list) else []


def remove_old_apm_entry(cwd: Path, scope: Scope, source: str) -> list[str]:
    """Run ``apm uninstall`` on an apm.yml entry naming the package another way than kmctl's.

    An entry written by hand (ADR 0013) brought the package's old SessionStart
    hook, which only ``apm uninstall`` removes (spike:apm-only-install/6), so
    this runs before kmctl rewrites apm.yml.

    Returns
    -------
    list[str]
        A note per entry removed.

    Raises
    ------
    PluginError
        When apm.yml cannot be read or the uninstall fails.
    """
    manifest = read_manifest(apm_dir(cwd, scope) / "apm.yml")
    old_layout = _old_layout(read_lock(cwd, scope))
    old = [e for e in apm_entries(manifest) if _names_old_package(e, old_layout)]
    if not old:
        return []
    _apm(
        ["uninstall", OLD_PACKAGE, *(["-g"] if scope == "user" else [])],
        apm_root(cwd, scope),
    )
    left = [
        e
        for e in apm_entries(read_manifest(apm_dir(cwd, scope) / "apm.yml"))
        if _names_old_package(e, old_layout)
    ]
    if left:
        raise PluginError(
            f"apm uninstall {OLD_PACKAGE} left the entry {_entry_label(left[0])} in "
            f"{apm_dir(cwd, scope) / 'apm.yml'}; run apm uninstall with that entry "
            "by hand, then kmctl plugin install again"
        )
    return [
        f"removed the old APM entry {_entry_label(e)} and its SessionStart hook "
        "with apm uninstall"
        for e in old
    ]


# apm.yml and the APM install ---------------------------------------------------


def kmctl_entry(source: str) -> dict[str, object]:
    """The apm.yml dependency entry naming this CLI's package in ``source``.

    An ``http://`` source, such as a local test server, also carries
    ``allow_insecure: true``, which APM requires for it.
    """
    entry: dict[str, object] = {
        "git": source,
        "path": PACKAGE_PATH,
        "ref": package_ref(),
    }
    if source.startswith("http://"):
        entry["allow_insecure"] = True
    return entry


def write_manifest(
    path: Path, source: str, harnesses: Sequence[str], lock: Lock | None = None
) -> list[str]:
    """Put kmctl's entry and the harnesses into the apm.yml at ``path``, keeping the rest.

    The entry replaces the first earlier kmctl entry in place, from this
    source or another one (``lock`` says where kmctl came from), and any
    further kmctl entries are removed, so apm.yml never names the package
    twice. A missing file is created. ``targets`` gains each harness it
    lacks, because APM records targets in apm.yml only when it creates the
    file (spike:kmctl-doctor/1). Comments and layout are kept.

    Returns
    -------
    list[str]
        A note per replaced entry that came from another source.

    Raises
    ------
    PluginError
        When the existing file is not a YAML mapping.
    """
    data = read_manifest(path)
    if data is None:
        name = re.sub(r"[^A-Za-z0-9._-]", "-", path.parent.name).strip("-.")
        data = {"name": name or "project", "version": "0.1.0"}
    targets = data.get("targets")
    if not isinstance(targets, list):
        targets = [targets] if isinstance(targets, str) else []
        data["targets"] = targets
    for harness in harnesses:
        if harness not in targets:
            targets.append(harness)
    deps = data.get("dependencies")
    if not isinstance(deps, dict):
        deps = {}
        data["dependencies"] = deps
    entries = deps.get("apm")
    if not isinstance(entries, list):
        entries = []
        deps["apm"] = entries
    locked = _locked_kmctl_urls(lock)
    found = [i for i, e in enumerate(entries) if _is_kmctl_entry(e, source, locked)]
    notes = [
        f"replaced the kmctl entry from {entries[i]['git']} with one from {source}"
        for i in found
        if entries[i].get("git") != source
    ]
    for i in reversed(found[1:]):
        del entries[i]
    if found:
        entries[found[0]] = kmctl_entry(source)
    else:
        entries.append(kmctl_entry(source))
    out = StringIO()
    _roundtrip().dump(data, out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out.getvalue(), encoding="utf-8")
    return notes


def apm_install_args(
    harnesses: Sequence[str], scope: Scope, source: str, force: bool
) -> list[str]:
    """The arguments ``install`` gives ``apm``, after ``uvx --from APM_CLI apm``."""
    args = ["install", "--target", ",".join(harnesses)]
    if scope == "user":
        args.append("-g")
    if force:
        args.append("--force")
    if source.startswith("http://"):
        args.append("--allow-insecure")
    return args


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


def skipped_skills(
    cwd: Path, scope: Scope, harnesses: Sequence[str] = ("claude",)
) -> list[str]:
    """The kmctl skill folders APM left alone because files it did not write were there.

    APM prints only a count (spike:apm-only-install/5), so this compares the
    skills this release ships, in each harness's skills folder, with the
    paths the lock says APM deployed. Antigravity installs at project scope
    only.
    """
    root = apm_root(cwd, scope)
    package = kmctl_package(read_lock(cwd, scope))
    deployed = {
        (root / p).resolve() for p in (package.deployed_files if package else [])
    }
    names = sorted(p.name for p in skills_dir().iterdir() if p.is_dir())
    found = []
    for harness in harnesses:
        if harness == "claude" and scope == "user":
            folder, shown = claude_config_dir(), str(claude_config_dir())
        else:
            shown = ".agents" if harness == "antigravity" else ".claude"
            folder = cwd / shown
        found += [
            f"{shown}/skills/{n}"
            for n in names
            if (folder / "skills" / n).resolve() not in deployed
        ]
    return found


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
            f"{path} is not valid JSON ({error}); fix it, then run kmctl plugin "
            "install again"
        ) from error
    if not isinstance(data, dict):
        raise PluginError(
            f"{path} is not a JSON object; fix it, then run kmctl plugin install again"
        )
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    """Write ``data`` to ``path`` as indented JSON, creating its folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _is_kmctl_hook(hook: object) -> bool:
    """Whether a settings.json hook is kmctl's, which kmctl knows by its command."""
    return isinstance(hook, dict) and HOOK_MARK in str(hook.get("command", ""))


def merge_hook(path: Path) -> None:
    """Put exactly one kmctl SessionStart hook into the settings.json at ``path``.

    The first hook that runs ``kmctl briefing`` is replaced in place and any
    other is removed, with a group it leaves empty; with none, a new
    SessionStart group is appended. Every other key and hook is kept, and a
    missing file is created.

    Raises
    ------
    PluginError
        When the file, or its ``hooks`` value, is not a JSON object.
    """
    data = read_json(path)
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise PluginError(
            f'{path} has a "hooks" value that is not an object; fix it, then run '
            "kmctl plugin install again"
        )
    groups = hooks.get("SessionStart")
    placed = False
    merged: list[object] = []
    for group in groups if isinstance(groups, list) else []:
        inner = group.get("hooks") if isinstance(group, dict) else None
        if not isinstance(inner, list) or not any(_is_kmctl_hook(h) for h in inner):
            merged.append(group)
            continue
        kept = []
        for hook in inner:
            if not _is_kmctl_hook(hook):
                kept.append(hook)
            elif not placed:
                kept.append(hook_entry())
                placed = True
        if kept:
            merged.append({**group, "hooks": kept})
    if not placed:
        merged.append({"hooks": [hook_entry()]})
    hooks["SessionStart"] = merged
    _write_json(path, data)


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


def merge_mcp(path: Path) -> str | None:
    """Put kmctl's okf-bundle server into the .mcp.json at ``path``, keeping other servers.

    It replaces a server named ``okf-bundle``, so a new okf pin reaches it.
    When another server already runs okf's script, it adds none and removes
    its own, so one okf server is left.

    Returns
    -------
    str | None
        The name of the other okf server it kept, or None when it wrote its own.

    Raises
    ------
    PluginError
        When the file is not a JSON object.
    """
    data = read_json(path)
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        servers = {}
        data["mcpServers"] = servers
    other = other_okf_server(servers)
    if other is not None:
        if servers.pop(MCP_NAME, None) is not None:
            _write_json(path, data)
        return other
    servers[MCP_NAME] = okf_mcp_server()
    _write_json(path, data)
    return None


def install_mcp(cwd: Path, scope: Scope) -> list[str]:
    """Declare okf's MCP server for Claude Code at ``scope``, and say what happened.

    At project scope it merges the server into the repository's .mcp.json; at
    user scope it runs ``claude mcp add-json --scope user``. Either way it
    keeps an okf server that is already there under another name.

    Raises
    ------
    PluginError
        When .mcp.json is not a JSON object or ``claude mcp add-json`` fails.
    """
    if scope == "project":
        kept = merge_mcp(cwd / ".mcp.json")
        if kept is not None:
            return [
                (
                    f"kept the okf MCP server {kept!r} already in .mcp.json, so kmctl "
                    f"added no {MCP_NAME}"
                )
            ]
        return [
            (
                f"declared okf's MCP server {MCP_NAME} in .mcp.json; Claude Code asks "
                "you to approve it once"
            )
        ]
    config = user_mcp_file()
    try:
        servers = read_json(config).get("mcpServers")
    except PluginError:
        servers = None
    kept = other_okf_server(servers)
    own = isinstance(servers, dict) and MCP_NAME in servers
    has_claude = shutil.which("claude") is not None
    if kept is not None:
        if own and has_claude:
            remove = ["mcp", "remove", MCP_NAME, "--scope", "user"]
            _require(_run(["claude", *remove], cwd), f"claude {' '.join(remove)}")
        return [
            (
                f"kept the okf MCP server {kept!r} already in {config}, so kmctl "
                f"added no {MCP_NAME}"
            )
        ]
    server = json.dumps(okf_mcp_server())
    add = ["mcp", "add-json", MCP_NAME, server, "--scope", "user"]
    if not has_claude:
        return [
            (
                "the claude CLI is not on PATH, so kmctl did not add okf's MCP server; "
                f"run claude mcp add-json {MCP_NAME} '{server}' --scope user"
            )
        ]
    # add-json refuses a name that exists, so drop kmctl's own entry first.
    if own:
        remove = ["mcp", "remove", MCP_NAME, "--scope", "user"]
        _require(_run(["claude", *remove], cwd), f"claude {' '.join(remove)}")
    _require(_run(["claude", *add], cwd), f"claude mcp add-json {MCP_NAME}")
    return [f"declared okf's MCP server {MCP_NAME} at user scope"]


# Install -----------------------------------------------------------------------


def install(
    cwd: Path,
    harnesses: Sequence[str],
    scope: Scope = "project",
    source: str = DEFAULT_SOURCE,
    force: bool = False,
) -> InstallResult:
    """Install this CLI's package for ``harnesses`` with APM, then the hook and okf's MCP server.

    In order: refuse early when uvx is missing or a file it edits does not
    parse; ``apm uninstall`` an old apm.yml entry; write kmctl's entry and the
    targets into apm.yml; run ``apm install`` (``-g`` at user scope,
    ``--force`` when asked); fail when APM left a skill folder in place; only
    then remove the old claude plugin, so a failed install leaves it working;
    then, for Claude Code, write the SessionStart hook and declare okf's MCP
    server, and for Antigravity, rewrite its plugin folder
    (``antigravity.write_plugin``) and delete APM's copies of kmctl's rules
    there (``antigravity.drop_apm_rules``). ``kmctl plugin update`` runs the
    same.

    Parameters
    ----------
    cwd :
        The repository; at user scope, only where claude runs.
    harnesses :
        Names from ``HARNESSES``, as ``parse_harnesses`` returns them.
    scope :
        ``project`` (this repository) or ``user`` (every repository).
    source :
        The git URL holding the package.
    force :
        Pass ``--force`` to APM, which then replaces files it did not write.

    Returns
    -------
    InstallResult
        The harnesses and scope, the ref the lock records, and notes on what
        else it did.

    Raises
    ------
    PluginError
        When a step fails, or APM left files in place, naming the fix.
    """
    # antigravity imports this module, so it is imported here, not at the top.
    from kmctl import antigravity

    _preflight(cwd, scope, harnesses)
    notes = remove_old_apm_entry(cwd, scope, source)
    notes += write_manifest(
        apm_dir(cwd, scope) / "apm.yml", source, harnesses, read_lock(cwd, scope)
    )
    args = apm_install_args(harnesses, scope, source, force)
    proc = _apm_run(args, apm_root(cwd, scope))
    _require(proc, f"uvx --from {APM_CLI} apm {' '.join(args)}")
    if SKIP_LINE in proc.stdout + proc.stderr:
        skipped = skipped_skills(cwd, scope, harnesses) or ["files APM does not name"]
        again = "kmctl plugin install --harness " + ",".join(harnesses)
        again += " --scope user" if scope == "user" else ""
        raise PluginError(
            f"APM left in place files it did not write: {', '.join(skipped)}; run "
            f"{again} --force to replace them (--force replaces each of those "
            "folders whole, deleting any file you added there)"
        )
    if "claude" in harnesses:
        notes = remove_old_plugin(cwd, scope) + notes
        merge_hook(settings_path(cwd, scope))
        notes += install_mcp(cwd, scope)
    package = kmctl_package(read_lock(cwd, scope))
    if "antigravity" in harnesses:
        folder = antigravity.write_plugin(cwd)
        antigravity.drop_apm_rules(cwd, package.deployed_files if package else [])
        notes.append(
            f"wrote {shown_path(folder, cwd)}/ (the agents, the rules, the SessionStart "
            f"hook and okf's MCP server {antigravity.MCP_NAME}); Antigravity loads it "
            "once you trust this folder"
        )
    return InstallResult(
        scope, list(harnesses), package.resolved_ref if package else None, notes
    )


def _preflight(cwd: Path, scope: Scope, harnesses: Sequence[str]) -> None:
    """Refuse before changing anything when uvx is missing, a file kmctl edits does not parse, or Antigravity is asked for at user scope.

    Raises
    ------
    PluginError
        Naming the missing tool, the broken file or the unsupported scope, and the fix.
    """
    if scope == "user" and "antigravity" in harnesses:
        raise PluginError(
            "antigravity installs per repository only: APM 0.33.0 writes no "
            "rules or hooks at Antigravity's user scope; run kmctl plugin "
            "install --harness antigravity in each repository, without --scope user"
        )
    if shutil.which("uvx") is None:
        raise PluginError(
            "uvx is not on PATH, and kmctl runs APM through it; install uv "
            "(https://docs.astral.sh/uv/), then run kmctl plugin install again"
        )
    read_manifest(apm_dir(cwd, scope) / "apm.yml")
    if "claude" in harnesses:
        read_json(settings_path(cwd, scope))
        if scope == "project":
            read_json(cwd / ".mcp.json")


def shown_path(path: Path, cwd: Path) -> str:
    """``path`` as a reader finds it: relative to ``cwd`` when inside it, else in full."""
    try:
        return str(path.relative_to(cwd))
    except ValueError:
        return str(path)
