import json
from pathlib import Path

from conftest import okf_validate
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.okf import front_matter

SKELETONS = {
    "decision": ["## Context", "## Decision", "## Consequences"],
    "practice": ["## What happened", "## The lesson", "## Evidence"],
    "proposal": ["## Problem", "## Proposal", "## Open questions"],
    "prototype": ["## Question", "## Method", "## Results", "## Conclusion"],
    "handoff": [
        "## Summary",
        "## Where it stands",
        "## Next steps",
        "## Key references",
    ],
}


def _invoke(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _repo(root: Path) -> Path:
    """A repository set up with kmctl init."""
    assert _invoke("init", "--path", str(root)).exit_code == 0
    return root


def _new(root: Path, kind: str, title: str, *extra: str) -> Result:
    return _invoke(
        "new",
        kind,
        title,
        "--description",
        f"About {title}.",
        "--path",
        str(root),
        *extra,
    )


def _path(root: Path, kind: str, title: str) -> Path:
    return root / json.loads(_new(root, kind, title, "--json").stdout)["path"]


def test_new_creates_each_kind(tmp_path: Path) -> None:
    _repo(tmp_path)

    expected = {
        "decision": (
            ".okf/decisions/0002-first-decision.md",
            "ADR 0002: First decision",
        ),
        "practice": (".okf/practices/first-practice.md", "First practice"),
        "proposal": (".okf/proposals/first-proposal.md", "First proposal"),
        "prototype": (".okf/prototypes/first-prototype/README.md", "First prototype"),
        "handoff": (".okf/handoffs/first-handoff.md", "First handoff"),
    }
    for kind, headings in SKELETONS.items():
        path = _path(tmp_path, kind, f"First {kind}")
        meta = front_matter(path)
        body = path.read_text()

        assert path.relative_to(tmp_path).as_posix() == expected[kind][0]
        assert meta["title"] == expected[kind][1]
        assert meta["type"] == kind
        assert meta["description"] == f"About First {kind}."
        assert {"title", "tags", "generated"} <= meta.keys()
        assert all(h in body for h in headings), kind
    assert (tmp_path / ".okf/prototypes/first-prototype/README.md").is_file()
    assert (tmp_path / ".okf/decisions/0002-first-decision.md").is_file()


def test_new_numbers_and_dates(tmp_path: Path) -> None:
    _repo(tmp_path)
    (tmp_path / ".okf/decisions").mkdir(exist_ok=True)
    (tmp_path / ".okf/decisions/0007-earlier.md").write_text(
        "---\ntype: decision\n---\n"
    )

    decision = _path(tmp_path, "decision", "Use a queue")
    handoff = _path(tmp_path, "handoff", "Where the queue stands")

    assert decision.name == "0008-use-a-queue.md"
    assert front_matter(handoff).get("stale_after")


def test_new_creates_section(tmp_path: Path) -> None:
    _repo(tmp_path)

    _new(tmp_path, "practice", "Measure first")

    assert (tmp_path / ".okf/practices/index.md").is_file()
    assert "(practices/index.md)" in (tmp_path / ".okf/index.md").read_text()


def test_new_indexes_logs_and_validates(tmp_path: Path) -> None:
    _repo(tmp_path)

    for kind in SKELETONS:
        assert _new(tmp_path, kind, f"One {kind}").exit_code == 0

    log = (tmp_path / ".okf/log.md").read_text()
    assert (
        "(0002-one-decision.md)" in (tmp_path / ".okf/decisions/index.md").read_text()
    )
    assert (
        "(one-prototype/README.md)"
        in (tmp_path / ".okf/prototypes/index.md").read_text()
    )
    assert "`decisions/0002-one-decision`" in log
    assert "`handoffs/one-handoff`" in log
    assert _invoke("check", "--path", str(tmp_path)).exit_code == 0
    check = okf_validate(tmp_path / ".okf")
    assert check.returncode == 0, check.stdout + check.stderr


def test_new_refuses_existing(tmp_path: Path) -> None:
    _repo(tmp_path)
    _new(tmp_path, "handoff", "Same title")
    before = {p: p.read_text() for p in (tmp_path / ".okf").rglob("*.md")}

    result = _new(tmp_path, "handoff", "Same title")

    assert result.exit_code != 0
    assert {p: p.read_text() for p in (tmp_path / ".okf").rglob("*.md")} == before


def test_new_title_with_brackets_stays_listed(tmp_path: Path) -> None:
    _repo(tmp_path)

    result = _new(tmp_path, "practice", "Use [WIP] flags")

    assert result.exit_code == 0, result.output
    index = (tmp_path / ".okf/practices/index.md").read_text()
    assert "- [Use (WIP) flags](use-wip-flags.md)" in index
    assert _invoke("check", "--path", str(tmp_path)).exit_code == 0


def test_new_title_with_accents_keeps_its_letters(tmp_path: Path) -> None:
    _repo(tmp_path)

    path = _path(tmp_path, "practice", "Café état")

    assert path.name == "cafe-etat.md"


def test_new_description_newline_stays_on_one_line(tmp_path: Path) -> None:
    _repo(tmp_path)

    _invoke(
        "new",
        "practice",
        "Two lines",
        "--description",
        "First.\nSecond.",
        "--path",
        str(tmp_path),
    )

    index = (tmp_path / ".okf/practices/index.md").read_text()
    assert "- [Two lines](two-lines.md): First. Second.\n" in index
