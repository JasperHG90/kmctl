import re
from pathlib import Path

from conftest import okf_validate
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.okf import front_matter

OLD = ".okf/decisions/0002-use-a-queue.md"
NEW = ".okf/decisions/0003-use-a-stream.md"


def _invoke(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _repo(root: Path) -> Path:
    """A bundle with init's decision 0001 and two more; 0002 carries a hand-added decision_status."""
    assert _invoke("init", "--path", str(root)).exit_code == 0
    for title in ("Use a queue", "Use a stream"):
        result = _invoke(
            "new", "decision", title, "--description", f"{title}.", "--path", str(root)
        )
        assert result.exit_code == 0, result.output
    old = root / OLD
    old.write_text(
        old.read_text().replace(
            "status: stable\n", "status: stable\ndecision_status: Accepted\n"
        )
    )
    return root


def _supersede(root: Path, old: str = "0002", new: str = "0003") -> Result:
    return _invoke("decision", "supersede", old, "--by", new, "--path", str(root))


def test_supersede_marks_old_record(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    before = (root / OLD).read_text()
    body_before = before.split("\n---\n", 1)[1]

    result = _supersede(root)
    after = (root / OLD).read_text()

    assert result.exit_code == 0, result.output
    assert front_matter(root / OLD)["status"] == "deprecated"
    assert front_matter(root / OLD)["decision_status"] == "Accepted"
    assert after.split("\n---\n", 1)[1].startswith(body_before)


def test_supersede_links_both_ways(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    _supersede(root)

    old = (root / OLD).read_text()
    assert re.search(r"^## Correction, \d{4}-\d{2}-\d{2}$", old, re.MULTILINE)
    assert "(0003-use-a-stream.md)" in old.split("## Correction, ", 1)[1]
    assert "(0002-use-a-queue.md)" in (root / NEW).read_text()


def test_supersede_updates_index(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    _supersede(root)

    [line] = [
        line
        for line in (root / ".okf/decisions/index.md").read_text().splitlines()
        if "(0002-use-a-queue.md)" in line
    ]
    assert "(superseded by ADR 0003)" in line


def test_supersede_logs_and_validates(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    _supersede(root)

    last = (root / ".okf/log.md").read_text().strip().splitlines()[-1]
    assert "`decisions/0002-use-a-queue`" in last
    assert "`decisions/0003-use-a-stream`" in last
    check = okf_validate(root / ".okf")
    assert check.returncode == 0, check.stdout + check.stderr
    assert _invoke("check", "--path", str(root)).exit_code == 0


def test_supersede_refusals(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _supersede(root)
    snapshot = {p: p.read_text() for p in (root / ".okf").rglob("*.md")}

    cases = [
        ("0009", "0003"),
        ("0003", "0009"),
        ("0002", "0003"),
        ("0003", "0003"),
        ("\u00b2", "0003"),
    ]
    for old, new in cases:
        result = _supersede(root, old, new)
        assert result.exit_code == 1, (old, new, result.output)
        assert "refused:" in result.stderr, (old, new)

    assert {p: p.read_text() for p in (root / ".okf").rglob("*.md")} == snapshot


def test_supersede_refuses_without_index_entry(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    index = root / ".okf/decisions/index.md"
    index.write_text(
        "\n".join(
            line
            for line in index.read_text().splitlines()
            if "0002-use-a-queue.md" not in line
        )
        + "\n"
    )

    result = _supersede(root)

    assert result.exit_code == 1
    assert "add a line" in result.stderr
    assert front_matter(root / OLD)["status"] == "stable"


def test_supersede_note_goes_after_a_wrapped_entry(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    index = root / ".okf/decisions/index.md"
    index.write_text(
        index.read_text().replace(
            "(0002-use-a-queue.md): Use a queue.",
            "(0002-use-a-queue.md): Use a\n  queue for jobs.",
        )
    )

    _supersede(root)

    text = index.read_text()
    assert "Use a\n  queue for jobs. (superseded by ADR 0003)\n" in text
