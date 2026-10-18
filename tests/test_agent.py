"""The standalone CI agent, action/agent.py, run offline with PydanticAI's function model (ADR 0017)."""

import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "action" / "agent.py"

_spec = importlib.util.spec_from_file_location("ci_agent", SCRIPT)
assert _spec is not None and _spec.loader is not None
agent = importlib.util.module_from_spec(_spec)
sys.modules["ci_agent"] = agent
_spec.loader.exec_module(agent)

TRACE_VARS = (
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_BASE_URL",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    "OTEL_EXPORTER_OTLP_HEADERS",
)

#: Cites only README.md, which Recorder reads before it hands the report in.
REPORT = {
    "summary": "One page drifted.",
    "checked": [
        {
            "subject": "README.md",
            "against": "itself",
            "evidence": ["README.md:1-2"],
        }
    ],
    "findings": [
        {
            "title": "readme/greeting",
            "severity": "high",
            "path": "README.md",
            "summary": "It says hello, then world.",
            "claim": "README.md:2",
            "contradicted_by": ["README.md:1"],
            "fix": "Say hello once.",
        },
        {
            "title": "readme/style",
            "severity": "info",
            "path": "README.md",
            "summary": "Lower case.",
            "claim": "README.md:1",
            "contradicted_by": ["README.md:2"],
            "fix": "None needed.",
        },
    ],
}


class Recorder:
    """A FunctionModel body that records what the model saw and returns REPORT.

    It makes ``calls``, then reads README.md, then returns each of ``reports``
    in turn (REPORT when none are left).
    """

    def __init__(
        self,
        calls: list[tuple[str, dict]] | None = None,
        reports: list[dict] | None = None,
    ) -> None:
        self.calls = [*(calls or []), ("read_file", {"path": "README.md"})]
        self.reports = list(reports or [])
        self.instructions: str | None = None
        self.prompt: str | None = None
        self.returns: list[str] = []
        self.retries: list[str] = []

    def __call__(self, messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        first = messages[0]
        assert isinstance(first, ModelRequest)
        self.instructions = first.instructions
        self.prompt = next(
            str(p.content) for p in first.parts if isinstance(p, UserPromptPart)
        )
        last = messages[-1]
        if isinstance(last, ModelRequest):
            self.returns += [
                str(p.content) for p in last.parts if p.part_kind == "tool-return"
            ]
            self.retries += [
                p.model_response() for p in last.parts if p.part_kind == "retry-prompt"
            ]
        if self.calls:
            name, args = self.calls.pop(0)
            return ModelResponse(parts=[ToolCallPart(name, args)])
        report = self.reports.pop(0) if self.reports else REPORT
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, report)])


def _skill(folder: Path, name: str, front: str | None = None) -> Path:
    path = folder / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        front
        if front is not None
        else f"---\nname: {name}\ndescription: Do the {name} thing.\n---\n\n# {name}\n"
    )
    return path


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    (path / "README.md").write_text("hello\nworld\n")
    for name in (*agent.TOKEN_VARS, *TRACE_VARS):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    return path


def _main(repo: Path, tmp_path: Path, model, *extra: str) -> int:
    return agent.main(
        [
            "run",
            "--model",
            "unused",
            "--repo",
            str(repo),
            "--out",
            str(tmp_path / "out"),
            *extra,
        ],
        model=model,
    )


