"""The GitHub Action's audit mode, run locally with a stub hermes and gh (ADR 0005, I2)."""

import json
import os
import re
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import yaml
from conftest import okf_validate
from test_action import _kmctl_bin, _repo

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "action" / "knowledge-audit.sh"
ISSUE_SCRIPT = ROOT / "action" / "knowledge-audit-issue.sh"
BODY = "kmctl-audit-body.md"
TOKENS = ("GH_TOKEN", "GITHUB_TOKEN")
WORKFLOW = ROOT / ".github" / "workflows" / "knowledge-audit.yml"
SKILLS = ROOT / "plugin" / "skills"
AUDITOR = ROOT / "plugin" / "agents" / "kmctl-auditor.md"
SETTINGS = {
    "KMCTL_AUDIT_PROVIDER": "my-provider",
    "KMCTL_AUDIT_MODEL": "my-model",
    "KMCTL_AUDIT_BASE_URL": "http://127.0.0.1:9/v1",
    "KMCTL_AUDIT_API_KEY_ENV": "MY_AUDIT_KEY",
    "MY_AUDIT_KEY": "key-1234",
}

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
    tmp_path: Path,
    reply: str,
    issues: str = "[]",
    list_fails: bool = False,
    sleep: int = 0,
) -> Path:
    """A bin folder with kmctl, a hermes that records its call and prints reply, and a gh that records."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    bin_dir = _kmctl_bin(tmp_path)
    (tmp_path / "reply.txt").write_text(reply)
    (bin_dir / "hermes").write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$@" > "{tmp_path}/hermes-args"\n'
        f'env > "{tmp_path}/hermes-env"\n'
        f'cp -R "$HOME/.hermes" "{tmp_path}/hermes-home"\n'
        f'ls -A "$HERMES_WRITE_SAFE_ROOT" > "{tmp_path}/safe-root-listing"\n'
        + (f"sleep {sleep}\n" if sleep else "")
        + f'cat "{tmp_path}/reply.txt"\n'
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
    for name in ("hermes", "gh"):
        (bin_dir / name).chmod(0o755)
    return bin_dir


def _hermes_env(tmp_path: Path) -> dict[str, str]:
    """The environment the stub hermes ran with."""
    lines = (tmp_path / "hermes-env").read_text().splitlines()
    return dict(line.split("=", 1) for line in lines if "=" in line)


def _prompt(tmp_path: Path) -> str:
    """The prompt the stub hermes got after -z."""
    args = (tmp_path / "hermes-args").read_text()
    return args.split("-z\n", 1)[1]


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
        **SETTINGS,
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
    checks = [s for s in steps if "knowledge-ci.sh" in str(s.get("run", ""))]
    audit = [s for s in steps if "knowledge-audit.sh" in str(s.get("run", ""))]
    assert checks and audit
    assert all("inputs.mode == 'checks'" in s.get("if", "") for s in checks)
    for step in steps:
        if "hermes" in str(step.get("run", "")) or step in audit:
            assert "inputs.mode == 'audit'" in step.get("if", ""), step


def test_audit_writes_body_without_gh(tmp_path: Path) -> None:
    proc, summary = _audit(tmp_path, _stubs(tmp_path, _reply()))
    body = (tmp_path / "runner-temp" / BODY).read_text()

    assert proc.returncode == 0, proc.stdout + proc.stderr
    for finding in FINDINGS:
        assert finding["concept"] in summary and finding["verdict"] in summary
        assert finding["concept"] in body and finding["verdict"] in body
    assert not (tmp_path / "gh-calls").exists(), "the audit step never calls gh"
    prompt = _prompt(tmp_path)
    assert "decisions/0001-one" in prompt
    assert '"note"' not in prompt, "only architecture, decisions and practices go in"


def test_audit_skips_when_nothing_in_scope(tmp_path: Path) -> None:
    proc, summary = _audit(tmp_path, _stubs(tmp_path, _reply()), in_scope=False)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Nothing in scope is due" in summary
    assert not (tmp_path / "hermes-args").exists()
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
        assert not (run / "hermes-args").exists(), name


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
        assert not (run / "hermes-args").exists(), event


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


def _flags(tmp_path: Path) -> list[str]:
    """The stub hermes's arguments before the prompt."""
    args = (tmp_path / "hermes-args").read_text().split("-z\n", 1)[0]
    return args.splitlines()


def _code_lines(path: Path) -> str:
    """A shell script's text without its comments."""
    return "\n".join(
        re.sub(r"(^|\s)#.*$", "", line) for line in path.read_text().splitlines()
    )


