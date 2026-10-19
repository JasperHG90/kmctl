"""Run the kmctl a project pins, and say when a newer release is out (ADR 0026).

One ``kmctl`` sits on PATH, but each project pins its own release in
``apm.lock.yaml``. Before any command runs, the copy on PATH finds the
project's lock and, when it pins another release, runs that release's kmctl
through ``uvx`` at the lock's commit, which uv keeps cached per commit. The
child runs with ``KMCTL_PINNED=1``, so it runs as itself. The copy on PATH
(the one without ``KMCTL_PINNED``) also adds the briefing's notices, so a
project pinned to a release from before the hand-off still gets them, and
names the lock after a handed-off ``--version``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from kmctl.plugin import Lock, cli_version, kmctl_package, package_ref

PINNED_ENV = "KMCTL_PINNED"
NO_UPDATE_CHECK_ENV = "KMCTL_NO_UPDATE_CHECK"
SOURCE = "git+https://github.com/JasperHG90/kmctl"
REMOTE = "https://github.com/JasperHG90/kmctl"
LOCK = "apm.lock.yaml"
#: How old the cached newest release may get before a refresh starts.
CACHE_SECONDS = 24 * 60 * 60
#: How long the detached refresh waits for ``git ls-remote``.
REFRESH_TIMEOUT_SECONDS = 30
#: How long the briefing waits for the offline probe; a miss takes about 60 ms
#: (spike:kmctl-follows-the-pin/4).
PROBE_TIMEOUT_SECONDS = 5
_TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?$")
_PRE = {"a": 0, "b": 1, "rc": 2}


@dataclass(frozen=True)
class Pin:
    """The kmctl release a project's lock pins.

    Attributes
    ----------
    ref : str
        The tag APM installed, such as v0.6.0.
    commit : str
        The commit that tag resolved to, which uvx runs.
    """

    ref: str
    commit: str


@dataclass(frozen=True)
class Notice:
    """One line the briefing adds, with the key it goes under in --json.

    Attributes
    ----------
    key : str
        The key in the briefing's JSON object.
    value : dict[str, str]
        What goes under the key.
    text : str
        The line in the text briefing and Antigravity's message.
    """

    key: str
    value: dict[str, str]
    text: str


def pinned() -> bool:
    """Whether this kmctl runs as a project's pinned copy, so it hands off nothing and adds no notices."""
    return bool(os.environ.get(PINNED_ENV))


def path_arg(args: list[str]) -> Path | None:
    """The ``--path`` value in ``args``, as ``--path X`` or ``--path=X``, or None."""
    for i, arg in enumerate(args):
        if arg == "--path" and i + 1 < len(args):
            return Path(args[i + 1])
        if arg.startswith("--path="):
            return Path(arg.removeprefix("--path="))
    return None


def find_lock(start: Path) -> Path | None:
    """The ``apm.lock.yaml`` of the project holding ``start``, or None.

    It looks in ``start``, then each parent, and stops at the first folder
    holding ``.git`` (a folder, or a file in a worktree or submodule), so it
    never reads a parent project's lock. Antigravity runs its hooks in
    ``.agents/``, which the walk takes up to the repository.
    """
    folder = start.resolve()
    for candidate in (folder, *folder.parents):
        if (candidate / LOCK).is_file():
            return candidate / LOCK
        if (candidate / ".git").exists():
            return None
    return None


def project_pin(start: Path) -> Pin | None:
    """The kmctl release the project holding ``start`` pins, or None when its lock pins none."""
    lock_path = find_lock(start)
    if lock_path is None:
        return None
    try:
        lock = Lock.model_validate(yaml.safe_load(lock_path.read_text()) or {})
    except (OSError, yaml.YAMLError, ValidationError):
        return None
    package = kmctl_package(lock)
    if package is None or not package.resolved_ref or not package.resolved_commit:
        return None
    return Pin(ref=package.resolved_ref, commit=package.resolved_commit)


def _uvx(pin: Pin, args: list[str], *, offline: bool) -> list[str] | None:
    """The command that runs ``kmctl ARGS`` at ``pin``'s commit, or None when uvx is not on PATH."""
    uvx = shutil.which("uvx")
    if uvx is None:
        return None
    flags = ["--offline"] if offline else []
    return [uvx, *flags, "--from", f"{SOURCE}@{pin.commit}", "kmctl", *args]


