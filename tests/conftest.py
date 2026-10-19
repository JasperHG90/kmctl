import os
import re
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from importlib.metadata import version
from pathlib import Path

import pytest
from _pytest.runner import runtestprotocol

pytest_plugins = ("pytester",)

VALIDATOR = Path(__file__).parent / "vendor" / "okf" / "okf_validate.py"
ROOT = Path(__file__).resolve().parents[1]
GITHTTP = Path(__file__).parent / "fixtures" / "githttp.py"

# git's wording for a network failure, as kmctl passes on claude's fatal: and error: lines.
NETWORK_ERRORS = (
    "Could not resolve host",
    "Failed to connect",
    "Connection refused",
    "Connection timed out",
    "Operation timed out",
    "Temporary failure in name resolution",
)
RUNS = 3
RETRY_DELAY_SECONDS = 5


# typer forces a colour terminal on GitHub Actions, so help carries ANSI codes.
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def plain(text: str) -> str:
    """``text`` without ANSI colour codes: what a reader sees."""
    return ANSI.sub("", text)


def okf_validate(bundle: Path) -> subprocess.CompletedProcess[str]:
    """Run the pinned okf validator in strict mode on ``bundle``."""
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(bundle), "--strict"],
        capture_output=True,
        text=True,
        check=False,
    )


def _network_failure(reports: list[pytest.TestReport]) -> bool:
    return any(
        r.failed and any(e in r.longreprtext for e in NETWORK_ERRORS) for r in reports
    )


def pytest_runtest_protocol(
    item: pytest.Item, nextitem: pytest.Item | None
) -> bool | None:
    """Run an integration test up to RUNS times while it fails on a network error.

    Only the last run's reports reach the terminal, so a test that passes on a
    later run is reported as passed, and one that fails RUNS times as failed.
    """
    if item.get_closest_marker("integration") is None:
        return None
    item.ihook.pytest_runtest_logstart(nodeid=item.nodeid, location=item.location)
    for run in range(1, RUNS + 1):
        reports = runtestprotocol(item, nextitem=nextitem, log=False)
        if run == RUNS or not _network_failure(reports):
            break
        time.sleep(RETRY_DELAY_SECONDS)
    for report in reports:
        item.ihook.pytest_runtest_logreport(report=report)
    item.ihook.pytest_runtest_logfinish(nodeid=item.nodeid, location=item.location)
    return True


# A real install: this tree on a local git server, and a scratch consumer ----


def _free_port() -> int:
    """A TCP port on 127.0.0.1 that nothing listens on now."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _git(*args: str, cwd: Path) -> None:
    """Run git in ``cwd``, failing the test with its stderr."""
    res = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    assert res.returncode == 0, res.stderr


def tree_repo(dest: Path) -> Path:
    """Copy this tree's files (not git-ignored ones) into a new git repository at ``dest``, tagged v<version>."""
    dest.mkdir(parents=True, exist_ok=True)
    files = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.split(b"\0")
    for name in filter(None, files):
        src = ROOT / os.fsdecode(name)
        if src.is_file():
            (dest / os.fsdecode(name)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / os.fsdecode(name))
    _git("init", "-q", "-b", "main", cwd=dest)
    # No background gc: it repacks objects while a test clones the repository.
    _git("config", "gc.auto", "0", cwd=dest)
    _git("add", "-A", cwd=dest)
    _git(
        *("-c", "user.email=t@e.invalid", "-c", "user.name=t"),
        *("commit", "-qm", "tree"),
        cwd=dest,
    )
    _git("tag", f"v{version('kmctl')}", cwd=dest)
    return dest


@pytest.fixture
def served(tmp_path: Path) -> Iterator[str]:
    """This tree's files (not git-ignored ones) served as kmctl.git, tagged v<version>; yields its URL."""
    work = tree_repo(tmp_path / "kmctl")
    # APM wants an owner/repo path, as on GitHub.
    srv = tmp_path / "srv"
    bare = srv / "o" / "kmctl.git"
    bare.parent.mkdir(parents=True)
    _git("clone", "-q", "--bare", str(work), str(bare), cwd=tmp_path)
    _git("update-server-info", cwd=bare)
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-I", str(GITHTTP), str(srv), str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        yield f"http://127.0.0.1:{port}/o/kmctl.git"
    finally:
        proc.terminate()
        proc.wait()


@pytest.fixture(autouse=True, scope="session")
def _uv_cache(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """Give the run its own uv cache, and delete it when the run ends.

    Every uvx or uv run a test starts builds an environment that uv keeps in
    its cache for good: APM's alone is about 60 packages, so the shared cache
    grew by hundreds of gigabytes over many runs. Downloads now repeat once
    per run instead.
    """
    cache = tmp_path_factory.mktemp("uv-cache")
    saved = os.environ.get("UV_CACHE_DIR")
    os.environ["UV_CACHE_DIR"] = str(cache)
    yield
    if saved is None:
        os.environ.pop("UV_CACHE_DIR", None)
    else:
        os.environ["UV_CACHE_DIR"] = saved
    shutil.rmtree(cache, ignore_errors=True)


@pytest.fixture(autouse=True)
def _pinned(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run every kmctl as itself: no hand-off to a lock's pin, no update check.

    Fixture locks pin other releases, and a hand-off would fetch them from
    GitHub. Tests of the hand-off unset KMCTL_PINNED themselves.
    """
    monkeypatch.setenv("KMCTL_PINNED", "1")


@pytest.fixture
def consumer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch git repository as the working folder, with scratch HOME and Claude config.

    PATH holds uv, uvx and the system folders only, so the real claude CLI is
    never run.
    """
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    tools = tmp_path / "tools"
    tools.mkdir()
    for tool in ("uv", "uvx"):
        found = shutil.which(tool)
        assert found, f"{tool} must be on PATH"
        (tools / tool).symlink_to(found)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / ".claude"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    monkeypatch.setenv("PATH", f"{tools}:/usr/bin:/bin")
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    repo = tmp_path / "consumer"
    repo.mkdir()
    _git("init", "-q", cwd=repo)
    monkeypatch.chdir(repo)
    return repo


def apm_install(consumer: Path, served: str, targets: str) -> str:
    """Install kmctl's package as a user does (ADR 0021): the apm.yml entry, apm install, kmctl plugin patch.

    The entry names ``served`` at this kmctl's tag; APM 0.33.0 runs through
    uvx. Returns kmctl plugin patch's output; fails the test when a step fails.
    """
    import yaml
    from typer.testing import CliRunner

    from kmctl import app

    entry = {
        "git": served,
        "path": "apm",
        "ref": f"v{version('kmctl')}",
        "allow_insecure": True,
    }
    manifest = {
        "name": "consumer",
        "version": "0.1.0",
        "dependencies": {"apm": [entry]},
        "targets": targets.split(","),
    }
    (consumer / "apm.yml").write_text(yaml.safe_dump(manifest))
    proc = subprocess.run(
        ["uvx", "--from", "apm-cli==0.33.0", "apm", "install", "--allow-insecure"],
        cwd=consumer,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    result = CliRunner().invoke(app, ["plugin", "patch"])
    assert result.exit_code == 0, result.output
    return result.stdout
