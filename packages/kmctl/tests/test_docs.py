"""kmctl's own README, docs/ pages and architecture page say what exists and pass its checks."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import okf_validate
from typer.core import TyperGroup
from typer.main import get_command
from typer.testing import CliRunner

from kmctl import app
from kmctl.plugin import subdirectory_fragment

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"
#: kmctl's README, which holds its install and use; the root README is a short map.
README = ROOT / "packages" / "kmctl" / "README.md"
INSTALL = "uv tool install git+https://github.com/JasperHG90/kmctl"
#: kmctl's source at a ref: every release after v0.12.2 builds from packages/kmctl (ADR 0044).
#: The ref (group 1) never ends in a full stop, so a hint's closing one is left out.
AT_REF = re.compile(
    r"git\+https://github\.com/JasperHG90/kmctl@([^\s#'`]*[^\s#'`.])(#[^\s'`]*[^\s'`.])?"
)
SUBDIRECTORY = "#subdirectory=packages/kmctl"
#: The folder every kmaudit install line builds from, whatever its ref.
KMAUDIT_SUBDIRECTORY = "#subdirectory=packages/kmaudit"
#: A kmaudit install line names the package before its URL: ``kmaudit @`` or ``kmaudit[extra] @``.
KMAUDIT_NAME = re.compile(r"kmaudit(\[[^\]]*\])? @ ")
#: The files whose install lines the cutoff check reads, relative to the repository root.
INSTALL_FILES = (
    "packages/kmctl/README.md",
    "packages/kmaudit/README.md",
    "packages/kmctl/apm/claude/.apm/hooks/hooks.json",
    ".github/release-notes.md",
    ".github/release-notes-kmaudit.md",
)


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
    """kmctl's README holds its install and use and links every kmctl docs page, each link resolving."""
    text = README.read_text()
    flat = " ".join(text.split())
    links = {
        (README.parent / link).resolve()
        for link in _links(text)
        if link and "://" not in link
    }
    pages = sorted(
        p.resolve()
        for p in DOCS.rglob("*.md")
        if (p.parent == DOCS or p.name != "README.md")
        and not p.name.startswith("kmaudit-")
    )

    assert INSTALL in text
    assert "kmctl plugin install" in text
    for words in (
        "git: https://github.com/JasperHG90/kmctl.git",
        "path: packages/kmctl/apm",
        "#### Claude Code",
        "#### Antigravity",
        "#### OpenCode",
        "#### More than one",
        "### Upgrade",
        "### Remove",
        "kmctl plugin patch --undo",
    ):
        assert words in flat, words
    assert pages
    assert [str(p) for p in pages if p not in links] == []
    assert [str(p) for p in links if not p.exists()] == []


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


def _summary_rows(text: str) -> dict[str, str]:
    """The Summary table of the commands reference: command to its one-line text."""
    rows = re.findall(r"^\| `(kmctl[^`]*)` \| (.+?) \|$", text, re.MULTILINE)
    return {command: summary for command, summary in rows}


def test_reference_rows_quote_the_help_they_summarize() -> None:
    """The review due and briefing rows quote their help, which names what each covers."""
    rows = _summary_rows(_reference())
    helps = {
        f"kmctl {' '.join(words)}": (command.help or "").strip().splitlines()[0]
        for words, command in _commands(get_command(app))
        if command.help
    }

    for name in ("kmctl review due", "kmctl briefing"):
        assert rows[name].replace("`", "") == helps[name], name
    assert "docs/" in helps["kmctl review due"]
    assert "the rule for reading knowledge" in helps["kmctl briefing"]


def test_reference_new_json_keys_match_the_help() -> None:
    """kmctl new --json lists the same keys in the reference and in its help."""
    keys = "(id, path, created_section, updated)"
    [command] = [c for w, c in _commands(get_command(app)) if w == ("new", "decision")]
    [json_help] = [p.help for p in command.params if "--json" in getattr(p, "opts", [])]

    assert keys in (json_help or "")
    assert (
        keys.replace("(", "(`").replace(", ", "`, `").replace(")", "`)") in _reference()
    )


def _install_lines(root: Path) -> dict[str, tuple[str, str, bool]]:
    """Each install line at a ref under ``root``: its ref, its fragment and whether it installs kmaudit.

    A line installs kmaudit when it names ``kmaudit @`` (or ``kmaudit[extra] @``),
    builds from packages/kmaudit, or pins a ``kmaudit-v`` tag; every other line
    installs kmctl.
    """
    files = [root / rel for rel in INSTALL_FILES] + sorted(
        (root / "docs").rglob("*.md")
    )
    found = {}
    for path in files:
        text = path.read_text()
        for m in AT_REF.finditer(text):
            ref, rest = m.group(1), m.group(2) or ""
            before = text[text.rfind("\n", 0, m.start()) + 1 : m.start()]
            kmaudit = (
                KMAUDIT_NAME.search(before) is not None
                or ref.startswith("kmaudit-v")
                or "packages/kmaudit" in rest
            )
            found[f"{path.relative_to(root)}: {m.group(0)}"] = (ref, rest, kmaudit)
    return found