def test_run_writes_report_files_and_summary(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    summary = tmp_path / "summary.md"
    summary.write_text("")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    assert _main(repo, tmp_path, FunctionModel(Recorder())) == 0

    out = tmp_path / "out"
    report = agent.Report.model_validate_json((out / "report.json").read_text())
    assert report.model_dump() == REPORT
    markdown = (out / "report.md").read_text()
    for finding in REPORT["findings"]:
        assert finding["title"] in markdown
        assert finding["fix"] in markdown
    assert markdown.index("high") < markdown.index("| info")
    assert json.loads((out / "transcript.json").read_text())
    assert summary.read_text() == markdown


def test_evidence_gives_up_with_cli_test_model(repo: Path, tmp_path: Path) -> None:
    """`--model test` runs through the real command line, offline, and cites
    lines it never read, so the run stops at the retry limit with no report."""
    env = {k: v for k, v in os.environ.items() if k not in agent.TOKEN_VARS}
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "run",
            "--model",
            "test",
            "--repo",
            str(repo),
            "--out",
            str(tmp_path / "out"),
            "--prompt",
            "Say hi.",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1, proc.stderr
    assert "citations could not be checked" in proc.stderr
    assert not (tmp_path / "out" / "report.json").exists()


def test_report_shape_lists_checked_after_findings(repo: Path, tmp_path: Path) -> None:
    assert _main(repo, tmp_path, FunctionModel(Recorder())) == 0

    out = tmp_path / "out"
    report = json.loads((out / "report.json").read_text())
    assert report["checked"] == REPORT["checked"]
    for finding in report["findings"]:
        assert {"claim", "contradicted_by", "fix"} <= finding.keys()
    markdown = (out / "report.md").read_text()
    assert "`README.md` against itself: `README.md:1-2`" in markdown
    assert markdown.index("readme/style") < markdown.index("### Checked (1)")


def _citing(*cites: str) -> dict:
    """REPORT with its first finding's claim and the checked evidence replaced."""
    report = json.loads(json.dumps(REPORT))
    report["findings"][0]["claim"] = cites[0]
    report["checked"][0]["evidence"] = list(cites[1:])
    return report


def test_evidence_unread_lines_are_sent_back(repo: Path, tmp_path: Path) -> None:
    (repo / "big.md").write_text("".join(f"line {n}\n" for n in range(1, 11)))
    (repo / "other.md").write_text("never read\n")
    rec = Recorder(
        [("read_file", {"path": "big.md", "offset": 3, "limit": 2})],
        reports=[
            _citing(
                "big.md:4",
                "big.md:2",
                "other.md:1",
                "README.md:9",
                "nope",
                "big.md:9-1",
                "big.md:0",
            )
        ],
    )

    assert _main(repo, tmp_path, FunctionModel(rec)) == 0

    (retry,) = rec.retries
    assert "big.md:2: line 2 was neither read nor a search hit" in retry
    assert "other.md:1: line 1 was neither read nor a search hit" in retry
    assert "README.md:9: past the end of the file (2 lines)" in retry
    assert "nope: not path:line" in retry
    assert "big.md:9-1: lines count from 1, and a range runs first-last" in retry
    assert "big.md:0: lines count from 1" in retry
    assert "big.md:4" not in retry
    report = json.loads((tmp_path / "out" / "report.json").read_text())
    assert report == REPORT


def test_evidence_search_hits_count_as_seen(repo: Path, tmp_path: Path) -> None:
    (repo / "notes.md").write_text("alpha\nbeta\n")
    rec = Recorder(
        [("search_files", {"pattern": "beta"})],
        reports=[_citing("notes.md:2", "notes.md:1")],
    )

    assert _main(repo, tmp_path, FunctionModel(rec)) == 0

    (retry,) = rec.retries
    assert "notes.md:1: line 1 was neither read" in retry
    assert "notes.md:2" not in retry


def test_prompt_option_is_the_user_message(repo: Path, tmp_path: Path) -> None:
    rec = Recorder()

    assert (
        _main(repo, tmp_path, FunctionModel(rec), "--prompt", "Compare to the EA docs.")
        == 0
    )
    assert rec.prompt == "Compare to the EA docs."


def test_prompt_file_is_the_user_message(repo: Path, tmp_path: Path) -> None:
    rec = Recorder()
    task = tmp_path / "task.md"
    task.write_text("From a file.")

    assert _main(repo, tmp_path, FunctionModel(rec), "--prompt-file", str(task)) == 0
    assert rec.prompt == "From a file."


def test_default_prompt_is_okf_vs_code(repo: Path, tmp_path: Path) -> None:
    rec = Recorder()

    assert _main(repo, tmp_path, FunctionModel(rec)) == 0
    assert rec.prompt == (agent.PROMPTS / "okf-vs-code.md").read_text()


@pytest.mark.parametrize("name", ["docs-vs-code", "okf-vs-code", "okf-vs-docs"])
def test_audit_option_sends_its_prompt(repo: Path, tmp_path: Path, name: str) -> None:
    text = (agent.PROMPTS / f"{name}.md").read_text()
    assert text.strip()
    rec = Recorder()

    assert _main(repo, tmp_path, FunctionModel(rec), "--audit", name) == 0
    assert rec.prompt == text


@pytest.mark.parametrize("other", ["--prompt", "--prompt-file"])
def test_audit_choices_refuse_a_second_prompt(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], other: str
) -> None:
    code = _main(
        repo,
        tmp_path,
        FunctionModel(Recorder()),
        "--audit",
        "docs-vs-code",
        other,
        "x",
    )

    assert code == 2
    err = capsys.readouterr().err
    assert "--audit" in err and other in err