def _child_env() -> dict[str, str]:
    """This environment with ``KMCTL_PINNED=1``, for the pinned child."""
    return {**os.environ, PINNED_ENV: "1"}


def handoff_pin(args: list[str]) -> Pin | None:
    """The pin to hand ``args`` off to, or None when this kmctl runs them itself.

    None when this copy is pinned, the project's lock pins no kmctl, or it
    pins this copy's own release.
    """
    if pinned():
        return None
    pin = project_pin(path_arg(args) or Path.cwd())
    if pin is None or pin.ref == package_ref():
        return None
    return pin


def hand_off(args: list[str]) -> int | None:
    """Run ``args`` with the project's pinned kmctl and return its exit code, or None to run them here.

    Every command but ``briefing`` runs through uvx, which builds the pinned
    copy when uv has not cached it yet; after the pinned ``--version`` line
    it says the lock pins it and which kmctl is on PATH. ``briefing`` runs
    from session hooks that allow 10 s, so it runs only a cached copy: when
    the offline probe fails, it returns None and this kmctl gives the
    briefing, with a notice that the pin is not installed. Over the pinned
    briefing's output it adds the newer-release notice, in the output's own
    form.
    """
    pin = handoff_pin(args)
    if pin is None:
        return None
    if args[:1] != ["briefing"]:
        command = _uvx(pin, args, offline=False)
        if command is None:
            return None
        if args[:1] in (["--version"], ["-V"]):
            return _hand_off_version(command)
        return subprocess.run(command, env=_child_env(), check=False).returncode
    command = _uvx(pin, args, offline=True)
    probe = _uvx(pin, ["--version"], offline=True)
    if command is None or probe is None or not _probe(probe):
        return None
    res = subprocess.run(
        command, env=_child_env(), stdout=subprocess.PIPE, text=True, check=False
    )
    out = res.stdout
    if res.returncode == 0:
        out = add_notices(out, _format(args), update_notices(pin.ref))
    sys.stdout.write(out)
    sys.stdout.flush()
    return res.returncode


def _hand_off_version(command: list[str]) -> int:
    """Run the pinned ``--version`` and return its exit code, naming the lock and the kmctl on PATH after its line.

    The line keeps ``kmctl X.Y.Z`` first, so a script reading the second word
    still gets the version. Output from a failed run is passed on as it is.
    """
    res = subprocess.run(
        command, env=_child_env(), stdout=subprocess.PIPE, text=True, check=False
    )
    out = res.stdout
    line = out.removesuffix("\n")
    if res.returncode == 0 and line.startswith("kmctl ") and "\n" not in line:
        out = f"{line} (pinned by {LOCK}; kmctl {cli_version()} is on PATH)\n"
    sys.stdout.write(out)
    sys.stdout.flush()
    return res.returncode