def _wrong_install_lines(found: dict[str, tuple[str, str, bool]]) -> list[str]:
    """The lines that build from the wrong folder or pin the other package's tag.

    kmctl's lines build from packages/kmctl exactly when their ref is after
    v0.12.2; kmaudit's always build from packages/kmaudit, at a ``kmaudit-v``
    tag or the release notes template's ``$tag``.
    """
    return [
        key
        for key, (ref, rest, kmaudit) in found.items()
        if (
            rest != KMAUDIT_SUBDIRECTORY
            or not (ref.startswith("kmaudit-v") or ref == "$tag")
            if kmaudit
            else rest != subdirectory_fragment(ref)
        )
    ]


def test_install_subdirectory_follows_the_cutoff_on_every_install_line() -> None:
    """Every kmctl install line in its README, the docs, hook hints and release notes template builds from packages/kmctl exactly when its ref is after v0.12.2, and every kmaudit line from packages/kmaudit."""
    found = _install_lines(ROOT)

    assert len([k for k, (_, _, kmaudit) in found.items() if not kmaudit]) >= 8
    assert _wrong_install_lines(found) == []


def test_install_lines_pass_after_a_kmaudit_pin(tmp_path: Path) -> None:
    """After ``release.py --package kmaudit set 0.2.0`` on a copy, kmaudit's pinned lines pass the check and kmctl's are unchanged."""
    files = [
        *INSTALL_FILES,
        *(p.relative_to(ROOT).as_posix() for p in DOCS.rglob("*.md")),
        "packages/kmaudit/apm/apm.yml",
        "packages/kmaudit/apm/claude/apm.yml",
    ]
    for rel in files:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    before = _install_lines(tmp_path)

    res = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "release.py"),
            "--package",
            "kmaudit",
            "set",
            "0.2.0",
            "--repo",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    found = _install_lines(tmp_path)

    assert res.returncode == 0, res.stderr
    pinned = {k for k, (ref, _, kmaudit) in found.items() if ref == "kmaudit-v0.2.0"}
    assert {k.split(":")[0] for k in pinned} == {
        "packages/kmaudit/README.md",
        "docs/reference/kmaudit-commands.md",
    }
    assert all(found[k][2] for k in pinned)
    assert {k: v for k, v in found.items() if not v[2]} == {
        k: v for k, v in before.items() if not v[2]
    }
    assert _wrong_install_lines(found) == []


def _section(text: str, heading: str) -> str:
    """The body of the markdown section headed ``heading`` (any level), up to the next heading at its level or above."""
    lines = text.splitlines()
    [start] = [
        i
        for i, ln in enumerate(lines)
        if ln.lstrip("#").strip() == heading and ln.startswith("#")
    ]
    level = len(lines[start]) - len(lines[start].lstrip("#"))
    body = []
    for ln in lines[start + 1 :]:
        if ln.startswith("#") and len(ln) - len(ln.lstrip("#")) <= level:
            break
        body.append(ln)
    return "\n".join(body)


@pytest.mark.parametrize(
    ("page", "heading"),
    [
        ("packages/kmctl/README.md", "Upgrade"),
        ("docs/how-to/install-kmctl-with-apm.md", "Upgrade from v0.12"),
    ],
)
def test_upgrade_from_v0_12_gives_the_steps_in_order(page: str, heading: str) -> None:
    """A v0.12 user installs the new CLI first, moves the entry, reinstalls, and checks with doctor last."""
    body = _section((ROOT / page).read_text(), heading)
    flat = " ".join(body.split())

    # The steps after the CLI install, each found after the one before it.
    cli = flat.find("#subdirectory=packages/kmctl")
    entry = flat.find("path: packages/kmctl/apm", cli)
    install = flat.find("apm install", entry)
    doctor = flat.find("kmctl doctor", install)
    assert cli != -1 and entry != -1 and install != -1 and doctor != -1, body
    assert flat.find("kmctl doctor") > entry, body
    assert "path: apm" in flat
    assert "ref: v" in flat
    assert "just upgrade" in flat


def test_upgrade_docs_link_kmaudit() -> None:
    """kmctl's README links kmaudit's README, the separate package that checks docs against the code."""
    text = (ROOT / "packages" / "kmctl" / "README.md").read_text()

    assert "](../kmaudit/README.md)" in text
