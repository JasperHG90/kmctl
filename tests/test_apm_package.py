"""kmctl's APM package, apm/, and the knowledge that describes it (ADR 0014).

apm/apm.yml names the package, carries the one release version and depends
only on a pinned okf-skills; the skills, the audit agent and the four
knowledge rules sit under apm/.apm/. The tests without a marker read files
only. The ``integration`` test serves this tree from a local git server and
runs ``kmctl plugin install --harness claude --source <it>`` in a scratch
consumer, which runs the real APM 0.33.0 and fetches okf-skills from GitHub.
HOME, CLAUDE_CONFIG_DIR and XDG_DATA_HOME point at scratch folders, and the
claude CLI is left off PATH, so nothing reaches the real Claude Code config.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from datetime import date, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.doctor import run_doctor
from kmctl.kinds import schema, skeleton
from kmctl.okf import front_matter
from scripts.release import APM_DOC, APM_FILES, DOC_FILES, MANIFEST, set_version

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "apm"
DOT_APM = PACKAGE / ".apm"
SKILLS = DOT_APM / "skills"
AGENT = DOT_APM / "agents" / "kmctl-auditor.md"
INSTRUCTIONS = DOT_APM / "instructions"
DECISIONS = ROOT / ".okf" / "decisions"
DECISION = DECISIONS / "0014-apm-is-the-only-install-route.md"
MANIFESTO = ROOT / ".okf" / "manifesto.md"
OVERVIEW = ROOT / ".okf" / "architecture" / "overview.md"
COMMANDS = ROOT / "docs" / "reference" / "commands.md"
PAGE = ROOT / APM_DOC
INSTALL_HOW_TO = ROOT / "docs" / "how-to" / "install-the-plugin-and-the-ci-action.md"
#: The Claude Code folder of whoever runs the tests, read before any test
#: points CLAUDE_CONFIG_DIR elsewhere, to check the integration test leaves it alone.
REAL_CLAUDE = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
WATCHED = ("rules/okf-bundle.md", "agents/kmctl-auditor.md", "skills/audit")
APM_CLI = "apm-cli==0.33.0"
OKF_PIN = re.compile(r"^scaccogatto/okf-skills#[0-9a-f]{40}$")
OKF_SKILLS = ("okf", "validate", "backfill", "visualize")
FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)
SKILL_NAMES = (
    "architecture-review",
    "audit",
    "continue",
    "decision-log-review",
    "handoff",
    "practices-review",
    "write-docs",
)
#: Each rule's ``paths:`` globs and the sha256 of its body as they were in
#: src/kmctl/repo_rules/ before the move into the package.
OLD_RULES = {
    "diagrams-stay-current": (
        [".okf/**", "src/**", "lib/**", "app/**", "pkg/**", "cmd/**"],
        "03926d0d53cbf70ff5ec9a58771ff8287a91175855de0bada657a7d34b2712ac",
    ),
    "docs-layout": (
        ["docs/**", ".okf/**", "README.md"],
        "1ef431044b15db9f35ff9cc71ca627fc42f8c7b1cce2f2ceba74b4c779a864e4",
    ),
    "manifesto-invariants": (
        [".okf/manifesto.md", "tests/**", "test/**"],
        "d887d1cfcd72f0ca7126d91a1a4bc550cdf3db9ac47f66727edebb9b207bb5a1",
    ),
    "okf-bundle": (
        [".okf/**"],
        "c3c6fd59ea590ea52def9d98fd1b86628c9f97bade5062e1ba274b74cbdc5e60",
    ),
}


def _load(path: Path) -> dict[str, Any]:
    """The YAML mapping in ``path``."""
    return yaml.safe_load(path.read_text())


def _split(text: str) -> tuple[dict[str, Any], str]:
    """The front matter and the body of a markdown file; no front matter reads as empty."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end]) or {}, text[end + 5 :]


def _dev_items() -> list[str]:
    """The names of the dev rules and skills the root apm.yml installs here."""
    names = []
    for entry in _load(ROOT / "apm.yml")["dependencies"]["apm"]:
        path = entry.partition("#")[0]
        names.append(path.rsplit("/", 1)[1].removesuffix(".instructions.md"))
    return names


# r1: the package --------------------------------------------------------------


def test_package_names_itself_and_has_a_version() -> None:
    """apm/apm.yml has a name and a version, both of which APM requires."""
    data = _load(PACKAGE / "apm.yml")

    assert data["name"] == "kmctl"
    assert isinstance(data["version"], str) and data["version"]


def test_package_depends_only_on_a_pinned_okf() -> None:
    """The one dependency is okf-skills at a full commit; there is no git: parent."""
    deps = _load(PACKAGE / "apm.yml")["dependencies"]

    assert list(deps) == ["apm"]
    [okf] = deps["apm"]
    assert isinstance(okf, str) and OKF_PIN.match(okf), okf
    assert "parent" not in (PACKAGE / "apm.yml").read_text()


