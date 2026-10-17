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


ISSUE_SCRIPT = ROOT / "action" / "knowledge-audit-issue.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "knowledge-audit.yml"
TOKENS = ("GH_TOKEN", "GITHUB_TOKEN")
OLD_AUDIT = (
    "action/knowledge-audit.sh",
    "action/audit-batches.py",
    "action/audit-report.py",
    "action/hermes",
)


def _gh_bin(tmp_path: Path, issues: str = "[]", list_fails: bool = False) -> Path:
    """A bin folder with a gh that records its calls and the body file it is given."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    (tmp_path / "issues.json").write_text(issues)
    (bin_dir / "gh").write_text(
        "#!/bin/sh\n"
        f'echo "$@" >> "{tmp_path}/gh-calls"\n'
        + ('[ "$1 $2" = "issue list" ] && exit 4\n' if list_fails else "")
        + 'for a in "$@"; do case "$a" in --body-file) next=1 ;; *) '
        f'[ -n "$next" ] && cp "$a" "{tmp_path}/issue-body" && next= ;; esac; done\n'
        f'[ "$1 $2" = "issue list" ] && cat "{tmp_path}/issues.json"\n'
        "exit 0\n"
    )
    (bin_dir / "gh").chmod(0o755)
    return bin_dir


def _issue(
    tmp_path: Path, bin_dir: Path, body: str | None
) -> subprocess.CompletedProcess[str]:
    report = tmp_path / "agent-report" / "report.md"
    if body is not None:
        report.parent.mkdir()
        report.write_text(body)
    env = os.environ | {"PATH": f"{bin_dir}:{os.environ['PATH']}", "GH_TOKEN": "t"}
    return subprocess.run(
        ["bash", str(ISSUE_SCRIPT), str(report)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_issue_script_creates_the_issue(tmp_path: Path) -> None:
    proc = _issue(tmp_path, _gh_bin(tmp_path), "## Agent report\n")
    calls = (tmp_path / "gh-calls").read_text()

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "issue create --title Knowledge audit" in calls
    assert (tmp_path / "issue-body").read_text() == "## Agent report\n"


def test_issue_script_updates_the_open_issue(tmp_path: Path) -> None:
    issues = '[{"number": 7, "title": "Knowledge audit"}]'
    proc = _issue(tmp_path, _gh_bin(tmp_path, issues), "## Agent report\n")
    calls = (tmp_path / "gh-calls").read_text()

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "issue edit 7" in calls
    assert "issue create" not in calls


def test_issue_script_skips_without_a_report(tmp_path: Path) -> None:
    proc = _issue(tmp_path, _gh_bin(tmp_path), None)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not (tmp_path / "gh-calls").exists()


def test_failed_issue_lookup_fails(tmp_path: Path) -> None:
    proc = _issue(tmp_path, _gh_bin(tmp_path, list_fails=True), "## Agent report\n")
    calls = (tmp_path / "gh-calls").read_text()

    assert proc.returncode != 0
    assert "issue create" not in calls and "issue edit" not in calls


def test_old_audit_is_gone() -> None:
    texts = [
        (ROOT / "action.yml").read_text(),
        WORKFLOW.read_text(),
        (ROOT / "pyproject.toml").read_text(),
    ]

    for rel in OLD_AUDIT:
        assert not (ROOT / rel).exists(), rel
    for text in texts:
        assert "hermes" not in text.lower()


def _steps(steps: list[dict]) -> tuple[dict, dict, dict]:
    """The agent, artifact and issue steps, in that order in ``steps``."""
    agent = next(s for s in steps if "action/agent.py" in str(s.get("run", "")))
    keep = next(
        s for s in steps if str(s.get("uses", "")).startswith("actions/upload-artifact")
    )
    issue = next(
        s for s in steps if "knowledge-audit-issue.sh" in str(s.get("run", ""))
    )
    assert steps.index(agent) < steps.index(keep) < steps.index(issue)
    return agent, keep, issue


def test_workflow_runs_agent_keeps_report_then_posts() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    triggers = workflow[True]  # YAML 1.1 reads the key "on" as True
    steps = workflow["jobs"]["audit"]["steps"]
    checkout = next(
        s for s in steps if str(s.get("uses", "")).startswith("actions/checkout")
    )
    agent, keep, issue = _steps(steps)

    assert set(triggers) == {"workflow_dispatch", "schedule"}
    assert workflow["permissions"] == {"contents": "read", "issues": "write"}
    assert not any(str(s.get("uses", "")).startswith("./") for s in steps)
    assert checkout["with"]["persist-credentials"] is False
    assert checkout["with"]["fetch-depth"] == 0
    assert "uv run --script action/agent.py run" in agent["run"]
    assert "--out ${{ runner.temp }}/agent-report" in agent["run"]
    assert agent["env"]["AUDIT_API_KEY"] == "${{ secrets.AUDIT_API_KEY }}"
    for name in (*TOKENS, "github.token"):
        assert name not in yaml.safe_dump(agent), name
    assert keep["with"]["path"] == "${{ runner.temp }}/agent-report"
    assert keep["if"] == "always()"
    assert issue["env"]["GH_TOKEN"] == "${{ github.token }}"
    assert "${{ runner.temp }}/agent-report/report.md" in issue["run"]


def test_action_audit_mode_runs_agent_keeps_report_then_posts() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    steps = action["runs"]["steps"]
    agent, keep, issue = _steps(steps)

    assert action["inputs"]["mode"]["default"] == "checks"
    for name in (
        "model",
        "base_url",
        "api_key_env",
        "prompt",
        "prompt_file",
        "system_prompt_file",
        "context",
        "skills",
        "timeout",
    ):
        assert action["inputs"][name]["description"], name
        assert f"${{{{ inputs.{name} }}}}" in agent["env"].values(), name
    assert "provider" not in action["inputs"]
    for step in (agent, keep, issue):
        assert "inputs.mode == 'audit'" in step["if"], step
    assert "${{ github.action_path }}/action/agent.py" in agent["run"]
    for name in (*TOKENS, "github.token"):
        assert name not in yaml.safe_dump(agent), name
    assert keep["with"]["path"] == "${{ runner.temp }}/agent-report"
    assert issue["env"]["GH_TOKEN"] == "${{ github.token }}"
    assert issue["working-directory"] == agent["working-directory"]
    assert '"$RUNNER_TEMP/agent-report/report.md"' in issue["run"]


def _event_check(steps: list[dict]) -> dict:
    """The step that refuses events other than workflow_dispatch and schedule."""
    return next(s for s in steps if "GITHUB_EVENT_NAME" in str(s.get("run", "")))


def _run_check(step: dict, event: str) -> subprocess.CompletedProcess[str]:
    env = os.environ | {"GITHUB_EVENT_NAME": event}
    return subprocess.run(
        ["bash", "-c", step["run"]],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_action_audit_refuses_other_events() -> None:
    steps = yaml.safe_load((ROOT / "action.yml").read_text())["runs"]["steps"]
    check = _event_check(steps)
    agent, _, _ = _steps(steps)

    assert "inputs.mode == 'audit'" in check["if"]
    assert steps.index(check) < steps.index(agent)
    for event in ("workflow_dispatch", "schedule"):
        assert _run_check(check, event).returncode == 0, event
    for event in ("pull_request", "pull_request_target", "push"):
        proc = _run_check(check, event)
        assert proc.returncode != 0, event
        assert f"refused for event '{event}'" in proc.stderr
