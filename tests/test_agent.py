"""The standalone CI agent, action/agent.py, run offline with PydanticAI's function model (ADR 0017)."""

import importlib.util
import json
import os
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

REPORT = {
    "summary": "One page drifted.",
    "findings": [
        {
            "title": "architecture/overview",
            "severity": "high",
            "path": ".okf/architecture/overview.md",
            "summary": "It names a script that is gone.",
            "evidence": [".okf/architecture/overview.md:12"],
        },
        {
            "title": "decisions/0001",
            "severity": "info",
            "path": ".okf/decisions/0001.md",
            "summary": "Still holds.",
            "evidence": ["src/app.py:3"],
        },
    ],
}


class Recorder:
    """A FunctionModel body that records what the model saw and returns REPORT."""

    def __init__(self, calls: list[tuple[str, dict]] | None = None) -> None:
        self.calls = list(calls or [])
        self.instructions: str | None = None
        self.prompt: str | None = None
        self.returns: list[str] = []

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
        if self.calls:
            name, args = self.calls.pop(0)
            return ModelResponse(parts=[ToolCallPart(name, args)])
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, REPORT)])


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
    for name in agent.TOKEN_VARS:
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
        assert finding["evidence"][0] in markdown
    assert markdown.index("high") < markdown.index("| info")
    assert json.loads((out / "transcript.json").read_text())
    assert summary.read_text() == markdown


def test_run_writes_with_cli_test_model(repo: Path, tmp_path: Path) -> None:
    """`--model test` runs end to end through the real command line, offline."""
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

    assert proc.returncode == 0, proc.stderr
    agent.Report.model_validate_json((tmp_path / "out" / "report.json").read_text())


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


def test_default_prompt_is_the_audit(repo: Path, tmp_path: Path) -> None:
    rec = Recorder()

    assert _main(repo, tmp_path, FunctionModel(rec)) == 0
    assert rec.prompt and "audit skill" in rec.prompt
    assert agent.AUDITOR.read_text() in rec.prompt


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
    readme, ea, skill_md, search, listing = rec.returns
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
        block = options.split(f"  {option} ", 1)[1].split("\n  --", 1)[0]
        assert "Default" in block or "default" in block, option