def test_package_holds_the_skills_and_the_agent() -> None:
    """The 7 skills and the auditor sit under apm/.apm/, nothing else beside them."""
    assert sorted(p.name for p in SKILLS.iterdir()) == list(SKILL_NAMES)
    assert all((SKILLS / name / "SKILL.md").is_file() for name in SKILL_NAMES)
    assert sorted(p.name for p in (DOT_APM / "agents").iterdir()) == [
        "kmctl-auditor.md"
    ]
    assert sorted(p.name for p in DOT_APM.iterdir()) == [
        "agents",
        "instructions",
        "skills",
    ]


def test_package_rules_apply_to_the_old_globs_with_the_old_bodies() -> None:
    """Each rule's applyTo is its old paths, comma-joined, and its body is unchanged."""
    found = sorted(p.name for p in INSTRUCTIONS.iterdir())
    assert found == sorted(f"{name}.instructions.md" for name in OLD_RULES)
    for name, (globs, body_sha) in OLD_RULES.items():
        meta, body = _split((INSTRUCTIONS / f"{name}.instructions.md").read_text())
        assert meta == {"applyTo": ", ".join(globs)}, name
        assert hashlib.sha256(body.encode()).hexdigest() == body_sha, name


def test_package_old_layout_is_gone() -> None:
    """plugin/, the marketplace file and src/kmctl/repo_rules/ no longer exist."""
    for rel in ("plugin", ".claude-plugin/marketplace.json", "src/kmctl/repo_rules"):
        assert not (ROOT / rel).exists(), rel


# r2: the one version source -----------------------------------------------------


def test_version_copies_equal_the_package() -> None:
    """The root apm.yml carries apm/apm.yml's version, the one release version."""
    versions = {rel.as_posix(): str(_load(ROOT / rel)["version"]) for rel in APM_FILES}

    assert MANIFEST.as_posix() == "apm/apm.yml"
    assert versions == dict.fromkeys(
        ("apm.yml", "apm/apm.yml"), versions["apm/apm.yml"]
    )


def test_version_installed_cli_matches_the_package() -> None:
    """The kmctl this tree builds reports apm/apm.yml's version."""
    assert version("kmctl") == str(_load(PACKAGE / "apm.yml")["version"])