def test_hermes_config_from_env(tmp_path: Path) -> None:
    proc, _ = _audit(tmp_path, _stubs(tmp_path, _reply()))
    flags = _flags(tmp_path)
    env = _hermes_env(tmp_path)
    config = yaml.safe_load((tmp_path / "hermes-home" / "config.yaml").read_text())

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert flags[flags.index("--provider") + 1] == "my-provider"
    assert flags[flags.index("-m") + 1] == "my-model"
    assert config["model"]["provider"] == "my-provider"
    assert config["model"]["default"] == "my-model"
    assert config["model"]["base_url"] == "http://127.0.0.1:9/v1"
    assert config["model"]["api_key"] == "${MY_AUDIT_KEY}", "the key stays in env"
    assert "key-1234" not in (tmp_path / "hermes-home" / "config.yaml").read_text()
    assert env["MY_AUDIT_KEY"] == "key-1234"
    assert env["HOME"] != os.environ["HOME"]
    assert env["HERMES_HOME"] == env["HOME"] + "/.hermes"
    assert not Path(env["HOME"]).exists(), "the run's HOME is removed afterwards"


def test_hermes_config_defaults_and_refusals(tmp_path: Path) -> None:
    proc, _ = _audit(
        tmp_path / "default",
        _stubs(tmp_path / "default", _reply()),
        KMCTL_AUDIT_PROVIDER="",
        KMCTL_AUDIT_API_KEY_ENV="",
    )
    home = tmp_path / "default" / "hermes-home"
    config = yaml.safe_load((home / "config.yaml").read_text())
    flags = _flags(tmp_path / "default")

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert flags[flags.index("--provider") + 1] == "custom"
    assert "api_key" not in config["model"]

    cases = {
        "no-model": ({"KMCTL_AUDIT_MODEL": ""}, "KMCTL_AUDIT_MODEL"),
        "no-url": (
            {"KMCTL_AUDIT_PROVIDER": "custom", "KMCTL_AUDIT_BASE_URL": ""},
            "KMCTL_AUDIT_BASE_URL",
        ),
        "bad-name": ({"KMCTL_AUDIT_API_KEY_ENV": "A}B"}, "KMCTL_AUDIT_API_KEY_ENV"),
        "unset-key": ({"MY_AUDIT_KEY": ""}, "MY_AUDIT_KEY"),
    }
    for name, (extra, named) in cases.items():
        run = tmp_path / name
        proc, _ = _audit(run, _stubs(run, _reply()), **extra)

        assert proc.returncode != 0, name
        assert named in proc.stderr, (name, proc.stderr)
        assert not (run / "hermes-args").exists(), name


def test_hermes_config_script_names_no_vendor() -> None:
    for script in (SCRIPT, ROOT / "action" / "audit-report.py"):
        code = _code_lines(script).lower()
        for vendor in ("anthropic", "claude", "openai"):
            assert vendor not in code, (script.name, vendor)


def test_read_only_toolset_and_plugin(tmp_path: Path) -> None:
    proc, _ = _audit(
        tmp_path, _stubs(tmp_path, _reply()), HERMES_ENABLE_PROJECT_PLUGINS="1"
    )
    flags = _flags(tmp_path)
    env = _hermes_env(tmp_path)
    home = tmp_path / "hermes-home"
    config = yaml.safe_load((home / "config.yaml").read_text())
    plugin = ROOT / "action" / "hermes" / "kmctl-read"

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert flags[flags.index("-t") + 1] == "kmctl_read"
    assert flags.count("-t") == 1
    assert config["plugins"]["enabled"] == ["kmctl-read"]
    for name in ("plugin.yaml", "__init__.py"):
        installed = home / "plugins" / "kmctl-read" / name
        assert installed.read_text() == (plugin / name).read_text(), name
    safe_root = env["HERMES_WRITE_SAFE_ROOT"]
    assert safe_root and (tmp_path / "safe-root-listing").read_text() == ""
    assert not safe_root.startswith(str(tmp_path / "r")), "outside the repository"
    assert env["KMCTL_READ_ROOT"] == str((tmp_path / "r").resolve())
    assert "HERMES_ENABLE_PROJECT_PLUGINS" not in env, "no plugin from the repo"
    code = _code_lines(SCRIPT)
    assert re.search(r'timeout [^\n]*"\$limit" hermes', code), (
        "hermes runs under timeout"
    )


def test_read_only_time_limit(tmp_path: Path) -> None:
    start = time.monotonic()
    proc, _ = _audit(
        tmp_path, _stubs(tmp_path, _reply(), sleep=30), KMCTL_AUDIT_TIMEOUT="2s"
    )

    assert time.monotonic() - start < 20
    assert proc.returncode != 0
    assert "time limit" in proc.stderr
    assert not (tmp_path / "runner-temp" / BODY).exists()


def test_read_only_step_timeouts() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    steps = workflow["jobs"]["audit"]["steps"]
    audit = next(s for s in steps if "knowledge-audit.sh" in str(s.get("run", "")))
    action = yaml.safe_load((ROOT / "action.yml").read_text())

    assert isinstance(audit["timeout-minutes"], int)
    # A composite action's steps cannot take timeout-minutes, so action.yml
    # tells callers to set it on their uses: step, and the script's own
    # timeout bounds hermes inside the action.
    assert "timeout-minutes" in action["inputs"]["mode"]["description"]
    assert "KMCTL_AUDIT_TIMEOUT" in action["inputs"]["mode"]["description"]


