"""The release flow's knowledge: decision 0012, the architecture page and the upgrade step."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from typer.testing import CliRunner

from kmctl import app
from kmctl.kinds import schema, skeleton
from kmctl.okf import front_matter

ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / ".okf" / "decisions" / "0012-releases-come-from-ci.md"
OVERVIEW = ROOT / ".okf" / "architecture" / "overview.md"
HOW_TO = ROOT / "docs" / "how-to" / "install-the-plugin-and-the-ci-action.md"
SETTING = "Allow GitHub Actions to create and approve pull requests"


def _json_ready(value: Any) -> Any:
    """``value`` as JSON carries it: PyYAML's dates and datetimes as ISO strings."""
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    return value


def _sections(text: str, level: str = "##") -> dict[str, str]:
    """The ``level`` headings of ``text`` outside code fences, heading to body, in order."""
    found: dict[str, list[str]] = {}
    body: list[str] = []
    fence = ""
    for line in text.splitlines():
        marker = re.match(r"\s*(`{3,})", line)
        if marker and not fence:
            fence = marker.group(1)
        elif marker and line.strip() == fence:
            fence = ""
        elif not fence and line.startswith(f"{level} "):
            body = found.setdefault(line[len(level) + 1 :].strip(), [])
            continue
        body.append(line)
    return {heading: "\n".join(lines) for heading, lines in found.items()}


def test_decision_0012_matches_the_decision_schema() -> None:
    """The record's front matter validates and its sections are the decision skeleton."""
    validator = Draft202012Validator(schema("decision"))

    errors = [
        e.message for e in validator.iter_errors(_json_ready(front_matter(DECISION)))
    ]

    assert errors == []
    assert list(_sections(DECISION.read_text())) == skeleton("decision")


def test_decision_0012_names_what_it_rejected_and_needs() -> None:
    """Decision names the rejected hatch-vcs and PyPI; Consequences names the setting."""
    sections = _sections(DECISION.read_text())

    assert "hatch-vcs" in sections["Decision"]
    assert "PyPI" in sections["Decision"]
    assert SETTING in sections["Consequences"]


def test_the_overview_shows_the_release_path() -> None:
    """The architecture page names both release workflows, in the diagram and its Depicts list."""
    text = OVERVIEW.read_text()
    depicts = _sections(text)["Depicts"]

    for name in ("release.yml", "release-tag.yml"):
        assert name in text.split("## Depicts")[0]
        assert name in depicts
    assert list(_sections(text))[-1] == "Depicts"


def test_the_how_to_has_an_upgrade_step() -> None:
    """A step of the how-to says how to move to a newer release tag and refresh the plugin."""
    steps = _sections(_sections(HOW_TO.read_text())["Steps"], "###")
    upgrade = [body for heading, body in steps.items() if "upgrade" in heading.lower()]

    assert len(upgrade) == 1
    assert (
        "uv tool install --force git+https://github.com/JasperHG90/Knowledge-management@v"
        in upgrade[0]
    )
    assert "kmctl plugin update" in upgrade[0]


def test_the_bundle_passes_kmctl_check() -> None:
    """``kmctl check`` passes on this repository with the new pages."""
    result = CliRunner().invoke(app, ["check", "--path", str(ROOT)])

    assert result.exit_code == 0, result.output
