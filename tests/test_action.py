"""The GitHub Action's script, run locally against fixture repositories (ADR 0005)."""

import os
import subprocess
import sys
from pathlib import Path

import yaml

from kmctl.docs_index import folder_index

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


def test_script_passes_and_shows_root_missing_folder_link(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "r")
    (repo / "docs/how-to").mkdir(parents=True)
    (repo / "docs/README.md").write_text("# Docs\n")
    (repo / "docs/how-to/install.md").write_text("# Install\n")
    (repo / "docs/how-to/README.md").write_text(folder_index(repo / "docs/how-to"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "docs")

    proc, summary = _run(repo, _kmctl_bin(tmp_path), tmp_path)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "warning  index  docs/README.md  does not link how-to/" in summary
    assert "all checks passed, 1 warning" in summary


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


WORKFLOW = ROOT / ".github" / "workflows" / "knowledge-audit.yml"
AUDITS = ["docs-vs-code", "okf-vs-code", "okf-vs-docs"]
TOKENS = ("GH_TOKEN", "GITHUB_TOKEN")
OLD_AUDIT = (
    "action/knowledge-audit.sh",
    "action/audit-batches.py",
    "action/audit-report.py",
    "action/hermes/kmctl-read/__init__.py",
    "action/knowledge-audit-issue.sh",
)


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
        assert "knowledge-audit-issue" not in text


def _uses(steps: list[dict], prefix: str) -> list[dict]:
    return [s for s in steps if str(s.get("uses", "")).startswith(prefix)]


def _no_token(step_or_job: dict) -> None:
    text = yaml.safe_dump(step_or_job)
    for name in (*TOKENS, "github.token"):
        assert name not in text, name


def _no_cache(steps: list[dict]) -> None:
    """Every setup-uv turns its cache off, and no step uses actions/cache."""
    uvs = _uses(steps, "astral-sh/setup-uv")
    assert uvs
    for step in uvs:
        assert step.get("with", {}).get("enable-cache") is False, step
    assert _uses(steps, "actions/cache") == []


def _agent_steps(steps: list[dict]) -> tuple[dict, dict]:
    """The agent step and the upload after it."""
    agent = next(s for s in steps if "--model" in str(s.get("run", "")))
    keep = _uses(steps, "actions/upload-artifact")[0]
    assert steps.index(agent) < steps.index(keep)
    return agent, keep


def _publish_steps(steps: list[dict]) -> tuple[dict, dict]:
    """The artifact download and the publish step after it."""
    fetch = _uses(steps, "actions/download-artifact")[0]
    post = next(
        s
        for s in steps
        if "agent.py" in str(s.get("run", "")) and "publish" in str(s.get("run", ""))
    )
    assert steps.index(fetch) < steps.index(post)
    return fetch, post


def test_workflow_audit_job_runs_agent_without_token_or_cache() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    triggers = workflow[True]  # YAML 1.1 reads the key "on" as True
    job = workflow["jobs"]["audit"]
    steps = job["steps"]
    checkout = _uses(steps, "actions/checkout")[0]
    agent, keep = _agent_steps(steps)

    assert set(triggers) == {"workflow_dispatch", "schedule"}
    assert workflow["permissions"] == {"contents": "read"}
    assert "permissions" not in job
    assert not any(str(s.get("uses", "")).startswith("./") for s in steps)
    assert checkout["with"]["persist-credentials"] is False
    assert checkout["with"]["fetch-depth"] == 0
    assert "uv run --script action/agent.py run" in agent["run"]
    assert "--out ${{ runner.temp }}/agent-report" in agent["run"]
    assert "--audit ${{ matrix.audit }}" in agent["run"]
    assert job["strategy"] == {"fail-fast": False, "matrix": {"audit": AUDITS}}
    assert agent["env"]["AUDIT_API_KEY"] == "${{ secrets.AUDIT_API_KEY }}"
    _no_token(job)
    _no_cache(steps)
    assert keep["with"]["name"] == "agent-report-${{ matrix.audit }}"
    assert keep["with"]["path"] == "${{ runner.temp }}/agent-report"
    assert keep["if"] == "always()"


def test_workflow_publish_job_posts_from_the_artifact() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    job = workflow["jobs"]["publish"]
    steps = job["steps"]
    fetch, post = _publish_steps(steps)

    assert job["needs"] == "audit"
    assert job["if"] == "${{ !cancelled() }}"
    assert job["permissions"] == {"contents": "read", "issues": "write"}
    assert job["strategy"]["fail-fast"] is False
    include = job["strategy"]["matrix"]["include"]
    assert [row["audit"] for row in include] == AUDITS
    titles = [row["title"] for row in include]
    assert len(set(titles)) == len(titles) and all(titles)
    assert _uses(steps, "actions/checkout")[0]["with"]["persist-credentials"] is False
    _no_cache(steps)
    assert fetch["with"] == {
        "name": "agent-report-${{ matrix.audit }}",
        "path": "${{ runner.temp }}/agent-report",
    }
    assert "uv run --script action/agent.py publish" in post["run"]
    assert '--title "${{ matrix.title }}"' in post["run"]
    assert "${{ runner.temp }}/agent-report/report.json" in post["run"]
    assert post["env"]["GH_TOKEN"] == "${{ github.token }}"
    others = [s for s in steps if s is not post]
    for step in others:
        _no_token(step)


def test_action_audit_mode_runs_agent_without_token() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    steps = action["runs"]["steps"]
    agent, keep = _agent_steps(steps)

    assert action["inputs"]["mode"]["default"] == "checks"
    for name in (
        "model",
        "base_url",
        "api_key_env",
        "audit",
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
    for step in (agent, keep):
        assert "inputs.mode == 'audit'" in step["if"], step
    assert "${{ github.action_path }}/action/agent.py" in agent["run"]
    assert 'args+=(--audit "$AUDIT")' in agent["run"]
    _no_cache(steps)
    for step in steps:
        if "inputs.mode == 'audit'" in str(step.get("if", "")):
            _no_token(step)
    assert keep["with"] == {
        "name": "${{ inputs.report_name }}",
        "path": "${{ runner.temp }}/agent-report",
        "if-no-files-found": "ignore",
    }
    assert action["inputs"]["report_name"]["default"] == "agent-report"


def test_action_publish_mode_posts_from_the_artifact() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    steps = action["runs"]["steps"]
    fetch, post = _publish_steps(steps)

    for name in ("min_severity", "mention", "issue_title"):
        assert action["inputs"][name]["description"], name
        assert f"${{{{ inputs.{name} }}}}" in post["env"].values(), name
    assert action["inputs"]["min_severity"]["default"] == "high"
    for step in (fetch, post):
        assert "inputs.mode == 'publish'" in step["if"], step
    assert fetch["with"] == {
        "name": "${{ inputs.report_name }}",
        "path": "${{ runner.temp }}/agent-report",
    }
    assert "${{ github.action_path }}/action/agent.py" in post["run"]
    assert '"$RUNNER_TEMP/agent-report/report.json"' in post["run"]
    assert post["env"]["GH_TOKEN"] == "${{ github.token }}"
    for step in steps:
        if step is not post:
            _no_token(step)
    assert "publish" in action["inputs"]["mode"]["description"]


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
    agent, _ = _agent_steps(steps)

    assert "inputs.mode == 'audit'" in check["if"]
    assert steps.index(check) < steps.index(agent)
    for event in ("workflow_dispatch", "schedule"):
        assert _run_check(check, event).returncode == 0, event
    for event in ("pull_request", "pull_request_target", "push"):
        proc = _run_check(check, event)
        assert proc.returncode != 0, event
        assert f"refused for event '{event}'" in proc.stderr
