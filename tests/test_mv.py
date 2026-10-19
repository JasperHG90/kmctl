import json
import subprocess
from pathlib import Path

import pytest
from conftest import okf_validate
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.okf import front_matter

OLD_ID = "decisions/0003-use-a-stream"
NEW_ID = "decisions/0004-use-a-stream"
OLD = f".okf/{OLD_ID}.md"
NEW = f".okf/{NEW_ID}.md"
DOC = "docs/how-to/pick-a-queue.md"


def _invoke(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _repo(root: Path) -> Path:
    """A bundle with decisions 0001-0003, links to 0003 from .okf/ and docs/, and a mention outside them."""
    assert _invoke("init", "--path", str(root)).exit_code == 0
    for title in ("Use a queue", "Use a stream"):
        result = _invoke(
            "new", "decision", title, "--description", f"{title}.", "--path", str(root)
        )
        assert result.exit_code == 0, result.output
    assert (
        _invoke("new", "doc", "how-to", "Pick a queue", "--path", str(root)).exit_code
        == 0
    )
    queue = root / ".okf/decisions/0002-use-a-queue.md"
    queue.write_text(
        queue.read_text() + "\nSee [ADR 0003](0003-use-a-stream.md#context), and "
        "[the stream](/decisions/0003-use-a-stream.md).\n"
    )
    doc = root / DOC
    doc.write_text(
        doc.read_text()
        + "\nRead [the stream record](../../.okf/decisions/0003-use-a-stream.md).\n"
    )
    summary = root / ".okf/summary.md"
    summary.write_text(
        summary.read_text().replace(
            "tags: [summary]\n",
            "tags: [summary]\nchecked:\n  at: 2026-10-19T10:00:00Z\n  against:\n"
            f"    - decisions/0002-use-a-queue\n    - {OLD_ID}\n",
        )
    )
    (root / "AGENTS.md").write_text(
        "# Agents\n\nThe stream rule is .okf/decisions/0003-use-a-stream.md.\n"
    )
    return root


def _mv(root: Path, old: str = OLD_ID, new: str = NEW_ID, *flags: str) -> Result:
    return _invoke("mv", old, new, "--path", str(root), *flags)


def test_mv_renumbers_a_decision(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = _mv(root)

    assert result.exit_code == 0, result.output
    assert not (root / OLD).exists()
    assert front_matter(root / NEW)["title"] == "ADR 0004: Use a stream"
    assert "\n# ADR 0004: Use a stream\n" in (root / NEW).read_text()
    index = (root / ".okf/decisions/index.md").read_text().splitlines()
    assert "- [ADR 0004: Use a stream](0004-use-a-stream.md): Use a stream." in index
    assert "0003-use-a-stream" not in "\n".join(index)


def test_mv_rewrites_links_in_okf_and_docs(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    _mv(root)

    queue = (root / ".okf/decisions/0002-use-a-queue.md").read_text()
    assert (
        "See [ADR 0004](0004-use-a-stream.md#context), and "
        "[the stream](/decisions/0004-use-a-stream.md)." in queue
    )
    assert (
        "Read [the stream record](../../.okf/decisions/0004-use-a-stream.md)."
        in (root / DOC).read_text()
    )


def test_mv_leaves_links_in_code_alone_and_lists_them(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    queue = root / ".okf/decisions/0002-use-a-queue.md"
    code = (
        "In code: `[ADR 0003](0003-use-a-stream.md)`.\n\n"
        "```\n[the record](0003-use-a-stream.md)\n```\n"
    )
    queue.write_text(queue.read_text() + "\n" + code)

    result = _mv(root, OLD_ID, NEW_ID, "--json")

    assert queue.read_text().endswith(code)
    mentions = json.loads(result.stdout)["mentions"]
    assert {
        "file": ".okf/decisions/0002-use-a-queue.md",
        "line": 22,
        "text": "In code: `[ADR 0003](0003-use-a-stream.md)`.",
    } in mentions
    assert {
        "file": ".okf/decisions/0002-use-a-queue.md",
        "line": 25,
        "text": "[the record](0003-use-a-stream.md)",
    } in mentions


def test_mv_updates_the_summary_checked_against(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    _mv(root)

    checked = front_matter(root / ".okf/summary.md")["checked"]
    assert checked["against"] == ["decisions/0002-use-a-queue", NEW_ID]


def test_mv_logs_and_passes_the_checks(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    log_before = (root / ".okf/log.md").read_text()

    _mv(root)

    log = (root / ".okf/log.md").read_text()
    assert log.startswith(log_before.rstrip("\n"))
    assert log.strip().splitlines()[-1] == (
        f"- Moved `{OLD_ID}` to `{NEW_ID}` with `kmctl mv`, rewriting links to it "
        "in `decisions/0002-use-a-queue`, `decisions/index`, `summary`."
    )
    check = okf_validate(root / ".okf")
    assert check.returncode == 0, check.stdout + check.stderr
    result = _invoke("check", "--path", str(root))
    assert result.exit_code == 0, result.output


def test_mv_reports_what_it_did_as_json(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = _mv(root, OLD_ID, NEW_ID, "--json")

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == {
        "old": OLD_ID,
        "new": NEW_ID,
        "path": NEW,
        "updated": [
            ".okf/decisions/0002-use-a-queue.md",
            NEW,
            ".okf/decisions/index.md",
            ".okf/summary.md",
            DOC,
        ],
        "mentions": [
            {
                "file": "AGENTS.md",
                "line": 3,
                "text": "The stream rule is .okf/decisions/0003-use-a-stream.md.",
            },
        ],
    }


def test_mv_prints_the_mentions_and_the_next_step(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = _mv(root)

    lines = result.stdout.splitlines()
    assert lines[0] == f"moved {OLD_ID} to {NEW_ID} ({NEW})"
    assert (
        "not rewritten  AGENTS.md:3  The stream rule is "
        ".okf/decisions/0003-use-a-stream.md." in lines
    )
    assert lines[-1] == (
        "Next: fix or keep each line listed as not rewritten, then kmctl check"
    )


def test_mv_renames_a_prototype_folder(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    created = _invoke(
        "new",
        "prototype",
        "Parser speed",
        "--description",
        "Speed.",
        "--path",
        str(root),
    )
    assert created.exit_code == 0, created.output
    (root / ".okf/prototypes/parser-speed/results.csv").write_text("n,ms\n")

    result = _mv(root, "prototypes/parser-speed", "prototypes/parser-timing")

    assert result.exit_code == 0, result.output
    assert (root / ".okf/prototypes/parser-timing/results.csv").is_file()
    assert not (root / ".okf/prototypes/parser-speed").exists()
    assert (
        "- [Parser speed](parser-timing/README.md): Speed."
        in (root / ".okf/prototypes/index.md").read_text().splitlines()
    )
    assert _invoke("check", "--path", str(root)).exit_code == 0


def test_mv_keeps_the_number_when_only_the_name_changes(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = _mv(root, OLD_ID, "decisions/0003-use-an-event-stream")

    assert result.exit_code == 0, result.output
    path = root / ".okf/decisions/0003-use-an-event-stream.md"
    assert front_matter(path)["title"] == "ADR 0003: Use a stream"


@pytest.mark.parametrize(
    ("old", "new", "says"),
    [
        (OLD_ID, "decisions/0002-use-a-queue", "already exists"),
        (OLD_ID, "decisions/0002-use-a-stream", "decision 0002 is taken"),
        (OLD_ID, "practices/use-a-stream", "stay in its folder"),
        ("decisions/0009-nothing", NEW_ID, "no concept"),
        (OLD_ID, OLD_ID, "same"),
        ("decisions/index", "decisions/contents", "reserved"),
        (OLD_ID, "decisions/0004-Use_A_Stream", "not kebab-case"),
        (OLD_ID, "decisions/use-a-stream", "four-digit number"),
        ("summary", "overview", "summary and manifesto keep their names"),
        (f"{OLD_ID}/../0002-use-a-queue", NEW_ID, "no concept"),
    ],
)
def test_mv_refuses_and_writes_nothing(
    tmp_path: Path, old: str, new: str, says: str
) -> None:
    root = _repo(tmp_path)
    snapshot = {p: p.read_text() for p in root.rglob("*") if p.is_file()}

    result = _mv(root, old, new)

    assert result.exit_code == 1, result.output
    assert result.stderr.startswith("kmctl mv: refused: ")
    assert says in result.stderr
    assert result.stdout == ""
    assert {p: p.read_text() for p in root.rglob("*") if p.is_file()} == snapshot


def test_mv_cuts_a_long_mention_around_the_match(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "events.jsonl").write_text(
        '{"a": "' + "x" * 300 + f" see {OLD_ID} here " + "y" * 300 + '"}\n'
    )

    result = _mv(root, OLD_ID, NEW_ID, "--json")

    [mention] = [
        m for m in json.loads(result.stdout)["mentions"] if m["file"] == "events.jsonl"
    ]
    assert mention["text"] == (
        "..." + "x" * 35 + f" see {OLD_ID} here " + "y" * 87 + "..."
    )


def test_mv_stages_a_tracked_rename_and_skips_loop_history(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / ".loop").mkdir()
    (root / ".loop/events.jsonl").write_text(f'{{"concept": "{OLD_ID}"}}\n')
    git = ["git", "-C", str(root)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run(
        [*git, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "c"],
        check=True,
    )

    result = _mv(root, OLD_ID, NEW_ID, "--json")

    assert result.exit_code == 0, result.output
    staged = subprocess.run(
        [*git, "diff", "--cached", "--name-status", "-M"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    renames = [
        line.split("\t")[1:] for line in staged.splitlines() if line.startswith("R")
    ]
    assert [OLD, NEW] in renames
    files = {m["file"] for m in json.loads(result.stdout)["mentions"]}
    assert "AGENTS.md" in files
    assert not any(f.startswith(".loop/") for f in files)
