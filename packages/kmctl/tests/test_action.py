"""The GitHub Action's script, run locally against fixture repositories (ADR 0005)."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from kmctl.docs_index import folder_index

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "action" / "knowledge-ci.sh"
AGENT = ROOT / "action" / "agent.py"


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
    repo: Path, bin_dir: Path, tmp_path: Path, extra: dict[str, str] | None = None
) -> tuple[subprocess.CompletedProcess[str], str]:
    summary = tmp_path / "summary.md"
    summary.write_text("")
    env = (
        os.environ
        | {
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "GITHUB_STEP_SUMMARY": str(summary),
        }
        | (extra or {})
    )
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


RUN_ENV = {
    "GITHUB_SERVER_URL": "https://github.com",
    "GITHUB_REPOSITORY": "acme/widgets",
    "GITHUB_RUN_ID": "42",
    "GITHUB_RUN_ATTEMPT": "2",
}
RUN_URL = "https://github.com/acme/widgets/actions/runs/42/attempts/2"


def _error_lines(out: str) -> list[str]:
    return [line for line in out.splitlines() if line.startswith("::error")]


def test_script_prints_error_line_when_check_fails(tmp_path: Path) -> None:
    proc, _ = _run(
        _repo(tmp_path / "r", broken=True), _kmctl_bin(tmp_path), tmp_path, RUN_ENV
    )

    assert proc.returncode != 0
    lines = _error_lines(proc.stdout)
    assert len(lines) == 1, proc.stdout
    assert "kmctl check failed" in lines[0]
    assert "summary page" in lines[0]
    assert RUN_URL in lines[0]


def test_script_prints_error_line_when_review_due_crashes(tmp_path: Path) -> None:
    proc, _ = _run(
        _repo(tmp_path / "r"),
        _kmctl_bin(tmp_path, crash_review_due=True),
        tmp_path,
        RUN_ENV,
    )

    assert proc.returncode != 0
    lines = _error_lines(proc.stdout)
    assert len(lines) == 1, proc.stdout
    assert "kmctl review due failed" in lines[0]
    assert RUN_URL in lines[0]


def test_script_prints_no_error_line_when_passing(tmp_path: Path) -> None:
    proc, _ = _run(_repo(tmp_path / "r"), _kmctl_bin(tmp_path), tmp_path, RUN_ENV)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _error_lines(proc.stdout) == []


def test_script_prints_error_line_without_run_url(tmp_path: Path) -> None:
    env = {k: "" for k in RUN_ENV}
    proc, _ = _run(
        _repo(tmp_path / "r", broken=True), _kmctl_bin(tmp_path), tmp_path, env
    )

    assert proc.returncode != 0
    lines = _error_lines(proc.stdout)
    assert len(lines) == 1, proc.stdout
    assert "kmctl check failed" in lines[0]
    assert "summary page" in lines[0]
    assert "http" not in lines[0]
    assert "/actions/runs/" not in lines[0]


def test_action_and_workflow_wiring() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    workflows = list((ROOT / ".github" / "workflows").glob("*.yml"))

    assert action["runs"]["using"] == "composite"
    assert any(
        "knowledge-ci.sh" in str(step.get("run", ""))
        for step in action["runs"]["steps"]
    )
    assert any("uses: ./" in w.read_text() for w in workflows)


def test_action_install_subdirectory_is_packages_kmctl() -> None:
    """The action installs kmctl from packages/kmctl of the tag it runs at, not from the root (ADR 0044)."""
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    [install] = [
        s for s in action["runs"]["steps"] if "uv tool install" in s.get("run", "")
    ]

    assert (
        install["run"] == 'uv tool install "${{ github.action_path }}/packages/kmctl"'
    )
    assert (ROOT / "packages" / "kmctl" / "pyproject.toml").is_file()


WORKFLOW = ROOT / ".github" / "workflows" / "knowledge-audit.yml"
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
        (ROOT / "packages" / "kmctl" / "pyproject.toml").read_text(),
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


def test_action_audit_mode_runs_agent_without_token() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    steps = action["runs"]["steps"]
    agent, keep = _agent_steps(steps)

    assert action["inputs"]["mode"]["default"] == "checks"
    for name in ("model", "base_url", "api_key_env", "timeout"):
        assert action["inputs"][name]["description"], name
        assert f"${{{{ inputs.{name} }}}}" in agent["env"].values(), name
    assert "provider" not in action["inputs"]
    for step in (agent, keep):
        assert "inputs.mode == 'audit'" in step["if"], step
    assert "${{ github.action_path }}/action/agent.py" in agent["run"]
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


def test_removed_inputs_are_gone() -> None:
    """Only what the pull request reread needs is left (ADR 0060)."""
    action = yaml.safe_load((ROOT / "action.yml").read_text())

    for name in (
        "audit",
        "prompt",
        "prompt_file",
        "system_prompt_file",
        "context",
        "skills",
        "mention",
        "issue_title",
    ):
        assert name not in action["inputs"], name
    assert action["inputs"]["title"]["default"] == "Knowledge audit"


def test_action_installs_kmctl_only_for_checks() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    [install] = [
        s for s in action["runs"]["steps"] if "uv tool install" in s.get("run", "")
    ]

    assert install["if"] == "inputs.mode == 'checks'"


def test_action_publish_mode_posts_from_the_artifact() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    steps = action["runs"]["steps"]
    fetch, post = _publish_steps(steps)

    for name in ("min_severity", "title"):
        assert action["inputs"][name]["description"], name
        assert f"${{{{ inputs.{name} }}}}" in post["env"].values(), name
    assert action["inputs"]["min_severity"]["default"] == "low"
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
    """The step that decides whether the audit runs for this event."""
    return next(s for s in steps if "GITHUB_EVENT_NAME" in str(s.get("run", "")))


def _run_check(
    step: dict, event: str, tmp_path: Path, **env: str
) -> tuple[subprocess.CompletedProcess[str], str]:
    """Run the event check as GitHub would; return the process and what it wrote to GITHUB_OUTPUT."""
    output = tmp_path / f"output-{event}-{len(env)}"
    output.write_text("")
    proc = subprocess.run(
        ["bash", "-c", step["run"]],
        env=os.environ
        | {"GITHUB_EVENT_NAME": event, "GITHUB_OUTPUT": str(output)}
        | env,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc, output.read_text()


SAME_REPO = {"HEAD_REPO": "o/r", "BASE_REPO": "o/r", "ACTOR": "alice"}


def _action_steps() -> list[dict]:
    return yaml.safe_load((ROOT / "action.yml").read_text())["runs"]["steps"]


def test_event_check_runs_only_on_a_same_repository_pull_request(
    tmp_path: Path,
) -> None:
    steps = _action_steps()
    check = _event_check(steps)
    agent, _ = _agent_steps(steps)

    assert "inputs.mode == 'audit'" in check["if"]
    assert steps.index(check) < steps.index(agent)
    assert check["env"]["HEAD_REPO"] == (
        "${{ github.event.pull_request.head.repo.full_name }}"
    )
    assert check["env"]["BASE_REPO"] == "${{ github.repository }}"
    assert check["env"]["ACTOR"] == "${{ github.actor }}"
    proc, output = _run_check(check, "pull_request", tmp_path, **SAME_REPO)
    assert proc.returncode == 0, proc.stderr
    assert "run=true" in output
    for env in (
        {**SAME_REPO, "HEAD_REPO": "someone/fork"},
        {**SAME_REPO, "ACTOR": "dependabot[bot]"},
    ):
        proc, output = _run_check(check, "pull_request", tmp_path, **env)
        assert proc.returncode == 0, proc.stderr
        assert "run=false" in output
    for event in ("schedule", "workflow_dispatch"):
        proc, output = _run_check(check, event, tmp_path, **SAME_REPO)
        assert proc.returncode != 0, event
        assert f"refused for event '{event}'" in proc.stderr
        assert "run=true" not in output


def test_event_check_skips_fork_pull_request(tmp_path: Path) -> None:
    steps = _action_steps()
    check = _event_check(steps)
    agent, _ = _agent_steps(steps)

    for env in (
        {**SAME_REPO, "HEAD_REPO": "someone/fork"},
        {**SAME_REPO, "ACTOR": "dependabot[bot]"},
    ):
        proc, output = _run_check(check, "pull_request", tmp_path, **env)
        assert proc.returncode == 0, proc.stderr
        assert "::notice::" in proc.stdout
        assert "run=false" in output
    gate = f"steps.{check['id']}.outputs.run == 'true'"
    assert gate in agent["if"]


def test_event_check_refuses_other_events(tmp_path: Path) -> None:
    check = _event_check(_action_steps())

    for event in ("pull_request_target", "push", "issue_comment", "schedule"):
        proc, output = _run_check(check, event, tmp_path, **SAME_REPO)
        assert proc.returncode != 0, event
        assert f"refused for event '{event}'" in proc.stderr
        assert "run=true" not in output


def _stub_bin(tmp_path: Path) -> tuple[Path, Path]:
    """A uv that records its arguments and a git that answers the agent step's calls."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    calls = tmp_path / "uv-args.json"
    (bin_dir / "uv").write_text(
        f"#!{sys.executable}\nimport json, sys\n"
        f"json.dump(sys.argv[1:], open({str(calls)!r}, 'w'))\n"
    )
    (bin_dir / "git").write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        '  rev-parse) [ "$2" = --show-prefix ] && echo "sub/"; exit 0 ;;\n'
        '  worktree) [ -d "$5" ] && [ -z "$(ls -A "$5")" ] || exit 9; exit 0 ;;\n'
        "esac\n"
        "exit 0\n"
    )
    for name in ("uv", "git"):
        (bin_dir / name).chmod(0o755)
    return bin_dir, calls