def test_prompt_and_findings(tmp_path: Path) -> None:
    reply = _reply() + "\n---\nFile-mutation verifier: no files changed.\n"
    proc, summary = _audit(tmp_path, _stubs(tmp_path, reply))
    prompt = _prompt(tmp_path)
    body = (tmp_path / "runner-temp" / BODY).read_text()

    assert proc.returncode == 0, proc.stdout + proc.stderr
    for text in (
        (SKILLS / "audit" / "SKILL.md").read_text(),
        (SKILLS / "decision-log-review" / "SKILL.md").read_text(),
        AUDITOR.read_text(),
    ):
        assert text.strip() in prompt
    assert (SKILLS / "practices-review" / "SKILL.md").read_text().strip() not in prompt
    assert str((tmp_path / "r").resolve()) in prompt
    assert '"id": "decisions/0001-one"' in prompt
    assert '"note"' not in prompt
    for tool in ("kmctl_read_file", "kmctl_search_files", "kmctl_list_files"):
        assert tool in prompt
    for finding in FINDINGS:
        assert finding["summary"] in summary and finding["summary"] in body
    assert "File-mutation verifier" not in body


def test_workflow_spells_out_steps() -> None:
    text = WORKFLOW.read_text()
    workflow = yaml.safe_load(text)
    triggers = workflow[True]  # YAML 1.1 reads the key "on" as True
    steps = workflow["jobs"]["audit"]["steps"]
    runs = [str(s.get("run", "")) for s in steps]
    checkout = next(
        s for s in steps if str(s.get("uses", "")).startswith("actions/checkout")
    )
    audit = next(s for s in steps if "knowledge-audit.sh" in str(s.get("run", "")))
    issue = next(
        s for s in steps if "knowledge-audit-issue.sh" in str(s.get("run", ""))
    )

    assert set(triggers) == {"workflow_dispatch", "schedule"}
    assert workflow["permissions"] == {"contents": "read", "issues": "write"}
    assert not any(str(s.get("uses", "")).startswith("./") for s in steps)
    assert any("uv tool install" in r and "hermes-agent==0.19.0" in r for r in runs)
    assert any(re.search(r"uv tool install \S*\.\S*$", r.strip()) for r in runs)
    assert checkout["with"]["persist-credentials"] is False
    assert checkout["with"]["fetch-depth"] == 0
    for name in ("KMCTL_AUDIT_PROVIDER", "KMCTL_AUDIT_MODEL", "KMCTL_AUDIT_BASE_URL"):
        assert audit["env"][name], name
    key_env = audit["env"]["KMCTL_AUDIT_API_KEY_ENV"]
    assert audit["env"][key_env] == "${{ secrets." + key_env + " }}"
    for name in (*TOKENS, "github.token"):
        assert name not in yaml.safe_dump(audit), name
    assert issue["env"]["GH_TOKEN"] == "${{ github.token }}"


def test_workflow_action_inputs() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    steps = action["runs"]["steps"]
    audit = next(s for s in steps if "knowledge-audit.sh" in str(s.get("run", "")))
    mode_help = action["inputs"]["mode"]["description"]

    assert "anthropic_api_key" not in action["inputs"]
    for name in ("provider", "model", "base_url", "api_key_env"):
        assert name in action["inputs"], name
        assert action["inputs"][name]["description"], name
    assert action["inputs"]["provider"]["default"] == "custom"
    assert audit["env"]["KMCTL_AUDIT_PROVIDER"] == "${{ inputs.provider }}"
    assert audit["env"]["KMCTL_AUDIT_MODEL"] == "${{ inputs.model }}"
    assert audit["env"]["KMCTL_AUDIT_BASE_URL"] == "${{ inputs.base_url }}"
    assert audit["env"]["KMCTL_AUDIT_API_KEY_ENV"] == "${{ inputs.api_key_env }}"
    assert any(
        "hermes-agent==0.19.0" in str(s.get("run", ""))
        and "inputs.mode == 'audit'" in s.get("if", "")
        for s in steps
    )
    assert "persist-credentials" in mode_help and "fetch-depth" in mode_help


def test_decision_record() -> None:
    records = [
        p
        for p in sorted((ROOT / ".okf" / "decisions").glob("[0-9]*.md"))
        if "Hermes" in p.read_text() and not p.name.startswith("0005-")
    ]

    assert records, "no decision record names Hermes"
    text = records[0].read_text()
    assert "provider" in text and "0005-audits-report-only.md" in text
    assert "Claude Code" in text, "it names the runner it replaces"
    check = okf_validate(ROOT / ".okf")
    assert check.returncode == 0, check.stdout + check.stderr
