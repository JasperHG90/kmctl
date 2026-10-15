from pathlib import Path

from typer.testing import CliRunner, Result

from kmctl import app

TYPES = {
    "tutorial": (
        "tutorials",
        ["What you will build", "Before you start", "Steps", "What you learned"],
    ),
    "how-to": ("how-to", ["Before you start", "Steps", "Check it worked"]),
    "reference": ("reference", ["Summary", "Details"]),
    "explanation": (
        "explanation",
        ["The question", "How it works", "Why it is this way"],
    ),
}


def _invoke(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _repo(root: Path) -> Path:
    assert _invoke("init", "--path", str(root)).exit_code == 0
    return root


def _new_doc(root: Path, kind: str, title: str) -> Result:
    return _invoke("new", "doc", kind, title, "--path", str(root))


def test_new_doc_creates_page_per_type(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    for kind, (folder, headings) in TYPES.items():
        result = _new_doc(root, kind, f"First {kind}")
        page = root / "docs" / folder / f"first-{kind}.md"

        assert result.exit_code == 0, result.output
        assert page.read_text().startswith(f"# First {kind}\n"), kind
        assert all(f"## {h}" in page.read_text() for h in headings), kind


def test_new_doc_indexes_page(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    _new_doc(root, "how-to", "Install it")

    assert "](how-to/install-it.md)" in (root / "docs/README.md").read_text()
    assert _invoke("check", "--path", str(root)).exit_code == 0


def test_new_doc_refuses_without_index(tmp_path: Path) -> None:
    result = _new_doc(tmp_path, "how-to", "Install it")

    assert result.exit_code == 1
    assert "kmctl init" in result.stderr
    assert not (tmp_path / "docs").exists()


def test_new_doc_refuses_existing_page(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _new_doc(root, "how-to", "Install it")
    page = root / "docs/how-to/install-it.md"
    page.write_text("# Mine\n")

    result = _new_doc(root, "how-to", "Install it")

    assert result.exit_code == 1
    assert page.read_text() == "# Mine\n"


def test_new_doc_title_with_a_line_break_stays_listed(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = _new_doc(root, "how-to", "Install\nit")

    assert result.exit_code == 0, result.output
    assert (
        "- [Install it](how-to/install-it.md)" in (root / "docs/README.md").read_text()
    )
    assert _invoke("check", "--path", str(root)).exit_code == 0


def test_new_concept_title_with_a_line_break_stays_listed(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = _invoke(
        "new", "practice", "Two\nlines", "--description", "One.", "--path", str(root)
    )

    assert result.exit_code == 0, result.output
    assert _invoke("check", "--path", str(root)).exit_code == 0


def test_next_line_names_a_kmctl_step(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    out = _new_doc(root, "how-to", "Install it").stdout

    assert out.strip().splitlines()[-1].startswith("Next: ")
    assert "kmctl check" in out.strip().splitlines()[-1]