def _run_step(step: dict, tmp_path: Path, event: str, **env: str) -> list[str]:
    """Run a step's script with stub uv and git; return the arguments uv got."""
    bin_dir, calls = _stub_bin(tmp_path)
    (tmp_path / "runner").mkdir()
    script = step["run"].replace("${{ github.action_path }}", str(ROOT))
    base_env = {k: "" for k in step.get("env", {})}
    # GitHub runs a bash step as bash --noprofile --norc -eo pipefail.
    proc = subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
        cwd=tmp_path,
        env=os.environ
        | base_env
        | {
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "GITHUB_EVENT_NAME": event,
            "GITHUB_BASE_REF": "main",
            "RUNNER_TEMP": str(tmp_path / "runner"),
            "MODEL": "test",
            "TIMEOUT": "30m",
        }
        | env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(calls.read_text())


def test_agent_step_passes_base_without_a_worktree(tmp_path: Path) -> None:
    agent, _ = _agent_steps(_action_steps())

    args = _run_step(agent, tmp_path, "pull_request")

    assert args[args.index("--base") + 1] == "origin/main"
    assert "--instructions-root" not in args and "--no-shell" not in args
    assert "git worktree" not in agent["run"]
    assert not list((tmp_path / "runner").iterdir())


def test_publish_step_passes_pr(tmp_path: Path) -> None:
    _, post = _publish_steps(_action_steps())

    assert post["env"]["PR_NUMBER"] == "${{ github.event.pull_request.number }}"
    args = _run_step(
        post, tmp_path, "pull_request", PR_NUMBER="12", MIN_SEVERITY="high"
    )
    assert args[args.index("--pr") + 1] == "12"