def test_wheel_reports_the_set_version_and_carries_the_skills(tmp_path: Path) -> None:
    """After ``set 9.8.7`` the built wheel is 9.8.7 and holds every skill file."""
    project = tmp_path / "project"
    project.mkdir()
    for name in ("pyproject.toml", "README.md", *map(str, APM_FILES)):
        (project / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / name, project / name)
    for folder in ("src", "apm/.apm", "docs"):
        shutil.copytree(
            ROOT / folder,
            project / folder,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    set_version(project, "9.8.7")
    assert {str(_load(project / rel)["version"]) for rel in APM_FILES} == {"9.8.7"}

    build = subprocess.run(
        ["uv", "build", "-q", "--wheel", "-o", str(tmp_path / "dist"), str(project)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert build.returncode == 0, build.stderr
    [wheel] = (tmp_path / "dist").glob("*.whl")
    assert wheel.name == "kmctl-9.8.7-py3-none-any.whl"
    names = set(zipfile.ZipFile(wheel).namelist())
    want = {
        f"kmctl/_skills/{p.relative_to(SKILLS).as_posix()}"
        for p in SKILLS.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    assert want <= names
    assert "kmctl/_agents/kmctl-auditor.md" in names
    instructions = ROOT / "apm" / ".apm" / "instructions"
    for path in instructions.glob("*.instructions.md"):
        assert f"kmctl/_instructions/{path.name}" in names
    assert not [n for n in names if "_plugin" in n or "marketplace" in n]


# r10: the repository's own rules ------------------------------------------------


def test_rule_paths_scope_to_the_apm_package() -> None:
    """No rule here scopes to plugin/; the ones that did scope to apm/ instead."""
    rules = ROOT / ".claude" / "rules"
    paths = {p.stem: _split(p.read_text())[0].get("paths") for p in rules.glob("*.md")}

    assert [
        n for n, globs in paths.items() if any("plugin/" in g for g in globs or [])
    ] == []
    for name in (
        "skills-are-thin",
        "skills-via-skill-creator",
        "adversarial-reviews",
        "cli-version-floor",
        "diagrams-stay-current",
    ):
        assert any(g.startswith("apm/") for g in paths[name]), name
        assert "plugin/" not in (rules / f"{name}.md").read_text(), name


# r11: the decision, the manifesto and the docs ---------------------------------


def _json_ready(value: Any) -> Any:
    """``value`` as JSON carries it: PyYAML's dates and datetimes as ISO strings."""
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    return value


def _sections(text: str) -> dict[str, str]:
    """The ``##`` headings of ``text`` outside code fences, heading to body, in order."""
    found: dict[str, list[str]] = {}
    body: list[str] = []
    fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            fence = not fence
        elif not fence and line.startswith("## "):
            body = found.setdefault(line[3:].strip(), [])
            continue
        body.append(line)
    return {heading: "\n".join(lines) for heading, lines in found.items()}


def _flat(text: str) -> str:
    """``text`` with every run of whitespace made one space."""
    return " ".join(text.split())


def test_docs_decision_matches_the_decision_schema() -> None:
    """The new decision's front matter validates and its sections are the decision skeleton."""
    validator = Draft202012Validator(schema("decision"))

    errors = [
        e.message for e in validator.iter_errors(_json_ready(front_matter(DECISION)))
    ]

    assert errors == []
    assert list(_sections(DECISION.read_text())) == skeleton("decision")
    assert front_matter(DECISION)["status"] == "stable"


def test_docs_decision_records_each_choice() -> None:
    """The record names the route, the hook, the rules, --source, --force and the old installs."""
    sections = {k: _flat(v) for k, v in _sections(DECISION.read_text()).items()}
    decision = sections["Decision"]

    for words in (
        "kmctl plugin install --harness",
        "apm install",
        "settings.json",
        "apm/.apm/instructions",
        "--source",
        "--force",
        "kmctl@kmctl",
        "apm uninstall",
        "Rejected",
    ):
        assert words in decision, words
    text = _flat(DECISION.read_text())
    for adr in ("0001", "0003", "0011", "0012", "0013"):
        assert f"ADR {adr}" in text, adr


def test_docs_superseded_records_point_at_the_new_one() -> None:
    """ADR 0013 and ADR 0003 are deprecated, with a Correction naming the new record."""
    for old in (
        "0013-kmctl-installs-through-apm-too.md",
        "0003-claude-code-plugin-first-depends-on-okf.md",
    ):
        path = DECISIONS / old
        assert front_matter(path)["status"] == "deprecated", old
        corrections = [
            body
            for heading, body in _sections(path.read_text()).items()
            if heading.startswith("Correction, ")
        ]
        assert any(DECISION.name in body for body in corrections), old


@pytest.mark.parametrize(
    ("record", "words"),
    [
        ("0001-standalone-cli-installs-its-plugin.md", "apm/apm.yml"),
        (
            "0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code.md",
            "kmctl plugin install",
        ),
        ("0012-releases-come-from-ci.md", "apm/apm.yml"),
    ],
)
def test_docs_changed_records_name_what_changed(record: str, words: str) -> None:
    """ADR 0001, 0011 and 0012 each carry a 2026-10-16 Correction that names the new record."""
    path = DECISIONS / record
    sections = _sections(path.read_text())
    heading = next(
        (h for h in sections if h.startswith("Correction, 2026-10-16")), None
    )

    assert heading is not None, record
    assert DECISION.name in sections[heading], record
    assert words in _flat(sections[heading]), record
    assert front_matter(path)["status"] == "stable", record


def test_docs_manifesto_parts_name_the_apm_route() -> None:
    """The manifesto's Parts describe the APM package installed by kmctl plugin install."""
    sections = _sections(MANIFESTO.read_text())
    parts = _flat(sections["Parts"])

    assert "kmctl plugin install --harness" in parts
    assert "APM" in parts and "ADR 0014" in parts
    assert "tests/test_plugin.py" in sections["Invariants"]


@pytest.mark.parametrize(
    "page",
    [MANIFESTO, OVERVIEW, COMMANDS, PAGE, INSTALL_HOW_TO],
    ids=lambda p: p.name,
)
def test_docs_pages_drop_the_marketplace_route(page: Path) -> None:
    """None of these pages still describes plugin/ or the claude marketplace route."""
    text = page.read_text()

    for old in (
        "plugin/",
        "marketplace.json",
        "/reload-plugins",
        "scaccogatto marketplace",
        "XDG_DATA_HOME/kmctl",
        "claude plugin install",
    ):
        assert old not in text, old


def test_docs_overview_names_the_package_and_the_hook_writer() -> None:
    """The architecture overview shows apm/.apm, settings.json and plugin.py."""
    text = OVERVIEW.read_text()
    depicts = _sections(text)["Depicts"]

    assert "apm/.apm" in text
    assert "settings.json" in text
    assert "src/kmctl/plugin.py" in depicts


def test_docs_commands_reference_names_the_install_options() -> None:
    """The commands reference documents every install option and kmctl doctor."""
    text = _flat(COMMANDS.read_text())

    for option in ("--harness", "--source", "--force", "--scope"):
        assert option in text, option
    assert "kmctl doctor" in text


def test_docs_install_how_to_uses_the_harness_option() -> None:
    """The plugin install how-to installs with --harness claude and links the APM page."""
    text = INSTALL_HOW_TO.read_text()
    commands = "\n".join(FENCE.findall(text))

    assert "kmctl plugin install --harness claude" in commands
    assert "(install-kmctl-with-apm.md)" in text


def test_docs_apm_page_says_a_hand_added_entry_gets_no_hook() -> None:
    """The APM how-to says what a hand entry leaves out and how to get it."""
    text = _flat(PAGE.read_text())
    commands = "\n".join(FENCE.findall(PAGE.read_text()))

    assert "no SessionStart hook" in text
    assert "kmctl plugin install --harness claude" in text
    assert "- JasperHG90/Knowledge-management/apm#v" in commands
    assert "scaccogatto/okf-skills" not in commands
    assert "--trust-transitive-mcp" not in commands
    cli = commands.index(
        "uv tool install git+https://github.com/JasperHG90/Knowledge-management"
    )
    assert cli < commands.index("apm install")


def test_docs_release_set_moves_the_page_pins(tmp_path: Path) -> None:
    """``scripts/release.py set`` points the page's package and CLI lines at the new tag."""
    for rel in (*APM_FILES, APM_DOC, *DOC_FILES):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)

    set_version(tmp_path, "9.8.7")

    text = (tmp_path / APM_DOC).read_text()
    pins = re.findall(r"JasperHG90/Knowledge-management/apm(#\S*)?", text)
    assert pins and set(pins) == {"#v9.8.7"}
    assert "Knowledge-management@v9.8.7\n" in text


# r9: a real consumer ----------------------------------------------------------


def _kmctl(*args: str) -> Result:
    """Run kmctl in-process with ``args``."""
    return CliRunner().invoke(app, list(args))


def _same_tree(want: Path, got: Path) -> None:
    """Assert ``got`` holds exactly the files of ``want``, byte for byte."""
    want_files = sorted(p.relative_to(want) for p in want.rglob("*") if p.is_file())
    got_files = sorted(p.relative_to(got) for p in got.rglob("*") if p.is_file())
    assert got_files == want_files, got
    for rel in want_files:
        assert (got / rel).read_bytes() == (want / rel).read_bytes(), rel


@pytest.mark.integration
def test_consumer_gets_the_package_hook_and_okf_but_no_dev_items(
    consumer: Path, served: str, tmp_path: Path
) -> None:
    """``kmctl plugin install --harness claude`` against the served tree installs everything once."""
    before = {rel: (REAL_CLAUDE / rel).exists() for rel in WATCHED}

    result = _kmctl("plugin", "install", "--harness", "claude", "--source", served)
    again = _kmctl("plugin", "install", "--harness", "claude", "--source", served)

    assert result.exit_code == 0, result.output
    assert again.exit_code == 0, again.output
    claude = consumer / ".claude"
    for name in SKILL_NAMES:
        _same_tree(SKILLS / name, claude / "skills" / name)
    assert (claude / "agents" / "kmctl-auditor.md").read_bytes() == AGENT.read_bytes()
    for name, (globs, _) in OLD_RULES.items():
        meta, body = _split((claude / "rules" / f"{name}.md").read_text())
        assert meta == {"paths": globs}, name
        assert body.lstrip("\n") == _split(
            (INSTRUCTIONS / f"{name}.instructions.md").read_text()
        )[1].lstrip("\n"), name
    assert all((claude / "skills" / s / "SKILL.md").is_file() for s in OKF_SKILLS)
    settings = json.loads((claude / "settings.json").read_text())
    commands = [
        hook["command"]
        for group in settings["hooks"]["SessionStart"]
        for hook in group["hooks"]
    ]
    assert len([c for c in commands if "kmctl briefing" in c]) == 1
    servers = json.loads((consumer / ".mcp.json").read_text())["mcpServers"]
    assert list(servers) == ["okf-bundle"]
    dev = set(_dev_items())
    assert len(dev) == 16
    written = [p.relative_to(consumer).parts for p in consumer.rglob("*")]
    assert [
        "/".join(parts)
        for parts in written
        if parts[0] not in {".git", "apm_modules"}
        and (set(parts[:-1]) & dev or parts[-1].split(".")[0] in dev)
    ] == []
    assert "jasperhg90/skills" not in (consumer / "apm.lock.yaml").read_text().lower()
    checks = {c.id: c for c in run_doctor(consumer).checks}
    for cid in ("lock", "files", "okf-skills", "hook", "okf-mcp", "old-plugin"):
        assert checks[f"claude.{cid}"].ok, checks[f"claude.{cid}"]
    after = {rel: (REAL_CLAUDE / rel).exists() for rel in WATCHED}
    assert after == before, f"the install wrote into {REAL_CLAUDE}"
