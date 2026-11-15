"""The release workflows: a hand-run version pull request, then a tag and a GitHub Release (ADR 0012)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.release import (
    APM_DOC,
    APM_FILES,
    COPIER,
    DOC_FILES,
    HOOKS,
    KMAUDIT_README,
    KMAUDIT_VERSION,
    MANIFEST,
)

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
RELEASE = WORKFLOWS / "release.yml"
RELEASE_TAG = WORKFLOWS / "release-tag.yml"
KNOWLEDGE_AUDIT = WORKFLOWS / "knowledge-audit.yml"
ACTION = ROOT / "action.yml"
CI = WORKFLOWS / "ci.yml"
HERMES_INTERACTIVE = WORKFLOWS / "hermes-interactive.yaml"
HERMES_TRIAGE = WORKFLOWS / "hermes-issue-triage.yaml"
PROMPTS = ROOT / ".github" / "prompts"
MEMBERS = 'contains(fromJSON(\'["MEMBER","OWNER","COLLABORATOR"]\'), github.event.comment.author_association)'
# The job in each workflow that may write; every other job reads only.
WRITERS = {RELEASE: {"bump"}, RELEASE_TAG: {"tag"}}
# Each package builds from packages/<package> (ADR 0044); --package picks its pyproject.
CHECK_WHEEL = 'uv run scripts/check_wheel.py --package "$PACKAGE" dist/*.whl'
SMOKE_WHEEL = (
    'uv run scripts/smoke_wheel.py --package "$PACKAGE" dist/*.whl --version "$VERSION"'
)


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
    """release.yml runs only on workflow_dispatch, with package, increment, pre-release, version, dry run."""
    on = _load(RELEASE)["on"]

    assert list(on) == ["workflow_dispatch"]
    inputs = on["workflow_dispatch"]["inputs"]
    assert list(inputs) == ["package", "increment", "prerelease", "version", "dry_run"]
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
        _index(steps, 'git ls-remote --exit-code --tags origin "refs/tags/$TAG"')
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
        _index(steps, 'uv run scripts/release.py --package "$PACKAGE" set "$VERSION"'),
        _index(steps, 'uv build --package "$PACKAGE" -o dist'),
        _index(steps, "uvx twine check dist/*"),
        _index(steps, CHECK_WHEEL),
        _index(steps, SMOKE_WHEEL),
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
    """A real run commits ``release.py set`` on release/TAG, staging every file it wrote."""
    job = _load(RELEASE)["jobs"]["bump"]
    runs = _runs(RELEASE, "bump")

    assert job["if"] == "${{ !inputs.dry_run }}"
    assert set(job["needs"]) == {"resolve", "test", "build", "notes"}
    assert 'BRANCH="release/$TAG"' in runs
    assert 'uv run scripts/release.py --package "$PACKAGE" set "$VERSION"' in runs
    adds = [
        line.split()[2:]
        for line in runs.splitlines()
        if line.strip().startswith("git add")
    ]
    staged = {path for add in adds for path in add}
    written = {
        MANIFEST,
        *APM_FILES,
        *DOC_FILES,
        APM_DOC,
        COPIER,
        HOOKS,
        KMAUDIT_VERSION,
        KMAUDIT_README,
    }
    assert {p.as_posix() for p in written} <= staged
    assert "gh pr create --base main" in runs
    assert "Allow GitHub Actions to create and approve pull requests" in runs
    assert 'git push origin --delete "$BRANCH"' in runs


def test_release_tag_runs_on_a_version_source_change_on_main() -> None:
    """release-tag.yml runs on a push to main touching either package's version source, and nothing else."""
    on = _load(RELEASE_TAG)["on"]

    assert on == {
        "push": {
            "branches": ["main"],
            "paths": [MANIFEST.as_posix(), KMAUDIT_VERSION.as_posix()],
        }
    }


def test_release_tag_builds_before_it_tags_and_publishes_the_release() -> None:
    """Build and check, then the annotated tag, then a Release with wheel, sdist and SHA256SUMS."""
    steps = _steps(RELEASE_TAG, "tag")
    runs = _runs(RELEASE_TAG, "tag")

    order = [
        _index(steps, "uv run scripts/release.py compare"),
        _index(steps, 'uv build --package "$PACKAGE" -o dist'),
        _index(steps, 'git tag -a "$TAG"'),
        _index(steps, 'gh release create "$TAG"'),
    ]
    assert order == sorted(order)
    build = steps[order[1]]["run"]
    for needle in (
        "uvx twine check dist/*",
        CHECK_WHEEL,
        SMOKE_WHEEL,
        "sha256sum ./* > SHA256SUMS",
    ):
        assert needle in build
    assert "dist/*" in steps[order[3]]["run"]
    assert "uv run scripts/release.py is-prerelease" in runs
    assert "--prerelease" in runs


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
    assert '--package "$PACKAGE"' in line
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
        env={"RUNNER_TEMP": str(tmp_path), "PACKAGE": "kmctl", "PATH": "/usr/bin:/bin"},
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


@pytest.mark.parametrize(
    "path",
    [RELEASE, RELEASE_TAG, KNOWLEDGE_AUDIT, ACTION, HERMES_INTERACTIVE, HERMES_TRIAGE],
    ids=lambda p: p.name,
)
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
    assert (
        steps[-1]["run"]
        == "uv run pytest packages/kmctl/tests/test_starter.py -m integration"
    )
    assert (ROOT / "packages" / "kmctl" / "tests" / "test_starter.py").is_file()


def _installs_just_before(path: Path, job: str, pytest_step: int) -> bool:
    """Whether ``job`` in ``path`` installs just with uv in a step before step ``pytest_step``."""
    steps = _steps(path, job)
    return any(
        "uv tool install rust-just==" in s.get("run", "") for s in steps[:pytest_step]
    )


