"""The release workflows: a hand-run version pull request, then a tag and a GitHub Release (ADR 0012)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.release import APM_DOC, APM_FILES, COPIER, DOC_FILES, MANIFEST

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
RELEASE = WORKFLOWS / "release.yml"
RELEASE_TAG = WORKFLOWS / "release-tag.yml"
CI = WORKFLOWS / "ci.yml"
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


def test_release_bump_stages_copier_yml() -> None:
    """The bump step stages copier.yml, so the version pull request carries kmctl_ref's new default."""
    adds = [
        line.split()[2:]
        for line in _runs(RELEASE, "bump").splitlines()
        if line.strip().startswith("git add")
    ]

    assert COPIER.as_posix() in {path for add in adds for path in add}


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
    written = {MANIFEST, *APM_FILES, *DOC_FILES, APM_DOC, COPIER}
    assert {p.as_posix() for p in written} <= staged
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


def _before_read() -> str:
    """The line of release-tag.yml's plan step that reads the before commit's version."""
    [line] = [
        line.strip()
        for line in _runs(RELEASE_TAG, "tag").splitlines()
        if line.strip().startswith("OLD=")
    ]
    return line


def test_release_tag_reads_the_before_version_from_the_manifest_alone() -> None:
    """The before read uses ``release.py manifest``, not ``current``, which refuses differing copies."""
    line = _before_read()

    assert 'scripts/release.py --repo "$RUNNER_TEMP/before" manifest' in line
    assert " current" not in line


def test_release_tag_reports_lowered_when_the_before_root_apm_yml_differs(
    tmp_path: Path,
) -> None:
    """A before commit at 0.3.0 whose root apm.yml says 0.2.9 still makes 0.2.0 lowered.

    The plan step's before read runs in bash against such a folder, with the
    test's Python in place of ``uv run``, and its OLD goes to ``compare``.
    """
    before = tmp_path / "before"
    (before / MANIFEST).parent.mkdir(parents=True)
    (before / MANIFEST).write_text("name: kmctl\nversion: 0.3.0\n")
    (before / "apm.yml").write_text("name: kmctl\nversion: 0.2.9\n")
    script = _before_read().replace("uv run ", f"{sys.executable} ")

    res = subprocess.run(
        ["bash", "-c", f'set -euo pipefail\n{script}\nprintf %s "$OLD"'],
        cwd=ROOT,
        env={"RUNNER_TEMP": str(tmp_path), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )
    verdict = subprocess.run(
        [sys.executable, "scripts/release.py", "compare", res.stdout, "0.2.0"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert res.returncode == 0, res.stderr
    assert res.stdout == "0.3.0"
    assert verdict.stdout == "lowered\n"


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


def test_ci_starter_job_bootstraps_a_generated_project() -> None:
    """ci.yml's starter job installs uv and just and runs the starter's integration test."""
    steps = _steps(CI, "starter")

    assert any(s.get("uses", "").startswith("astral-sh/setup-uv@") for s in steps)
    assert "uv tool install rust-just==" in _runs(CI, "starter")
    assert steps[-1]["run"] == "uv run pytest tests/test_starter.py -m integration"


def _installs_just_before(path: Path, job: str, pytest_step: int) -> bool:
    """Whether ``job`` in ``path`` installs just with uv in a step before step ``pytest_step``."""
    steps = _steps(path, job)
    return any(
        "uv tool install rust-just==" in s.get("run", "") for s in steps[:pytest_step]
    )


def test_ci_and_release_test_jobs_install_just() -> None:
    """The default tier runs the template's just recipes (tests/test_starter.py), so both test jobs install just first."""
    ci = _steps(CI, "tests")
    [ci_pytest] = [
        i for i, s in enumerate(ci) if "toiminnot/actions/pytest@" in s.get("uses", "")
    ]
    release = _steps(RELEASE, "test")
    [release_pytest] = [
        i for i, s in enumerate(release) if s.get("run") == "uv run pytest"
    ]

    assert _installs_just_before(CI, "tests", ci_pytest)
    assert _installs_just_before(RELEASE, "test", release_pytest)
