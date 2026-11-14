"""``scripts/next_release_version.py``: the next version from the newest ``v*`` tag (ADR 0012)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.next_release_version import Refused, newest_tag, next_version

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "next_release_version.py"
GIT = ["git", "-c", "user.email=o@e.com", "-c", "user.name=O"]


def _repo(tmp_path: Path, *tags: str) -> Path:
    """A real git repository with one commit carrying ``tags``."""
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(
        [*GIT, "commit", "-q", "--allow-empty", "-m", "i"], cwd=repo, check=True
    )
    for tag in tags:
        subprocess.run(["git", "tag", tag], cwd=repo, check=True)
    return repo


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the script against ``repo``."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--repo", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("newest", "args", "expected"),
    [
        ("v0.2.0", ("PATCH",), "0.2.1"),
        ("v0.2.0", ("MINOR",), "0.3.0"),
        ("v0.2.0", ("MAJOR",), "1.0.0"),
        ("v0.2.0", ("MINOR", "--pre", "a"), "0.3.0a1"),
        ("v0.2.0", ("PATCH", "--pre", "rc"), "0.2.1rc1"),
        ("v0.3.0a1", ("PRE",), "0.3.0a2"),
        ("v0.3.0a2", ("PRE", "--pre", "b"), "0.3.0b1"),
        ("v0.3.0b3", ("PRE", "--pre", "rc"), "0.3.0rc1"),
        ("v0.3.0rc2", ("FINAL",), "0.3.0"),
        ("v0.3.0rc2", ("PATCH",), "0.3.1"),
        ("v0.2.0", ("PATCH", "--version", "0.4.0"), "0.4.0"),
    ],
)
def test_each_increment_in_a_real_repository(
    tmp_path: Path, newest: str, args: tuple[str, ...], expected: str
) -> None:
    """Run as a script, each increment raises the newest tag and prints it without ``v``."""
    repo = _repo(tmp_path, "v0.1.0", newest, "not-a-version")

    res = _run(repo, *args)

    assert res.returncode == 0, res.stderr
    assert res.stdout == f"{expected}\n"


def test_a_first_release_needs_a_version(tmp_path: Path) -> None:
    """With no ``v*`` tag, the script exits 1 naming ``--version`` and prints no version."""
    repo = _repo(tmp_path, "release-1")

    res = _run(repo, "PATCH")

    assert res.returncode == 1
    assert res.stdout == ""
    assert "--version" in res.stderr


def test_a_first_release_with_a_version(tmp_path: Path) -> None:
    """With no ``v*`` tag, ``--version`` is taken as typed."""
    res = _run(_repo(tmp_path), "PATCH", "--version", "0.2.0")

    assert res.returncode == 0, res.stderr
    assert res.stdout == "0.2.0\n"


@pytest.mark.parametrize(
    ("newest", "increment", "pre", "needle"),
    [
        (None, "PATCH", None, r"no v\* tag"),
        ("0.2.0", "PRE", None, "not a pre-release"),
        ("0.2.0", "FINAL", None, "not a pre-release"),
        ("0.3.0rc1", "PRE", "a", "goes backwards"),
        ("0.2.0", "SIDEWAYS", None, "increment"),
        ("0.2.0", "PATCH", "dev", "pre-release label"),
    ],
)
def test_next_version_refuses(
    newest: str | None, increment: str, pre: str | None, needle: str
) -> None:
    """A first release without a version, or an increment that cannot apply, refuses."""
    with pytest.raises(Refused, match=needle):
        next_version(newest, increment, pre)


@pytest.mark.parametrize(
    ("newest", "explicit", "needle"),
    [
        ("0.2.0", "0.2.0", "not above"),
        (None, "banana", "not a version"),
        (None, "v0.2.0-rc1", r"type it as 0\.2\.0rc1"),
        (None, "0.2", "X.Y.Z"),
    ],
)
def test_an_explicit_version_is_checked(
    newest: str | None, explicit: str, needle: str
) -> None:
    """The override must be a canonical X.Y.Z version above the newest release."""
    with pytest.raises(Refused, match=needle):
        next_version(newest, "PATCH", None, explicit=explicit)


def test_newest_tag_ignores_other_tags() -> None:
    """Only ``v<version>`` tags, pre-releases included, count; the highest wins."""
    tags = ["v0.1.0", "v0.2.0a1", "v0.2.0", "okf--v9.9.9", "vnext", "v0.2.1rc1"]

    assert newest_tag(tags) == "0.2.1rc1"
    assert newest_tag(["release-1", "other"]) is None


def test_package_aware_newest_tag_reads_one_family() -> None:
    """kmctl counts only ``v*`` tags and kmaudit only ``kmaudit-v*`` tags."""
    tags = ["v0.5.0", "kmaudit-v0.1.0", "kmaudit-v0.2.0rc1", "kmaudit-vnext"]

    assert newest_tag(tags) == "0.5.0"
    assert newest_tag(tags, prefix="v") == "0.5.0"
    assert newest_tag(tags, prefix="kmaudit-v") == "0.2.0rc1"
    assert newest_tag(["v0.5.0"], prefix="kmaudit-v") is None


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (("PATCH",), "0.5.1"),
        (("PATCH", "--package", "kmctl"), "0.5.1"),
        (("PATCH", "--package", "kmaudit"), "0.1.1"),
        (("MINOR", "--package", "kmaudit"), "0.2.0"),
    ],
)
def test_package_aware_increment_raises_the_family_s_tag(
    tmp_path: Path, args: tuple[str, ...], expected: str
) -> None:
    """Each package raises its own family's newest tag, never the other's."""
    repo = _repo(tmp_path, "v0.5.0", "kmaudit-v0.1.0")

    res = _run(repo, *args)

    assert res.returncode == 0, res.stderr
    assert res.stdout == f"{expected}\n"


def test_package_aware_first_kmaudit_release_needs_a_version(tmp_path: Path) -> None:
    """With only ``v*`` tags, kmaudit has no release yet and asks for ``--version``."""
    repo = _repo(tmp_path, "v0.5.0")

    refused = _run(repo, "PATCH", "--package", "kmaudit")
    given = _run(repo, "PATCH", "--package", "kmaudit", "--version", "0.1.0")

    assert refused.returncode == 1
    assert "kmaudit-v*" in refused.stderr
    assert "--version" in refused.stderr
    assert given.stdout == "0.1.0\n"


def test_package_aware_kmaudit_version_is_checked_against_its_own_family(
    tmp_path: Path,
) -> None:
    """An override below kmctl's newest tag is fine for kmaudit, and refused at or below kmaudit's."""
    repo = _repo(tmp_path, "v0.5.0", "kmaudit-v0.2.0")

    ok = _run(repo, "PATCH", "--package", "kmaudit", "--version", "0.3.0")
    low = _run(repo, "PATCH", "--package", "kmaudit", "--version", "0.2.0")

    assert ok.stdout == "0.3.0\n"
    assert low.returncode == 1
    assert "not above" in low.stderr
