"""Install kmctl's APM package for an agent harness, and the pieces APM leaves out (ADR 0014, ADR 0020).

``install`` writes the kmctl entry into the repository's apm.yml and runs
``apm install`` at the version pinned in ``APM_CLI``. The package carries the
skills, rules, SessionStart hooks and okf's MCP server for each harness, so
kmctl adds only what APM cannot install yet: for Antigravity, the plugin
folder of agents ``kmctl.antigravity`` builds, and the removal of APM's broken
okf Stop handler. Before that it moves older installs over: the claude plugin
``kmctl@kmctl`` (ADR 0003), an apm.yml entry naming the package another way
(ADR 0013), and the hook and MCP entry an older kmctl wrote itself.

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
from urllib.parse import urlsplit

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


def _require(
    proc: subprocess.CompletedProcess[str],
    what: str,
    again: str = "kmctl plugin install",
) -> None:
    """Raise when ``proc`` failed, naming the command ``what``, its cause and the verb ``again`` to rerun."""
    if proc.returncode != 0:
        output = f"{proc.stderr}\n{proc.stdout}"
        raise PluginError(
            f"{what} failed: {_cause(output)}; run it by hand to see why, then "
            f"{again} again"
        )


def _apm(args: list[str], cwd: Path, again: str = "kmctl plugin install") -> None:
    """Run APM at ``APM_CLI`` through uvx, raising when it fails.

    Raises
    ------
    PluginError
        When uvx is not on PATH or APM fails, with APM's cause.
    """
    _require(
        _apm_run(args, cwd, again), f"uvx --from {APM_CLI} apm {' '.join(args)}", again
    )


def _apm_run(
    args: list[str], cwd: Path, again: str = "kmctl plugin install"
) -> subprocess.CompletedProcess[str]:
    """Run APM at ``APM_CLI`` through uvx and return what it did.

    Raises
    ------
    PluginError
        When uvx is not on PATH.
    """
    if shutil.which("uvx") is None:
        raise PluginError(
            "uvx is not on PATH, and kmctl runs APM through it; install uv "
            f"(https://docs.astral.sh/uv/), then run {again} again"
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


def kmctl_entry(source: str, ref: str | None = None) -> dict[str, object]:
    """The apm.yml dependency entry naming the package in ``source`` at ``ref``, by default this CLI's.

    An ``http://`` source, such as a local test server, also carries
    ``allow_insecure: true``, which APM requires for it.
    """
    entry: dict[str, object] = {
        "git": source,
        "path": PACKAGE_PATH,
        "ref": ref or package_ref(),
    }
    if source.startswith("http://"):
        entry["allow_insecure"] = True
    return entry


def write_manifest(
    path: Path,
    source: str,
    harnesses: Sequence[str],
    lock: Lock | None = None,
    ref: str | None = None,
) -> list[str]:
    """Put kmctl's entry and the harnesses into the apm.yml at ``path``, keeping the rest.

    The entry replaces the first earlier kmctl entry in place, from this
    source or another one (``lock`` says where kmctl came from), and any
    further kmctl entries are removed, so apm.yml never names the package
    twice. A missing file is created. ``targets`` gains each harness it
    lacks, because APM records targets in apm.yml only when it creates the
    file (spike:kmctl-doctor/1). Comments and layout are kept. ``ref`` is
    the tag the entry names, by default this CLI's (``package_ref``).

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
        entries[found[0]] = kmctl_entry(source, ref)
    else:
        entries.append(kmctl_entry(source, ref))
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


def drop_old_mcp(cwd: Path, scope: Scope) -> list[str]:
    """Take out an ``okf-bundle`` entry an older kmctl wrote that differs from the package's.

    APM skips an MCP server that is already configured, so an entry at an
    older okf pin would stay; once it is gone, ``apm install`` writes the
    package's (spike:plugin-patch/1, spike:apm-hands-back/5). At user scope
    it uses ``claude mcp remove``. Every other server stays.

    Returns
    -------
    list[str]
        A note when the claude CLI is missing and the entry stays.
    """
    if scope == "project":
        path = cwd / ".mcp.json"
        if not path.is_file():
            return []
        data = read_json(path)
        servers = data.get("mcpServers")
        if (
            isinstance(servers, dict)
            and MCP_NAME in servers
            and not okf_server_current(servers[MCP_NAME])
        ):
            del servers[MCP_NAME]
            _write_json(path, data)
        return []
    try:
        servers = read_json(user_mcp_file()).get("mcpServers")
    except PluginError:
        servers = None
    if not (
        isinstance(servers, dict)
        and MCP_NAME in servers
        and not okf_server_current(servers[MCP_NAME])
    ):
        return []
    args = ["mcp", "remove", MCP_NAME, "--scope", "user"]
    if shutil.which("claude") is None:
        return [
            (
                f"the claude CLI is not on PATH, so kmctl left an older {MCP_NAME} "
                f"that APM will not replace; run claude {' '.join(args)}, then "
                "kmctl plugin install again"
            )
        ]
    _require(_run(["claude", *args], cwd), f"claude {' '.join(args)}")
    return []


# Install -----------------------------------------------------------------------


