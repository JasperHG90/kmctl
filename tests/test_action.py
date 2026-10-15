"""The GitHub Action's script, run locally against fixture repositories (ADR 0005)."""

import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "action" / "knowledge-ci.sh"


def _git(cwd: Path, *args: str) -> None:
    env = os.environ | {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True)


def _kmctl_bin(tmp_path: Path, crash_review_due: bool = False) -> Path:
    """A folder with a kmctl that runs this checkout's code, optionally crashing on review due."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    crash = (
        'if [ "$1" = review ]; then echo "Traceback: boom" >&2; exit 2; fi\n'
        if crash_review_due
        else ""
    )
    (bin_dir / "kmctl").write_text(
        f'#!/bin/sh\n{crash}exec {sys.executable} -c "import sys; from kmctl import main; sys.argv[0] = \'kmctl\'; main()" "$@"\n'
    )
    (bin_dir / "kmctl").chmod(0o755)
    return bin_dir


def _repo(path: Path, *, broken: bool = False, due: bool = False) -> Path:
    """A committed repository with a bundle; optionally an unlisted concept, or a concept due."""
    path.mkdir(parents=True)
    _git(path, "init", "-q", "-b", "main")
    okf = path / ".okf"
    okf.mkdir()
    (okf / "index.md").write_text('---\nokf_version: "0.2"\n---\n\n# Bundle\n')
    (okf / "log.md").write_text("# Log\n")
    if broken:
        (okf / "unlisted.md").write_text(
            '---\ntype: note\ntitle: "U"\ndescription: "U."\n---\n'
        )
    if due:
        (okf / "index.md").write_text(
            (okf / "index.md").read_text() + "\n- [Note](note.md): a note.\n"
        )
        (okf / "note.md").write_text(
            '---\ntype: note\ntitle: "N"\ndescription: "N."\n---\n'
        )
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "c")
    return path


def _run(
    repo: Path, bin_dir: Path, tmp_path: Path
) -> tuple[subprocess.CompletedProcess[str], str]:
    summary = tmp_path / "summary.md"
    summary.write_text("")
    env = os.environ | {
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "GITHUB_STEP_SUMMARY": str(summary),
    }
    proc = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc, summary.read_text()


def test_script_passes_and_writes_both_reports(tmp_path: Path) -> None:
    proc, summary = _run(_repo(tmp_path / "r"), _kmctl_bin(tmp_path), tmp_path)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "## kmctl check" in summary
    assert "## kmctl review due" in summary


def test_script_fails_when_check_fails(tmp_path: Path) -> None:
    proc, summary = _run(
        _repo(tmp_path / "r", broken=True), _kmctl_bin(tmp_path), tmp_path
    )

    assert proc.returncode != 0
    assert "unlisted.md" in summary


def test_script_passes_when_concepts_due(tmp_path: Path) -> None:
    proc, summary = _run(
        _repo(tmp_path / "r", due=True), _kmctl_bin(tmp_path), tmp_path
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "note" in summary.split("## kmctl review due", 1)[1]


def test_script_deepens_shallow_clone(tmp_path: Path) -> None:
    origin = _repo(tmp_path / "origin", due=True)
    (origin / "extra.txt").write_text("x\n")
    _git(origin, "add", "-A")
    _git(origin, "commit", "-q", "-m", "second")
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", origin.resolve().as_uri(), str(clone)],
        check=True,
        capture_output=True,
    )

    proc, summary = _run(clone, _kmctl_bin(tmp_path), tmp_path)
    shallow = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=clone,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert shallow == "false"
    assert "not checked" not in summary


def test_script_fails_when_review_due_crashes(tmp_path: Path) -> None:
    proc, summary = _run(
        _repo(tmp_path / "r"), _kmctl_bin(tmp_path, crash_review_due=True), tmp_path
    )

    assert proc.returncode != 0
    assert "kmctl review due failed" in summary


def test_action_and_workflow_wiring() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    workflows = list((ROOT / ".github" / "workflows").glob("*.yml"))

    assert action["runs"]["using"] == "composite"
    assert any(
        "knowledge-ci.sh" in str(step.get("run", ""))
        for step in action["runs"]["steps"]
    )
    assert any("uses: ./" in w.read_text() for w in workflows)
