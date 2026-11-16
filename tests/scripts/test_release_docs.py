"""The release flow's knowledge: decision 0012, the architecture page and the upgrade step."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest
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
    """The record's front matter validates; its sections are the skeleton, then corrections."""
    validator = Draft202012Validator(schema("decision"))

    errors = [
        e.message for e in validator.iter_errors(_json_ready(front_matter(DECISION)))
    ]

    assert errors == []
    sections = list(_sections(DECISION.read_text()))
    assert sections[:3] == skeleton("decision")
    assert all(re.fullmatch(r"Correction, \d{4}-\d{2}-\d{2}", s) for s in sections[3:])


def test_decision_0012_names_what_it_rejected_and_needs() -> None:
    """Decision names the rejected hatch-vcs and PyPI; Consequences names the setting."""
    sections = _sections(DECISION.read_text())

    assert "hatch-vcs" in sections["Decision"]
    assert "PyPI" in sections["Decision"]
    assert SETTING in sections["Consequences"]


def test_decision_0012_corrects_for_releases_per_package() -> None:
    """A dated Correction names the package input, both tag families, kmaudit's VERSION file and the committed notes file."""
    sections = _sections(DECISION.read_text())
    corrections = [
        " ".join(body.split())
        for heading, body in sections.items()
        if heading.startswith("Correction, ")
    ]

    assert any(
        all(
            needle in c
            for needle in (
                "`package`",
                "`vX.Y.Z`",
                "`kmaudit-vX.Y.Z`",
                "`packages/kmaudit/VERSION`",
                "`.github/release-notes/TAG.md`",
                "Drafted-From",
                "Latest",
            )
        )
        for c in corrections
    )


def test_the_overview_shows_the_release_path() -> None:
    """The architecture page names both release workflows, in the diagram and its Depicts list."""
    text = OVERVIEW.read_text()
    depicts = _sections(text)["Depicts"]

    for name in ("release.yml", "release-tag.yml"):
        assert name in text.split("## Depicts")[0]
        assert name in depicts
    assert list(_sections(text))[-1] == "Depicts"


def test_the_how_to_has_an_upgrade_step() -> None:
    """A step of the how-to says how to move to a newer release tag and install the package again."""
    steps = _sections(_sections(HOW_TO.read_text())["Steps"], "###")
    upgrade = [body for heading, body in steps.items() if "upgrade" in heading.lower()]

    assert len(upgrade) == 1
    assert (
        "uv tool install --force git+https://github.com/JasperHG90/kmctl@v"
        in upgrade[0]
    )
    assert "apm install" in upgrade[0] and "kmctl plugin patch" in upgrade[0]


def test_the_bundle_passes_kmctl_check() -> None:
    """``kmctl check`` passes on this repository with the new pages."""
    result = CliRunner().invoke(app, ["check", "--path", str(ROOT)])

    assert result.exit_code == 0, result.output


DECISIONS = ROOT / ".okf" / "decisions"
ADR_0045 = "(0045-each-package-keeps-its-apm-package-and-version.md)"


def _corrections(path: Path) -> list[str]:
    """Each dated Correction section of the decision at ``path``, whitespace collapsed."""
    return [
        " ".join(body.split())
        for heading, body in _sections(path.read_text()).items()
        if heading.startswith("Correction, ")
    ]


def _watched() -> list[str]:
    """The paths in release-tag.yml's ``paths`` filter."""
    workflow = (ROOT / ".github" / "workflows" / "release-tag.yml").read_text()
    block = workflow.split("paths:\n", 1)[1]
    return re.findall(r"^\s+- (\S+)$", block.split("\n\n", 1)[0], re.MULTILINE)


@pytest.mark.parametrize(
    "name",
    [
        "0001-standalone-cli-installs-its-plugin.md",
        "0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code.md",
        "0012-releases-come-from-ci.md",
        "0014-apm-is-the-only-install-route.md",
        "0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest.md",
    ],
)
def test_decision_names_kmctl_s_apm_package_since_adr_0045(name: str) -> None:
    """A Correction names packages/kmctl/apm/apm.yml and links ADR 0045, so the old apm/ path is not the latest word."""
    assert any(
        "`packages/kmctl/apm/apm.yml`" in c and ADR_0045 in c
        for c in _corrections(DECISIONS / name)
    )


def test_decision_0012_names_both_version_sources_since_adr_0045() -> None:
    """ADR 0012's Correction for ADR 0045 names kmaudit's apm.yml and every path release-tag.yml watches."""
    watched = _watched()

    assert "packages/kmaudit/apm/apm.yml" in watched
    assert any(
        ADR_0045 in c and all(f"`{path}`" in c for path in watched)
        for c in _corrections(DECISION)
    )


@pytest.mark.parametrize(
    "number", ["0012-releases-come-from-ci", "0014-apm-is-the-only-install-route"]
)
def test_index_note_names_no_path_adr_0045_removed(number: str) -> None:
    """The index note for the decision names no bare apm/apm.yml and no apm/ folder outside packages/."""
    index = (DECISIONS / "index.md").read_text()
    entry = index.split(f"]({number}.md)", 1)[1].split("\n- [", 1)[0]
    note = " ".join(entry.split())

    assert not re.search(r"(?<![\w/])apm/apm\.yml", note)
    assert not re.search(r"(?<![\w/])in apm/", note)
