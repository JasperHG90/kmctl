"""The GitHub Action's audit mode, run locally with a stub claude and gh (ADR 0005, I2)."""

import json
import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import yaml
from test_action import _kmctl_bin, _repo

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "action" / "knowledge-audit.sh"
ISSUE_SCRIPT = ROOT / "action" / "knowledge-audit-issue.sh"
BODY = "kmctl-audit-body.md"
TOKENS = ("GH_TOKEN", "GITHUB_TOKEN")

FINDINGS = [
    {
        "concept": "architecture/overview",
        "path": ".okf/architecture/overview.md",
        "review": "architecture",
        "verdict": "drifted",
        "summary": "The page says greet says Hello; it says Hi.",
        "evidence": [".okf/architecture/overview.md:5", "src/greet.py:2"],
    },
    {
        "concept": "decisions/0001-one",
        "path": ".okf/decisions/0001-one.md",
        "review": "decision",
        "verdict": "holds",
        "summary": "Still true.",
        "evidence": ["src/a.py:1"],
    },
]


def _stubs(
    tmp_path: Path, reply: str, issues: str = "[]", list_fails: bool = False
) -> Path:
    """A bin folder with kmctl, a claude that records its call and prints reply, and a gh that records."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    bin_dir = _kmctl_bin(tmp_path)
    result = json.dumps({"type": "result", "result": reply})
    (tmp_path / "reply.json").write_text(result)
    (bin_dir / "claude").write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$@" > "{tmp_path}/claude-args"\n'
        f'cat > "{tmp_path}/claude-stdin"\n'
        f'env > "{tmp_path}/claude-env"\n'
        f'cat "{tmp_path}/reply.json"\n'
    )
    (tmp_path / "issues.json").write_text(issues)
    (bin_dir / "gh").write_text(
        "#!/bin/sh\n"
        f'echo "$@" >> "{tmp_path}/gh-calls"\n'
        f'env > "{tmp_path}/gh-env"\n'
        + ('[ "$1 $2" = "issue list" ] && exit 4\n' if list_fails else "")
        + 'for a in "$@"; do case "$a" in --body-file) next=1 ;; *) '
        f'[ -n "$next" ] && cp "$a" "{tmp_path}/issue-body" && next= ;; esac; done\n'
        f'[ "$1 $2" = "issue list" ] && cat "{tmp_path}/issues.json"\n'
        "exit 0\n"
    )
    for name in ("claude", "gh"):
        (bin_dir / name).chmod(0o755)
    return bin_dir


def _with_due_decision(repo: Path) -> Path:
    """Add a due decision record, a kind the audit covers, next to the fixture's note."""
    okf = repo / ".okf"
    (okf / "decisions").mkdir()
    (okf / "decisions" / "0001-one.md").write_text(
        '---\ntype: decision\ntitle: "One"\ndescription: "One."\n---\n'
    )
    (okf / "index.md").write_text(
        (okf / "index.md").read_text() + "- [One](decisions/0001-one.md): one.\n"
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.com",
            "commit",
            "-qm",
            "d",
        ],
        cwd=repo,
        check=True,
    )
    return repo


def _env(tmp_path: Path, bin_dir: Path, **extra: str) -> dict[str, str]:
    """The step's environment: this one without GitHub tokens, plus the runner's paths."""
    runner_temp = tmp_path / "runner-temp"
    runner_temp.mkdir(parents=True, exist_ok=True)
    base = {k: v for k, v in os.environ.items() if k not in TOKENS}
    return base | {
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.md"),
        "RUNNER_TEMP": str(runner_temp),
        "KMCTL_PLUGIN_DIR": str(ROOT / "plugin"),
        **extra,
    }


def _audit(
    tmp_path: Path,
    bin_dir: Path,
    event: str = "workflow_dispatch",
    in_scope: bool = True,
    repo_setup: Callable[[Path], None] | None = None,
    **extra: str,
) -> tuple[subprocess.CompletedProcess[str], str]:
    repo = _repo(tmp_path / "r", due=True)
    if in_scope:
        _with_due_decision(repo)
    if repo_setup:
        repo_setup(repo)
    summary = tmp_path / "summary.md"
    summary.write_text("")
    env = _env(tmp_path, bin_dir, GITHUB_EVENT_NAME=event, **extra)
    proc = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc, summary.read_text()