def test_ci_kmctl_and_release_test_jobs_install_just() -> None:
    """The default tier runs the template's just recipes (packages/kmctl/tests/test_starter.py), so kmctl's CI job and the release test job install just first."""
    ci = _steps(CI, "kmctl")
    [ci_pytest] = [
        i for i, s in enumerate(ci) if "toiminnot/actions/pytest@" in s.get("uses", "")
    ]
    release = _steps(RELEASE, "test")
    [release_pytest] = [
        i for i, s in enumerate(release) if s.get("run") == "uv run pytest"
    ]

    assert _installs_just_before(CI, "kmctl", ci_pytest)
    assert _installs_just_before(RELEASE, "test", release_pytest)


def _setup_uv_steps(path: Path) -> list[dict[str, Any]]:
    """Every astral-sh/setup-uv step in the workflow at ``path``, across its jobs."""
    jobs = yaml.safe_load(path.read_text())["jobs"]
    return [
        step
        for job in jobs.values()
        for step in job.get("steps", [])
        if step.get("uses", "").startswith("astral-sh/setup-uv@")
    ]


@pytest.mark.parametrize("path", [RELEASE, RELEASE_TAG], ids=["release", "release-tag"])
def test_release_workflows_never_restore_the_uv_cache(path: Path) -> None:
    """A cache entry the audit agent could write on main must never reach a release build (ADR 0017)."""
    steps = _setup_uv_steps(path)

    assert steps
    assert all(s.get("with", {}).get("enable-cache") is False for s in steps), steps


def test_release_workflows_cache_record_names_the_reason() -> None:
    """ADR 0017 carries a dated Correction saying the release workflows run without the uv cache."""
    [adr] = (ROOT / ".okf" / "decisions").glob("0017-*.md")
    text = " ".join(adr.read_text().split())
    corrections = text.split("## Correction, ")[1:]

    assert any(
        "release.yml" in c and "release-tag.yml" in c and "cache" in c
        for c in corrections
    )


def test_hermes_trigger_is_slash_hermes_from_a_member() -> None:
    """Hermes answers a member's /hermes comment; @hermes would mention another account."""
    job = _load(HERMES_INTERACTIVE)["jobs"]["respond"]
    hermes = next(s for s in job["steps"] if "hermes-interactive" in s.get("uses", ""))

    assert hermes["with"]["trigger_phrase"] == "/hermes"
    assert "contains(github.event.comment.body, '/hermes')" in job["if"]
    assert MEMBERS in job["if"]


def test_hermes_trigger_for_triage_is_an_opened_issue_or_a_member_s_slash_triage() -> (
    None
):
    """Triage runs on a new issue, by hand, or on a member's /triage comment."""
    data = _load(HERMES_TRIAGE)
    condition = data["jobs"]["triage"]["if"]

    assert set(data["on"]) == {"issues", "issue_comment", "workflow_dispatch"}
    assert data["on"]["issues"]["types"] == ["opened"]
    assert "startsWith(github.event.comment.body, '/triage')" in condition
    assert MEMBERS in condition


@pytest.mark.parametrize(
    "path",
    [
        HERMES_INTERACTIVE,
        HERMES_TRIAGE,
        PROMPTS / "interactive-system.md",
        PROMPTS / "issue-triage-system.md",
    ],
    ids=lambda p: p.name,
)
def test_hermes_trigger_never_says_at_hermes(path: Path) -> None:
    """No workflow or prompt says @hermes."""
    assert "@hermes" not in path.read_text().lower()


def test_hermes_trusted_prompt_and_skills_come_from_the_default_branch() -> None:
    """A pull request cannot rewrite the instructions of the agent that holds the key."""
    steps = _steps(HERMES_INTERACTIVE, "respond")
    trusted = next(
        s for s in steps if s.get("with", {}).get("path") == ".hermes-trusted"
    )
    hermes = next(s for s in steps if "hermes-interactive" in s.get("uses", ""))

    assert trusted["with"]["ref"] == "${{ github.event.repository.default_branch }}"
    assert hermes["with"]["system_prompt_file"].startswith(".hermes-trusted/")
    assert hermes["with"]["skills_dir"].startswith(".hermes-trusted/")


@pytest.mark.parametrize(
    "path", [HERMES_INTERACTIVE, HERMES_TRIAGE], ids=lambda p: p.name
)
def test_hermes_step_outputs_never_expand_into_a_shell_line(path: Path) -> None:
    """A step output reaches a script through env, so no run: line is built from one."""
    for job in _load(path)["jobs"]:
        assert "${{ steps." not in _runs(path, job)


def test_hermes_step_outputs_apply_triage_reads_a_quoted_response_file() -> None:
    """Apply triage takes the response file from RESPONSE_FILE, quoted."""
    step = next(
        s for s in _steps(HERMES_TRIAGE, "triage") if s.get("name") == "Apply triage"
    )

    assert step["env"]["RESPONSE_FILE"] == "${{ steps.hermes.outputs.response_file }}"
    assert '"$RESPONSE_FILE"' in step["run"]


# The release flow per package (ADR 0012): release.yml takes a package, drafts
# its notes and commits them in the version pull request; release-tag.yml
# publishes that file for whichever package's version rose.

GIT = ["git", "-c", "user.email=o@e.com", "-c", "user.name=O"]


def _step(path: Path, job: str, name: str) -> dict[str, Any]:
    """The step of ``job`` named ``name``."""
    [step] = [s for s in _steps(path, job) if s.get("name") == name]
    return step


