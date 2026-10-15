import json
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from conftest import okf_validate
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.concepts import new_concept, stale_after_time
from kmctl.okf import ALLOWED_FIELDS, as_datetime, front_matter

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


def _path(root: Path, kind: str, title: str, *extra: str) -> Path:
    result = _new(root, kind, title, "--json", *extra)
    assert result.exit_code == 0, result.output
    return root / json.loads(result.stdout)["path"]


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


# Freshness: --stale-after and --source


NOW = datetime(2026, 1, 31, 12, 30, tzinfo=UTC)


def _stale_after(path: Path) -> datetime | None:
    return as_datetime(front_matter(path).get("stale_after"))


def test_new_stale_after_for_every_kind(tmp_path: Path) -> None:
    _repo(tmp_path)

    for kind in SKELETONS:
        path = _path(tmp_path, kind, f"Timed {kind}", "--stale-after", "30d")
        written = as_datetime(front_matter(path)["generated"]["at"])

        assert written is not None
        assert _stale_after(path) == written + timedelta(days=30), kind


def test_new_stale_after_forms(tmp_path: Path) -> None:
    _repo(tmp_path)
    expected = {
        "30d": datetime(2026, 3, 2, 12, 30, tzinfo=UTC),
        "12w": datetime(2026, 4, 25, 12, 30, tzinfo=UTC),
        "1m": datetime(2026, 2, 28, 12, 30, tzinfo=UTC),  # clamped to the month's end
        "6m": datetime(2026, 7, 31, 12, 30, tzinfo=UTC),
        "13m": datetime(2027, 2, 28, 12, 30, tzinfo=UTC),
        "1y": datetime(2027, 1, 31, 12, 30, tzinfo=UTC),
        "2027-01-15": datetime(2027, 1, 15, tzinfo=UTC),
        "2027-01-15T08:00:00Z": datetime(2027, 1, 15, 8, tzinfo=UTC),
        "2027-01-15T10:00:00+02:00": datetime(2027, 1, 15, 8, tzinfo=UTC),
    }
    for i, (value, when) in enumerate(expected.items()):
        result = new_concept(
            tmp_path, "practice", f"Form {i}", "One.", now=NOW, stale_after=value
        )

        assert _stale_after(tmp_path / result.path) == when, value
        assert (
            f"stale_after: {when:%Y-%m-%dT%H:%M:%SZ}\n"
            in (tmp_path / result.path).read_text()
        )


def test_new_stale_after_leap_day_year() -> None:
    leap = datetime(2028, 2, 29, tzinfo=UTC)

    assert stale_after_time("1y", leap) == datetime(2029, 2, 28, tzinfo=UTC)


def test_new_handoff_stale_after_replaces_default(tmp_path: Path) -> None:
    _repo(tmp_path)

    plain = new_concept(tmp_path, "handoff", "Plain", "One.", now=NOW)
    timed = new_concept(tmp_path, "handoff", "Timed", "One.", now=NOW, stale_after="2d")
    keyed = new_concept(
        tmp_path, "handoff", "Keyed", "One.", now=NOW, key="k", stale_after="3d"
    )
    again = new_concept(
        tmp_path, "handoff", "Keyed", "Two.", now=NOW, key="k", stale_after="5d"
    )

    assert _stale_after(tmp_path / plain.path) == NOW + timedelta(days=14)
    assert _stale_after(tmp_path / timed.path) == NOW + timedelta(days=2)
    assert again.updated and again.path == keyed.path
    assert _stale_after(tmp_path / again.path) == NOW + timedelta(days=5)
    assert (tmp_path / again.path).read_text().count("stale_after:") == 1


def test_new_stale_after_refused(tmp_path: Path) -> None:
    _repo(tmp_path)
    before = {p: p.read_text() for p in (tmp_path / ".okf").rglob("*.md")}
    today = datetime.now(UTC).date().isoformat()

    for value in ("2020-01-01", today, "0d", "soon", "30x", "-3d", "2027-13-01", ""):
        for kind in ("decision", "handoff"):
            result = _new(tmp_path, kind, "Refused", "--stale-after", value)

            assert result.exit_code == 1, (value, result.output)
            assert f"--stale-after {value!r}" in result.stderr, value
    assert {p: p.read_text() for p in (tmp_path / ".okf").rglob("*.md")} == before


