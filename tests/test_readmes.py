"""The root README maps the repository to the package READMEs and docs/, and every README link resolves."""

import json
import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
READMES = (
    ROOT / "README.md",
    ROOT / "packages" / "kmctl" / "README.md",
    ROOT / "packages" / "kmaudit" / "README.md",
)


def _relative_links(text: str) -> list[str]:
    """The markdown link and image targets in ``text`` that name a local file, without anchors."""
    targets = re.findall(r"\]\(([^)\s]+)\)", text) + re.findall(
        r'<img[^>]*\bsrc="([^"]+)"', text
    )
    return [
        t.split("#")[0]
        for t in targets
        if "://" not in t and not t.startswith(("#", "mailto:"))
    ]


def test_root_readme_is_a_short_map() -> None:
    """The root README stays under 80 lines and links both package READMEs and docs/."""
    readme = ROOT / "README.md"
    text = readme.read_text()
    links = {(ROOT / link).resolve() for link in _relative_links(text)}

    assert len(text.splitlines()) < 80
    for target in (
        ROOT / "packages" / "kmctl" / "README.md",
        ROOT / "packages" / "kmaudit" / "README.md",
    ):
        assert target in links, target
    assert any(link == ROOT / "docs" or ROOT / "docs" in link.parents for link in links)


@pytest.mark.parametrize("readme", READMES, ids=lambda p: str(p.relative_to(ROOT)))
def test_every_relative_link_resolves(readme: Path) -> None:
    """Each relative link in the README names a file or folder that exists."""
    links = _relative_links(readme.read_text())

    assert links
    assert [link for link in links if not (readme.parent / link).exists()] == []


REPO = "https://github.com/JasperHG90/kmctl"
CI_BADGE = f"{REPO}/actions/workflows/ci.yml/badge.svg?branch=main"
RELEASE = "https://img.shields.io/github/v/release/JasperHG90/kmctl?"
#: Each package's tag-family filter in its release badge, and its lifecycle.
PACKAGES = {"kmctl": ("filter=v*", "stable"), "kmaudit": ("filter=kmaudit-v*", "beta")}


def _badges(text: str) -> list[str]:
    """The image URLs of the badges in ``text``: markdown images whose target is a URL."""
    return re.findall(r"!\[[^\]]*\]\((https://[^)\s]+)\)", text)


def _root_entry(package: str) -> str:
    """The root README's Packages list entry for ``package``, joined to one line."""
    text = (ROOT / "README.md").read_text()
    entry = text.split(f"**[{package}](", 1)[1].split("\n- ", 1)[0]
    return " ".join(entry.split("\n\n", 1)[0].split())


def _query(url: str) -> list[str]:
    """The ``key=value`` parts of ``url``'s query string."""
    return url.split("?", 1)[1].split("&") if "?" in url else []


def _release_badge(badges: list[str], package: str) -> str:
    """The one release badge in ``badges`` that filters to ``package``'s tag family."""
    found = [
        b for b in badges if b.startswith(RELEASE) and PACKAGES[package][0] in _query(b)
    ]
    assert len(found) == 1, (package, badges)
    return found[0]


@pytest.mark.parametrize("readme", READMES, ids=lambda p: str(p.relative_to(ROOT)))
def test_readme_opens_with_ci_licence_and_python_badges(readme: Path) -> None:
    """Each README carries a CI badge for ci.yml on main, a licence badge and a Python badge before its first section."""
    head = readme.read_text().split("\n## ", 1)[0]
    badges = _badges(head)

    assert CI_BADGE in badges
    assert any("img.shields.io/github/license/JasperHG90/kmctl" in b for b in badges)
    assert any("img.shields.io/badge/python-3.12" in b for b in badges)


