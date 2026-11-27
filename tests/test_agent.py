"""The CI agent, action/agent.py, run offline with PydanticAI's function model (ADR 0060)."""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
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

#: Cites only README.md, which Recorder reads before it hands the report in.
#: The fields of a report the run sets, not the model.
RUN_FIELDS = ("fixed", "commit", "previous_commit", "fixed_titles")


def _model_part(report: dict) -> dict:
    """``report`` without the fields the run sets, and without each finding's ``earlier``."""
    out = {k: v for k, v in report.items() if k not in RUN_FIELDS}
    out["findings"] = [
        {k: v for k, v in f.items() if k != "earlier"} for f in out["findings"]
    ]
    return out


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
        self.tools: list[str] = []
        self.returns: list[str] = []
        self.retries: list[str] = []

    def __call__(self, messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        """Answer one model request: the next tool call, or the next report."""
        first = messages[0]
        assert isinstance(first, ModelRequest)
        self.instructions = first.instructions
        self.prompt = next(
            str(p.content) for p in first.parts if isinstance(p, UserPromptPart)
        )
        self.tools = [t.name for t in info.function_tools]
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


def _never(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    """A FunctionModel body that fails the test if the model is called at all."""
    raise AssertionError("the model was called")


def _git(cwd: Path, *args: str) -> str:
    """Run git in ``cwd`` with a fixed author and return its output."""
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _page(
    repo: Path, rel: str, sources: list[str], status: str | None = "stable"
) -> None:
    """Write a page at ``rel`` whose front matter names ``sources`` and ``status``."""
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    listed = "\n".join(f'  - resource: "{s}"' for s in sources)
    state = f"status: {status}\n" if status else ""
    path.write_text(f"---\n{state}sources:\n{listed}\n---\n\n# {path.stem}\n")


def _commit_change(repo: Path, *changed: str) -> None:
    """Commit the tree as branch ``base``, then change each of ``changed`` and commit."""
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "base")
    _git(repo, "branch", "base")
    for rel in changed:
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("changed\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "change")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A repository whose last commit changed src/app.py, which one docs page names."""
    path = tmp_path / "repo"
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    (path / "README.md").write_text("hello\nworld\n")
    (path / "src").mkdir()
    (path / "src" / "app.py").write_text("x = 1\n")
    _page(path, "docs/how-to/run-it.md", ["src/app.py"], status=None)
    _commit_change(path, "src/app.py")
    for name in agent.TOKEN_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    return path


def _main(repo: Path, tmp_path: Path, model, *extra: str) -> int:
    """Run ``agent.py run`` on ``repo`` against branch ``base`` with ``model``."""
    return agent.main(
        [
            "run",
            "--model",
            "unused",
            "--base",
            "base",
            "--repo",
            str(repo),
            "--out",
            str(tmp_path / "out"),
            *extra,
        ],
        model=model,
    )


# run ----------------------------------------------------------------------


def test_run_writes_report_files_and_summary(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    summary = tmp_path / "summary.md"
    summary.write_text("")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    assert _main(repo, tmp_path, FunctionModel(Recorder())) == 0

    out = tmp_path / "out"
    report = agent.Report.model_validate_json((out / "report.json").read_text())
    assert _model_part(report.model_dump()) == REPORT
    markdown = (out / "report.md").read_text()
    for finding in REPORT["findings"]:
        assert finding["title"] in markdown
        assert finding["fix"] in markdown
    assert markdown.index("readme/greeting") < markdown.index("readme/style")
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
            "--base",
            "base",
            "--repo",
            str(repo),
            "--out",
            str(tmp_path / "out"),
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
    assert "- `README.md` against itself: `README.md:1-2`" in markdown
    assert markdown.index("readme/style") < markdown.index("Checked (1):")


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
    assert _model_part(report) == REPORT


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


def test_prompt_is_the_shipped_prompt_then_the_pages_in_scope(
    repo: Path, tmp_path: Path
) -> None:
    rec = Recorder()

    assert _main(repo, tmp_path, FunctionModel(rec)) == 0

    assert rec.prompt is not None
    assert rec.prompt.startswith(agent.PROMPT.read_text())
    assert "## Pages in scope" in rec.prompt
    assert "- docs/how-to/run-it.md (docs page): src/app.py" in rec.prompt


def test_system_prompt_names_the_repo_and_no_shell(repo: Path, tmp_path: Path) -> None:
    rec = Recorder()

    assert _main(repo, tmp_path, FunctionModel(rec)) == 0

    assert rec.instructions is not None
    assert str(repo.resolve()) in rec.instructions
    assert "You have no shell." in rec.instructions
    assert "Report only" in rec.instructions


def test_prompt_names_draft_verify_and_summary_ack() -> None:
    text = agent.PROMPT.read_text()

    assert "kmctl new decision --draft" in text
    assert re.search(r"kmctl verify ID .*--by human:", text, re.DOTALL)
    assert "kmctl summary ack" in text


def test_script_has_no_tracing() -> None:
    text = SCRIPT.read_text()
    header = text.split("# ///", 2)[1]

    assert "opentelemetry" not in header
    assert "LANGFUSE" not in text
    assert "Instrumentation" not in text


# scope --------------------------------------------------------------------


def test_scope_takes_every_page_kind(repo: Path) -> None:
    _page(repo, ".okf/decisions/0001-stable.md", ["lib/core.py"])
    _page(repo, ".okf/decisions/0002-draft.md", ["lib/core.py"], status="draft")
    _page(repo, ".okf/architecture/overview.md", ["lib/core.py"])
    _page(repo, "docs/reference/core.md", ["lib/core.py"], status=None)
    _page(repo, ".okf/decisions/0003-untouched.md", ["lib/other.py"])
    (repo / "lib").mkdir()
    (repo / "lib" / "other.py").write_text("y = 1\n")
    _git(repo, "branch", "-D", "base")
    _commit_change(repo, "lib/core.py")

    pages = agent.changed_pages(repo, "base")

    assert {(p.path, p.status, tuple(p.files)) for p in pages} == {
        (".okf/decisions/0001-stable.md", "stable", ("lib/core.py",)),
        (".okf/decisions/0002-draft.md", "draft", ("lib/core.py",)),
        (".okf/architecture/overview.md", "stable", ("lib/core.py",)),
        ("docs/reference/core.md", "docs page", ("lib/core.py",)),
    }


def test_scope_leaves_out_superseded_handoffs_log_and_urls(repo: Path) -> None:
    _page(repo, ".okf/decisions/0001-old.md", ["lib/core.py"], status="superseded")
    _page(repo, ".okf/decisions/0002-gone.md", ["lib/core.py"], status="deprecated")
    _page(repo, ".okf/handoffs/note.md", ["lib/core.py"])
    _page(repo, ".okf/log.md", ["lib/core.py"])
    _page(repo, ".okf/decisions/index.md", ["lib/core.py"])
    _page(repo, ".okf/decisions/0003-url.md", ["https://example.com/lib/core.py"])
    _git(repo, "branch", "-D", "base")
    _commit_change(repo, "lib/core.py")

    assert agent.changed_pages(repo, "base") == []


def test_scope_matches_folder_source_as_prefix(repo: Path) -> None:
    _page(repo, ".okf/decisions/0001-folder.md", ["pkg/lib/"])
    _page(repo, ".okf/decisions/0002-bare-folder.md", ["pkg/lib"])
    _page(repo, ".okf/decisions/0003-near-miss.md", ["pkg/li"])
    _git(repo, "branch", "-D", "base")
    _commit_change(repo, "pkg/lib/util.py")

    pages = {p.path: p.files for p in agent.changed_pages(repo, "base")}

    assert pages == {
        ".okf/decisions/0001-folder.md": ["pkg/lib/util.py"],
        ".okf/decisions/0002-bare-folder.md": ["pkg/lib/util.py"],
    }


def test_scope_takes_a_page_whose_source_was_renamed(repo: Path) -> None:
    """A page that still names a moved file's old path is the one most likely outdated."""
    (repo / "lib").mkdir()
    (repo / "lib" / "old.py").write_text("".join(f"line {n}\n" for n in range(20)))
    _page(repo, "docs/reference/old.md", ["lib/old.py"], status=None)
    _git(repo, "branch", "-D", "base")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "branch", "base")
    _git(repo, "mv", "lib/old.py", "lib/new.py")
    _git(repo, "commit", "-q", "-m", "move")

    pages = {p.path: p.files for p in agent.changed_pages(repo, "base")}

    assert pages == {"docs/reference/old.md": ["lib/old.py"]}


def test_nothing_in_scope_calls_no_model(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    summary = tmp_path / "summary.md"
    summary.write_text("")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    _git(repo, "branch", "-D", "base")
    _commit_change(repo, "unrelated.txt")

    assert _main(repo, tmp_path, FunctionModel(_never)) == 0

    report = json.loads((tmp_path / "out" / "report.json").read_text())
    assert report["findings"] == [] and report["checked"] == []
    assert "No page under .okf/ or docs/ names a file" in report["summary"]
    assert "nothing was reread" in summary.read_text()


def test_scope_with_an_unknown_base_exits_2(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = agent.main(
        ["run", "--model", "unused", "--base", "nope", "--repo", str(repo)],
        model=FunctionModel(_never),
    )

    assert code == 2
    assert "git diff" in capsys.readouterr().err


# tools --------------------------------------------------------------------


def test_tools_are_read_only(repo: Path, tmp_path: Path) -> None:
    rec = Recorder()

    assert _main(repo, tmp_path, FunctionModel(rec)) == 0

    assert rec.tools == ["read_file", "search_files", "list_files"]
    ws = agent.Workspace(repo.resolve(), [repo.resolve()])
    assert [t.__name__ for t in agent.make_tools(ws)] == rec.tools


def test_tools_read_search_and_list_the_repo(repo: Path, tmp_path: Path) -> None:
    rec = Recorder(
        [
            ("read_file", {"path": "README.md"}),
            ("search_files", {"pattern": "hello"}),
            ("list_files", {"path": "src"}),
        ]
    )

    assert _main(repo, tmp_path, FunctionModel(rec)) == 0

    readme, search, listing, _ = rec.returns
    assert "1|hello" in readme
    assert "README.md:1: hello" in search
    assert "src/app.py" in listing


def test_tools_refuse_paths_outside_the_repo(repo: Path, tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("key\n")
    (repo / "link.txt").symlink_to(secret)
    (repo / "linkdir").symlink_to(tmp_path)
    ws = agent.Workspace(repo.resolve(), [repo.resolve()])
    read_file, search_files, list_files = agent.make_tools(ws)

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
    _, search_files, _ = agent.make_tools(ws)

    result = search_files("a.b")

    assert "a.txt:1: a.b" in result and "axb" not in result


# model and refusals -------------------------------------------------------


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
            "--base",
            "base",
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

    assert _main(repo, tmp_path, FunctionModel(_never)) == 2
    assert f"refused: {name} is set" in capsys.readouterr().err


def test_run_refuses_a_checkout_with_a_token_header(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """read_file reaches .git/config, so a checkout that kept its token is refused."""
    _git(
        repo, "config", "http.https://github.com/.extraheader", "AUTHORIZATION: basic x"
    )
    ws = agent.Workspace(repo.resolve(), [repo.resolve()])
    read_file, _, _ = agent.make_tools(ws)
    assert "AUTHORIZATION" in read_file(".git/config")

    assert _main(repo, tmp_path, FunctionModel(_never)) == 2
    assert "persist-credentials: false" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


# command line -------------------------------------------------------------


def _subparser(name: str) -> argparse.ArgumentParser:
    """Return the ``run`` or ``publish`` subparser."""
    return agent.parser()._subparsers._group_actions[0].choices[name]


def _options(name: str) -> set[str]:
    """Return the long options the ``name`` subcommand takes, --help aside."""
    return {
        opt
        for action in _subparser(name)._actions
        for opt in action.option_strings
        if opt.startswith("--") and opt != "--help"
    }


def test_run_takes_only_the_pr_options() -> None:
    assert _options("run") == {
        "--model",
        "--base-url",
        "--api-key-env",
        "--base",
        "--head",
        "--previous",
        "--repo",
        "--out",
        "--timeout",
        "--max-requests",
    }
    with pytest.raises(SystemExit):
        agent.parser().parse_args(["run", "--model", "m"])
    for removed in ("--audit", "--prompt", "--skills", "--context", "--no-shell"):
        with pytest.raises(SystemExit):
            agent.parser().parse_args(
                ["run", "--model", "m", "--base", "b", removed, "x"]
            )


def test_publish_takes_only_the_pr_options() -> None:
    assert _options("publish") == {"--pr", "--min-severity", "--title"}
    with pytest.raises(SystemExit):
        agent.parser().parse_args(["publish", "report.json"])


def test_help_shows_no_empty_defaults() -> None:
    text = _subparser("run").format_help()

    assert "(default: None)" not in text and "(default: [])" not in text
    options = text.split("options:", 1)[1]
    for option in (
        "--base-url",
        "--api-key-env",
        "--repo",
        "--out",
        "--timeout",
        "--max-requests",
    ):
        # The option's own line, not a mention wrapped into another's help.
        start = re.search(rf"^  {re.escape(option)}(?=[ \n])", options, re.MULTILINE)
        assert start, option
        block = options[start.end() :].split("\n  --", 1)[0]
        assert "Default" in block or "default" in block, option


# publish ------------------------------------------------------------------


def _gh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fail: bool = False) -> Path:
    """Put a gh on PATH that records each call to calls.jsonl, and fails if asked."""
    bin_dir = tmp_path / "gh-bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls.jsonl"
    (bin_dir / "gh").write_text(
        f"#!{sys.executable}\n"
        "import json, sys\n"
        f"open({str(calls)!r}, 'a').write(json.dumps(sys.argv[1:]) + '\\n')\n"
        + ("sys.exit(4)\n" if fail else "print('[]')\n")
    )
    (bin_dir / "gh").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    return calls


def _calls(calls: Path) -> list[list[str]]:
    """Return the gh calls recorded in ``calls``."""
    if not calls.exists():
        return []
    return [json.loads(line) for line in calls.read_text().splitlines()]


def _report_file(tmp_path: Path, severities: list[str]) -> Path:
    """Write a report with one finding per severity and return its path."""
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


def _publish(report: Path, *extra: str) -> int:
    """Run ``agent.py publish`` on ``report`` for pull request 12."""
    return agent.main(["publish", str(report), "--pr", "12", *extra])


def _pr_gh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a gh on PATH that keeps a pull request's comments in comments.json."""
    bin_dir = tmp_path / "pr-gh-bin"
    bin_dir.mkdir()
    store = tmp_path / "comments.json"
    store.write_text("[]")
    (bin_dir / "gh").write_text(
        f"#!{sys.executable}\n"
        "import json, sys\n"
        "args = sys.argv[1:]\n"
        f"store = {str(store)!r}\n"
        "comments = json.load(open(store))\n"
        "def body_of(flag, prefix=''):\n"
        "    value = args[args.index(flag) + 1]\n"
        "    return open(value[len(prefix):]).read()\n"
        "if args[:2] == ['pr', 'comment']:\n"
        "    comments.append({'id': len(comments) + 1, 'body': body_of('--body-file')})\n"
        "elif args[0] == 'api' and '-X' in args and args[args.index('-X') + 1] == 'PATCH':\n"
        "    cid = int(next(a for a in args if '/issues/comments/' in a).rsplit('/', 1)[1])\n"
        "    for c in comments:\n"
        "        if c['id'] == cid:\n"
        "            c['body'] = body_of('-F', 'body=@')\n"
        "elif args[0] == 'api':\n"
        "    print(json.dumps(comments))\n"
        "json.dump(comments, open(store, 'w'))\n"
    )
    (bin_dir / "gh").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    return store


def test_publish_pr_creates_then_replaces_comment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _pr_gh(tmp_path, monkeypatch)
    first = _report_file(tmp_path, ["high"])

    assert _publish(first) == 0
    comments = json.loads(store.read_text())
    assert len(comments) == 1 and "concept/0" in comments[0]["body"]

    second = tmp_path / "second.json"
    report = json.loads(first.read_text())
    report["findings"][0]["title"] = "concept/changed"
    second.write_text(json.dumps(report))
    assert _publish(second) == 0
    comments = json.loads(store.read_text())
    assert len(comments) == 1
    assert "concept/changed" in comments[0]["body"]
    assert "concept/0" not in comments[0]["body"]


def test_publish_default_threshold_posts_low_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no --min-severity, a report of only low findings is posted, every finding listed."""
    store = _pr_gh(tmp_path, monkeypatch)

    assert _publish(_report_file(tmp_path, ["low", "low"])) == 0

    (comment,) = json.loads(store.read_text())
    assert "concept/0" in comment["body"] and "concept/1" in comment["body"]


def test_system_prompt_rates_a_contradicted_claim_high() -> None:
    """The rubric rates a claim the code contradicts high, and keeps medium for probably wrong."""
    rubric = " ".join(agent.SYSTEM_PROMPT.split())

    assert (
        "high for a claim the code contradicts that would lead a reader to act wrongly"
        in rubric
    )
    assert (
        "low for a claim that is wrong but would still leave a reader acting correctly"
        in rubric
    )
    assert (
        "medium for a claim that is probably wrong, or that you could not check"
        in rubric
    )
    assert "something wrong that someone must fix" not in rubric


FIXTURE = ROOT / "tests" / "fixtures" / "agent-report-46024647635.json"


def _visible(markdown: str) -> str:
    """The part of a rendered report above its folded evidence."""
    return markdown.split("<details>", 1)[0]


def test_render_is_compact_on_a_live_report() -> None:
    """The live run that posted a 14 KB comment renders to a short one, with nothing lost."""
    report = agent.Report.model_validate_json(FIXTURE.read_text())

    markdown = agent.render(report)
    visible = _visible(markdown)

    assert len(visible.encode()) < 3000
    assert visible.startswith("**4 of 9 pages need a look** · 3 medium · 3 low\n")
    assert "##" not in markdown
    bullets = [line for line in visible.splitlines() if line.startswith("- ")]
    assert len(bullets) == len(report.findings)
    assert "(ADR 0060:33-34)" in bullets[0]
    assert visible.count("Still hold: ") == 1
    assert "ADR 0025" in visible.split("Still hold: ")[1]
    folded = markdown.split("<details>", 1)[1]
    for finding in report.findings:
        assert f"Fix: {finding.fix}" in folded
        assert finding.fix not in visible
        for cite in finding.contradicted_by:
            assert f"`{cite}`" in folded and cite not in visible
    assert "kmctl verify .okf/decisions/0025-" in folded
    assert "kmctl verify" not in visible.replace("see `kmctl verify` below", "")


def test_render_names_pages_short() -> None:
    """A decision is ADR NNNN:line, another page its file name; a checked note is dropped."""
    assert agent.short_name(".okf/decisions/0060-x-y.md:18-20") == "ADR 0060:18-20"
    assert agent.short_name("docs/how-to/run-it.md:3") == "run-it:3"
    assert agent.short_name(".okf/architecture/overview.md") == "overview"
    assert agent.page_path("docs/how-to/run-it.md (added: the change rewrites it)") == (
        "docs/how-to/run-it.md"
    )
    report = agent.Report(
        summary="One page.",
        checked=[
            agent.Checked(
                subject="docs/how-to/run-it.md (added: why)",
                against="src/app.py",
                evidence=["docs/how-to/run-it.md:1"],
            ),
            agent.Checked(subject="src/app.py", against="itself", evidence=[]),
        ],
        findings=[],
    )

    visible = _visible(agent.render(report))

    assert "Still hold: run-it." in visible
    assert "added: why" not in visible and "app" not in visible


def test_render_counts_pages_only() -> None:
    """The page count leaves out a checked file that is not a page and adds a finding's page."""
    finding = agent.Finding(
        title="t",
        severity="high",
        path="docs/how-to/x.md",
        summary="S.",
        claim="docs/how-to/x.md:1",
        contradicted_by=["src/x.py:1"],
        fix="F.",
    )
    held = agent.render(
        agent.Report(
            summary="S.",
            checked=[
                agent.Checked(subject=s, against="x", evidence=[])
                for s in ("README.md", "docs/how-to/a.md", "docs/how-to/b.md")
            ],
            findings=[],
        )
    )
    assert held.startswith("**All 2 pages hold**")

    unchecked = agent.render(agent.Report(summary="S.", checked=[], findings=[finding]))
    assert unchecked.startswith("**1 of 1 pages need a look**")


def test_render_short_names_keep_abbreviations_and_folders() -> None:
    """A sentence does not end after "e.g.", and two pages with one file name keep their folders."""
    assert agent.first_sentence("Say e.g. `x` here. Then more.") == "Say e.g. `x` here."
    held = agent.render(
        agent.Report(
            summary="S.",
            checked=[
                agent.Checked(subject=s, against="x", evidence=[])
                for s in ("docs/how-to/run.md", "docs/reference/run.md")
            ],
            findings=[],
        )
    )
    assert "Still hold: how-to/run, reference/run." in held


def test_render_empty_and_all_hold_reports() -> None:
    """An empty report has no holds line or verify command; an all-hold one names them all."""
    empty = agent.render(
        agent.Report(summary="Nothing in scope.", checked=[], findings=[])
    )
    assert empty == "**No page in scope**\n\nNothing in scope.\n"

    held = agent.render(
        agent.Report(
            summary="Both hold.",
            checked=[
                agent.Checked(subject=p, against="src/app.py", evidence=[])
                for p in (".okf/decisions/0001-a.md", "docs/how-to/b.md")
            ],
            findings=[],
        )
    )
    assert held.startswith("**All 2 pages hold**\n")
    assert "Still hold: ADR 0001, b." in held
    assert (
        "kmctl verify .okf/decisions/0001-a.md docs/how-to/b.md --by human:<you>"
        in held
    )
    assert "\n\n\n" not in held


def test_prompt_asks_for_short_fields() -> None:
    """The prompt asks for one-sentence fields, a bare path, and no holds list in the summary."""
    text = " ".join(agent.PROMPT.read_text().split())

    assert "summary in one sentence, fix in one sentence" in text
    assert "summary: one or two sentences" in text
    assert "Do not list the pages that hold or a command" in text
    assert "subject is the page's path and nothing else" in text
    assert "in its checked entry's against" in text
    assert "End the summary with the pages that still hold" not in text


def test_tutorial_quotes_the_empty_report(repo: Path, tmp_path: Path) -> None:
    """The tutorial's empty-report output is what the agent prints today."""
    page = (
        ROOT / "docs" / "tutorials" / "audit-your-repository-with-the-agent.md"
    ).read_text()
    empty = agent.render(
        agent.Report(
            summary=(
                "No page under .okf/ or docs/ names a file this change touched "
                "(compared with main) in its sources, so nothing was reread."
            ),
            checked=[],
            findings=[],
        )
    )

    assert f"```\n{empty}" in page
    assert "## Agent report" not in page


def test_publish_lists_only_findings_at_or_above_the_threshold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Under --min-severity medium the low finding, its page and its count stay out."""
    store = _pr_gh(tmp_path, monkeypatch)
    report = {
        "summary": "Two pages drifted.",
        "checked": [
            {"subject": ".okf/decisions/0001-a.md", "against": "x", "evidence": []},
            {"subject": ".okf/decisions/0002-b.md", "against": "x", "evidence": []},
            {"subject": ".okf/decisions/0003-c.md", "against": "x", "evidence": []},
        ],
        "findings": [
            {
                "title": f"t-{s}",
                "severity": s,
                "path": f".okf/decisions/{n}.md",
                "summary": f"S {s}.",
                "claim": f".okf/decisions/{n}.md:1",
                "contradicted_by": ["src/x.py:1"],
                "fix": f"F {s}.",
            }
            for s, n in (("medium", "0001-a"), ("low", "0002-b"))
        ],
    }
    path = tmp_path / "r.json"
    path.write_text(json.dumps(report))

    assert _publish(path, "--min-severity", "medium") == 0

    (comment,) = json.loads(store.read_text())
    body = comment["body"]
    assert "t-medium" in body and "t-low" not in body and "F low." not in body
    assert "**1 of 3 pages need a look** · 1 medium\n" in body
    assert "1 finding(s) below medium left out." in body
    assert "Still hold: ADR 0003." in body
    assert "ADR 0002" not in body

    report["findings"] = [report["findings"][1]]
    path.write_text(json.dumps(report))
    assert _publish(path, "--min-severity", "medium") == 0
    (comment,) = json.loads(store.read_text())
    assert (
        "found nothing at or above medium; 1 finding(s) below it left out."
        in comment["body"]
    )


def test_publish_below_threshold_posts_nothing_new(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store = _pr_gh(tmp_path, monkeypatch)

    assert _publish(_report_file(tmp_path, ["medium"]), "--min-severity", "high") == 0
    assert json.loads(store.read_text()) == []
    assert "no comment was written" in capsys.readouterr().err


def test_publish_below_threshold_replaces_an_earlier_comment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _pr_gh(tmp_path, monkeypatch)
    assert _publish(_report_file(tmp_path, ["high"])) == 0

    assert _publish(_report_file(tmp_path, ["low"]), "--min-severity", "high") == 0

    (comment,) = json.loads(store.read_text())
    assert "found nothing at or above high" in comment["body"]


def test_publish_custom_title_marks_the_comment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _pr_gh(tmp_path, monkeypatch)

    assert _publish(_report_file(tmp_path, ["high"]), "--title", "Docs reread") == 0

    (comment,) = json.loads(store.read_text())
    assert comment["body"].startswith(
        agent.COMMENT_MARK.format(title="Docs reread") + "\n## Docs reread"
    )


def test_publish_pr_ignores_a_person_quoting_the_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _pr_gh(tmp_path, monkeypatch)
    mark = agent.COMMENT_MARK.format(title="Knowledge audit")
    quoted = f"> {mark}\n> ## Knowledge audit\n\nIs this finding right?"
    store.write_text(json.dumps([{"id": 1, "body": quoted}]))
    report = _report_file(tmp_path, ["high"])

    assert _publish(report) == 0
    assert _publish(report) == 0

    comments = json.loads(store.read_text())
    assert comments[0] == {"id": 1, "body": quoted}
    assert len(comments) == 2
    assert comments[1]["body"].startswith(mark)


def test_publish_fails_when_gh_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = _gh(tmp_path, monkeypatch, fail=True)

    assert _publish(_report_file(tmp_path, ["high"])) == 1
    assert not any(c[:2] == ["pr", "comment"] for c in _calls(calls))
    assert "gh" in capsys.readouterr().err


def test_publish_without_report_posts_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = _gh(tmp_path, monkeypatch)

    assert _publish(tmp_path / "missing" / "report.json") == 0
    assert _calls(calls) == []
    assert "no report" in capsys.readouterr().err


@pytest.mark.parametrize("content", ["not json", '{"summary": "x"}'])
def test_publish_fails_on_bad_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    content: str,
) -> None:
    calls = _gh(tmp_path, monkeypatch)
    report = tmp_path / "report.json"
    report.write_text(content)

    assert _publish(report) == 2
    assert "report" in capsys.readouterr().err
    assert _calls(calls) == []


# state: the previous report -------------------------------------------------


def _finding(title: str, page: str, earlier: str | None = None) -> dict:
    """A finding on ``page``'s line 1, contradicted by README.md:1, which runs read."""
    return {
        "title": title,
        "severity": "medium",
        "path": page,
        "summary": f"{title} is wrong.",
        "claim": f"{page}:1",
        "contradicted_by": ["README.md:1"],
        "fix": "Fix it.",
        "earlier": earlier,
    }


@pytest.fixture
def stateful(repo: Path) -> tuple[Path, str]:
    """A repo with two docs pages; the last commit touched only run-it.md's source."""
    _page(repo, "docs/how-to/other.md", ["src/other.py"], status=None)
    (repo / "src" / "other.py").write_text("y = 1\n")
    _git(repo, "branch", "-D", "base")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "branch", "base")
    (repo / "src" / "other.py").write_text("y = 2\n")
    _git(repo, "commit", "-qam", "touch other")
    previous_head = _git(repo, "rev-parse", "HEAD").strip()
    (repo / "src" / "app.py").write_text("x = 3\n")
    _git(repo, "commit", "-qam", "touch app")
    return repo, previous_head


#: The fake model reads both docs pages first, so findings may cite their line 1.
READ_PAGES = [
    ("read_file", {"path": "docs/how-to/run-it.md"}),
    ("read_file", {"path": "docs/how-to/other.md"}),
]


def _previous_file(tmp_path: Path, commit: str, findings: list[dict]) -> Path:
    """Write a previous report.json made at ``commit`` and return its path."""
    path = tmp_path / "previous.json"
    path.write_text(
        json.dumps(
            {
                "summary": "Before.",
                "checked": [],
                "findings": findings,
                "commit": commit,
            }
        )
    )
    return path


def _report(findings: list[dict], fixed: list[str]) -> dict:
    """A model report citing README.md, with ``findings`` and ``fixed`` ids."""
    return {
        "summary": "After.",
        "checked": [
            {"subject": "README.md", "against": "x", "evidence": ["README.md:1"]}
        ],
        "findings": findings,
        "fixed": fixed,
    }


def test_previous_report_goes_into_the_prompt(
    stateful: tuple[Path, str], tmp_path: Path
) -> None:
    repo, prev = stateful
    previous = _previous_file(
        tmp_path, prev, [_finding("old one", "docs/how-to/run-it.md")]
    )
    rec = Recorder(READ_PAGES, reports=[_report([], ["e1"])])

    assert _main(repo, tmp_path, FunctionModel(rec), "--previous", str(previous)) == 0

    assert rec.prompt is not None
    assert "## Earlier findings" in rec.prompt
    assert f"at commit {prev}" in rec.prompt
    assert "- e1 [medium] old one (docs/how-to/run-it.md:1)" in rec.prompt
    assert "Pages changed since that commit: docs/how-to/run-it.md" in rec.prompt


def test_validator_requires_every_earlier_finding_answered(
    stateful: tuple[Path, str], tmp_path: Path
) -> None:
    repo, prev = stateful
    previous = _previous_file(
        tmp_path,
        prev,
        [
            _finding("a", "docs/how-to/run-it.md"),
            _finding("b", "docs/how-to/run-it.md"),
        ],
    )
    rec = Recorder(
        READ_PAGES,
        reports=[
            _report([], ["e1"]),
            _report([_finding("b", "docs/how-to/run-it.md", earlier="e2")], ["e1"]),
        ],
    )

    assert _main(repo, tmp_path, FunctionModel(rec), "--previous", str(previous)) == 0

    (retry,) = rec.retries
    assert "e2 (b): neither kept as a finding's earlier nor listed in fixed" in retry
    report = json.loads((tmp_path / "out" / "report.json").read_text())
    assert report["fixed"] == ["e1"] and report["fixed_titles"] == ["a"]


def test_validator_drops_new_findings_on_unchanged_pages(
    stateful: tuple[Path, str], tmp_path: Path
) -> None:
    repo, prev = stateful
    previous = _previous_file(tmp_path, prev, [])
    rec = Recorder(
        READ_PAGES,
        reports=[
            _report(
                [
                    _finding("on unchanged", "docs/how-to/other.md"),
                    _finding("on changed", "docs/how-to/run-it.md"),
                ],
                [],
            ),
            _report([_finding("on changed", "docs/how-to/run-it.md")], []),
        ],
    )

    assert _main(repo, tmp_path, FunctionModel(rec), "--previous", str(previous)) == 0

    (retry,) = rec.retries
    assert "on unchanged: a new finding on docs/how-to/other.md" in retry
    assert "on changed" not in retry
    report = json.loads((tmp_path / "out" / "report.json").read_text())
    assert [f["title"] for f in report["findings"]] == ["on changed"]


@pytest.mark.parametrize("commit", ["", "0" * 40])
def test_previous_commit_missing_from_history_is_ignored(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    commit: str,
) -> None:
    previous = _previous_file(
        tmp_path, commit, [_finding("x", "docs/how-to/run-it.md")]
    )
    rec = Recorder()

    assert _main(repo, tmp_path, FunctionModel(rec), "--previous", str(previous)) == 0

    assert rec.prompt is not None and "Earlier findings" not in rec.prompt
    assert "ignored the previous report" in capsys.readouterr().err
    report = json.loads((tmp_path / "out" / "report.json").read_text())
    assert "ignored the previous report" in report["summary"]
    assert report["previous_commit"] == ""


def test_report_records_commit_and_renders_the_delta(
    stateful: tuple[Path, str], tmp_path: Path
) -> None:
    repo, prev = stateful
    head = _git(repo, "rev-parse", "HEAD").strip()
    previous = _previous_file(
        tmp_path,
        prev,
        [
            _finding("gone", "docs/how-to/run-it.md"),
            _finding("stays", "docs/how-to/run-it.md"),
        ],
    )
    rec = Recorder(
        READ_PAGES,
        reports=[
            _report(
                [
                    _finding("stays", "docs/how-to/run-it.md", earlier="e2"),
                    _finding("fresh", "docs/how-to/run-it.md"),
                ],
                ["e1"],
            )
        ],
    )

    assert (
        _main(
            repo,
            tmp_path,
            FunctionModel(rec),
            "--previous",
            str(previous),
            "--head",
            head,
        )
        == 0
    )

    report = json.loads((tmp_path / "out" / "report.json").read_text())
    assert report["commit"] == head != prev
    assert report["previous_commit"] == prev and report["fixed"] == ["e1"]
    markdown = (tmp_path / "out" / "report.md").read_text()
    assert "Since the last run: 1 fixed · 1 still open · 1 new" in markdown
    assert "Fixed: gone." in markdown
    assert "**stays** (still open)" in markdown
    assert "**fresh** (" in markdown


def test_run_without_previous_renders_as_before(repo: Path, tmp_path: Path) -> None:
    head = _git(repo, "rev-parse", "HEAD").strip()

    assert _main(repo, tmp_path, FunctionModel(Recorder())) == 0

    report = json.loads((tmp_path / "out" / "report.json").read_text())
    assert report["commit"] == head and report["previous_commit"] == ""
    assert "Since the last run" not in (tmp_path / "out" / "report.md").read_text()

    base = _git(repo, "rev-parse", "base").strip()
    assert _main(repo, tmp_path, FunctionModel(Recorder()), "--head", base) == 0
    report = json.loads((tmp_path / "out" / "report.json").read_text())
    assert report["commit"] == base != head


def _prev_gh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, comments: list) -> Path:
    """Put a gh on PATH that lists ``comments`` and fakes ``run download``."""
    bin_dir = tmp_path / "prev-gh-bin"
    bin_dir.mkdir()
    calls = tmp_path / "prev-calls.jsonl"
    (bin_dir / "gh").write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "args = sys.argv[1:]\n"
        f"open({str(calls)!r}, 'a').write(json.dumps(args) + '\\n')\n"
        "if args[0] == 'api':\n"
        f"    print(json.dumps([{json.dumps(comments)}]))\n"
        "elif args[:2] == ['run', 'download']:\n"
        "    out = args[args.index('-D') + 1]\n"
        "    os.makedirs(out, exist_ok=True)\n"
        "    open(os.path.join(out, 'report.json'), 'w').write(json.dumps({'run': args[2]}))\n"
    )
    (bin_dir / "gh").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    return calls


def test_previous_downloads_the_linked_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mark = agent.COMMENT_MARK.format(title="Knowledge audit")
    body = f"{mark}\n## Knowledge audit\n\nRun and its report artifact: https://github.com/o/r/actions/runs/4242\n"
    calls = _prev_gh(tmp_path, monkeypatch, [{"id": 1, "body": body}])
    out = tmp_path / "prev"

    assert agent.main(["previous", "--pr", "12", "--out", str(out)]) == 0

    assert json.loads((out / "report.json").read_text()) == {"run": "4242"}
    assert ["run", "download", "4242", "-n", "agent-report", "-D", str(out)] in [
        json.loads(line) for line in calls.read_text().splitlines()
    ]


@pytest.mark.parametrize(
    "comments",
    [[], [{"id": 1, "body": "<!-- kmctl-audit: Knowledge audit -->\nno link here"}]],
)
def test_previous_writes_nothing_without_a_comment_or_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, comments: list
) -> None:
    calls = _prev_gh(tmp_path, monkeypatch, comments)
    out = tmp_path / "prev"

    assert agent.main(["previous", "--pr", "12", "--out", str(out)]) == 0

    assert not out.exists()
    assert not any(
        json.loads(line)[:2] == ["run", "download"]
        for line in calls.read_text().splitlines()
    )