def test_new_source_written_in_order(tmp_path: Path) -> None:
    _repo(tmp_path)
    for rel in ("src/b.py", "src/a.py", ".okf/practices/notes.txt"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("x\n")

    path = _path(
        tmp_path,
        "practice",
        "Sourced",
        "--source",
        "src/b.py",
        "--source",
        "notes.txt",
        "--source",
        "/manifesto",
        "--source",
        "src/a.py",
    )

    assert front_matter(path)["sources"] == [
        {"resource": "src/b.py"},
        {"resource": "notes.txt"},
        {"resource": "/manifesto"},
        {"resource": "src/a.py"},
    ]
    for kind in ("decision", "proposal", "prototype"):
        other = _path(tmp_path, kind, f"Sourced {kind}", "--source", "src/a.py")
        assert front_matter(other)["sources"] == [{"resource": "src/a.py"}], kind


def test_new_source_accepts_untracked_file_without_git(tmp_path: Path) -> None:
    _repo(tmp_path)
    (tmp_path / "new.py").write_text("x\n")

    result = _new(tmp_path, "decision", "Untracked", "--source", "new.py")

    assert result.exit_code == 0, result.output


def test_new_source_refused(tmp_path: Path) -> None:
    _repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.py").write_text("x\n")
    (tmp_path.parent / "outside.py").write_text("x\n")
    before = {p: p.read_text() for p in (tmp_path / ".okf").rglob("*.md")}

    for value in ("src/missing.py", "../outside.py", " "):
        result = _new(
            tmp_path, "decision", "Refused", "--source", "src/a.py", "--source", value
        )

        assert result.exit_code == 1, (value, result.output)
        assert f"--source {value!r}" in result.stderr, value
    handoff = _new(tmp_path, "handoff", "Refused", "--source", "src/a.py")

    assert handoff.exit_code == 1
    assert "--source" in handoff.stderr and "handoff" in handoff.stderr
    assert {p: p.read_text() for p in (tmp_path / ".okf").rglob("*.md")} == before


def _git(root: Path, *args: str, date: str = "2026-01-01T00:00:00+00:00") -> None:
    env = os.environ | {
        "GIT_AUTHOR_DATE": date,
        "GIT_COMMITTER_DATE": date,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True)


def test_new_source_changed_makes_concept_due(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q", "-b", "main")
    _repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text("x = 1\n")
    path = _path(tmp_path, "decision", "Use app", "--source", "src/app.py")
    text = path.read_text()
    path.write_text(
        text.replace(
            "tags: [decision]\n",
            "tags: [decision]\nverified:\n  - {by: 'human:j', at: '2026-06-01T00:00:00Z'}\n",
        )
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "c")

    def reasons() -> list[str]:
        data = json.loads(
            _invoke("review", "due", "--path", str(tmp_path), "--json").stdout
        )
        rel = path.relative_to(tmp_path).as_posix()
        return [r for d in data["due"] if d["path"] == rel for r in d["reasons"]]

    assert reasons() == []
    (tmp_path / "src/app.py").write_text("x = 2\n")
    _git(tmp_path, "commit", "-q", "-am", "c", date="2026-09-01T00:00:00+00:00")

    assert reasons() == ["source changed: src/app.py"]


def test_new_freshness_valid(tmp_path: Path) -> None:
    _repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text("x\n")

    for kind in SKELETONS:
        extra = ("--source", "src/app.py") if kind != "handoff" else ()
        result = _new(tmp_path, kind, f"Fresh {kind}", "--stale-after", "6m", *extra)
        assert result.exit_code == 0, result.output

    written: set[str] = set()
    for page in (tmp_path / ".okf").rglob("*.md"):
        meta = front_matter(page)
        written |= set(meta)
        written |= {f"sources[].{k}" for s in meta.get("sources", []) for k in s}
    assert {"stale_after", "sources", "sources[].resource"} <= written
    assert written <= set(ALLOWED_FIELDS), written - set(ALLOWED_FIELDS)
    check = okf_validate(tmp_path / ".okf")
    assert check.returncode == 0, check.stdout + check.stderr
    assert "warn" not in (check.stdout + check.stderr).lower()


def test_new_freshness_documented() -> None:
    result = CliRunner().invoke(
        app, ["new", "decision", "--help"], env={"COLUMNS": "200"}, terminal_width=200
    )
    reference = (Path(__file__).parents[1] / "docs/reference/commands.md").read_text()

    for option in ("--stale-after", "--source"):
        assert option in result.stdout, option
        assert f"`{option} " in reference, option
    for form in ("30d", "12w", "6m", "1y", "2027-01-15"):
        assert form in result.stdout, form
        assert form in reference, form


def test_stale_after_refused_odd_counts(tmp_path: Path) -> None:
    from kmctl.concepts import ConceptError

    for value in ("9" * 5000 + "d", "\u0663d", "1234567d"):
        with pytest.raises(ConceptError) as err:
            stale_after_time(value, NOW)
        assert "--stale-after" in str(err.value), value
