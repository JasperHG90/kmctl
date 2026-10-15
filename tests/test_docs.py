"""kmctl's own README, docs/ pages and architecture page say what exists and pass its checks."""

import re
from pathlib import Path

from conftest import okf_validate
from typer.core import TyperGroup
from typer.main import get_command
from typer.testing import CliRunner

from kmctl import app

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
INSTALL = "uv tool install git+https://github.com/JasperHG90/Knowledge-management"


def _commands(
    group: TyperGroup, prefix: tuple[str, ...] = ()
) -> list[tuple[tuple[str, ...], object]]:
    """Every command and subcommand under ``group``, with the words that invoke it."""
    found = []
    for name, command in group.commands.items():
        words = (*prefix, name)
        found.append((words, command))
        if isinstance(command, TyperGroup):
            found += _commands(command, words)
    return found


def _links(text: str) -> set[str]:
    """The targets of the markdown links in ``text``, without anchors."""
    return {t.split("#")[0] for t in re.findall(r"\]\(([^)\s]+)\)", text)}


def _reference() -> str:
    return "\n".join(p.read_text() for p in (DOCS / "reference").glob("*.md"))


def test_readme_install_and_links() -> None:
    text = (ROOT / "README.md").read_text()
    links = _links(text)
    pages = sorted(p.relative_to(ROOT).as_posix() for p in DOCS.rglob("*.md"))

    assert INSTALL in text
    assert "kmctl plugin install" in text
    assert pages
    assert [p for p in pages if p not in links] == []


def test_docs_pages_by_type() -> None:
    for folder in ("tutorials", "how-to", "reference", "explanation"):
        pages = [p for p in (DOCS / folder).glob("*.md") if p.name != "README.md"]
        assert pages, folder

    result = CliRunner().invoke(app, ["check", "--path", str(ROOT)])

    assert result.exit_code == 0, result.output


def test_reference_covers_commands() -> None:
    text = _reference()
    commands = _commands(get_command(app))
    options = {
        opt
        for _, command in commands
        for param in command.params
        for opt in getattr(param, "opts", [])
        if opt.startswith("--")
    }

    assert [w for w, _ in commands if f"kmctl {' '.join(w)}" not in text] == []
    assert sorted(o for o in options if f"`{o}" not in text) == []


def _depicts(text: str) -> str:
    match = re.search(r"^## Depicts\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert match, "no ## Depicts section"
    return match.group(1)


def test_architecture_depicts_invariants() -> None:
    manifesto = (ROOT / ".okf" / "manifesto.md").read_text()
    invariants = set(re.findall(r"^- \*\*(I\d+)\.", manifesto, re.MULTILINE))
    depicts = _depicts((ROOT / ".okf" / "architecture" / "overview.md").read_text())

    assert invariants
    assert set(re.findall(r"\bI\d+\b", depicts)) == invariants


def test_bundle_valid_with_architecture() -> None:
    check = okf_validate(ROOT / ".okf")
    index = (ROOT / ".okf" / "index.md").read_text()

    assert check.returncode == 0, check.stdout + check.stderr
    assert "architecture/index.md" in _links(index)