def test_audit_choices_refuse_an_unknown_name(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exit:
        _main(repo, tmp_path, FunctionModel(Recorder()), "--audit", "nope")

    assert exit.value.code == 2
    assert "invalid choice: 'nope'" in capsys.readouterr().err


def test_audit_choices_are_in_help(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # argparse wraps at hyphens, so a narrow terminal splits okf-vs-code.
    monkeypatch.setenv("COLUMNS", "500")
    with pytest.raises(SystemExit):
        agent.main(["run", "--help"])

    help_text = " ".join(capsys.readouterr().out.split())
    for name in agent.AUDITS:
        assert name in help_text
    assert "Default: okf-vs-code" in help_text


def test_prompt_defaults_keep_holds_out_of_findings(repo: Path, tmp_path: Path) -> None:
    rec = Recorder()

    assert _main(repo, tmp_path, FunctionModel(rec)) == 0
    assert rec.instructions and rec.prompt
    system = " ".join(rec.instructions.split())
    assert "Something that holds goes here, never in findings" in system
    assert "The report is checked" in system
    assert "holds is info" not in rec.prompt


def test_system_prompt_file_replaces_the_default(repo: Path, tmp_path: Path) -> None:
    rec = Recorder()
    system = tmp_path / "system.md"
    system.write_text("You are terse.")

    assert (
        _main(repo, tmp_path, FunctionModel(rec), "--system-prompt-file", str(system))
        == 0
    )
    assert rec.instructions == "You are terse."


def test_both_prompt_options_exit_2(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    task = tmp_path / "task.md"
    task.write_text("x")

    code = _main(
        repo,
        tmp_path,
        FunctionModel(Recorder()),
        "--prompt",
        "a",
        "--prompt-file",
        str(task),
    )

    assert code == 2
    err = capsys.readouterr().err
    assert "--prompt" in err and "--prompt-file" in err


def test_skills_from_every_folder_are_listed(repo: Path, tmp_path: Path) -> None:
    one, two = tmp_path / "one", tmp_path / "two"
    a = _skill(one, "alpha")
    b = _skill(two, "beta")
    rec = Recorder()

    assert (
        _main(
            repo,
            tmp_path,
            FunctionModel(rec),
            "--skills",
            str(one),
            "--skills",
            str(two),
        )
        == 0
    )
    assert rec.instructions
    for name, path in (("alpha", a), ("beta", b)):
        assert f"- {name}: Do the {name} thing." in rec.instructions
        assert str(path.resolve()) in rec.instructions


def test_skills_default_to_kmctls(repo: Path, tmp_path: Path) -> None:
    rec = Recorder()

    assert _main(repo, tmp_path, FunctionModel(rec)) == 0
    assert agent.DEFAULT_SKILLS == ROOT / "apm" / ".apm" / "skills"
    assert rec.instructions and "- audit: " in rec.instructions
    assert str(agent.DEFAULT_SKILLS / "audit" / "SKILL.md") in rec.instructions


def test_skills_bad_front_matter_stops_the_run(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = _skill(tmp_path / "skills", "broken", "---\nname: broken\n---\n")

    assert (
        _main(
            repo,
            tmp_path,
            FunctionModel(Recorder()),
            "--skills",
            str(tmp_path / "skills"),
        )
        == 2
    )
    assert str(bad) in capsys.readouterr().err


def test_tools_reach_repo_context_and_skills(repo: Path, tmp_path: Path) -> None:
    context = tmp_path / "context"
    context.mkdir()
    (context / "ea.md").write_text("enterprise rule\n")
    skills = tmp_path / "skills"
    skill = _skill(skills, "alpha")
    rec = Recorder(
        [
            ("read_file", {"path": "README.md"}),
            ("read_file", {"path": str(context / "ea.md")}),
            ("read_file", {"path": str(skill)}),
            ("search_files", {"pattern": "rule", "path": str(context)}),
            ("list_files", {"path": str(skills)}),
        ]
    )

    assert (
        _main(
            repo,
            tmp_path,
            FunctionModel(rec),
            "--context",
            str(context),
            "--skills",
            str(skills),
        )
        == 0
    )
    readme, ea, skill_md, search, listing, _ = rec.returns
    assert "1|hello" in readme
    assert "1|enterprise rule" in ea
    assert "name: alpha" in skill_md
    assert "ea.md:1: enterprise rule" in search
    assert "SKILL.md" in listing


def test_tools_refuse_paths_outside_every_root(repo: Path, tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("key\n")
    (repo / "link.txt").symlink_to(secret)
    (repo / "linkdir").symlink_to(tmp_path)
    ws = agent.Workspace(repo.resolve(), [repo.resolve()])
    read_file, search_files, list_files, _ = agent.make_tools(ws)

    for result in (
        read_file(str(secret)),
        read_file("../secret.txt"),
        read_file("link.txt"),
        search_files("key", str(tmp_path)),
        list_files(str(tmp_path)),
    ):
        assert "error" in json.loads(result), result
    assert "secret" not in list_files(".")
    assert "no line holds" in search_files("key")


def test_tools_search_is_plain_text(repo: Path) -> None:
    (repo / "a.txt").write_text("a.b\naxb\n")
    ws = agent.Workspace(repo.resolve(), [repo.resolve()])
    _, search_files, _, _ = agent.make_tools(ws)

    result = search_files("a.b")

    assert "a.txt:1: a.b" in result and "axb" not in result


def test_shell_drops_key_and_tokens(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AUDIT_API_KEY", "sk-secret")
    monkeypatch.setenv("GH_TOKEN", "gh-secret")
    monkeypatch.setenv("GITHUB_TOKEN", "gh-secret2")
    ws = agent.Workspace(repo.resolve(), [repo.resolve()])
    *_, run_shell = agent.make_tools(ws)

    result = run_shell("env; echo out; echo err >&2; exit 3")

    assert result.startswith("exit 3\n")
    assert "out" in result and "err" in result
    assert "secret" not in result
    assert "PATH=" in result


def test_shell_runs_in_repo(repo: Path) -> None:
    ws = agent.Workspace(repo.resolve(), [repo.resolve()])
    *_, run_shell = agent.make_tools(ws)

    assert "hello" in run_shell("cat README.md")


def test_shell_stops_at_time_limit(repo: Path) -> None:
    ws = agent.Workspace(repo.resolve(), [repo.resolve()], shell_timeout=1)
    *_, run_shell = agent.make_tools(ws)

    assert "ran past 1s" in run_shell("sleep 5")


def test_shell_output_is_cut(repo: Path) -> None:
    ws = agent.Workspace(repo.resolve(), [repo.resolve()])
    *_, run_shell = agent.make_tools(ws)

    result = run_shell(f"head -c {agent.SHELL_OUTPUT_CHARS * 2} /dev/zero | tr '\\0' x")

    assert "[cut at" in result and len(result) < agent.SHELL_OUTPUT_CHARS + 100


def test_model_base_url_and_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic_ai.models.openai import OpenAIChatModel

    monkeypatch.setenv("AUDIT_API_KEY", "sk-test")
    model = agent.build_model("qwen3", "http://localhost:9/v1", "AUDIT_API_KEY")

    assert isinstance(model, OpenAIChatModel)
    assert model.model_name == "qwen3"
    assert str(model.client.base_url).startswith("http://localhost:9/v1")
    assert model.client.api_key == "sk-test"


def test_model_provider_string_passes_through() -> None:
    assert agent.build_model("openai:gpt-5", "", "") == "openai:gpt-5"


def test_model_empty_key_stops_before_any_call(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("AUDIT_API_KEY", "")
    code = agent.main(
        [
            "run",
            "--model",
            "m",
            "--base-url",
            "http://localhost:9/v1",
            "--api-key-env",
            "AUDIT_API_KEY",
            "--repo",
            str(repo),
            "--out",
            str(tmp_path / "o"),
        ]
    )

    assert code == 2
    assert "AUDIT_API_KEY is empty" in capsys.readouterr().err
    assert not (tmp_path / "o").exists()


@pytest.mark.parametrize("name", ["GH_TOKEN", "GITHUB_TOKEN"])
def test_run_refuses_with_token(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    name: str,
) -> None:
    monkeypatch.setenv(name, "t")
    rec = Recorder()

    assert _main(repo, tmp_path, FunctionModel(rec)) == 2
    assert f"refused: {name} is set" in capsys.readouterr().err
    assert rec.prompt is None


def test_run_refuses_with_extraheader(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    subprocess.run(
        [
            "git",
            "config",
            "http.https://github.com/.extraheader",
            "AUTHORIZATION: basic x",
        ],
        cwd=repo,
        check=True,
    )

    assert _main(repo, tmp_path, FunctionModel(Recorder())) == 2
    assert "persist-credentials: false" in capsys.readouterr().err


def test_shell_time_limit_stops_child_processes(repo: Path) -> None:
    ws = agent.Workspace(repo.resolve(), [repo.resolve()], shell_timeout=1)
    *_, run_shell = agent.make_tools(ws)

    result = run_shell("bash -c 'sleep 2; touch late'; true")
    time.sleep(2.5)

    assert "ran past 1s" in result
    assert not (repo / "late").exists()


def test_help_shows_no_empty_defaults() -> None:
    text = agent.parser()._subparsers._group_actions[0].choices["run"].format_help()

    assert "(default: None)" not in text and "(default: [])" not in text
    options = text.split("options:", 1)[1]
    for option in (
        "--base-url",
        "--api-key-env",
        "--repo",
        "--out",
        "--timeout",
        "--shell-timeout",
        "--max-requests",
        "--skills",
        "--prompt",
    ):
        # The option's own line, not a mention wrapped into another's help.
        start = re.search(rf"^  {re.escape(option)}(?=[ \n])", options, re.MULTILINE)
        assert start, option
        block = options[start.end() :].split("\n  --", 1)[0]
        assert "Default" in block or "default" in block, option


# publish ------------------------------------------------------------------


def _gh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    issues: str = "[]",
    fail: bool = False,
) -> Path:
    """Put a gh on PATH that records each call (and any body file) to calls.jsonl."""
    bin_dir = tmp_path / "gh-bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls.jsonl"
    (tmp_path / "issues.json").write_text(issues)
    (bin_dir / "gh").write_text(
        f"#!{sys.executable}\n"
        "import json, sys\n"
        "args = sys.argv[1:]\n"
        "body = None\n"
        "if '--body-file' in args:\n"
        "    body = open(args[args.index('--body-file') + 1]).read()\n"
        f"open({str(calls)!r}, 'a').write(json.dumps({{'args': args, 'body': body}}) + '\\n')\n"
        + ("sys.exit(4)\n" if fail else "")
        + "if args[:2] == ['issue', 'list']:\n"
        f"    print(open({str(tmp_path / 'issues.json')!r}).read())\n"
    )
    (bin_dir / "gh").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    return calls


def _calls(calls: Path) -> list[dict]:
    if not calls.exists():
        return []
    return [json.loads(line) for line in calls.read_text().splitlines()]


def _report_file(tmp_path: Path, severities: list[str]) -> Path:
    report = {
        "summary": "Audit done.",
        "findings": [
            {
                "title": f"concept/{n}",
                "severity": s,
                "path": f".okf/c{n}.md",
                "summary": f"Finding {n}.",
                "claim": f".okf/c{n}.md:1",
                "contradicted_by": [f"src/c{n}.py:1"],
                "fix": f"Fix {n}.",
            }
            for n, s in enumerate(severities)
        ],
        "checked": [],
    }
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    return path


def _publish(repo: Path, report: Path, *extra: str) -> int:
    return agent.main(["publish", str(report), "--repo", str(repo), *extra])


OPEN = '[{"number": 7, "title": "Knowledge audit"}, {"number": 8, "title": "Knowledge audit 2"}]'


def test_publish_below_threshold_posts_nothing(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = _gh(tmp_path, monkeypatch)

    assert _publish(repo, _report_file(tmp_path, ["medium", "info"])) == 0
    made = [c["args"][:2] for c in _calls(calls)]
    assert ["issue", "create"] not in made and ["issue", "edit"] not in made
    assert ["issue", "comment"] not in made and ["issue", "close"] not in made
    assert "no issue" in capsys.readouterr().err


def test_publish_below_threshold_closes_open_issue(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _gh(tmp_path, monkeypatch, OPEN)

    assert (
        _publish(repo, _report_file(tmp_path, ["low"]), "--min-severity", "medium") == 0
    )
    made = _calls(calls)
    comment = next(c for c in made if c["args"][:3] == ["issue", "comment", "7"])
    close = next(c for c in made if c["args"][:3] == ["issue", "close", "7"])
    assert made.index(comment) < made.index(close)
    assert "medium" in " ".join(comment["args"])
    assert not any(
        c["args"][:2] in (["issue", "create"], ["issue", "edit"]) for c in made
    )


def test_publish_posts_new_issue_with_run_link(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _gh(tmp_path, monkeypatch)
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setenv("GITHUB_RUN_ID", "42")

    assert _publish(repo, _report_file(tmp_path, ["high", "info"])) == 0
    create = next(c for c in _calls(calls) if c["args"][:2] == ["issue", "create"])
    assert create["args"][create["args"].index("--title") + 1] == "Knowledge audit"
    assert "concept/0" in create["body"] and "concept/1" in create["body"]
    assert "https://github.com/o/r/actions/runs/42" in create["body"]


def test_publish_posts_edit_and_comment_on_open_issue(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _gh(tmp_path, monkeypatch, OPEN)

    assert (
        _publish(
            repo, _report_file(tmp_path, ["high", "high", "low"]), "--mention", "@alice"
        )
        == 0
    )
    made = _calls(calls)
    edit = next(c for c in made if c["args"][:3] == ["issue", "edit", "7"])
    comment = next(c for c in made if c["args"][:3] == ["issue", "comment", "7"])
    assert "concept/0" in edit["body"]
    text = " ".join(comment["args"])
    assert "@alice" in text and "2 high" in text
    assert not any(c["args"][:2] == ["issue", "create"] for c in made)


def test_publish_posts_custom_title(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _gh(tmp_path, monkeypatch, OPEN)

    assert (
        _publish(
            repo,
            _report_file(tmp_path, ["info"]),
            "--min-severity",
            "info",
            "--title",
            "EA review",
        )
        == 0
    )
    create = next(c for c in _calls(calls) if c["args"][:2] == ["issue", "create"])
    assert create["args"][create["args"].index("--title") + 1] == "EA review"


def _codeowners(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _created_body(calls: Path) -> str:
    return next(c for c in _calls(calls) if c["args"][:2] == ["issue", "create"])[
        "body"
    ]


def test_mention_codeowners_last_star_rule(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _codeowners(
        repo,
        ".github/CODEOWNERS",
        "# owners\n* @old\n/docs/ @docs-team\n*   @alice @org/core  # leads\n",
    )
    _codeowners(repo, "CODEOWNERS", "* @root-file\n")
    calls = _gh(tmp_path, monkeypatch)

    assert _publish(repo, _report_file(tmp_path, ["high"])) == 0
    body = _created_body(calls)
    assert "@alice" in body and "@org/core" in body
    for other in ("@old", "@docs-team", "@root-file"):
        assert other not in body


def test_mention_codeowners_order(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _codeowners(repo, "CODEOWNERS", "* @root-file\n")
    _codeowners(repo, "docs/CODEOWNERS", "* @docs-file\n")
    calls = _gh(tmp_path, monkeypatch)

    assert _publish(repo, _report_file(tmp_path, ["high"])) == 0
    body = _created_body(calls)
    assert "@root-file" in body and "@docs-file" not in body


def test_mention_option_replaces_codeowners(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _codeowners(repo, ".github/CODEOWNERS", "* @alice\n")
    calls = _gh(tmp_path, monkeypatch)

    assert (
        _publish(
            repo,
            _report_file(tmp_path, ["high"]),
            "--mention",
            "bob",
            "--mention",
            "@org/team",
        )
        == 0
    )
    body = _created_body(calls)
    assert "@bob" in body and "@org/team" in body and "@alice" not in body


def test_mention_none_without_owners(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _gh(tmp_path, monkeypatch)

    assert _publish(repo, _report_file(tmp_path, ["high"])) == 0
    body = _created_body(calls)
    assert "cc" not in body.lower().split("## agent report")[0]
    assert "@" not in body.split("## Agent report")[0]


def test_publish_fails_when_gh_fails(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = _gh(tmp_path, monkeypatch, fail=True)

    assert _publish(repo, _report_file(tmp_path, ["high"])) == 1
    assert not any(c["args"][:2] == ["issue", "create"] for c in _calls(calls))
    assert "gh" in capsys.readouterr().err


@pytest.mark.parametrize("content", [None, "not json", '{"summary": "x"}'])
def test_publish_fails_on_bad_report(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    content: str | None,
) -> None:
    calls = _gh(tmp_path, monkeypatch)
    report = tmp_path / "report.json"
    if content is not None:
        report.write_text(content)

    assert _publish(repo, report) == 2
    assert "report" in capsys.readouterr().err
    assert _calls(calls) == []


class Collector:
    """A local OTLP/HTTP receiver that keeps each request's path, headers and span names."""

    def __init__(self) -> None:
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from threading import Thread

        from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
            ExportTraceServiceRequest,
        )

        self.requests: list[tuple[str, dict, list[str]]] = []
        collector = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                body = self.rfile.read(int(self.headers["Content-Length"]))
                message = ExportTraceServiceRequest.FromString(body)
                names = [
                    span.name
                    for resource in message.resource_spans
                    for scope in resource.scope_spans
                    for span in scope.spans
                ]
                collector.requests.append(
                    (self.path, {k.lower(): v for k, v in self.headers.items()}, names)
                )
                self.send_response(200)
                self.end_headers()

            def log_message(self, *args: object) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        Thread(target=self.server.serve_forever, daemon=True).start()

    @property
    def spans(self) -> list[str]:
        return [name for _, _, names in self.requests for name in names]


@pytest.fixture
def collector():
    found = Collector()
    yield found
    found.server.shutdown()


def test_traces_langfuse_sends_run_model_and_tool_spans(
    repo: Path, tmp_path: Path, collector: Collector, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-1")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-2")
    monkeypatch.setenv("LANGFUSE_BASE_URL", collector.url + "/")

    assert _main(repo, tmp_path, FunctionModel(Recorder())) == 0

    path, headers, _ = collector.requests[0]
    assert path == "/api/public/otel/v1/traces"
    assert headers["authorization"] == "Basic cGstbGYtMTpzay1sZi0y"
    spans = collector.spans
    assert any(name.startswith("invoke_agent") for name in spans), spans
    assert any(name.startswith("chat") for name in spans), spans
    assert "execute_tool read_file" in spans


def test_traces_langfuse_default_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk")
    monkeypatch.delenv("LANGFUSE_BASE_URL", raising=False)

    provider = agent.tracer_provider()

    assert provider is not None
    exporter = provider._active_span_processor._span_processors[
        0
    ]._batch_processor._exporter
    assert exporter._endpoint == "https://cloud.langfuse.com/api/public/otel/v1/traces"
    provider.shutdown()


def test_traces_optional_off_without_variables(repo: Path) -> None:
    """No variables: no provider, and OpenTelemetry's SDK and exporter are never
    imported (PydanticAI itself loads the small API package)."""
    env = {k: v for k, v in os.environ.items() if k not in TRACE_VARS}
    code = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('a', {str(SCRIPT)!r})\n"
        "a = importlib.util.module_from_spec(spec); sys.modules['a'] = a\n"
        "spec.loader.exec_module(a)\n"
        "print(a.tracer_provider(), any(m.startswith(('opentelemetry.sdk', "
        "'opentelemetry.exporter')) for m in sys.modules))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert proc.stdout.split() == ["None", "False"]


def test_traces_optional_any_otlp_endpoint(
    repo: Path, tmp_path: Path, collector: Collector, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", collector.url + "/v1/traces"
    )

    assert _main(repo, tmp_path, FunctionModel(Recorder())) == 0

    assert collector.requests[0][0] == "/v1/traces"
    assert "authorization" not in collector.requests[0][1]
    assert any(name.startswith("invoke_agent") for name in collector.spans)


def test_traces_safe_keys_stay_out_of_the_shell(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-secret")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-secret")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", "Authorization=Basic secret")
    ws = agent.Workspace(repo.resolve(), [repo.resolve()])
    *_, run_shell = agent.make_tools(ws)

    result = run_shell("env")

    assert "secret" not in result and "LANGFUSE" not in result and "OTEL" not in result


def test_traces_safe_flushed_on_timeout(
    repo: Path, tmp_path: Path, collector: Collector, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk")
    monkeypatch.setenv("LANGFUSE_BASE_URL", collector.url)

    async def stall(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        import asyncio

        await asyncio.sleep(30)
        raise AssertionError("not reached")

    assert _main(repo, tmp_path, FunctionModel(stall), "--timeout", "1") == 1

    assert any(name.startswith("invoke_agent") for name in collector.spans)