def install(
    cwd: Path,
    harnesses: Sequence[str],
    scope: Scope = "project",
    source: str = DEFAULT_SOURCE,
    force: bool = False,
    ref: str | None = None,
) -> InstallResult:
    """Install this CLI's package for ``harnesses`` with APM, then what APM cannot install yet.

    In order: refuse early when uvx is missing or a file it edits does not
    parse; ``apm uninstall`` an old apm.yml entry; for Claude Code, remove
    what an older kmctl wrote that APM now writes (``drop_old_hook``,
    ``drop_old_mcp``); write kmctl's entry and the targets into apm.yml; run
    ``apm install`` (``-g`` at user scope, ``--force`` when asked), which
    writes the skills, rules, hooks and okf's MCP server (ADR 0020); fail when
    APM left a skill folder in place; only then remove the old claude plugin,
    so a failed install leaves it working; and for Antigravity, write the
    plugin folder of translated agents (``antigravity.write_plugin``) and take
    APM's broken okf Stop handler out (``antigravity.drop_apm_okf_stop``).
    ``kmctl plugin update`` runs the same.

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
    ref :
        The package tag to install, by default this CLI's; ``kmctl plugin
        remove`` passes the removed entry's, so the harnesses it keeps stay
        at their version.

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
    if "claude" in harnesses:
        drop_old_hook(settings_path(cwd, scope))
        notes += drop_old_mcp(cwd, scope)
    notes += write_manifest(
        apm_dir(cwd, scope) / "apm.yml",
        source,
        harnesses,
        read_lock(cwd, scope),
        ref,
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
    package = kmctl_package(read_lock(cwd, scope))
    if "antigravity" in harnesses:
        folder = antigravity.write_plugin(cwd)
        antigravity.drop_apm_okf_stop(cwd)
        notes.append(
            f"wrote {shown_path(folder, cwd)}/ (the agents, which APM does not "
            "install for Antigravity yet); Antigravity loads it once you trust "
            "this folder"
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


# Remove ------------------------------------------------------------------------
#
# ``apm uninstall`` on kmctl's entry takes kmctl's and okf's skills, agent,
# rules, hooks and lock entries (spike:plugin-remove/3). Dropping one target
# and installing again would leave okf's Antigravity hook script behind
# (spike:plugin-remove/2), so removing some of the installed harnesses
# uninstalls the package and installs the kept ones again, from the same
# source at the same ref (ADR 0019).


#: The command a failed step of ``remove`` tells the reader to run again.
REMOVE_AGAIN = "kmctl plugin remove"


@dataclass
class RemoveResult:
    """What ``remove`` did.

    Attributes
    ----------
    scope : str
        ``project`` or ``user``.
    removed : list[str]
        The harnesses kmctl was removed from.
    kept : list[str]
        The harnesses still installed, reinstalled at their ref.
    notes : list[str]
        One line per thing a reader should know: a harness that was not
        installed, a target kept, a step skipped and why.
    """

    scope: str
    removed: list[str]
    kept: list[str]
    notes: list[str]


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


def _kmctl_entries(cwd: Path, scope: Scope) -> list[object]:
    """kmctl's entries in the apm.yml at ``scope``, as ``write_manifest`` finds them."""
    locked = _locked_kmctl_urls(read_lock(cwd, scope))
    manifest = read_manifest(apm_dir(cwd, scope) / "apm.yml")
    return [e for e in apm_entries(manifest) if _is_kmctl_entry(e, "", locked)]


def _drop_targets(cwd: Path, scope: Scope, removed: list[str]) -> list[str]:
    """Take ``removed`` out of apm.yml's ``targets`` when no other dependency is left there.

    Install only adds targets, so a target may be one the repository's own
    packages use; with another ``dependencies.apm`` entry left, the target
    stays and a note says so.
    """
    path = apm_dir(cwd, scope) / "apm.yml"
    data: Any = read_manifest(path)
    if not isinstance(data, dict):
        return []
    targets = data.get("targets")
    if not isinstance(targets, list):
        return []
    named = [h for h in removed if h in targets]
    if not named:
        return []
    if apm_entries(data):
        return [
            (
                f"kept {', '.join(named)} in apm.yml's targets, because other "
                "packages there may use it; a bare apm install (without --target) "
                "would deploy kmctl's package to it again"
            )
        ]
    for harness in named:
        targets.remove(harness)
    out = StringIO()
    _roundtrip().dump(data, out)
    path.write_text(out.getvalue(), encoding="utf-8")
    return []


def unhook(path: Path) -> bool:
    """Take kmctl's SessionStart hook out of the settings.json at ``path``; return whether it was there.

    Every other key and hook stays; a group left empty goes, and so does a
    SessionStart list or hooks object left empty. A missing file is left
    missing.
    """
    if not path.is_file():
        return False
    data = read_json(path)
    hooks = data.get("hooks")
    groups = hooks.get("SessionStart") if isinstance(hooks, dict) else None
    if not isinstance(groups, list):
        return False
    found = False
    kept: list[object] = []
    for group in groups:
        inner = group.get("hooks") if isinstance(group, dict) else None
        if not isinstance(inner, list) or not any(_is_kmctl_hook(h) for h in inner):
            kept.append(group)
            continue
        found = True
        rest = [h for h in inner if not _is_kmctl_hook(h)]
        if rest:
            kept.append({**group, "hooks": rest})
    if not found:
        return False
    assert isinstance(hooks, dict)
    if kept:
        hooks["SessionStart"] = kept
    else:
        del hooks["SessionStart"]
    if not hooks:
        del data["hooks"]
    _write_json(path, data)
    return True