@pytest.mark.parametrize("package", PACKAGES)
def test_package_readme_has_its_lifecycle_and_release_badge(package: str) -> None:
    """A package README's head carries its own lifecycle badge and a release badge filtered to its own tags."""
    readme = ROOT / "packages" / package / "README.md"
    badges = _badges(readme.read_text().split("\n## ", 1)[0])
    lifecycle = PACKAGES[package][1]

    assert f"https://img.shields.io/badge/lifecycle-{lifecycle}-" in " ".join(badges)
    _release_badge(badges, package)
    other = next(p for p in PACKAGES if p != package)
    assert not any(
        b.startswith(RELEASE) and PACKAGES[other][0] in _query(b) for b in badges
    )


@pytest.mark.parametrize("package", PACKAGES)
def test_root_readme_entry_has_the_package_s_lifecycle_and_release_badge(
    package: str,
) -> None:
    """The root README's entry for each package carries that package's lifecycle badge and release badge."""
    badges = _badges(_root_entry(package))
    lifecycle = PACKAGES[package][1]

    assert f"https://img.shields.io/badge/lifecycle-{lifecycle}-" in " ".join(badges)
    _release_badge(badges, package)


def test_kmaudit_is_marked_beta_in_text() -> None:
    """kmaudit's README, its command reference and the root README's kmaudit entry say it is beta."""
    readme = (ROOT / "packages" / "kmaudit" / "README.md").read_text()
    reference = (ROOT / "docs" / "reference" / "kmaudit-commands.md").read_text()
    prose = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", readme.split("\n## ", 1)[0])

    assert re.search(r"\bbeta\b", prose)
    assert re.search(r"\bbeta\b", reference.split("\n## ", 1)[0])
    assert re.search(
        r"\bbeta\b", re.sub(r"!\[[^\]]*\]\([^)]*\)", "", _root_entry("kmaudit"))
    )


@pytest.mark.parametrize(
    ("package", "status"),
    [
        ("kmctl", "Development Status :: 5 - Production/Stable"),
        ("kmaudit", "Development Status :: 4 - Beta"),
    ],
)
def test_package_metadata_carries_its_development_status(
    package: str, status: str
) -> None:
    """Each package's pyproject declares the Development Status its lifecycle badge shows."""
    project = tomllib.loads(
        (ROOT / "packages" / package / "pyproject.toml").read_text()
    )["project"]

    assert status in project.get("classifiers", [])


DIRECTION = next((ROOT / ".okf" / "decisions").glob("0046-*.md"))


def test_direction_decision_states_both_directions() -> None:
    """Decision 0046 matches the decision schema, says which way each package works and links ADR 0043."""
    from jsonschema import Draft202012Validator

    from kmctl.kinds import schema, skeleton
    from kmctl.okf import front_matter

    meta = json.loads(json.dumps(front_matter(DIRECTION), default=str))
    errors = list(Draft202012Validator(schema("decision")).iter_errors(meta))
    text = DIRECTION.read_text()
    headings = re.findall(r"^## (.+)$", text, re.MULTILINE)
    decision = " ".join(text.split("## Decision", 1)[1].split("## ", 1)[0].split())

    assert errors == []
    assert headings[:3] == skeleton("decision")
    assert "**kmctl starts from the code and the decisions**" in decision
    assert "**kmaudit starts from `docs/` and `.okf/`**" in decision
    assert "(0043-the-audit-is-its-own-library-kmaudit-served-over-mcp.md)" in text


def test_root_readme_names_each_direction_and_links_the_decision() -> None:
    """The root README's kmctl entry says it starts from the code, kmaudit's that it starts from docs, and the map links decision 0046."""
    text = (ROOT / "README.md").read_text()
    links = {(ROOT / link).resolve() for link in _relative_links(text)}

    assert "starts from the code and the decisions" in _root_entry("kmctl")
    assert "starts from a folder of markdown docs" in _root_entry("kmaudit")
    assert DIRECTION.resolve() in links


def test_claude_md_routes_to_the_direction_decision() -> None:
    """CLAUDE.md's routing table has a row naming decision 0046 for which package a feature belongs in."""
    rows = [
        line
        for line in (ROOT / "CLAUDE.md").read_text().splitlines()
        if line.startswith("|")
    ]

    assert any(
        "Which package a feature belongs in" in row
        and f".okf/decisions/{DIRECTION.name}" in row
        for row in rows
    )
