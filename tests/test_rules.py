"""The rules in .claude/rules/ that apm.yml does not install hold for kmctl.

The copied rules came from loop-harness. These tests fail when one still names
loop-harness, cites an ADR kmctl does not have, or points at a path that is
neither here nor planned.
"""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / ".claude" / "rules"

#: Folders and files the design or a registered ticket says will exist.
PLANNED = (
    ".okf/architecture/",
    ".okf/practices/",
    ".okf/proposals/",
    ".okf/prototypes/",
    ".okf/handoffs/",
    "plugin/",
    "docs/",
    "src/kmctl/",
    ".github/workflows/",
    "action.yml",
)


def _apm_managed() -> set[str]:
    """Installed names of the rules apm.yml lists: `<name>.instructions.md` lands as `<name>.md`."""
    manifest = yaml.safe_load((ROOT / "apm.yml").read_text())
    entries = (e.partition("#")[0] for e in manifest["dependencies"]["apm"])
    suffix = ".instructions.md"
    return {
        Path(e).name.removesuffix(suffix) + ".md" for e in entries if e.endswith(suffix)
    }


def _own_rules() -> list[Path]:
    managed = _apm_managed()
    return sorted(p for p in RULES.glob("*.md") if p.name not in managed)


def _cited_paths(text: str) -> list[str]:
    """Backticked tokens and paths: globs that look like repository paths."""
    tokens = re.findall(r"`([^`\s]+)`", text)
    match = re.search(r"^paths:\s*\[(.*)\]", text, re.MULTILINE)
    if match:
        tokens += re.findall(r'"([^"]+)"', match.group(1))
    return [t for t in tokens if "/" in t and _from_root(t)]


def _from_root(token: str) -> bool:
    """True for a path from the repository root, not a slash command or a producer id."""
    first = token.split("/", 1)[0]
    roots = (
        {p.name for p in ROOT.iterdir()}
        | {p.split("/", 1)[0] for p in PLANNED}
        | {"**"}
    )
    has_extension = (
        re.search(r"\.(py|md|json|jsonl|toml|ya?ml|sh|txt)$", token) is not None
    )
    return first in roots or (has_extension and not token.startswith("/"))


def _is_glob_or_folder(path: str) -> bool:
    return path.endswith("/") or any(c in path for c in "*<{")


def _resolves(path: str) -> bool:
    if (ROOT / path).exists() or path == "action.yml":
        return True
    prefix = re.split(r"[*<{]", path, maxsplit=1)[0]
    if _is_glob_or_folder(path) and (ROOT / prefix).exists():
        return True
    if path.startswith("**/"):
        return True
    planned = any(path == p or path.startswith(p) for p in PLANNED)
    return planned and _is_glob_or_folder(path)


@pytest.mark.parametrize("rule", _own_rules(), ids=lambda p: p.name)
def test_no_loop_harness_history(rule: Path) -> None:
    text = rule.read_text()
    found = re.findall(r"loop_harness|loop-harness|\bv[12]\b", text, re.IGNORECASE)
    assert not found, f"{rule.name} still names {sorted(set(found))}"


@pytest.mark.parametrize("rule", _own_rules(), ids=lambda p: p.name)
def test_cited_adrs_exist(rule: Path) -> None:
    decisions = ROOT / ".okf" / "decisions"
    missing = [
        n
        for n in re.findall(r"ADR (\d{4})", rule.read_text())
        if not list(decisions.glob(f"{n}-*.md"))
    ]
    assert not missing, (
        f"{rule.name} cites ADRs kmctl does not have: {sorted(set(missing))}"
    )


@pytest.mark.parametrize("rule", _own_rules(), ids=lambda p: p.name)
def test_cited_paths_exist_or_are_planned(rule: Path) -> None:
    bad = [p for p in _cited_paths(rule.read_text()) if not _resolves(p)]
    assert not bad, f"{rule.name} cites paths that neither exist nor are planned: {bad}"


def test_agents_md_drops_ticket_note() -> None:
    assert "adapt-copied-rules" not in (ROOT / "AGENTS.md").read_text()