def _stub_bin(tmp_path: Path, gh: str = "") -> Path:
    """A folder with a ``uv`` that runs ``uv run scripts/X`` as this repo's script, and a ``gh``.

    ``gh`` records each argument on its own line in ``$RUNNER_TEMP/gh-args``,
    and copies ``--notes-file`` or ``--body-file`` to ``$RUNNER_TEMP/gh-file``.
    """
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    (bin_ / "uv").write_text(
        f'#!/bin/sh\nshift\nf="$1"; shift\nexec {sys.executable} "{ROOT}/$f" "$@"\n'
    )
    (bin_ / "gh").write_text(
        "#!/bin/bash\n"
        'printf "%s\\n" "$@" > "$RUNNER_TEMP/gh-args"\n'
        "prev=''\n"
        'for a in "$@"; do\n'
        '  case "$prev" in --notes-file|--body-file) cp "$a" "$RUNNER_TEMP/gh-file" ;; esac\n'
        '  prev="$a"\n'
        "done\n" + gh
    )
    for f in bin_.iterdir():
        f.chmod(0o755)
    return bin_


def _bash(
    script: str, cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Run a workflow step's script in bash, as GitHub's ``shell: bash`` does."""
    return subprocess.run(
        ["bash", "-e", "-c", script],
        cwd=cwd,
        env={"PATH": "/usr/bin:/bin", "HOME": str(cwd), **env},
        capture_output=True,
        text=True,
        check=False,
    )


def _git_out(repo: Path, *args: str) -> str:
    return subprocess.run(
        [*GIT, "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _change(repo: Path, subject: str, *paths: str) -> str:
    """Commit ``subject`` with a new line in each of ``paths``; return the commit."""
    for rel in paths:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as fh:
            fh.write(f"{subject}\n")
        _git_out(repo, "add", rel)
    _git_out(repo, "commit", "-q", "-m", subject)
    return _git_out(repo, "rev-parse", "HEAD")


def test_release_package_input_picks_kmctl_or_kmaudit() -> None:
    """The first input is package, a choice of kmctl or kmaudit, kmctl by default."""
    inputs = _load(RELEASE)["on"]["workflow_dispatch"]["inputs"]

    assert next(iter(inputs)) == "package"
    assert inputs["package"]["type"] == "choice"
    assert inputs["package"]["options"] == ["kmctl", "kmaudit"]
    assert inputs["package"]["default"] == "kmctl"


def test_release_package_steps_read_the_input() -> None:
    """Every release.yml step that uses $PACKAGE gets it from the package input."""
    for job in ("resolve", "build", "notes", "bump"):
        for step in _steps(RELEASE, job):
            if "$PACKAGE" in step.get("run", ""):
                assert step["env"]["PACKAGE"] == "${{ inputs.package }}", step["name"]


def test_release_package_resolve_works_out_the_family_s_version_and_tag(
    tmp_path: Path,
) -> None:
    """Run in bash, resolve raises kmaudit's own newest tag and names a kmaudit-v tag."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_out(repo, "init", "-q", "-b", "main")
    _change(repo, "start", "README.md")
    for tag in ("v0.5.0", "kmaudit-v0.1.0"):
        _git_out(repo, "tag", tag)
    steps = _steps(RELEASE, "resolve")
    work = _step(RELEASE, "resolve", "Work out the version")
    out = tmp_path / "output"

    res = _bash(
        work["run"],
        repo,
        {
            "PATH": f"{_stub_bin(tmp_path)}:/usr/bin:/bin",
            "PACKAGE": "kmaudit",
            "INCREMENT": "MINOR",
            "PRE": "none",
            "OVERRIDE": "",
            "GITHUB_OUTPUT": str(out),
        },
    )

    assert res.returncode == 0, res.stderr
    assert out.read_text().splitlines() == ["version=0.2.0", "tag=kmaudit-v0.2.0"]
    check = steps[
        _index(steps, 'git ls-remote --exit-code --tags origin "refs/tags/$TAG"')
    ]
    assert check["env"]["TAG"] == "${{ steps.next.outputs.tag }}"
    assert _load(RELEASE)["jobs"]["resolve"]["outputs"]["tag"] == (
        "${{ steps.next.outputs.tag }}"
    )


def test_release_package_build_builds_and_checks_the_chosen_package() -> None:
    """build sets the package's version, runs uv build --package and both wheel checks for it."""
    runs = _runs(RELEASE, "build")

    assert 'uv build --package "$PACKAGE" -o dist' in runs
    assert "uv build --package kmctl" not in runs
    assert CHECK_WHEEL in runs
    assert SMOKE_WHEEL in runs


def test_release_package_notes_job_drafts_in_dry_runs_and_uploads_the_file() -> None:
    """The notes job has no dry-run condition, drafts the file in a step of its own, shows it and uploads it."""
    job = _load(RELEASE)["jobs"]["notes"]
    steps = job["steps"]
    draft = _step(RELEASE, "notes", "Draft the notes")
    upload = [
        s for s in steps if s.get("uses", "").startswith("actions/upload-artifact@")
    ]

    assert "if" not in job
    assert job["needs"] == "resolve"
    assert job["outputs"]["sha"] == "${{ steps.draft.outputs.sha }}"
    assert draft["id"] == "draft"
    assert (
        'uv run scripts/release_notes.py --package "$PACKAGE" "$TAG" --ref HEAD'
        ' --out "$RUNNER_TEMP/release-notes/$TAG.md"' in draft["run"]
    )
    assert 'echo "sha=$(git rev-parse HEAD)" >> "$GITHUB_OUTPUT"' in draft["run"]
    assert "GITHUB_STEP_SUMMARY" not in draft["run"]
    assert draft["env"]["TAG"] == "${{ needs.resolve.outputs.tag }}"
    show = steps.index(_step(RELEASE, "notes", "Show the notes"))
    assert 'cat "$DIR/$TAG.md"' in steps[show]["run"]
    assert '>> "$GITHUB_STEP_SUMMARY"' in steps[show]["run"]
    assert len(upload) == 1
    assert steps.index(draft) < show < steps.index(upload[0])
    assert upload[0]["with"]["name"] == "release-notes"
    assert upload[0]["with"]["path"] == "${{ runner.temp }}/release-notes/"
    # It reads the whole history, so the family's previous tag is there.
    assert steps[0]["with"]["fetch-depth"] == 0


def test_release_package_bump_starts_from_the_drafted_commit_with_the_notes() -> None:
    """bump checks out the notes job's commit and downloads the notes before it commits."""
    job = _load(RELEASE)["jobs"]["bump"]
    steps = job["steps"]
    [checkout] = [s for s in steps if s.get("uses", "").startswith("actions/checkout@")]
    [download] = [
        s for s in steps if s.get("uses", "").startswith("actions/download-artifact@")
    ]
    commit = _step(
        RELEASE, "bump", "Commit the version and the notes, and open the pull request"
    )

    assert "notes" in job["needs"]
    assert checkout["with"]["ref"] == "${{ needs.notes.outputs.sha }}"
    assert download["with"] == {
        "name": "release-notes",
        "path": "${{ runner.temp }}/release-notes",
    }
    assert steps.index(checkout) < steps.index(download) < steps.index(commit)
    assert commit["env"]["DRAFTED"] == "${{ needs.notes.outputs.sha }}"
    assert commit["env"]["TAG"] == "${{ needs.resolve.outputs.tag }}"


def _run_bump(
    tmp_path: Path, notes: str, before: str | None = None
) -> tuple[subprocess.CompletedProcess[str], Path, str, Path]:
    """Run bump's commit step in bash for kmaudit-v0.2.0 with ``notes`` (and a before-Hermes file).

    Returns the result, the origin repository, the drafted commit and RUNNER_TEMP.
    """
    origin = tmp_path / "origin.git"
    _git_out(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_out(repo, "init", "-q", "-b", "main")
    for rel in (KMAUDIT_VERSION, KMAUDIT_README):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_bytes((ROOT / rel).read_bytes())
    _git_out(repo, "add", ".")
    _git_out(repo, "commit", "-q", "-m", "start")
    _git_out(repo, "remote", "add", "origin", str(origin))
    _git_out(repo, "push", "-q", "origin", "main")
    drafted = _git_out(repo, "rev-parse", "HEAD")
    temp = tmp_path / "runner"
    (temp / "release-notes").mkdir(parents=True)
    (temp / "release-notes" / "kmaudit-v0.2.0.md").write_text(notes)
    if before is not None:
        (temp / "release-notes" / "kmaudit-v0.2.0.before-hermes.md").write_text(before)
    commit = _step(
        RELEASE, "bump", "Commit the version and the notes, and open the pull request"
    )

    res = _bash(
        commit["run"],
        repo,
        {
            "PATH": f"{_stub_bin(tmp_path)}:/usr/bin:/bin",
            "GH_TOKEN": "x",
            "PACKAGE": "kmaudit",
            "VERSION": "0.2.0",
            "TAG": "kmaudit-v0.2.0",
            "DRAFTED": drafted,
            "RUNNER_TEMP": str(temp),
            "GITHUB_STEP_SUMMARY": str(temp / "summary"),
        },
    )
    return res, origin, drafted, temp


def test_release_package_bump_commits_the_notes_and_makes_them_the_body(
    tmp_path: Path,
) -> None:
    """Run in bash for kmaudit, bump commits VERSION, the README and the notes file on the drafted commit.

    The commit carries a Drafted-From trailer, and the pull request body
    holds the notes file and the same trailer.
    """
    notes = "## What changed\n\n- kmaudit learns a trick. (`trick`)\n"

    res, origin, drafted, temp = _run_bump(tmp_path, notes)

    assert res.returncode == 0, res.stdout + res.stderr
    branch = "release/kmaudit-v0.2.0"
    assert _git_out(origin, "log", "-1", "--format=%P", branch) == drafted
    assert _git_out(origin, "log", "-1", "--format=%s", branch) == (
        "release: kmaudit-v0.2.0"
    )
    trailer = _git_out(
        origin, "log", "-1", "--format=%(trailers:key=Drafted-From,valueonly)", branch
    )
    assert trailer == drafted
    assert set(
        _git_out(origin, "diff", "--name-only", drafted, branch).splitlines()
    ) == {
        KMAUDIT_VERSION.as_posix(),
        KMAUDIT_README.as_posix(),
        ".github/release-notes/kmaudit-v0.2.0.md",
    }
    committed = _git_out(
        origin, "show", f"{branch}:.github/release-notes/kmaudit-v0.2.0.md"
    )
    assert committed + "\n" == notes
    args = (temp / "gh-args").read_text().splitlines()
    assert args[:2] == ["pr", "create"]
    assert "--body-file" in args
    body = (temp / "gh-file").read_text()
    assert notes in body
    assert f"Drafted-From: {drafted}" in body
    assert "Draft before Hermes" not in body


def test_release_tag_runs_once_per_package() -> None:
    """The tag job is a matrix over kmctl and kmaudit, each comparing its own version before and after."""
    job = _load(RELEASE_TAG)["jobs"]["tag"]
    plan = _step(RELEASE_TAG, "tag", "Decide whether this push releases")["run"]

    assert job["strategy"]["matrix"] == {"package": ["kmctl", "kmaudit"]}
    assert job["strategy"]["fail-fast"] is False
    assert job["env"] == {"PACKAGE": "${{ matrix.package }}"}
    assert 'uv run scripts/release.py current --package "$PACKAGE"' in plan
    assert 'uv run scripts/release.py compare "$OLD" "$VERSION"' in plan
    assert 'uv run scripts/release.py tag "$VERSION" --package "$PACKAGE"' in plan


def test_release_tag_kmaudit_before_its_version_file_releases_nothing(
    tmp_path: Path,
) -> None:
    """A before commit with no packages/kmaudit/VERSION gives an empty OLD, and 0.1.0.dev0 then skips."""
    (tmp_path / "before").mkdir()
    script = _before_read().replace("uv run ", f"{sys.executable} ")

    res = _bash(
        f'set -euo pipefail\n{script}\nprintf %s "$OLD"',
        ROOT,
        {"RUNNER_TEMP": str(tmp_path), "PACKAGE": "kmaudit"},
    )
    verdict = subprocess.run(
        [sys.executable, "scripts/release.py", "compare", res.stdout, "0.1.0.dev0"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert res.returncode == 0, res.stderr
    assert res.stdout == ""
    assert verdict.stdout == "skip\n"


REFUSE = "Refuse a release without its committed notes"
LATE = "Name commits that landed after the notes were drafted"
PUBLISH = "Publish the GitHub Release"


def test_release_tag_refuses_missing_notes_before_it_tags() -> None:
    """The notes check runs before the build, the tag and the publish, for both verdicts that publish."""
    steps = _steps(RELEASE_TAG, "tag")
    refuse = steps.index(_step(RELEASE_TAG, "tag", REFUSE))

    assert refuse < _index(steps, 'uv build --package "$PACKAGE" -o dist')
    assert refuse < _index(steps, 'git tag -a "$TAG"')
    assert steps[refuse]["if"] == steps[_index(steps, 'gh release create "$TAG"')]["if"]


@pytest.mark.parametrize(
    ("content", "code"),
    [(None, 1), ("", 1), ("  \n\n\t\n", 1), ("## What changed\n\n- A thing.\n", 0)],
    ids=["missing", "empty", "blank", "written"],
)
def test_release_tag_refuses_missing_or_blank_notes(
    tmp_path: Path, content: str | None, code: int
) -> None:
    """Run in bash, the notes check fails on a missing, empty or blank file, naming it, and passes a written one."""
    notes = tmp_path / ".github" / "release-notes" / "kmaudit-v0.2.0.md"
    if content is not None:
        notes.parent.mkdir(parents=True)
        notes.write_text(content)

    res = _bash(
        _step(RELEASE_TAG, "tag", REFUSE)["run"],
        tmp_path,
        {"TAG": "kmaudit-v0.2.0", "PACKAGE": "kmaudit"},
    )

    assert res.returncode == code, res.stdout + res.stderr
    if code:
        assert "::error::.github/release-notes/kmaudit-v0.2.0.md" in res.stdout


@pytest.mark.parametrize(
    ("package", "version", "latest"),
    [
        ("kmctl", "0.3.0", ["--latest"]),
        ("kmaudit", "0.2.0", ["--latest=false"]),
        ("kmctl", "0.3.0rc1", ["--prerelease", "--latest=false"]),
    ],
)
def test_release_tag_publishes_the_committed_notes_latest_only_for_kmctl(
    tmp_path: Path, package: str, version: str, latest: list[str]
) -> None:
    """Run in bash, the publish step passes the committed notes file, byte for byte, and --latest only for a kmctl release."""
    tag = f"{'v' if package == 'kmctl' else 'kmaudit-v'}{version}"
    notes = tmp_path / ".github" / "release-notes" / f"{tag}.md"
    notes.parent.mkdir(parents=True)
    notes.write_bytes(b"## What changed\n\n- Reviewed by hand. \n")
    reviewed = notes.read_bytes()
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "a.whl").write_text("x")
    temp = tmp_path / "runner"
    temp.mkdir()

    res = _bash(
        _step(RELEASE_TAG, "tag", PUBLISH)["run"],
        tmp_path,
        {
            "PATH": f"{_stub_bin(tmp_path)}:/usr/bin:/bin",
            "PACKAGE": package,
            "VERSION": version,
            "TAG": tag,
            "GH_TOKEN": "x",
            "RUNNER_TEMP": str(temp),
            "GITHUB_STEP_SUMMARY": str(temp / "summary"),
        },
    )

    assert res.returncode == 0, res.stdout + res.stderr
    args = (temp / "gh-args").read_text().splitlines()
    assert args[:3] == ["release", "create", tag]
    assert args[args.index("--notes-file") + 1] == f".github/release-notes/{tag}.md"
    assert (temp / "gh-file").read_bytes() == reviewed
    assert [a for a in args if a.startswith(("--latest", "--prerelease"))] == latest


def test_release_tag_never_writes_its_own_notes() -> None:
    """release-tag.yml neither runs release_notes.py nor asks GitHub to generate notes."""
    text = RELEASE_TAG.read_text()

    assert "release_notes.py" not in text
    assert "--generate-notes" not in text


@pytest.fixture
def released(tmp_path: Path) -> dict[str, Any]:
    """A repo where the notes were drafted, then kmctl, kmaudit and loop commits landed on main.

    Returns the repo, the drafted commit and the release branch, whose one
    commit carries the notes file and the Drafted-From trailer.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_out(repo, "init", "-q", "-b", "main")
    _change(repo, "Start", "README.md", "packages/kmaudit/VERSION")
    drafted = _git_out(repo, "rev-parse", "HEAD")
    _git_out(repo, "switch", "-q", "-c", "release/kmaudit-v0.2.0")
    notes = repo / ".github" / "release-notes" / "kmaudit-v0.2.0.md"
    notes.parent.mkdir(parents=True)
    notes.write_text("## What changed\n\n- Reviewed.\n")
    (repo / "packages" / "kmaudit" / "VERSION").write_text("0.2.0\n")
    _git_out(repo, "add", ".")
    _git_out(
        repo,
        "commit",
        "-q",
        "-m",
        "release: kmaudit-v0.2.0",
        "-m",
        f"Drafted-From: {drafted}",
    )
    _git_out(repo, "switch", "-q", "main")
    return {"repo": repo, "drafted": drafted, "notes": notes}


def _land_late_commits(repo: Path) -> None:
    _change(repo, "Late kmctl fix", "docs/a.md")
    _change(repo, "Late kmaudit fix", "packages/kmaudit/a.py")
    _change(repo, "loop: stamp", ".loop/a.json")


def _merge_release(repo: Path, squash: bool, trailer: bool = True) -> None:
    """Land release/kmaudit-v0.2.0 on main as a merge commit or a squash merge, without the Drafted-From trailer when ``trailer`` is false."""
    if not squash:
        if not trailer:
            # The release commit as the bump job would write it without the
            # trailer, such as one made by hand.
            _git_out(repo, "switch", "-q", "release/kmaudit-v0.2.0")
            message = _git_out(repo, "log", "-1", "--format=%B")
            _git_out(
                repo, "commit", "-q", "--amend", "-m", message.split("Drafted-From")[0]
            )
            _git_out(repo, "switch", "-q", "main")
        _git_out(
            repo,
            "merge",
            "-q",
            "--no-ff",
            "-m",
            "Merge pull request #3",
            "release/kmaudit-v0.2.0",
        )
        return
    message = _git_out(repo, "log", "-1", "--format=%B", "release/kmaudit-v0.2.0")
    if not trailer:
        message = message.split("Drafted-From")[0]
    _git_out(repo, "merge", "-q", "--squash", "release/kmaudit-v0.2.0")
    _git_out(repo, "commit", "-q", "-m", f"release: kmaudit-v0.2.0 (#3)\n\n* {message}")


def _late(
    repo: Path, tmp_path: Path, package: str
) -> tuple[subprocess.CompletedProcess[str], str]:
    """Run the late-commits step for ``package`` on HEAD; return the result and the step summary.

    The step runs from the checkout's root, so the repo gets this tree's
    scripts/release_paths.py, untracked and excluded, which the step asks who owns a path.
    """
    (repo / "scripts").mkdir(exist_ok=True)
    (repo / "scripts" / "release_paths.py").write_text(
        (ROOT / "scripts" / "release_paths.py").read_text()
    )
    with (repo / ".git" / "info" / "exclude").open("a") as fh:
        fh.write("/scripts/release_paths.py\n")
    summary = tmp_path / f"summary-{package}"
    summary.write_text("")
    res = _bash(
        _step(RELEASE_TAG, "tag", LATE)["run"],
        repo,
        {
            "PACKAGE": package,
            "TAG": "kmaudit-v0.2.0",
            "GITHUB_SHA": _git_out(repo, "rev-parse", "HEAD"),
            "GITHUB_STEP_SUMMARY": str(summary),
        },
    )
    return res, summary.read_text()


@pytest.mark.parametrize("squash", [False, True], ids=["merge", "squash"])
@pytest.mark.parametrize(
    ("package", "named", "unnamed"),
    [
        ("kmaudit", "Late kmaudit fix", "Late kmctl fix"),
        ("kmctl", "Late kmctl fix", "Late kmaudit fix"),
    ],
)
def test_release_tag_names_the_package_s_late_commits(
    released: dict[str, Any],
    tmp_path: Path,
    squash: bool,
    package: str,
    named: str,
    unnamed: str,
) -> None:
    """Run in bash, the step finds the drafted commit and warns, naming only the package's later commits.

    The reviewed notes file stays byte for byte as committed.
    """
    repo: Path = released["repo"]
    _land_late_commits(repo)
    _merge_release(repo, squash)
    reviewed = released["notes"].read_bytes()

    res, summary = _late(repo, tmp_path, package)

    assert res.returncode == 0, res.stdout + res.stderr
    [warning] = [ln for ln in res.stdout.splitlines() if ln.startswith("::warning::")]
    assert named in warning
    assert unnamed not in warning
    assert "loop: stamp" not in warning
    assert released["drafted"] in warning
    assert "## Commits missing from the kmaudit-v0.2.0 notes" in summary
    assert named in summary and unnamed not in summary
    assert released["notes"].read_bytes() == reviewed
    assert _git_out(repo, "status", "--porcelain") == ""


@pytest.mark.parametrize("squash", [False, True], ids=["merge", "squash"])
def test_release_tag_stays_quiet_without_late_commits(
    released: dict[str, Any], tmp_path: Path, squash: bool
) -> None:
    """With nothing landed after the draft, the step writes no warning and no summary section."""
    repo: Path = released["repo"]
    _merge_release(repo, squash)

    res, summary = _late(repo, tmp_path, "kmaudit")

    assert res.returncode == 0, res.stdout + res.stderr
    assert "::warning::" not in res.stdout
    assert summary == ""


def test_release_tag_warns_when_it_cannot_find_the_drafted_commit(
    released: dict[str, Any], tmp_path: Path
) -> None:
    """A squash merge that lost the trailer warns that late commits were not checked, and does not fail."""
    repo: Path = released["repo"]
    _land_late_commits(repo)
    _merge_release(repo, squash=True, trailer=False)

    res, _ = _late(repo, tmp_path, "kmaudit")

    assert res.returncode == 0, res.stdout + res.stderr
    assert "::warning::Could not find the commit" in res.stdout


# Hermes rewrites the drafted notes for users; scripts/hermes_release_notes.py
# keeps the rewrite only when it passes its checks, else the draft (ADR 0035).

HERMES_ACTION = (
    "JasperHG90/toiminnot/actions/hermes@551e8a6cbb23aba74045fa3578bf4c14ffb92893"
)
# Every Hermes toolset: an empty enabled_toolsets is dropped by the runner and
# loads the defaults, so each one is disabled by name.
TOOLSETS = {
    "browser",
    "clarify",
    "code_execution",
    "delegation",
    "file",
    "memory",
    "project",
    "session_search",
    "skills",
    "terminal",
    "todo",
    "tts",
    "web",
    "vision",
}
HERMES_DRAFT = (
    "## What changed\n\n- Add kmaudit mcp. (`kmaudit-mcp`)\n\n"
    "## Other changes\n\nNone.\n\n## Install\n\nFirst release.\n"
)
HERMES_REWRITE = HERMES_DRAFT.replace(
    "Add kmaudit mcp.", "Drive the audit from any MCP harness."
)
BEFORE = "kmaudit-v0.2.0.before-hermes.md"


def test_hermes_release_step_is_pinned_with_every_tool_off() -> None:
    """The notes job's Hermes step: pinned action, key, model, prompt, no tools, 3 turns, may fail, times out."""
    hermes = _step(RELEASE, "notes", "Rewrite the notes with Hermes")
    triage = next(s for s in _steps(HERMES_TRIAGE, "triage") if s.get("id") == "hermes")
    w = hermes["with"]

    assert hermes["id"] == "hermes"
    assert hermes["uses"] == HERMES_ACTION == triage["uses"]
    assert w["api_key"] == "${{ secrets.OLLAMA_API_KEY }}"
    assert w["model"] == "deepseek-v4.1-flash"
    assert w["system_prompt_file"] == ".github/prompts/release-notes-system.md"
    assert (ROOT / w["system_prompt_file"]).is_file()
    assert set(w["disabled_toolsets"].split(",")) == TOOLSETS
    assert not w.get("enabled_toolsets")
    assert "skills_dir" not in w
    assert w["max_iterations"] == "3"
    assert w["user_message"] == (
        "@${{ runner.temp }}/release-notes/${{ needs.resolve.outputs.tag }}.md"
    )
    assert hermes["continue-on-error"] is True
    assert 0 < hermes["timeout-minutes"] <= 15


def test_hermes_release_step_sits_between_the_draft_and_the_upload() -> None:
    """Draft, Hermes, the check, the summary, then the upload, in that order."""
    steps = _steps(RELEASE, "notes")
    order = [
        steps.index(_step(RELEASE, "notes", name))
        for name in (
            "Draft the notes",
            "Rewrite the notes with Hermes",
            "Check the rewrite",
            "Show the notes",
        )
    ]
    [upload] = [
        i
        for i, s in enumerate(steps)
        if s.get("uses", "").startswith("actions/upload-artifact@")
    ]

    assert order == sorted(order)
    assert order[-1] < upload


def test_hermes_release_prompt_rewrites_only_what_changed() -> None:
    """The prompt keeps references, other sections, and never says work was deferred."""
    text = (PROMPTS / "release-notes-system.md").read_text()

    assert "## What changed" in text
    assert "## Other changes" in text
    assert "postponed, deferred or planned" in text
    assert "@hermes" not in text.lower()


def test_hermes_release_runs_never_expand_an_expression() -> None:
    """Step outputs, the tag and commit-derived values reach release.yml's scripts through env only."""
    for job in _load(RELEASE)["jobs"]:
        assert "${{" not in _runs(RELEASE, job), job


def _check_rewrite(tmp_path: Path, response: str | None) -> Path:
    """Run the Check the rewrite step in bash on HERMES_DRAFT; return the release-notes folder."""
    temp = tmp_path / "runner"
    notes = temp / "release-notes"
    notes.mkdir(parents=True)
    (notes / "kmaudit-v0.2.0.md").write_text(HERMES_DRAFT)
    resp = ""
    if response is not None:
        (tmp_path / "response.md").write_text(response)
        resp = str(tmp_path / "response.md")
    step = _step(RELEASE, "notes", "Check the rewrite")

    res = _bash(
        step["run"],
        ROOT,
        {
            "PATH": f"{_stub_bin(tmp_path)}:/usr/bin:/bin",
            "TAG": "kmaudit-v0.2.0",
            "RESPONSE_FILE": resp,
            "RUNNER_TEMP": str(temp),
        },
    )

    assert res.returncode == 0, res.stdout + res.stderr
    assert step["env"]["RESPONSE_FILE"] == "${{ steps.hermes.outputs.response_file }}"
    assert step["env"]["TAG"] == "${{ needs.resolve.outputs.tag }}"
    return notes


def test_hermes_release_notes_file_is_the_cleaning_script_s_output(
    tmp_path: Path,
) -> None:
    """A passing rewrite becomes TAG.md, with the draft's What changed in the before-Hermes file."""
    notes = _check_rewrite(tmp_path, HERMES_REWRITE)

    assert (notes / "kmaudit-v0.2.0.md").read_text() == HERMES_REWRITE
    before = (notes / BEFORE).read_text()
    assert "Draft before Hermes" in before
    assert "- Add kmaudit mcp. (`kmaudit-mcp`)" in before


@pytest.mark.parametrize(
    "response",
    [None, "", HERMES_REWRITE.replace("(`kmaudit-mcp`)", "(`other`)")],
    ids=["no-response", "empty", "rejected"],
)
def test_hermes_release_failure_keeps_the_draft(
    tmp_path: Path, response: str | None
) -> None:
    """No response, an empty one or a rejected rewrite leaves the draft as TAG.md and no before file."""
    notes = _check_rewrite(tmp_path, response)

    assert (notes / "kmaudit-v0.2.0.md").read_text() == HERMES_DRAFT
    assert not (notes / BEFORE).exists()


@pytest.mark.parametrize("kept", [True, False], ids=["hermes", "draft"])
def test_hermes_release_summary_names_the_source_and_the_draft(
    tmp_path: Path, kept: bool
) -> None:
    """The summary says which source won and, when Hermes won, shows the draft before Hermes."""
    notes = _check_rewrite(tmp_path, HERMES_REWRITE if kept else None)
    summary = tmp_path / "summary"
    step = _step(RELEASE, "notes", "Show the notes")

    res = _bash(
        step["run"],
        ROOT,
        {
            "TAG": "kmaudit-v0.2.0",
            "RUNNER_TEMP": str(notes.parent),
            "GITHUB_STEP_SUMMARY": str(summary),
        },
    )

    assert res.returncode == 0, res.stderr
    text = summary.read_text()
    first = text.splitlines()[0]
    assert (notes / "kmaudit-v0.2.0.md").read_text() in text
    if kept:
        assert "Hermes" in first and "draft" in first
        assert "Draft before Hermes" in text
        assert "- Add kmaudit mcp. (`kmaudit-mcp`)" in text
    else:
        assert first.startswith("**Notes source:** the draft")
        assert "Draft before Hermes" not in text


def test_hermes_release_pr_body_carries_the_draft_before_hermes(
    tmp_path: Path,
) -> None:
    """When Hermes won, the body adds the draft's What changed, collapsed; the file is not committed."""
    before = "<details>\n<summary>Draft before Hermes</summary>\n\n## What changed\n\n- Add kmaudit mcp. (`kmaudit-mcp`)\n\n</details>\n"

    res, origin, drafted, temp = _run_bump(tmp_path, HERMES_REWRITE, before)

    assert res.returncode == 0, res.stdout + res.stderr
    body = (temp / "gh-file").read_text()
    assert HERMES_REWRITE in body
    assert before in body
    assert body.index(HERMES_REWRITE) < body.index(before)
    changed = _git_out(
        origin, "diff", "--name-only", drafted, "release/kmaudit-v0.2.0"
    ).splitlines()
    assert not any("before-hermes" in path for path in changed)


def test_release_tag_reads_the_trailer_past_an_update_branch_merge(
    released: dict[str, Any], tmp_path: Path
) -> None:
    """A release branch that took an "Update branch" merge from main, then a later commit, still names the late commits.

    The second parent's parent is then the update merge, whose history holds
    the late commits, so the step must read the release commit's trailer.
    """
    repo: Path = released["repo"]
    _land_late_commits(repo)
    _git_out(repo, "switch", "-q", "release/kmaudit-v0.2.0")
    _git_out(repo, "merge", "-q", "--no-ff", "-m", "Merge branch 'main'", "main")
    _change(repo, "Edit notes", ".github/release-notes/kmaudit-v0.2.0.md")
    _git_out(repo, "switch", "-q", "main")
    _merge_release(repo, squash=False)

    res, summary = _late(repo, tmp_path, "kmaudit")

    assert res.returncode == 0, res.stdout + res.stderr
    [warning] = [ln for ln in res.stdout.splitlines() if ln.startswith("::warning::")]
    assert "Late kmaudit fix" in warning
    assert released["drafted"] in warning
    assert "Late kmaudit fix" in summary


def test_release_tag_falls_back_to_the_parent_for_a_merge_without_a_trailer(
    released: dict[str, Any], tmp_path: Path
) -> None:
    """A merged release commit with no Drafted-From trailer takes the second parent's parent as the drafted commit."""
    repo: Path = released["repo"]
    _land_late_commits(repo)
    _merge_release(repo, squash=False, trailer=False)
    assert "Drafted-From" not in _git_out(repo, "log", "-1", "--format=%B", "HEAD^2")

    res, summary = _late(repo, tmp_path, "kmaudit")

    assert res.returncode == 0, res.stdout + res.stderr
    [warning] = [ln for ln in res.stdout.splitlines() if ln.startswith("::warning::")]
    assert "Late kmaudit fix" in warning
    assert released["drafted"] in warning
    assert "Late kmaudit fix" in summary


@pytest.mark.parametrize("package", ["kmctl", "kmaudit"])
def test_release_tag_leaves_out_late_bookkeeping_commits(
    released: dict[str, Any], tmp_path: Path, package: str
) -> None:
    """A late commit touching only .okf/ and uv.lock ships in no package, so neither release names it."""
    repo: Path = released["repo"]
    _change(repo, "Late bundle edit", ".okf/summary.md", "uv.lock")
    _land_late_commits(repo)
    _merge_release(repo, squash=False)

    res, summary = _late(repo, tmp_path, package)

    assert res.returncode == 0, res.stdout + res.stderr
    [warning] = [ln for ln in res.stdout.splitlines() if ln.startswith("::warning::")]
    assert f"Late {package} fix" in warning
    assert "Late bundle edit" not in warning + summary


def test_release_tag_asks_release_paths_who_owns_a_path() -> None:
    """The late-commit step pipes paths to release_paths.py and keeps no copy of the rule."""
    run = _step(RELEASE_TAG, "tag", LATE)["run"]

    assert "scripts/release_paths.py" in run
    assert "awk" not in run.split("LATE=()")[1].split("done")[0]
    assert "packages/kmaudit" not in run
