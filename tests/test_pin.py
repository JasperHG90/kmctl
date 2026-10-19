"""The kmctl on PATH runs the kmctl a project's lock pins (ADR 0026).

The default tier puts a fake ``uvx`` on PATH that records how it was
called; the ``integration`` test runs a real ``uvx`` against a file://
clone of this tree, with git rewriting GitHub's URL to it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest
import yaml
from conftest import tree_repo

ROOT = Path(__file__).resolve().parents[1]
TAG = f"v{version('kmctl')}"
OTHER = "v0.5.1"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
SOURCE = "git+https://github.com/JasperHG90/kmctl"
KMCTL_GIT = "https://github.com/JasperHG90/kmctl.git"
# Runs kmctl's entry point as the console script does.
MAIN = "import sys; from kmctl import main; sys.argv[0] = 'kmctl'; main()"
FAKE_UVX = """#!{python}
import json, os, sys
asks_version = "--version" in sys.argv or "-V" in sys.argv
with open(os.environ["FAKE_UVX_LOG"], "a") as log:
    log.write(json.dumps({{
        "args": sys.argv[1:],
        "cwd": os.getcwd(),
        "pinned": os.environ.get("KMCTL_PINNED"),
        "stdin": "" if asks_version else sys.stdin.read(),
    }}) + "\\n")
if asks_version:
    if os.environ.get("FAKE_UVX_MISS"):
        sys.exit(1)
    sys.stdout.write("kmctl 0.5.1\\n")
    sys.exit(int(os.environ.get("FAKE_UVX_EXIT", "0")))
sys.stdout.write(os.environ.get("FAKE_UVX_OUT", "pinned output\\n"))
sys.exit(int(os.environ.get("FAKE_UVX_EXIT", "0")))
"""


def write_lock(
    root: Path, ref: str = OTHER, commit: str | None = COMMIT, name: str = "kmctl"
) -> Path:
    """Write an apm.lock.yaml in ``root`` naming kmctl's package at ``ref`` and ``commit``."""
    entry: dict[str, object] = {
        "repo_url": "jasperhg90/kmctl",
        "name": name,
        "virtual_path": "apm",
        "resolved_ref": ref,
    }
    if commit is not None:
        entry["resolved_commit"] = commit
    lock = root / "apm.lock.yaml"
    lock.write_text(yaml.safe_dump({"lockfile_version": "1", "dependencies": [entry]}))
    return lock


@pytest.fixture
def fake_uvx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fake uvx first on PATH that logs each call; returns the log, and unsets KMCTL_PINNED."""
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    uvx = bin_dir / "uvx"
    uvx.write_text(FAKE_UVX.format(python=sys.executable))
    uvx.chmod(0o755)
    log = tmp_path / "uvx.log"
    log.touch()
    monkeypatch.setenv("FAKE_UVX_LOG", str(log))
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.delenv("KMCTL_PINNED")
    monkeypatch.setenv("KMCTL_NO_UPDATE_CHECK", "1")
    return log


def calls(log: Path) -> list[dict[str, object]]:
    """The fake uvx's logged calls."""
    return [json.loads(line) for line in log.read_text().splitlines()]


