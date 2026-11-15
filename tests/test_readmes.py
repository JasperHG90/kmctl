"""The root README maps the repository to the package READMEs and docs/, and every README link resolves."""

import re
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
