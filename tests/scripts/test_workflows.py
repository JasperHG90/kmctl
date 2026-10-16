"""The release workflows: a hand-run version pull request, then a tag and a GitHub Release (ADR 0012)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.release import DOC_FILES, MANIFEST

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
RELEASE = WORKFLOWS / "release.yml"
RELEASE_TAG = WORKFLOWS / "release-tag.yml"
# The job in each workflow that may write; every other job reads only.
WRITERS = {RELEASE: {"bump"}, RELEASE_TAG: {"tag"}}


def _load(path: Path) -> dict[Any, Any]:
    """Parse a workflow; PyYAML reads the ``on:`` key as True, so put it back under ``on``."""
    data: dict[Any, Any] = yaml.safe_load(path.read_text())
    data["on"] = data.pop(True)
    return data


def _steps(path: Path, job: str) -> list[dict[str, Any]]:
    """The steps of ``job`` in the workflow at ``path``."""
    steps: list[dict[str, Any]] = _load(path)["jobs"][job]["steps"]
    return steps


def _index(steps: list[dict[str, Any]], needle: str) -> int:
    """The index of the first step whose ``run`` holds ``needle``."""
    for i, step in enumerate(steps):
        if needle in step.get("run", ""):
            return i
    raise AssertionError(f"no step runs {needle!r}")


def _runs(path: Path, job: str) -> str:
    """Every ``run`` script of ``job``, joined."""
    return "\n".join(step.get("run", "") for step in _steps(path, job))


def test_release_starts_by_hand_with_its_inputs() -> None:
    """release.yml runs only on workflow_dispatch, with increment, pre-release, version, dry run."""
    on = _load(RELEASE)["on"]

    assert list(on) == ["workflow_dispatch"]
    inputs = on["workflow_dispatch"]["inputs"]
    assert list(inputs) == ["increment", "prerelease", "version", "dry_run"]
    assert inputs["increment"]["type"] == "choice"
    assert inputs["increment"]["options"] == ["PATCH", "MINOR", "MAJOR", "PRE", "FINAL"]
    assert inputs["increment"]["default"] == "PATCH"
    assert inputs["prerelease"]["options"] == ["none", "a", "b", "rc"]
    assert inputs["prerelease"]["default"] == "none"
    assert inputs["version"]["type"] == "string"
    assert inputs["version"]["required"] is False
    assert inputs["dry_run"]["type"] == "boolean"
    assert inputs["dry_run"]["default"] is True


def test_release_resolves_and_refuses() -> None:
    """The version comes from the script; a real run off main and an existing tag refuse."""
    steps = _steps(RELEASE, "resolve")
    runs = _runs(RELEASE, "resolve")

    assert "uv run scripts/next_release_version.py" in runs
    off_main = [
        s
        for s in steps
        if "!inputs.dry_run" in s.get("if", "")
        and "github.ref != 'refs/heads/main'" in s.get("if", "")
    ]
    assert len(off_main) == 1
    assert "exit 1" in off_main[0]["run"]
    tag = steps[
        _index(steps, 'git ls-remote --exit-code --tags origin "refs/tags/v$VERSION"')
    ]
    assert "already exists" in tag["run"]
    assert "exit 1" in tag["run"]


def test_release_runs_the_lint_and_the_tests() -> None:
    """The lint and test commands run as their own steps, since the version PR starts no workflow."""
    runs = [s.get("run", "").strip() for s in _steps(RELEASE, "test")]

    assert "uv run ruff check" in runs
    assert "uv run ruff format --check" in runs
    assert "uv run pytest" in runs


def test_release_builds_and_checks_at_the_release_version() -> None:
    """The build job sets the version, builds, runs twine check and the two wheel scripts."""
    steps = _steps(RELEASE, "build")

    order = [
        _index(steps, 'uv run scripts/release.py set "$VERSION"'),
        _index(steps, "uv build"),
        _index(steps, "uvx twine check dist/*"),
        _index(steps, "uv run scripts/check_wheel.py dist/*.whl"),
        _index(steps, 'uv run scripts/smoke_wheel.py dist/*.whl --version "$VERSION"'),
    ]
    assert order == sorted(order)
    assert '*-"$VERSION"-*.whl | *-"$VERSION".tar.gz' in _runs(RELEASE, "build")


def test_release_bump_opens_the_version_pull_request() -> None:
    """A real run commits ``release.py set`` on release/vX.Y.Z, staging every file it wrote."""
    job = _load(RELEASE)["jobs"]["bump"]
    runs = _runs(RELEASE, "bump")

    assert job["if"] == "${{ !inputs.dry_run }}"
    assert set(job["needs"]) == {"resolve", "test", "build"}
    assert 'BRANCH="release/v$VERSION"' in runs
    assert 'uv run scripts/release.py set "$VERSION"' in runs
    adds = [
        line.split()[2:]
        for line in runs.splitlines()
        if line.strip().startswith("git add")
    ]
    staged = {path for add in adds for path in add}
    assert {MANIFEST.as_posix(), *(p.as_posix() for p in DOC_FILES)} <= staged
    assert "gh pr create --base main" in runs
    assert "Allow GitHub Actions to create and approve pull requests" in runs
    assert 'git push origin --delete "$BRANCH"' in runs


def test_release_tag_runs_on_a_manifest_change_on_main() -> None:
    """release-tag.yml runs on a push to main touching apm/apm.yml, the version source, and nothing else."""
    on = _load(RELEASE_TAG)["on"]

    assert on == {"push": {"branches": ["main"], "paths": [MANIFEST.as_posix()]}}


def test_release_tag_builds_before_it_tags_and_publishes_the_release() -> None:
    """Build and check, then the annotated tag, then a Release with wheel, sdist and SHA256SUMS."""
    steps = _steps(RELEASE_TAG, "tag")
    runs = _runs(RELEASE_TAG, "tag")

    order = [
        _index(steps, "uv run scripts/release.py compare"),
        _index(steps, "uv build"),
        _index(steps, 'git tag -a "v$VERSION"'),
        _index(steps, 'gh release create "v$VERSION"'),
    ]
    assert order == sorted(order)
    build = steps[order[1]]["run"]
    for needle in (
        "uvx twine check dist/*",
        "uv run scripts/check_wheel.py dist/*.whl",
        'uv run scripts/smoke_wheel.py dist/*.whl --version "$VERSION"',
        "sha256sum ./* > SHA256SUMS",
    ):
        assert needle in build
    assert "dist/*" in steps[order[3]]["run"]
    assert "uv run scripts/release.py is-prerelease" in runs
    assert "--prerelease" in runs
    assert "--notes-start-tag" in runs


@pytest.mark.parametrize("path", [RELEASE, RELEASE_TAG], ids=lambda p: p.name)
def test_no_workflow_publishes_to_pypi(path: Path) -> None:
    """GitHub Releases only: no upload to PyPI and no publish action."""
    text = path.read_text().lower()

    for needle in (
        "twine upload",
        "uv publish",
        "pypa/gh-action-pypi-publish",
        "pypi.org",
    ):
        assert needle not in text
    assert "id-token" not in text


@pytest.mark.parametrize("path", [RELEASE, RELEASE_TAG], ids=lambda p: p.name)
def test_every_action_is_pinned_by_commit_sha(path: Path) -> None:
    """Each ``uses:`` names a 40-character commit SHA with its version as a comment."""
    lines = [line for line in path.read_text().splitlines() if "uses:" in line]

    assert lines
    for line in lines:
        assert re.search(
            r"uses: [\w.-]+/[\w./-]+@[0-9a-f]{40} # v\d+\.\d+\.\d+$", line
        ), line


@pytest.mark.parametrize("path", [RELEASE, RELEASE_TAG], ids=lambda p: p.name)
def test_only_the_writing_job_asks_for_write(path: Path) -> None:
    """The top level reads only; write permissions sit on the one job that writes."""
    data = _load(path)

    assert data["permissions"] == {"contents": "read"}
    writers = {
        name
        for name, job in data["jobs"].items()
        if "write" in (job.get("permissions") or {}).values()
    }
    assert writers == WRITERS[path]
