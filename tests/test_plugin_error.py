"""What kmctl says when the APM install it runs fails.

A stub ``uvx`` on PATH prints a recorded stderr and exits 1, so these tests
need no network and never run the real APM. The SSH-fallback stderr is what
claude 2.1.300 printed with github.com unresolvable, kept because a git clone
fails the same way under APM: HTTPS fails with git's network line, then SSH
ends on an access-rights line that hides the cause.
"""

import os
import stat
import time
from pathlib import Path

import pytest

from kmctl import plugin
from kmctl.plugin import PluginError

CONFTEST = Path(__file__).parent / "conftest.py"

SSH_FALLBACK = """\
✘ Failed to add marketplace: Fetching the marketplace from GitHub failed on both attempts. HTTPS (https://github.com/scaccogatto/okf-skills.git): Failed to clone marketplace repository: Network error or timeout while cloning repository. Please check your internet connection and try again.

Original error: Cloning into '/tmp/cc/plugins/marketplaces/scaccogatto-okf-skills..clone'...
fatal: unable to access 'https://github.com/scaccogatto/okf-skills.git/': Could not resolve host: github.com

SSH (git@github.com:scaccogatto/okf-skills.git): Failed to clone marketplace repository: SSH authentication failed. Please ensure your SSH keys are configured for GitHub, or use an HTTPS URL instead.

Original error: Cloning into '/tmp/cc/plugins/marketplaces/scaccogatto-okf-skills..clone'...
ssh: Could not resolve hostname github.com: Name or service not known
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
"""


PREFIX = "uvx --from apm-cli==0.33.0 apm install --target claude failed: "
SUFFIX = "; run it by hand to see why, then kmctl plugin install again"


@pytest.fixture
def stub_uvx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Put a ``uvx`` on PATH, alone with the system folders, that prints ``stderr`` and exits 1."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "home" / ".claude"))

    def install(stderr: str) -> None:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        (tmp_path / "stderr.txt").write_text(stderr, encoding="utf-8")
        uvx = bin_dir / "uvx"
        uvx.write_text(f"#!/bin/sh\ncat '{tmp_path / 'stderr.txt'}' >&2\nexit 1\n")
        uvx.chmod(uvx.stat().st_mode | stat.S_IEXEC)
        monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}/usr/bin:/bin")

    return install


def _message(tmp_path: Path) -> str:
    repo = tmp_path / "repo"
    repo.mkdir(exist_ok=True)
    with pytest.raises(PluginError) as caught:
        plugin.install(repo, ["claude"])
    return str(caught.value)


def test_cause_named_on_ssh_fallback(stub_uvx, tmp_path: Path) -> None:
    stub_uvx(SSH_FALLBACK)

    message = _message(tmp_path)

    https = message.index("Could not resolve host: github.com")
    ssh = message.index("fatal: Could not read from remote repository.")
    last = message.index("and the repository exists.")
    assert https < ssh < last, message
    assert message.startswith(PREFIX + "fatal: unable to")
    assert "; fatal: Could not read" in message


def test_cause_keeps_error_lines(stub_uvx, tmp_path: Path) -> None:
    stub_uvx("cloning\nerror: RPC failed; curl 56\nfatal: early EOF\ngave up\n")

    message = _message(tmp_path)

    assert "failed: error: RPC failed; curl 56; fatal: early EOF; gave up; run it" in (
        message
    )


def test_cause_not_doubled_when_last_line_is_fatal(stub_uvx, tmp_path: Path) -> None:
    stub_uvx("cloning\nfatal: repository not found\n")

    message = _message(tmp_path)

    assert message.count("fatal: repository not found") == 1, message


def test_last_line_and_cap_single_line_as_before(stub_uvx, tmp_path: Path) -> None:
    stub_uvx("Plugin not found in marketplace\n")

    assert _message(tmp_path) == PREFIX + "Plugin not found in marketplace" + SUFFIX


def test_last_line_and_cap_no_output(stub_uvx, tmp_path: Path) -> None:
    stub_uvx("")

    assert "failed: no output; run it by hand" in _message(tmp_path)


def test_last_line_and_cap_long_stderr(stub_uvx, tmp_path: Path) -> None:
    stub_uvx("".join(f"fatal: line {n} {'x' * 80}\n" for n in range(20)))

    message = _message(tmp_path)
    cause = message.removeprefix(PREFIX).removesuffix(SUFFIX)

    assert len(cause) <= plugin.CAUSE_CAP, len(cause)
    assert cause.startswith("fatal: line 0 ")
    assert cause.endswith("…")
    assert message.endswith("then kmctl plugin install again")


GENERATED = """
import pytest
from pathlib import Path

COUNT = Path(__file__).parent / "count"


@pytest.mark.integration
def test_flaky():
    runs = int(COUNT.read_text()) + 1 if COUNT.exists() else 1
    COUNT.write_text(str(runs))
    assert runs > 2, {message!r}
"""


def test_ssh_fallback_retried(
    stub_uvx,
    tmp_path: Path,
    pytester: pytest.Pytester,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_uvx(SSH_FALLBACK)
    message = _message(tmp_path)
    pytester.makeconftest(CONFTEST.read_text())
    pytester.makeini(
        "[pytest]\naddopts = --strict-markers\nmarkers =\n    integration: test\n"
    )
    monkeypatch.setattr(time, "sleep", lambda _: None)
    pytester.makepyfile(GENERATED.format(message=message))

    result = pytester.runpytest_inprocess("-p", "no:cacheprovider")

    result.assert_outcomes(passed=1)
    assert (pytester.path / "count").read_text() == "3"
