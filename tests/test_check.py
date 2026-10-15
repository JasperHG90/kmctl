import json
from pathlib import Path

from typer.testing import CliRunner, Result

from kmctl import app

CONCEPT = (
    '---\ntype: note\ntitle: "{title}"\ndescription: "A note."\n---\n\n# {title}\n'
)


def _write(root: Path, rel: str, text: str) -> None:
    """Write ``text`` to ``root / rel``, making its folders."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _good_repo(root: Path) -> None:
    """A repository whose docs/ and .okf/ indexes all agree with their folders."""
    _write(
        root,
        "docs/README.md",
        "# Docs\n\n- [Install](how-to/install.md): install it.\n",
    )
    _write(root, "docs/how-to/install.md", "# Install\n")
    _write(
        root,
        ".okf/index.md",
        '---\nokf_version: "0.2"\n---\n\n# Bundle\n\n'
        "- [Manifesto](manifesto.md): the design.\n"
        "- [Decisions](decisions/index.md): why.\n",
    )
    _write(root, ".okf/log.md", "# Log\n")
    _write(root, ".okf/manifesto.md", CONCEPT.format(title="Manifesto"))
    _write(
        root,
        ".okf/decisions/index.md",
        "# Decisions\n\n- [ADR 0001](0001-first.md): the first.\n",
    )
    _write(root, ".okf/decisions/0001-first.md", CONCEPT.format(title="ADR 0001"))


def _check(root: Path, *args: str) -> Result:
    """Run ``kmctl check`` on ``root``."""
    return CliRunner().invoke(app, ["check", "--path", str(root), *args])


def _findings(root: Path) -> list[dict]:
    """The error findings ``kmctl check --json`` reports for ``root``."""
    return [
        f for f in json.loads(_check(root, "--json").stdout) if f["level"] == "error"
    ]


def test_index_check_passes(tmp_path: Path) -> None:
    _good_repo(tmp_path)

    result = _check(tmp_path)

    assert result.exit_code == 0, result.output
    assert _findings(tmp_path) == []


def test_index_check_missing_entry(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(tmp_path, "docs/how-to/upgrade.md", "# Upgrade\n")
    _write(tmp_path, ".okf/decisions/0002-second.md", CONCEPT.format(title="ADR 0002"))

    result = _check(tmp_path)
    files = {f["file"] for f in _findings(tmp_path) if f["check"] == "index"}

    assert result.exit_code != 0
    assert files == {"docs/how-to/upgrade.md", ".okf/decisions/0002-second.md"}


def test_index_check_entry_without_file(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    (tmp_path / "docs/how-to/install.md").unlink()

    result = _check(tmp_path)
    [finding] = _findings(tmp_path)

    assert result.exit_code != 0
    assert finding["file"] == "docs/README.md"
    assert finding["line"] == 3
    assert finding["check"] == "index"


def test_index_check_unlinked_section(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(
        tmp_path,
        ".okf/practices/index.md",
        "# Practices\n\n- [One](one.md): a lesson.\n",
    )
    _write(tmp_path, ".okf/practices/one.md", CONCEPT.format(title="One"))

    result = _check(tmp_path)
    files = [f["file"] for f in _findings(tmp_path)]

    assert result.exit_code != 0
    assert files == [".okf/practices"]


def test_index_check_skips_missing_docs(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    for path in sorted((tmp_path / "docs").rglob("*"), reverse=True):
        path.rmdir() if path.is_dir() else path.unlink()
    (tmp_path / "docs").rmdir()

    result = _check(tmp_path)

    assert result.exit_code == 0, result.output
    assert "skipped docs/" in result.stdout


def test_check_json_findings(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(tmp_path, "docs/how-to/upgrade.md", "# Upgrade\n")

    data = json.loads(_check(tmp_path, "--json").stdout)

    assert isinstance(data, list)
    assert data
    for finding in data:
        assert {"check", "file", "line", "message"} <= finding.keys()


def test_check_prototype_readme_is_the_concept(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(
        tmp_path,
        ".okf/index.md",
        (tmp_path / ".okf/index.md").read_text()
        + "- [Prototypes](prototypes/index.md): spikes.\n",
    )
    _write(
        tmp_path,
        ".okf/prototypes/index.md",
        "# Prototypes\n\n- [Speed](speed/README.md): a spike.\n",
    )
    _write(tmp_path, ".okf/prototypes/speed/README.md", CONCEPT.format(title="Speed"))
    _write(tmp_path, ".okf/prototypes/speed/notes.md", "raw notes\n")

    assert _findings(tmp_path) == []


def test_check_ignores_entries_in_code_fences(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    readme = (tmp_path / "docs/README.md").read_text()
    fence = "\n```markdown\n- [Example](example.md): shown.\n```\n"
    _write(tmp_path, "docs/README.md", readme + fence)

    assert _findings(tmp_path) == []


def test_check_ignores_links_that_leave_the_folder(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    decisions = (tmp_path / ".okf/decisions/index.md").read_text()
    outside = "- [Outside](../outside.md): elsewhere.\n"
    _write(tmp_path, ".okf/decisions/index.md", decisions + outside)

    assert _findings(tmp_path) == []


def test_check_skips_hidden_pages(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(tmp_path, "docs/.drafts/wip.md", "# Draft\n")
    _write(tmp_path, ".okf/decisions/.scratch/note.md", "# Note\n")

    assert _findings(tmp_path) == []


def test_check_reports_non_utf8_index(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    (tmp_path / "docs/README.md").write_bytes(b"# Docs \xe9\n")

    result = _check(tmp_path)

    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "not UTF-8" in result.stdout


def test_check_ignores_entries_in_nested_fences(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    readme = (tmp_path / "docs/README.md").read_text()
    nested = "\n````markdown\n```\n- [Example](example.md): shown.\n```\n````\n"
    _write(tmp_path, "docs/README.md", readme + nested)

    assert _findings(tmp_path) == []


def test_check_non_utf8_root_index_is_one_finding(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    (tmp_path / ".okf/index.md").write_bytes(b'---\nokf_version: "0.2"\n---\n\xe9\n')

    findings = _findings(tmp_path)

    assert [f["file"] for f in findings] == [".okf/index.md"]