def _probe(command: list[str]) -> bool:
    """Whether uv has the pinned copy cached: the offline ``--version`` run passes."""
    try:
        res = subprocess.run(
            command,
            env=_child_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=PROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False
    return res.returncode == 0


def _format(args: list[str]) -> str:
    """The briefing's output form in ``args``: json, antigravity or text."""
    if "--json" in args:
        return "json"
    for i, arg in enumerate(args):
        value = arg.removeprefix("--format=") if arg.startswith("--format=") else None
        if arg == "--format" and i + 1 < len(args):
            value = args[i + 1]
        if value == "antigravity":
            return "antigravity"
    return "text"


def add_notices(out: str, form: str, notices: list[Notice]) -> str:
    """``out``, a briefing in ``form`` (text, json or antigravity), with ``notices`` added.

    Text gets each notice as a last line; json a key per notice; antigravity
    each line at the end of its message. Output that is not the JSON the
    form promises is left as it is.
    """
    if not notices:
        return out
    end = "\n" if out.endswith("\n") else ""
    body = out.removesuffix("\n")
    if form == "text":
        return "\n".join([body, *(n.text for n in notices)]) + end
    try:
        data = json.loads(body)
        if form == "json":
            data.update({n.key: n.value for n in notices})
        else:
            message = data["injectSteps"][0]["systemMessage"]
            message["systemMessage"] = "\n".join(
                [message["systemMessage"], *(n.text for n in notices)]
            )
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return out
    return json.dumps(data) + end


def not_installed_notice(pin: Pin) -> Notice:
    """The notice that the project's pinned kmctl is not in uv's cache yet."""
    return Notice(
        key="pin_not_installed",
        value={"pinned": pin.ref, "running": package_ref()},
        text=(
            f"This project pins kmctl {pin.ref}, which is not installed yet, so "
            f"kmctl {package_ref()} gave this briefing; run `just install` (or "
            f"`uvx --from {SOURCE}@{pin.commit} kmctl --version`)."
        ),
    )


def briefing_notices(root: Path) -> list[Notice]:
    """The notices the copy on PATH adds to a briefing it gives itself, for the project at ``root``.

    None when this copy is pinned. When the project pins another release,
    which this copy did not hand off to, the notice says the pin is not
    installed; when a newer release is out than the pin, it says so.
    """
    if pinned():
        return []
    pin = project_pin(root)
    if pin is None:
        return []
    notices = [] if pin.ref == package_ref() else [not_installed_notice(pin)]
    return notices + update_notices(pin.ref)


def update_notices(ref: str) -> list[Notice]:
    """The newer-release notice for a project pinning ``ref``, from the cache, or none.

    It starts a detached refresh when the cache is missing or older than a
    day, and never waits for one. ``KMCTL_NO_UPDATE_CHECK`` turns it off.
    """
    if os.environ.get(NO_UPDATE_CHECK_ENV):
        return []
    latest = cached_latest()
    if latest is None or not newer(latest, ref):
        return []
    return [
        Notice(
            key="newer_release",
            value={"latest": latest, "pinned": ref},
            text=(
                f"kmctl {latest} is out; this project pins {ref}. Tell the user; "
                f"`just upgrade {latest}` moves it."
            ),
        )
    ]


def _version(tag: str) -> tuple[int, ...] | None:
    """``tag`` (vX.Y.Z, or with an a, b or rc suffix) as a sortable tuple, or None."""
    match = _TAG.match(tag)
    if match is None:
        return None
    major, minor, patch, pre, n = match.groups()
    tail = (_PRE[pre], int(n)) if pre else (3, 0)
    return (int(major), int(minor), int(patch), *tail)


def newer(latest: str, ref: str) -> bool:
    """Whether release ``latest`` is newer than the pinned ``ref``."""
    a, b = _version(latest), _version(ref)
    return a is not None and b is not None and a > b


def cache_file() -> Path:
    """The file holding the newest kmctl release tag: kmctl/latest-release in the user's cache folder."""
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "kmctl" / "latest-release"


def cached_latest() -> str | None:
    """The cached newest release tag, starting a detached refresh when the cache is stale or missing."""
    path = cache_file()
    try:
        age = time.time() - path.stat().st_mtime
        latest: str | None = path.read_text().strip() or None
    except OSError:
        age, latest = float("inf"), None
    if age > CACHE_SECONDS:
        start_refresh()
    return latest


def start_refresh() -> None:
    """Start ``python -m kmctl.pin`` detached, with its stdio closed and in its own session.

    The session hook that runs the briefing then neither waits for it nor
    kills it (spike:kmctl-follows-the-pin/2).
    """
    try:
        subprocess.Popen(
            [sys.executable, "-m", "kmctl.pin"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return


def newest_release(ls_remote: str) -> str | None:
    """The newest release tag in ``git ls-remote --tags`` output, skipping pre-releases."""
    tags = [
        line.rsplit("refs/tags/", 1)[-1]
        for line in ls_remote.splitlines()
        if "refs/tags/" in line
    ]
    releases = [t for t in tags if (v := _version(t)) is not None and v[3] == 3]
    return max(releases, key=lambda t: _version(t) or (), default=None)


def refresh() -> None:
    """Write the newest release tag from GitHub to the cache; on any failure, leave the cache as it was."""
    git = shutil.which("git")
    if git is None:
        return
    try:
        res = subprocess.run(
            [git, "ls-remote", "--tags", "--refs", REMOTE],
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=REFRESH_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return
    latest = newest_release(res.stdout) if res.returncode == 0 else None
    if latest is None:
        return
    path = cache_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_suffix(".part")
        part.write_text(latest + "\n")
        part.replace(path)
    except OSError:
        return


if __name__ == "__main__":
    refresh()