def kmctl(cwd: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    """Run kmctl's entry point in ``cwd`` with ``args``."""
    return subprocess.run(
        [sys.executable, "-c", MAIN, *args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def project(tmp_path: Path, name: str = "proj") -> Path:
    """An empty git repository folder."""
    root = tmp_path / name
    (root / ".git").mkdir(parents=True)
    return root


# r1: the hand-off ---------------------------------------------------------------


def test_hands_off_to_the_pinned_commit(tmp_path: Path, fake_uvx: Path) -> None:
    """A lock pinning another release runs uvx at its commit with the args, pinned, streams and code intact."""
    root = project(tmp_path)
    write_lock(root)

    res = subprocess.run(
        [sys.executable, "-c", MAIN, "check", "--json"],
        cwd=root,
        input="some input",
        capture_output=True,
        text=True,
        env={**os.environ, "FAKE_UVX_EXIT": "3"},
        check=False,
    )

    assert res.returncode == 3
    assert res.stdout == "pinned output\n"
    [call] = calls(fake_uvx)
    assert call["args"] == ["--from", f"{SOURCE}@{COMMIT}", "kmctl", "check", "--json"]
    assert call["pinned"] == "1"
    assert call["cwd"] == str(root)
    assert call["stdin"] == "some input"


@pytest.mark.parametrize("form", ["--path", "--path="])
def test_hands_off_by_the_path_option(
    tmp_path: Path, fake_uvx: Path, form: str
) -> None:
    """--path names the project whose pin wins, not the current directory."""
    here = project(tmp_path, "here")
    there = project(tmp_path, "there")
    write_lock(there)
    args = [f"--path={there}"] if form == "--path=" else ["--path", str(there)]

    res = kmctl(here, "check", *args)

    assert res.returncode == 0, res.stderr
    [call] = calls(fake_uvx)
    assert call["args"][1] == f"{SOURCE}@{COMMIT}"
    assert call["args"][3:] == ["check", *args]


def test_hands_off_from_agents_with_the_hook_json(
    tmp_path: Path, fake_uvx: Path
) -> None:
    """Run from .agents/ as Antigravity's hook is, kmctl finds the lock above and the child gets stdin unread."""
    root = project(tmp_path)
    write_lock(root)
    agents = root / ".agents"
    agents.mkdir()
    hook = json.dumps({"workspacePaths": [str(root)]})

    res = kmctl(agents, "briefing", "--format", "antigravity", stdin=hook)

    assert res.returncode == 0, res.stderr
    probe, run = calls(fake_uvx)
    assert probe["args"] == [
        "--offline",
        "--from",
        f"{SOURCE}@{COMMIT}",
        "kmctl",
        "--version",
    ]
    assert run["args"][:3] == ["--offline", "--from", f"{SOURCE}@{COMMIT}"]
    assert run["args"][4:] == ["briefing", "--format", "antigravity"]
    assert run["stdin"] == hook
    assert run["cwd"] == str(agents)


@pytest.mark.parametrize("flag", ["--version", "-V"])
def test_version_names_the_pin(tmp_path: Path, fake_uvx: Path, flag: str) -> None:
    """A handed-off --version prints the pinned version, then says the lock pins it and which kmctl is on PATH."""
    root = project(tmp_path)
    write_lock(root)

    res = kmctl(root, flag)

    assert res.returncode == 0, res.stderr
    assert res.stdout == (
        f"kmctl 0.5.1 (pinned by apm.lock.yaml; kmctl {version('kmctl')} is on PATH)\n"
    )
    [call] = calls(fake_uvx)
    assert call["args"] == ["--from", f"{SOURCE}@{COMMIT}", "kmctl", flag]
    assert call["pinned"] == "1"


def test_version_of_a_failed_pin_is_left_as_is(tmp_path: Path, fake_uvx: Path) -> None:
    """When the pinned --version fails, kmctl passes on its output and exit code without the note."""
    root = project(tmp_path)
    write_lock(root)

    res = subprocess.run(
        [sys.executable, "-c", MAIN, "--version"],
        cwd=root,
        capture_output=True,
        text=True,
        env={**os.environ, "FAKE_UVX_EXIT": "2"},
        check=False,
    )

    assert res.returncode == 2
    assert res.stdout == "kmctl 0.5.1\n"


# r2: when kmctl runs as itself --------------------------------------------------


def _no_lock(root: Path) -> None:
    """Leave the project without a lock."""


def _bad_lock(root: Path) -> None:
    """A lock that does not parse."""
    (root / "apm.lock.yaml").write_text("dependencies: [unclosed\n")


def _no_package(root: Path) -> None:
    """A lock without kmctl's package."""
    write_lock(root, name="other")


def _own_ref(root: Path) -> None:
    """A lock pinning this CLI's own release."""
    write_lock(root, ref=TAG)


def _no_commit(root: Path) -> None:
    """A lock with no resolved_commit."""
    write_lock(root, commit=None)


@pytest.mark.parametrize(
    "setup", [_no_lock, _bad_lock, _no_package, _own_ref, _no_commit]
)
def test_runs_itself_without_a_pin_to_hand_off_to(
    tmp_path: Path, fake_uvx: Path, setup: object
) -> None:
    """No lock, a broken one, no kmctl entry, its own ref or no commit: kmctl runs as itself."""
    root = project(tmp_path)
    assert callable(setup)
    setup(root)

    res = kmctl(root, "--version")

    assert res.stdout == f"kmctl {version('kmctl')}\n"
    assert calls(fake_uvx) == []


def test_runs_itself_when_pinned(
    tmp_path: Path, fake_uvx: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """KMCTL_PINNED set: the pinned child runs as itself."""
    root = project(tmp_path)
    write_lock(root)
    monkeypatch.setenv("KMCTL_PINNED", "1")

    res = kmctl(root, "--version")

    assert res.stdout == f"kmctl {version('kmctl')}\n"
    assert calls(fake_uvx) == []


def test_runs_itself_without_uvx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No uvx on PATH: kmctl runs as itself."""
    root = project(tmp_path)
    write_lock(root)
    monkeypatch.delenv("KMCTL_PINNED")
    monkeypatch.setenv("PATH", "/nonexistent")

    res = kmctl(root, "--version")

    assert res.stdout == f"kmctl {version('kmctl')}\n"


def test_runs_itself_and_never_crosses_a_git_folder(
    tmp_path: Path, fake_uvx: Path
) -> None:
    """A lock in a parent project above the .git boundary is not this project's pin."""
    write_lock(tmp_path)
    root = project(tmp_path)
    worktree = tmp_path / "wt"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: elsewhere\n")

    for cwd in (root, worktree):
        res = kmctl(cwd, "--version")
        assert res.stdout == f"kmctl {version('kmctl')}\n"
    assert calls(fake_uvx) == []


# r7: the suite never hands off by accident --------------------------------------


def test_suite_is_pinned() -> None:
    """conftest sets KMCTL_PINNED for every test, so fixture locks never send kmctl to GitHub."""
    assert os.environ.get("KMCTL_PINNED") == "1"


# r10: the CI action runs its own tag --------------------------------------------


def test_action_runs_its_own_kmctl() -> None:
    """Every action.yml step that runs kmctl (the checks, and the agent, which runs shell commands) has KMCTL_PINNED=1.

    Publish runs in a job that never installs kmctl.
    """
    steps = yaml.safe_load((ROOT / "action.yml").read_text())["runs"]["steps"]
    runs_kmctl = [
        s
        for s in steps
        if s.get("if") in ("inputs.mode == 'checks'", "inputs.mode == 'audit'")
        and ("knowledge-ci.sh" in s.get("run", "") or "agent.py" in s.get("run", ""))
    ]

    assert runs_kmctl
    for step in runs_kmctl:
        assert step.get("env", {}).get("KMCTL_PINNED") == "1", step["name"]


# r3: a real uvx -----------------------------------------------------------------


@pytest.mark.integration
def test_hands_off_through_a_real_uvx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A lock pinning this tree's commit at another ref runs that commit's kmctl, then from uv's cache offline."""
    work = tree_repo(tmp_path / "kmctl")
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=work,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    bare = tmp_path / "srv" / "kmctl.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(work), str(bare)], check=True)
    gitconfig = tmp_path / "gitconfig"
    gitconfig.write_text(
        f'[url "file://{bare}"]\n'
        f"\tinsteadOf = {KMCTL_GIT}\n"
        f"\tinsteadOf = {KMCTL_GIT.removesuffix('.git')}\n"
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(gitconfig))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    monkeypatch.delenv("KMCTL_PINNED")
    monkeypatch.setenv("KMCTL_NO_UPDATE_CHECK", "1")
    root = project(tmp_path)
    write_lock(root, ref=OTHER, commit=commit)

    first = kmctl(root, "--version")
    second = kmctl(root, "briefing")

    assert first.returncode == 0, first.stderr
    assert first.stdout == (
        f"kmctl {version('kmctl')} (pinned by apm.lock.yaml; "
        f"kmctl {version('kmctl')} is on PATH)\n"
    )
    # briefing hands off only offline, so it ran from the cache the first run filled.
    assert second.returncode == 0, second.stderr
    assert "not installed yet" not in second.stdout
    assert f"kmctl briefing (kmctl {version('kmctl')})" in second.stdout


# r8: docs ------------------------------------------------------------------------


def test_docs_say_the_pin_wins() -> None:
    """The install how-to and README say the kmctl on PATH runs each project's pin, and a decision records it."""
    howto = " ".join(
        (ROOT / "docs" / "how-to" / "install-kmctl-with-apm.md").read_text().split()
    )
    readme = " ".join((ROOT / "README.md").read_text().split())
    decisions = list((ROOT / ".okf" / "decisions").glob("*pin*.md"))

    for text in (howto, readme):
        assert "apm.lock.yaml" in text
        assert "pinned" in text
    assert "newer release" in howto
    assert decisions, "no decision about the pin"
    decision = " ".join(decisions[0].read_text().split())
    for words in ("KMCTL_PINNED", "uvx", "mise", "by tag"):
        assert words in decision, words