def test_publish_step_refuses_without_a_pull_request(tmp_path: Path) -> None:
    _, post = _publish_steps(_action_steps())
    bin_dir, calls = _stub_bin(tmp_path)
    script = post["run"].replace("${{ github.action_path }}", str(ROOT))

    proc = subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
        env=os.environ
        | {
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "PR_NUMBER": "",
            "RUNNER_TEMP": str(tmp_path),
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "publish mode posts to a pull request" in proc.stderr
    assert not calls.exists()


def _agent_parser():
    """Load action/agent.py and return its argument parser."""
    spec = importlib.util.spec_from_file_location("action_agent", AGENT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["action_agent"] = module
    spec.loader.exec_module(module)
    return module.parser()


def _script_args(uv_args: list[str]) -> list[str]:
    """The arguments after agent.py in a captured ``uv run ... agent.py ...``."""
    at = next(i for i, a in enumerate(uv_args) if a.endswith("action/agent.py"))
    return uv_args[at + 1 :]


def test_step_arguments_parse_with_the_agent(tmp_path: Path) -> None:
    """A flag the agent no longer takes fails here, not in a consumer's first run."""
    steps = _action_steps()
    agent, _ = _agent_steps(steps)
    _, post = _publish_steps(steps)
    parser = _agent_parser()

    for extra in ({}, {"BASE_URL": "http://x/v1", "API_KEY_ENV": "K"}):
        run_args = _script_args(
            _run_step(agent, tmp_path / f"run{len(extra)}", "pull_request", **extra)
        )
        parsed = parser.parse_args(run_args)
        assert parsed.command == "run" and parsed.base == "origin/main"
    publish_args = _script_args(
        _run_step(
            post,
            tmp_path / "publish",
            "pull_request",
            PR_NUMBER="12",
            MIN_SEVERITY="high",
            TITLE="Knowledge audit",
        )
    )
    parsed = parser.parse_args(publish_args)
    assert parsed.command == "publish" and parsed.pr == 12


def test_publish_step_tolerates_missing_artifact() -> None:
    fetch, _ = _publish_steps(_action_steps())

    assert fetch["continue-on-error"] is True


def _draft_repo(path: Path) -> Path:
    """A committed repository from kmctl init with one draft decision, 0002."""
    from typer.testing import CliRunner

    from kmctl import app

    path.mkdir(parents=True)
    _git(path, "init", "-q", "-b", "main")
    runner = CliRunner()
    assert runner.invoke(app, ["init", "--path", str(path)]).exit_code == 0
    made = runner.invoke(
        app,
        [
            "new",
            "decision",
            "Use a queue",
            "--description",
            "Use a queue.",
            "--draft",
            "--path",
            str(path),
        ],
    )
    assert made.exit_code == 0, made.output
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "c")
    return path


def _run_drafts(
    tmp_path: Path, drafts: str | None, event: str | None, pr_draft: bool | None
) -> tuple[subprocess.CompletedProcess[str], str]:
    """Run the script on a repository with a draft decision, as GitHub would for ``event``."""
    repo = _draft_repo(tmp_path / "r")
    summary = tmp_path / "summary.md"
    summary.write_text("")
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH", "KMCTL_DRAFTS")
    } | {
        "PATH": f"{_kmctl_bin(tmp_path)}:{os.environ['PATH']}",
        "GITHUB_STEP_SUMMARY": str(summary),
    }
    if drafts is not None:
        env["KMCTL_DRAFTS"] = drafts
    if event is not None:
        payload = tmp_path / "event.json"
        payload.write_text(
            json.dumps({"pull_request": {"draft": pr_draft}})
            if pr_draft is not None
            else "{}"
        )
        env |= {"GITHUB_EVENT_NAME": event, "GITHUB_EVENT_PATH": str(payload)}
    proc = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc, summary.read_text()


