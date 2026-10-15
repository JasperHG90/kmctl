"""Install the Claude Code plugin that ships inside this kmctl release (ADR 0001, ADR 0003).

The plugin and its marketplace file are package data. ``install`` copies them
to one fixed staging folder, stamped with this CLI's version, registers that
folder as the ``kmctl`` marketplace, and installs ``kmctl@kmctl``. The okf
dependency lives in the scaccogatto marketplace, which ``claude plugin
install`` does not add by itself (spike:plugin-install-verb/1), so it is added
first. The command order follows loopctl's working installer.
"""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from typing import Literal

Scope = Literal["project", "user"]
MARKETPLACE = "kmctl"
PLUGIN_ID = "kmctl@kmctl"
OKF_MARKETPLACE = "scaccogatto"
OKF_SOURCE = "scaccogatto/okf-skills"


class PluginError(Exception):
    """An install step that failed; the message names the fix."""


@dataclass(frozen=True)
class PluginStatus:
    """The installed plugin against this CLI."""

    cli_version: str
    plugin_version: str | None
    staged_version: str | None
    marketplace_path: str | None
    problems: list[str]


def cli_version() -> str:
    """This kmctl's version, which the staged plugin is stamped with."""
    return version("kmctl")


def data_dir() -> Path:
    """Where kmctl keeps local state: $XDG_DATA_HOME/kmctl, by default ~/.local/share/kmctl."""
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "kmctl"


def staging_dir() -> Path:
    """The one folder the plugin is staged in, so the marketplace path never changes."""
    return data_dir() / "marketplace"


def _payload() -> tuple[Path, Path]:
    """The plugin folder and marketplace file: package data in a wheel, the repository in a checkout."""
    package = Path(str(files("kmctl")))
    if (package / "_plugin").is_dir():
        return package / "_plugin", package / "_marketplace.json"
    repo = Path(__file__).resolve().parents[2]
    return repo / "plugin", repo / ".claude-plugin" / "marketplace.json"


def skills_dir() -> Path:
    """The skills/ folder of the plugin this release ships."""
    return _payload()[0] / "skills"


def stage() -> Path:
    """Copy this release's plugin into the staging folder, stamped with this CLI's version."""
    plugin_src, marketplace_src = _payload()
    dest = staging_dir()
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(
        plugin_src, dest / "plugin", ignore=shutil.ignore_patterns("__pycache__")
    )
    (dest / ".claude-plugin").mkdir(parents=True)
    shutil.copyfile(marketplace_src, dest / ".claude-plugin" / "marketplace.json")
    manifest = dest / "plugin" / ".claude-plugin" / "plugin.json"
    data = json.loads(manifest.read_text())
    data["version"] = cli_version()
    manifest.write_text(json.dumps(data, indent=2) + "\n")
    return dest


def _claude(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    if shutil.which("claude") is None:
        raise PluginError("the claude CLI is not on PATH; install Claude Code first")
    return subprocess.run(
        ["claude", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def _require(proc: subprocess.CompletedProcess[str], args: list[str]) -> None:
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        raise PluginError(
            f"claude {' '.join(args)} failed: {detail[-1] if detail else 'no output'}; "
            "run it by hand to see why, then kmctl plugin install again"
        )


def _json(args: list[str], cwd: Path) -> list[dict]:
    proc = _claude(args, cwd)
    _require(proc, args)
    return json.loads(proc.stdout or "[]")


def _entry(cwd: Path, scope: Scope | None) -> dict | None:
    """This plugin's entry in ``claude plugin list`` for ``scope``, or for whichever applies here.

    claude lists project-scope installs of every repository, so a project entry
    counts only when its project path is ``cwd``. With no ``scope``, this
    repository's project install wins over a user install.
    """
    here = cwd.resolve()
    entries = [
        p for p in _json(["plugin", "list", "--json"], cwd) if p.get("id") == PLUGIN_ID
    ]
    project = [
        p
        for p in entries
        if p.get("scope") == "project"
        and p.get("projectPath")
        and Path(p["projectPath"]).resolve() == here
    ]
    user = [p for p in entries if p.get("scope") == "user"]
    if scope == "project":
        return project[0] if project else None
    if scope == "user":
        return user[0] if user else None
    found = project or user
    return found[0] if found else None


def install(scope: Scope, cwd: Path, reinstall: bool = False) -> PluginStatus:
    """Stage the plugin and install it with its okf dependency at ``scope``.

    Parameters
    ----------
    scope : Scope
        ``project`` (the repository at ``cwd``) or ``user`` (every repository).
    cwd : Path
        The repository a project-scope install is declared in.
    reinstall : bool
        Uninstall first, as ``kmctl plugin update`` does, so a newer staged
        version replaces the installed one.

    Returns
    -------
    PluginStatus
        What is installed afterwards.

    Raises
    ------
    PluginError
        When claude is missing, a step fails, or the plugin is not listed at
        this CLI's version afterwards.
    """
    folder = stage()
    # Declare the okf marketplace at this scope every time: another scope having it
    # does not declare it here, and adding it again is a no-op (spike 3).
    add_okf = ["plugin", "marketplace", "add", OKF_SOURCE, "--scope", scope]
    _require(_claude(add_okf, cwd), add_okf)
    add = ["plugin", "marketplace", "add", str(folder), "--scope", scope]
    if _claude(add, cwd).returncode != 0:
        refresh = ["plugin", "marketplace", "update", MARKETPLACE]
        _require(_claude(refresh, cwd), refresh)
    if reinstall:
        _claude(["plugin", "uninstall", PLUGIN_ID, "--scope", scope], cwd)
    put = ["plugin", "install", PLUGIN_ID, "--scope", scope]
    _require(_claude(put, cwd), put)
    result = status(cwd, scope)
    if result.plugin_version != cli_version():
        raise PluginError(
            f"claude lists {PLUGIN_ID} at {result.plugin_version}, not {cli_version()}; "
            "run kmctl plugin update"
        )
    return result


def status(cwd: Path, scope: Scope | None = None) -> PluginStatus:
    """Report the installed plugin, the staged copy and the marketplace path against this CLI.

    The installed version is the one ``claude plugin list`` reports for this
    repository (or ``scope``), never the staged copy kmctl itself writes.
    """
    entry = _entry(cwd, scope)
    markets = {
        m.get("name"): m
        for m in _json(["plugin", "marketplace", "list", "--json"], cwd)
    }
    path = (markets.get(MARKETPLACE) or {}).get("path")
    manifest = staging_dir() / "plugin" / ".claude-plugin" / "plugin.json"
    staged = (
        json.loads(manifest.read_text()).get("version") if manifest.is_file() else None
    )
    installed = entry.get("version") if entry else None
    problems = []
    if entry is None:
        problems.append(f"{PLUGIN_ID} is not installed here; run kmctl plugin install")
    elif installed != cli_version():
        problems.append(
            f"version mismatch: installed plugin {installed}, kmctl {cli_version()}; run kmctl plugin update"
        )
    if staged is not None and staged != cli_version():
        problems.append(
            f"version mismatch: staged plugin {staged}, kmctl {cli_version()}; run kmctl plugin update"
        )
    if path is not None and not Path(path).is_dir():
        problems.append(
            f"marketplace folder {path} does not exist on this machine; run kmctl plugin install"
        )
    return PluginStatus(cli_version(), installed, staged, path, problems)
