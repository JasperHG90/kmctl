"""kmctl verify writes a person's verified entry so the id leaves kmctl review due."""

import json
import os
import re
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.okf import front_matter

ROOT = Path(__file__).resolve().parents[1]
OLD = "2026-01-01T00:00:00+00:00"
STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _git(root: Path, *args: str, date: str = OLD) -> None:
    """Run git in ``root`` with a fixed author and commit date."""
    env = os.environ | {
        "GIT_AUTHOR_DATE": date,
        "GIT_COMMITTER_DATE": date,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True)


def _write(root: Path, rel: str, text: str) -> None:
    """Write ``text`` to ``root / rel``, making its folders."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _commit(root: Path, date: str = OLD) -> None:
    """Commit everything in ``root`` at ``date``."""
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "c", date=date)


def _an_hour_ago() -> str:
    """A commit date earlier today (or late yesterday), before any stamp kmctl verify writes."""
    return (datetime.now(UTC) - timedelta(hours=1)).isoformat(timespec="seconds")


def _repo(root: Path) -> Path:
    """A git repository with a bundle, a log and one committed source file."""
    _git(root, "init", "-q", "-b", "main")
    _write(root, ".okf/index.md", '---\nokf_version: "0.2"\n---\n')
    _write(root, ".okf/log.md", "# Log\n")
    _write(root, "src/app.py", "x = 1\n")
    return root


def _concept(root: Path, rel: str, front: str) -> Path:
    """Write a concept at ``.okf/rel`` with ``front`` as the extra front matter lines."""
    _write(
        root,
        f".okf/{rel}",
        f'---\ntype: note\ntitle: "{rel}"\ndescription: "A note."\n{front}---\n\n# {rel}\n\nBody.\n',
    )
    return root / ".okf" / rel


def _invoke(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _verify(root: Path, cid: str, *args: str, by: str = "human:jasper") -> Result:
    return _invoke("verify", cid, "--by", by, "--path", str(root), *args)


def _due_ids(root: Path) -> set[str]:
    result = _invoke("review", "due", "--path", str(root), "--json")
    return {d["id"] for d in json.loads(result.stdout)["due"]}


def _files(root: Path) -> dict[str, bytes]:
    """Every file under ``root`` outside .git, by path, with its bytes."""
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


@pytest.mark.parametrize(
    "front",
    [
        "",
        "sources:\n  - resource: src/app.py\n",
        (
            "verified:\n  - by: human:old\n    at: 2026-03-01T00:00:00Z\n"
            "sources:\n  - resource: src/app.py\n"
        ),
    ],
    ids=["unverified", "unverified-with-source", "source-changed-same-day"],
)
def test_verify_clears_a_due_concept(tmp_path: Path, front: str) -> None:
    root = _repo(tmp_path)
    path = _concept(root, "decisions/0001-x.md", front)
    _commit(root)
    _write(root, "src/app.py", "x = 2\n")
    _commit(root, date=_an_hour_ago())
    assert "decisions/0001-x" in _due_ids(root)

    result = _verify(root, "decisions/0001-x")

    assert result.exit_code == 0, result.output
    assert "decisions/0001-x" not in _due_ids(root)
    entry = front_matter(path)["verified"][-1]
    assert entry["by"] == "human:jasper"
    assert re.search(r"^\s+at: " + STAMP.pattern + "$", path.read_text(), re.MULTILINE)
    log = (root / ".okf/log.md").read_text()
    assert "`decisions/0001-x`" in log.splitlines()[-1]


def test_verify_clears_the_manifesto(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _concept(root, "manifesto.md", "")
    _commit(root)

    assert _verify(root, "manifesto").exit_code == 0
    assert "manifesto" not in _due_ids(root)


def test_verify_a_docs_page(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _write(
        root,
        "docs/how-to/run.md",
        "---\ndescription: How to run it.\nsources:\n  - resource: /src/app.py\n"
        "verified:\n  - by: human:old\n    at: 2026-03-01T00:00:00Z\n---\n\n# Run\n",
    )
    _commit(root)
    _write(root, "src/app.py", "x = 2\n")
    _commit(root, date=_an_hour_ago())
    assert "docs/how-to/run" in _due_ids(root)

    result = _verify(root, "docs/how-to/run")

    assert result.exit_code == 0, result.output
    assert "docs/how-to/run" not in _due_ids(root)
    assert front_matter(root / "docs/how-to/run.md")["verified"][-1]["by"] == (
        "human:jasper"
    )


@pytest.mark.parametrize(
    ("verified", "before"),
    [
        ("", []),
        ("verified:\n", []),
        ("verified: []\n", []),
        (
            (
                "verified:\n  - by: human:a\n    at: 2026-03-01T00:00:00Z\n"
                "  - by: human:b\n    at: 2026-04-01T00:00:00Z\n"
            ),
            ["human:a", "human:b"],
        ),
        (
            "verified:\n- by: human:a\n  at: 2026-03-01T00:00:00Z\n",
            ["human:a"],
        ),
        ("verified:\n  by: human:a\n  at: 2026-03-01T00:00:00Z\n", ["human:a"]),
        (
            "verified: [{by: 'human:a', at: '2026-03-01T00:00:00Z'}]\n",
            ["human:a"],
        ),
        ("verified: {by: 'human:a', at: '2026-03-01T00:00:00Z'}\n", ["human:a"]),
    ],
    ids=[
        "absent",
        "null",
        "empty-flow",
        "block-list",
        "block-list-unindented",
        "single-mapping",
        "flow-list",
        "flow-mapping",
    ],
)
def test_verify_keeps_every_other_line(
    tmp_path: Path, verified: str, before: list[str]
) -> None:
    root = _repo(tmp_path)
    other = (
        "tags: [decision]  # a comment\n"
        "generated:\n  by: claude-opus/5.5\n  at: 2026-01-01\n"
        "status: stable\n"
    )
    path = _concept(root, "decisions/0001-x.md", other + verified)
    original = path.read_text()
    _commit(root)

    result = _verify(root, "decisions/0001-x")

    assert result.exit_code == 0, result.output
    after = path.read_text()
    by = [e["by"] for e in front_matter(path)["verified"]]
    assert by == [*before, "human:jasper"]

    def outside(text: str) -> list[str]:
        """The lines that are not part of the verified block."""
        lines, keep, inside = text.splitlines(), [], False
        for line in lines:
            if line.startswith("verified:"):
                inside = True
                continue
            if inside and (line.startswith((" ", "-")) and line != "---"):
                continue
            inside = False
            keep.append(line)
        return keep

    assert outside(after) == outside(original)


@pytest.mark.parametrize(
    ("verified", "before"),
    [
        (
            "verified:  # checks\n  - by: human:a\n    at: 2026-03-01T00:00:00Z\n",
            ["human:a"],
        ),
        ("verified: []  # checks\n", []),
        ("verified:  # checks\n", []),
        ("verified: ~  # checks\n", []),
        (
            "verified:  # checks\n  by: human:a\n  at: 2026-03-01T00:00:00Z\n",
            ["human:a"],
        ),
        (
            "verified: [{by: 'human:a', at: '2026-03-01T00:00:00Z'}]  # checks\n",
            ["human:a"],
        ),
        (
            "verified: {by: 'human:a', at: '2026-03-01T00:00:00Z'}  # checks\n",
            ["human:a"],
        ),
    ],
    ids=[
        "block-list",
        "empty-flow",
        "null",
        "tilde",
        "single-mapping",
        "flow-list",
        "flow-mapping",
    ],
)
def test_verify_keeps_a_comment_on_the_verified_line(
    tmp_path: Path, verified: str, before: list[str]
) -> None:
    """A trailing comment on the verified line stays there, and the entry is added."""
    root = _repo(tmp_path)
    path = _concept(root, "decisions/0001-x.md", "status: stable\n" + verified)
    _commit(root)

    result = _verify(root, "decisions/0001-x")

    assert result.exit_code == 0, result.output
    by = [e["by"] for e in front_matter(path)["verified"]]
    assert by == [*before, "human:jasper"]
    [line] = [x for x in path.read_text().splitlines() if x.startswith("verified:")]
    assert line.endswith("  # checks")
    assert "status: stable" in path.read_text().splitlines()


def _bad_front_matter(root: Path) -> None:
    _write(root, ".okf/decisions/0001-x.md", "---\ntype: [unclosed\n---\n\n# X\n")


@pytest.mark.parametrize(
    ("cid", "by", "args", "setup", "fix"),
    [
        ("decisions/0001-x", "jasper", (), None, "human:"),
        ("decisions/0001-x", "agent:claude", (), None, "human:"),
        ("decisions/0001-x", "human:", (), None, "human:"),
        ("decisions/0099-missing", "human:jasper", (), None, "kmctl review due"),
        ("../outside", "human:jasper", (), None, "kmctl review due"),
        ("decisions/../handoffs/2026-10-01-x", "human:jasper", (), None, "review due"),
        ("docs/../.okf/handoffs/2026-10-01-x", "human:jasper", (), None, "review due"),
        ("docs/../README", "human:jasper", (), None, "kmctl review due"),
        ("./handoffs/2026-10-01-x", "human:jasper", (), None, "review due"),
        (".//handoffs/2026-10-01-x", "human:jasper", (), None, "review due"),
        ("/etc/passwd", "human:jasper", (), None, "kmctl review due"),
        ("docs//etc/passwd", "human:jasper", (), None, "kmctl review due"),
        ("handoffs/2026-10-01-x", "human:jasper", (), None, "never verified"),
        ("decisions/0001-x", "human:jasper", (), _bad_front_matter, "front matter"),
        ("stale", "human:jasper", (), None, "--stale-after"),
        ("stale", "human:jasper", ("--stale-after", "2020-01-01"), None, "future"),
    ],
    ids=[
        "by-not-a-person",
        "by-an-agent",
        "by-empty-id",
        "missing",
        "outside-the-bundle",
        "dotdot-into-handoffs",
        "docs-dotdot-into-handoffs",
        "docs-dotdot-to-root",
        "dot-slash-handoff",
        "dot-double-slash-handoff",
        "absolute",
        "docs-absolute",
        "handoff",
        "bad-front-matter",
        "stale-without-flag",
        "stale-after-in-the-past",
    ],
)
def test_verify_refuses(
    tmp_path: Path,
    cid: str,
    by: str,
    args: tuple[str, ...],
    setup: Callable[[Path], None] | None,
    fix: str,
) -> None:
    root = _repo(tmp_path)
    _concept(root, "decisions/0001-x.md", "")
    _concept(root, "stale.md", "stale_after: 2020-01-01T00:00:00Z\n")
    _concept(root, "handoffs/2026-10-01-x.md", "stale_after: 2999-01-01T00:00:00Z\n")
    if setup is not None:
        setup(root)
    _commit(root)
    before = _files(root)

    result = _verify(root, cid, *args, by=by)

    assert result.exit_code == 1, result.output
    assert result.stdout == ""
    lines = result.stderr.strip().splitlines()
    assert len(lines) == 1 and lines[0].startswith("kmctl verify: refused:"), lines
    assert fix in lines[0]
    assert _files(root) == before


def test_verify_stale_concept_with_stale_after(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    path = _concept(root, "stale.md", "stale_after: 2020-01-01T00:00:00Z\n")
    original = path.read_text()
    _commit(root)
    assert "stale" in _due_ids(root)

    result = _verify(root, "stale", "--stale-after", "6m")

    assert result.exit_code == 0, result.output
    assert "stale" not in _due_ids(root)
    meta = front_matter(path)
    assert meta["stale_after"] > datetime.now(UTC) + timedelta(days=150)
    kept = [
        line
        for line in path.read_text().splitlines()
        if not line.startswith(("stale_after:", "verified:", "  "))
    ]
    assert kept == [
        line
        for line in original.splitlines()
        if not line.startswith(("stale_after:", "verified:", "  "))
    ]


def test_verify_output(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _concept(root, "decisions/0001-x.md", "")
    _concept(root, "decisions/0002-y.md", "")
    _commit(root)

    data = json.loads(_verify(root, "decisions/0001-x", "--json").stdout)
    text = _verify(root, "decisions/0002-y")

    assert set(data) == {"id", "path", "by", "at", "stale_after"}
    assert data["id"] == "decisions/0001-x"
    assert data["path"] == ".okf/decisions/0001-x.md"
    assert data["by"] == "human:jasper"
    assert STAMP.fullmatch(data["at"])
    assert data["stale_after"] is None
    assert text.stdout.strip().splitlines()[-1] == "Next: kmctl review due"


@pytest.mark.parametrize(
    "rel",
    [
        "apm/.apm/skills/audit/SKILL.md",
        "apm/claude/.apm/instructions/okf-bundle.instructions.md",
        "apm/antigravity/.apm/instructions/okf-bundle.instructions.md",
    ],
)
def test_the_package_names_kmctl_verify(rel: str) -> None:
    text = " ".join((ROOT / rel).read_text().split())
    assert "kmctl verify <id> --by human:" in text
    assert "--stale-after" in text


def test_yaml_reads_the_written_stamp_as_a_time(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    path = _concept(root, "decisions/0001-x.md", "")
    _commit(root)

    _verify(root, "decisions/0001-x")

    head = path.read_text().split("\n---\n", 1)[0][4:]
    assert isinstance(yaml.safe_load(head)["verified"][0]["at"], datetime)


def test_verify_keeps_crlf_line_endings(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    path = root / ".okf/decisions/0001-x.md"
    path.parent.mkdir(parents=True)
    original = b'---\r\ntype: note\r\ntitle: "X"\r\n---\r\n\r\n# X\r\n\r\nBody.\r\n'
    path.write_bytes(original)
    _commit(root)

    result = _verify(root, "decisions/0001-x")

    assert result.exit_code == 0, result.output
    after = path.read_bytes()
    assert b"\n" not in after.replace(b"\r\n", b"")
    assert after.endswith(b"---\r\n\r\n# X\r\n\r\nBody.\r\n")
    assert after.startswith(b'---\r\ntype: note\r\ntitle: "X"\r\nverified:\r\n')
    assert "decisions/0001-x" not in _due_ids(root)