def _remove_mcp(cwd: Path, scope: Scope) -> list[str]:
    """Take kmctl's okf-bundle MCP server out, keeping every other server, okf's included."""
    if scope == "user":
        try:
            servers = read_json(user_mcp_file()).get("mcpServers")
        except PluginError:
            servers = None
        if not (isinstance(servers, dict) and _is_okf_server(servers.get(MCP_NAME))):
            return []
        args = ["mcp", "remove", MCP_NAME, "--scope", "user"]
        if shutil.which("claude") is None:
            return [
                (
                    "the claude CLI is not on PATH, so kmctl left okf's MCP server "
                    f"{MCP_NAME}; run claude {' '.join(args)}"
                )
            ]
        _require(_run(["claude", *args], cwd), f"claude {' '.join(args)}", REMOVE_AGAIN)
        return []
    path = cwd / ".mcp.json"
    if not path.is_file():
        return []
    data = read_json(path)
    servers = data.get("mcpServers")
    if isinstance(servers, dict) and _is_okf_server(servers.get(MCP_NAME)):
        del servers[MCP_NAME]
        _write_json(path, data)
    # APM's uninstall leaves the file with no servers; nothing else wrote it.
    if servers == {} and set(data) == {"mcpServers"}:
        path.unlink()
    return []


def _remove_antigravity(cwd: Path) -> None:
    """Delete kmctl's plugin folder, and APM's hooks.json and mcp_config.json when the uninstall left them empty."""
    from kmctl import antigravity

    folder = antigravity.plugin_dir(cwd)
    if folder.exists():
        shutil.rmtree(folder)
    for path, empty in (
        (cwd / antigravity.APM_HOOKS, {}),
        (cwd / ".agents" / "mcp_config.json", {"mcpServers": {}}),
    ):
        if not path.is_file():
            continue
        try:
            left = read_json(path)
        except PluginError:
            continue
        if left in ({}, empty):
            path.unlink()


def remove(cwd: Path, harnesses: list[str], scope: Scope = "project") -> RemoveResult:
    """Remove kmctl's package, hook and okf's MCP server from ``harnesses``, keeping the rest.

    In order: uninstall kmctl's apm.yml entry with APM (``-g`` at user
    scope); take each removed harness out of apm.yml's ``targets`` when no
    other dependency is left; delete what kmctl wrote for each removed
    harness; then, when harnesses stay installed, install them again from
    the removed entry's source at its ref.

    Parameters
    ----------
    cwd :
        The repository; at user scope, only where APM and claude run.
    harnesses :
        Names from ``HARNESSES``, as ``parse_harnesses`` returns them.
    scope :
        ``project`` or ``user``.

    Returns
    -------
    RemoveResult
        The harnesses removed and kept, and notes; nothing removed when none
        of ``harnesses`` is installed.

    Raises
    ------
    PluginError
        When a step fails. When the reinstall of the kept harnesses fails,
        it names APM's cause and the install that puts them back.
    """
    # doctor imports this module, so it is imported here, not at the top.
    from kmctl.doctor import harnesses_found

    installed = harnesses_found(cwd, scope)
    removed = [h for h in harnesses if h in installed]
    notes = [
        f"kmctl is not installed for {h} ({scope} scope); nothing to remove there"
        for h in harnesses
        if h not in installed
    ]
    if not removed:
        return RemoveResult(scope, [], installed, notes)
    kept = [h for h in installed if h not in removed]
    entries = _kmctl_entries(cwd, scope)
    entry = entries[0] if entries else None
    for each in entries:
        _apm(
            ["uninstall", uninstall_name(each), *(["-g"] if scope == "user" else [])],
            apm_root(cwd, scope),
            REMOVE_AGAIN,
        )
    notes += _drop_targets(cwd, scope, removed)
    if "claude" in removed:
        unhook(settings_path(cwd, scope))
        notes += _remove_mcp(cwd, scope)
    if "antigravity" in removed:
        _remove_antigravity(cwd)
    if kept and isinstance(entry, dict) and entry.get("git"):
        source, ref = str(entry["git"]), str(entry.get("ref") or "") or None
        try:
            notes += install(cwd, kept, scope, source=source, ref=ref).notes
        except PluginError as error:
            again = f"kmctl plugin install --harness {','.join(kept)} --source {source}"
            again += " --scope user" if scope == "user" else ""
            raise PluginError(
                f"{error}; kmctl removed its package from {', '.join(removed)} and "
                f"uninstalled it from {', '.join(kept)} too, so run {again} to put "
                "it back (it installs at this kmctl's version)"
            ) from error
    return RemoveResult(scope, removed, kept, notes)