def test_drafts_fail_on_a_pull_request_ready_for_review(tmp_path: Path) -> None:
    proc, summary = _run_drafts(tmp_path, None, "pull_request", pr_draft=False)

    assert proc.returncode != 0
    assert "error  draft  .okf/decisions/0002-use-a-queue.md" in summary
    assert "Draft decisions fail (drafts: fail-when-ready)." in summary


def test_drafts_pass_on_a_draft_pull_request(tmp_path: Path) -> None:
    proc, summary = _run_drafts(tmp_path, None, "pull_request", pr_draft=True)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Draft decisions pass here (drafts: fail-when-ready)." in summary


def test_drafts_pass_on_a_push(tmp_path: Path) -> None:
    proc, summary = _run_drafts(tmp_path, None, "push", pr_draft=None)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "draft  .okf/decisions" not in summary


def test_drafts_fail_always_and_pass_never(tmp_path: Path) -> None:
    failing, _ = _run_drafts(tmp_path / "a", "fail", "push", pr_draft=None)
    passing, _ = _run_drafts(tmp_path / "b", "pass", "pull_request", pr_draft=False)

    assert failing.returncode != 0
    assert passing.returncode == 0, passing.stdout + passing.stderr


def test_drafts_refuses_an_unknown_value(tmp_path: Path) -> None:
    proc, _ = _run_drafts(tmp_path, "sometimes", None, pr_draft=None)

    assert proc.returncode == 1
    assert (
        "drafts must be fail-when-ready, fail or pass, not 'sometimes'" in proc.stderr
    )


def test_action_passes_the_drafts_input_to_the_script() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text())

    assert action["inputs"]["drafts"]["default"] == "fail-when-ready"
    [step] = [
        s for s in action["runs"]["steps"] if "knowledge-ci.sh" in str(s.get("run", ""))
    ]
    assert step["env"]["KMCTL_DRAFTS"] == "${{ inputs.drafts }}"


def test_action_runs_the_agent_script_without_uv_config() -> None:
    agent, _ = _agent_steps(_action_steps())
    _, post = _publish_steps(_action_steps())

    for step in (agent, post):
        assert "uv run --no-config --script" in step["run"], step["name"]
        assert "uv run --script" not in step["run"], step["name"]