def _issue(
    tmp_path: Path, bin_dir: Path, body: str | None
) -> subprocess.CompletedProcess[str]:
    env = _env(tmp_path, bin_dir, GH_TOKEN="gh-secret")
    if body is not None:
        (Path(env["RUNNER_TEMP"]) / BODY).write_text(body)
    return subprocess.run(
        ["bash", str(ISSUE_SCRIPT)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _reply() -> str:
    return "Audit done.\n\n```json\n" + json.dumps(FINDINGS, indent=2) + "\n```\n"


def test_mode_input_defaults_to_checks() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    steps = action["runs"]["steps"]

    assert action["inputs"]["mode"]["default"] == "checks"
    assert action["inputs"]["mode"]["required"] is False
    assert "anthropic_api_key" in action["inputs"]
    checks = [s for s in steps if "knowledge-ci.sh" in str(s.get("run", ""))]
    audit = [s for s in steps if "knowledge-audit.sh" in str(s.get("run", ""))]
    assert checks and audit
    assert all("inputs.mode == 'checks'" in s.get("if", "") for s in checks)
    for step in steps:
        if "claude" in str(step.get("run", "")) or step in audit:
            assert "inputs.mode == 'audit'" in step.get("if", ""), step


def test_audit_writes_body_without_gh(tmp_path: Path) -> None:
    proc, summary = _audit(tmp_path, _stubs(tmp_path, _reply()))
    body = (tmp_path / "runner-temp" / BODY).read_text()

    assert proc.returncode == 0, proc.stdout + proc.stderr
    for finding in FINDINGS:
        assert finding["concept"] in summary and finding["verdict"] in summary
        assert finding["concept"] in body and finding["verdict"] in body
    assert not (tmp_path / "gh-calls").exists(), "the audit step never calls gh"
    prompt = (tmp_path / "claude-stdin").read_text()
    assert "decisions/0001-one" in prompt
    assert '"note"' not in prompt, "only architecture, decisions and practices go in"
    assert str(ROOT / "plugin" / "skills" / "audit" / "SKILL.md") in prompt


def test_audit_skips_when_nothing_in_scope(tmp_path: Path) -> None:
    proc, summary = _audit(tmp_path, _stubs(tmp_path, _reply()), in_scope=False)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Nothing in scope is due" in summary
    assert not (tmp_path / "claude-args").exists()
    assert not (tmp_path / "runner-temp" / BODY).exists()


def test_audit_refuses_a_reachable_token(tmp_path: Path) -> None:
    def header(repo: Path) -> None:
        subprocess.run(
            [
                "git",
                "config",
                "http.https://github.com/.extraheader",
                "AUTHORIZATION: basic eHg=",
            ],
            cwd=repo,
            check=True,
        )

    def included(repo: Path) -> None:
        creds = repo.parent / "creds.config"
        creds.write_text(
            '[http "https://github.com/"]\n\textraheader = AUTHORIZATION: basic eHg=\n'
        )
        subprocess.run(
            ["git", "config", f"includeIf.gitdir:{repo}/.git.path", str(creds)],
            cwd=repo,
            check=True,
        )

    cases = {
        "gh-token": ({"GH_TOKEN": "secret"}, None),
        "github-token": ({"GITHUB_TOKEN": "secret"}, None),
        "header": ({}, header),
        "included": ({}, included),
    }
    for name, (extra, setup) in cases.items():
        run = tmp_path / name
        proc, _ = _audit(run, _stubs(run, _reply()), repo_setup=setup, **extra)

        assert proc.returncode != 0, name
        assert "token" in proc.stderr, name
        assert "eHg=" not in proc.stdout + proc.stderr, (
            "the header must not reach the log"
        )
        assert not (run / "claude-args").exists(), name


def test_issue_script_creates_the_issue(tmp_path: Path) -> None:
    proc = _issue(tmp_path, _stubs(tmp_path, ""), "## Knowledge audit\n")
    calls = (tmp_path / "gh-calls").read_text()

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "issue create --title Knowledge audit" in calls
    assert (tmp_path / "issue-body").read_text() == "## Knowledge audit\n"


def test_issue_script_updates_the_open_issue(tmp_path: Path) -> None:
    issues = json.dumps([{"number": 7, "title": "Knowledge audit"}])
    proc = _issue(tmp_path, _stubs(tmp_path, "", issues), "## Knowledge audit\n")
    calls = (tmp_path / "gh-calls").read_text()

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "issue edit 7" in calls
    assert "issue create" not in calls


def test_issue_script_skips_without_a_body(tmp_path: Path) -> None:
    proc = _issue(tmp_path, _stubs(tmp_path, ""), None)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not (tmp_path / "gh-calls").exists()


def test_failed_issue_lookup_fails(tmp_path: Path) -> None:
    proc = _issue(
        tmp_path, _stubs(tmp_path, "", list_fails=True), "## Knowledge audit\n"
    )
    calls = (tmp_path / "gh-calls").read_text()

    assert proc.returncode != 0
    assert "issue create" not in calls and "issue edit" not in calls


def test_token_only_on_issue_step() -> None:
    steps = yaml.safe_load((ROOT / "action.yml").read_text())["runs"]["steps"]
    audit = next(s for s in steps if "knowledge-audit.sh" in str(s.get("run", "")))
    issue = next(
        s for s in steps if "knowledge-audit-issue.sh" in str(s.get("run", ""))
    )
    audit_text = yaml.safe_dump(audit)

    for name in (*TOKENS, "github.token"):
        assert name not in audit_text, name
    assert issue["env"]["GH_TOKEN"] == "${{ github.token }}"
    assert issue["env"]["GH_REPO"] == "${{ github.repository }}"
    assert issue["working-directory"] == audit["working-directory"]
    assert "inputs.mode == 'audit'" in issue["if"]


def test_audit_refuses_other_events(tmp_path: Path) -> None:
    for event in ("pull_request", "push", "pull_request_target", ""):
        run = tmp_path / (event or "unset")
        proc, _ = _audit(run, _stubs(run, _reply()), event=event)

        assert proc.returncode != 0, event
        assert "workflow_dispatch" in proc.stderr
        assert not (run / "claude-args").exists(), event


def test_claude_runs_read_only(tmp_path: Path) -> None:
    proc, _ = _audit(tmp_path, _stubs(tmp_path, _reply()))
    args = (tmp_path / "claude-args").read_text().splitlines()

    assert proc.returncode == 0, proc.stdout + proc.stderr

    def value(flag: str) -> str:
        return args[args.index(flag) + 1]

    assert "-p" in args
    assert value("--plugin-dir") == str(ROOT / "plugin")
    assert value("--tools") == "Read,Grep,Glob,Agent"
    assert value("--allowedTools") == "Read,Grep,Glob,Agent"
    assert value("--disallowedTools") == "Bash,Edit,Write,NotebookEdit"
    assert value("--setting-sources") == "project"
    assert "--strict-mcp-config" in args
    assert not any("kmctl-auditor" in a for a in args), "the prompt must go on stdin"
    assert "kmctl-auditor" in (tmp_path / "claude-stdin").read_text()


def test_audit_fails_without_findings(tmp_path: Path) -> None:
    for name, reply in (
        ("none", "I could not finish."),
        ("bad", "```json\n[{not json\n```"),
        ("shape", '```json\n[{"concept": "x"}]\n```'),
    ):
        proc, summary = _audit(tmp_path / name, _stubs(tmp_path / name, reply))

        assert proc.returncode != 0, name
        assert "findings" in proc.stderr + summary, name
        assert not (tmp_path / name / "runner-temp" / BODY).exists(), name


def test_example_workflow() -> None:
    path = ROOT / ".github" / "workflows" / "knowledge-audit.yml"
    text = path.read_text()
    workflow = yaml.safe_load(text)
    triggers = workflow[True]  # YAML 1.1 reads the key "on" as True

    assert set(triggers) == {"workflow_dispatch", "schedule"}
    assert workflow["permissions"] == {"contents": "read", "issues": "write"}
    assert "${{ secrets.ANTHROPIC_API_KEY }}" in text
    steps = workflow["jobs"]["audit"]["steps"]
    step = next(s for s in steps if s.get("uses") == "./")
    checkout = next(
        s for s in steps if str(s.get("uses", "")).startswith("actions/checkout")
    )
    mode_help = yaml.safe_load((ROOT / "action.yml").read_text())["inputs"]["mode"][
        "description"
    ]

    assert step["with"]["mode"] == "audit"
    assert checkout["with"]["persist-credentials"] is False
    assert checkout["with"]["fetch-depth"] == 0
    assert "persist-credentials" in mode_help and "fetch-depth" in mode_help
