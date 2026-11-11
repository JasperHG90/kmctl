"""Tests for finding the lines shown for a claim, on a real git repository."""

import pathlib as plb
import subprocess

import pytest

from audit_cli.checks.anchors import Anchor
from audit_cli.checks.lines import NOTHING, LineFinder
from audit_cli.checks.steps import Repository

WORKFLOW = "jobs:\n  audit:\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          persist-credentials: false\n"
CLI = 'import typer\n\napp = typer.Typer()\n\n\n@app.command("verify")\ndef verify(by: str) -> None:\n    """Record a check."""\n'
CONCEPT = "---\ntype: decision\nsources:\n  - resource: .github/workflows/audit.yml\n---\n\n# Audit\n\nThe checkout keeps no credentials.\n"


@pytest.fixture
def finder(tmp_path: plb.Path) -> LineFinder:
    """A repository with a workflow, a CLI module and filler code."""
    root = tmp_path / "lined"
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / "src").mkdir()
    (root / ".github" / "workflows" / "audit.yml").write_text(WORKFLOW)
    (root / "src" / "cli.py").write_text(CLI)
    (root / "src" / "other.py").write_text("".join(f"value_{n} = {n}\n" for n in range(60)))
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    return LineFinder(Repository(root))


def test_a_claim_with_anchors_gets_the_lines_around_them(finder: LineFinder) -> None:
    """A resolved name shows the lines around its match in the file it was found in."""
    anchors = [Anchor("verify", "name", "defined", ["src/cli.py"])]
    found = finder.find("`verify` records a check.", "", anchors, "", [])
    assert found.source == "anchors" and found.files == ["src/cli.py"] and "def verify" in found.text


def test_a_claim_that_names_nothing_gets_lines_from_its_concepts_sources(finder: LineFinder) -> None:
    """With no anchor, the concept's sources front matter is the area, and the claim's words pick its lines."""
    found = finder.find("The checkout keeps no credentials.", "", [], CONCEPT, [])
    assert found.source == "area" and found.files == [".github/workflows/audit.yml"]
    assert "persist-credentials" in found.text


def test_a_command_claim_gets_the_file_that_registers_the_command(finder: LineFinder) -> None:
    """A command anchor with nowhere to show lines points at the code that registers its verb."""
    anchors = [Anchor("kmctl verify", "command", "found", ["kmctl verify"])]
    found = finder.find("`kmctl verify` records a person's check.", "", anchors, "", [])
    assert found.source == "commands" and found.files == ["src/cli.py"]


def test_with_no_area_every_readable_file_is_searched_and_a_miss_says_so(finder: LineFinder) -> None:
    """Without an area the whole repository is searched; words found nowhere show that nothing was found."""
    assert finder.find("The verify command records a check.", "", [], "", []).source == "everywhere"
    nothing = finder.find("Zebras graze quietly.", "", [], "", [])
    assert (nothing.source, nothing.text, nothing.files) == ("nothing", NOTHING, [])
