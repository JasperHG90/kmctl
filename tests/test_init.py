import json
import re
import shutil
from pathlib import Path

import pytest
from conftest import okf_validate
from typer.testing import CliRunner

from kmctl import app, plugin
from kmctl.scaffold import (
    FIRST_DECISION,
    MANIFESTO_LINE,
    SUMMARY_LINE,
    ScaffoldResult,
    scaffold,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_FILES = (
    "docs/README.md",
    ".okf/index.md",
    ".okf/log.md",
    ".okf/manifesto.md",
    ".okf/summary.md",
)
DECISION = ".okf/decisions/0001-keep-project-knowledge-in-an-okf-bundle.md"
FILES = (
    *BASE_FILES,
    "CLAUDE.md",
    ".okf/decisions/index.md",
    DECISION,
)
START, END = "<!-- kmctl:start -->", "<!-- kmctl:end -->"


def _init(root: Path, *args: str):
    return CliRunner().invoke(app, ["init", "--path", str(root), *args])


def _snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    """Every file under ``root`` with its bytes and modification time."""
    return {
        p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file()
    }


def test_init_creates_docs_and_bundle(tmp_path: Path) -> None:
    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    for f in FILES:
        assert (tmp_path / f).is_file(), f
        assert f in result.stdout, f


def test_init_twice_changes_nothing(tmp_path: Path) -> None:
    _init(tmp_path)
    before = _snapshot(tmp_path)

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    assert "created" not in result.stdout.lower()


def test_init_keeps_existing_files(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / ".okf").mkdir()
    (tmp_path / "docs" / "README.md").write_text("my docs\n")
    (tmp_path / ".okf" / "manifesto.md").write_text("my manifesto\n")

    _init(tmp_path)

    assert (tmp_path / "docs" / "README.md").read_text() == "my docs\n"
    assert (tmp_path / ".okf" / "manifesto.md").read_text() == "my manifesto\n"


@pytest.mark.parametrize("rel", [f for f in FILES if f != "CLAUDE.md"])
def test_init_keeps_each_edited_file(tmp_path: Path, rel: str) -> None:
    """A second init leaves a file the user edited byte for byte, and lists it as neither created nor updated.

    CLAUDE.md is left out: its kmctl block is the documented exception, and
    test_init_claude_md_appends_and_keeps_text covers the text around it.
    """
    _init(tmp_path)
    path = tmp_path / rel
    path.write_text(path.read_text() + "\nA line the user wrote.\n")
    before = _snapshot(tmp_path)

    result = _init(tmp_path, "--json")

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    report = json.loads(result.stdout)
    assert rel not in report["created"] + report["updated"]


def test_init_bundle_is_conformant(tmp_path: Path) -> None:
    _init(tmp_path)

    check = okf_validate(tmp_path / ".okf")

    assert check.returncode == 0, check.stdout + check.stderr


def test_init_creates_no_empty_folders(tmp_path: Path) -> None:
    _init(tmp_path)

    dirs = [p for p in tmp_path.rglob("*") if p.is_dir()]
    assert [p for p in dirs if not any(p.iterdir())] == []


def test_init_json_output(tmp_path: Path) -> None:
    first = json.loads(_init(tmp_path, "--json").stdout)
    second = json.loads(_init(tmp_path, "--json").stdout)

    assert sorted(first["created"]) == sorted(FILES)
    assert first["skipped"] == first["updated"] == []
    assert second["created"] == second["updated"] == []
    assert sorted(second["skipped"]) == sorted([*BASE_FILES, "CLAUDE.md"])


def test_init_refuses_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "typo"

    result = _init(missing)

    assert result.exit_code != 0
    assert not missing.exists()


def test_init_refuses_file_path(tmp_path: Path) -> None:
    target = tmp_path / "a-file"
    target.write_text("")

    result = _init(target)

    assert result.exit_code != 0
    assert result.exception is None or isinstance(result.exception, SystemExit)


def _partial_bundle(root: Path) -> str:
    (root / ".okf").mkdir()
    index = '---\nokf_version: "0.2"\n---\n\n# Bundle\n'
    (root / ".okf" / "index.md").write_text(index)
    (root / ".okf" / "log.md").write_text("# Log\n")
    return index


SUMMARY_ENTRY = f"- [Summary](summary.md): {SUMMARY_LINE}\n"
MANIFESTO_ENTRY = f"- [Manifesto](manifesto.md): {MANIFESTO_LINE}\n"


def test_init_links_new_pages_from_a_kept_index(tmp_path: Path) -> None:
    index = _partial_bundle(tmp_path)

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert (tmp_path / ".okf" / "index.md").read_text() == (
        index
        + SUMMARY_ENTRY
        + MANIFESTO_ENTRY
        + "- [Decisions](decisions/index.md): the decisions.\n"
    )
    log = (tmp_path / ".okf" / "log.md").read_text()
    assert "- Added `manifesto` with `kmctl init`." in log
    assert "- Added `summary` with `kmctl init`." in log
    assert "warning" not in result.stderr
    assert "linked   .okf/manifesto.md from .okf/index.md" in result.stdout
    assert "linked   .okf/summary.md from .okf/index.md" in result.stdout
    check = CliRunner().invoke(app, ["check", "--path", str(tmp_path)])
    assert check.exit_code == 0, check.output


def test_init_json_lists_linked_pages_and_no_warnings(tmp_path: Path) -> None:
    _partial_bundle(tmp_path)

    data = json.loads(_init(tmp_path, "--json").stdout)

    assert data["warnings"] == []
    assert data["linked"] == [".okf/manifesto.md", ".okf/summary.md"]
    assert ".okf/index.md" in data["updated"] and ".okf/log.md" in data["updated"]


def test_init_update_adds_the_summary_to_an_old_bundle(tmp_path: Path) -> None:
    """A bundle from before the summary: update writes it, links it, and check passes."""
    _init(tmp_path)
    okf = tmp_path / ".okf"
    fresh_index = (okf / "index.md").read_text()
    (okf / "summary.md").unlink()
    (okf / "index.md").write_text(fresh_index.replace(SUMMARY_ENTRY, ""))
    log = (okf / "log.md").read_text().replace("`manifesto`, `summary`", "`manifesto`")
    (okf / "log.md").write_text(log)

    result = CliRunner().invoke(app, ["update", "--path", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "warning" not in result.stderr
    assert (okf / "index.md").read_text() == fresh_index
    assert (okf / "log.md").read_text() == (
        log.rstrip("\n") + "\n- Added `summary` with `kmctl init`.\n"
    )
    check = CliRunner().invoke(app, ["check", "--path", str(tmp_path)])
    assert check.exit_code == 0, check.output
    before = _snapshot(tmp_path)
    again = CliRunner().invoke(app, ["update", "--path", str(tmp_path)])
    assert again.exit_code == 0, again.output
    assert _snapshot(tmp_path) == before


def test_init_update_says_no_log_line_when_the_kept_log_is_not_utf8(
    tmp_path: Path,
) -> None:
    """With a kept log.md that is not UTF-8, the linked line does not claim a log line was written."""
    _init(tmp_path)
    okf = tmp_path / ".okf"
    fresh_index = (okf / "index.md").read_text()
    (okf / "summary.md").unlink()
    (okf / "index.md").write_text(fresh_index.replace(SUMMARY_ENTRY, ""))
    (okf / "log.md").write_bytes(b"\xff\xfe not utf-8\n")

    result = CliRunner().invoke(app, ["update", "--path", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "linked   .okf/summary.md from .okf/index.md\n" in result.stdout
    assert "with a line in .okf/log.md" not in result.stdout
    assert "log.md is not UTF-8" in result.stderr


def test_init_update_links_the_manifesto_after_a_wrapped_entry(tmp_path: Path) -> None:
    """A missing manifesto goes in after the summary's entry, even one wrapped over lines."""
    _init(tmp_path)
    okf = tmp_path / ".okf"
    (okf / "manifesto.md").unlink()
    head = '---\nokf_version: "0.2"\n---\n\n# Bundle\n\n'
    summary = (
        "- [Summary](summary.md): what the bundle knows,\n  wrapped onto two lines.\n"
    )
    rest = "- [Decisions](decisions/index.md): the decisions.\n"
    (okf / "index.md").write_text(head + summary + rest)

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert (okf / "index.md").read_text() == head + summary + MANIFESTO_ENTRY + rest
    check = CliRunner().invoke(app, ["check", "--path", str(tmp_path)])
    assert check.exit_code == 0, check.output
    before = _snapshot(tmp_path)
    assert _init(tmp_path).exit_code == 0
    assert _snapshot(tmp_path) == before


def test_init_no_warning_when_kept_index_already_links_manifesto(
    tmp_path: Path,
) -> None:
    (tmp_path / ".okf").mkdir()
    index = (
        '---\nokf_version: "0.2"\n---\n\n- [Manifesto](manifesto.md): the design.\n'
        "- [Summary](summary.md): start here.\n"
    )
    (tmp_path / ".okf" / "index.md").write_text(index)
    (tmp_path / ".okf" / "log.md").write_text(
        "# Log\n\n- Wrote `manifesto` and `summary`.\n"
    )

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert "warning" not in result.stderr


def test_init_warns_on_non_utf8_kept_index(tmp_path: Path) -> None:
    (tmp_path / ".okf").mkdir()
    (tmp_path / ".okf" / "index.md").write_bytes(
        b'---\nokf_version: "0.2"\n---\n\xe9\n'
    )

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert result.exception is None
    assert "not UTF-8" in result.stderr


# Rules come with kmctl's APM package, not from init (apm-only-install r8)


def test_init_writes_no_rules(tmp_path: Path) -> None:
    """init writes nothing in .claude/; the knowledge rules come with the APM package."""
    result = _init(tmp_path, "--json")

    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    listed = report["created"] + report["updated"] + report["skipped"]
    assert [rel for rel in listed if rel.startswith(".claude/")] == []
    assert not (tmp_path / ".claude").exists()


def test_init_leaves_existing_rules(tmp_path: Path) -> None:
    """A rule already in .claude/rules/, even one named like kmctl's, is left alone."""
    rules = tmp_path / ".claude" / "rules"
    rules.mkdir(parents=True)
    for name in ("okf-bundle.md", "my-rule.md"):
        (rules / name).write_text("mine\n")
    before = _snapshot(rules)

    for _ in range(2):
        report = json.loads(_init(tmp_path, "--json").stdout)
        listed = report["created"] + report["updated"] + report["skipped"]
        assert [rel for rel in listed if rel.startswith(".claude/")] == []

    assert _snapshot(rules) == before


def test_init_next_line_installs_the_package_with_apm(tmp_path: Path) -> None:
    """init's Next: line starts with installing kmctl's package with APM, which brings the rules."""
    last = _init(tmp_path).stdout.strip().splitlines()[-1]

    assert last.startswith("Next: install kmctl's package with APM")
    assert "apm install" in last and "kmctl plugin patch" in last
    assert "knowledge rules" in last
    assert "plugin install" not in last


def test_init_help_says_rules_come_from_plugin_install() -> None:
    help_text = CliRunner().invoke(app, ["init", "--help"], terminal_width=80).stdout
    flat = " ".join(help_text.split())

    assert "It writes no rules" in flat
    assert "apm install" in flat and "kmctl plugin patch" in flat


# The agent-file block (r2)


def _block(text: str) -> str:
    assert text.count(START) == text.count(END) == 1, text
    return text[text.index(START) : text.index(END) + len(END)]


def test_init_claude_md_written_when_missing(tmp_path: Path) -> None:
    _init(tmp_path)

    block = _block((tmp_path / "CLAUDE.md").read_text())
    for where in (
        "docs/",
        ".okf/manifesto.md",
        ".okf/decisions/",
        ".okf/architecture/",
    ):
        assert where in block, where
    assert "kmctl new decision" in block
    assert "Keep `.okf/architecture/` matching the code" in block
    assert "Run `kmctl check` before you finish" in block
    assert not (tmp_path / "AGENTS.md").exists()


def test_init_claude_md_appends_and_keeps_text(tmp_path: Path) -> None:
    mine = "# My project\n\nBuild with make.\n"
    (tmp_path / "CLAUDE.md").write_text(mine)
    (tmp_path / "AGENTS.md").write_text(mine)

    result = _init(tmp_path)

    for name in ("CLAUDE.md", "AGENTS.md"):
        text = (tmp_path / name).read_text()
        assert text.startswith(mine), name
        assert text.replace(_block(text), "").rstrip() == mine.rstrip(), name
        assert f"updated {name}" in result.stdout, name


def test_init_claude_md_replaces_only_the_block(tmp_path: Path) -> None:
    before, after = "# Top\n\n", "\n\n## Bottom\n\nKeep me.\n"
    old = f"{START}\nold routing\n{END}"
    (tmp_path / "AGENTS.md").write_text(before + old + after)

    _init(tmp_path)

    text = (tmp_path / "AGENTS.md").read_text()
    assert text.startswith(before) and text.endswith(after)
    assert "old routing" not in text
    assert ".okf/decisions/" in _block(text)
    assert (tmp_path / "CLAUDE.md").read_text() == "@AGENTS.md\n"


def test_init_claude_md_symlink_gets_one_block(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# Agents\n")
    (tmp_path / "CLAUDE.md").symlink_to("AGENTS.md")

    _init(tmp_path)
    _init(tmp_path)

    assert (tmp_path / "CLAUDE.md").is_symlink()
    _block((tmp_path / "AGENTS.md").read_text())


def test_init_claude_md_second_run_adds_no_block(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# Mine\n")
    _init(tmp_path)

    result = _init(tmp_path)

    _block((tmp_path / "CLAUDE.md").read_text())
    assert "kept    CLAUDE.md" in result.stdout


def test_init_claude_md_with_broken_markers_is_left_alone(tmp_path: Path) -> None:
    mine = f"# Mine\n\n{START}\nhalf a block\n"
    (tmp_path / "CLAUDE.md").write_text(mine)

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert (tmp_path / "CLAUDE.md").read_text() == mine
    assert "CLAUDE.md has <!-- kmctl:start --> without" in result.stderr


# CLAUDE.md beside AGENTS.md imports it (init-claude-md-always r1)


def test_init_agents_only_adds_block_and_writes_import(tmp_path: Path) -> None:
    mine = "# Agents\n\nBuild with make.\n"
    (tmp_path / "AGENTS.md").write_text(mine)

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    text = (tmp_path / "AGENTS.md").read_text()
    assert text.startswith(mine)
    assert text.replace(_block(text), "").rstrip() == mine.rstrip()
    assert (tmp_path / "CLAUDE.md").read_text() == "@AGENTS.md\n"
    assert "created CLAUDE.md" in result.stdout
    assert "updated AGENTS.md" in result.stdout


def test_init_agents_only_rule_leaves_empty_repo_with_block_in_claude_md(
    tmp_path: Path,
) -> None:
    _init(tmp_path)

    _block((tmp_path / "CLAUDE.md").read_text())
    assert not (tmp_path / "AGENTS.md").exists()


def test_init_agents_only_twice_changes_nothing(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# Agents\n")
    _init(tmp_path)
    before = _snapshot(tmp_path)

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    assert (tmp_path / "CLAUDE.md").read_text() == "@AGENTS.md\n"
    assert "kept    CLAUDE.md" in result.stdout


def test_init_agents_only_importing_claude_md_gets_no_block(tmp_path: Path) -> None:
    mine = "# Mine\n\n@AGENTS.md\n\nUse uv.\n"
    (tmp_path / "CLAUDE.md").write_text(mine)
    (tmp_path / "AGENTS.md").write_text("# Agents\n")

    _init(tmp_path)

    assert (tmp_path / "CLAUDE.md").read_text() == mine
    _block((tmp_path / "AGENTS.md").read_text())


# Symlinks that are dangling or leave the repository (init-claude-md-always r2)


def _repo_and_outside(tmp_path: Path) -> tuple[Path, Path]:
    repo, outside = tmp_path / "repo", tmp_path / "outside"
    repo.mkdir()
    outside.mkdir()
    return repo, outside


def test_init_unsafe_link_dangling_claude_md_is_left_alone(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").symlink_to("missing.md")

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert (tmp_path / "CLAUDE.md").is_symlink()
    assert not (tmp_path / "missing.md").exists()
    assert not (tmp_path / "AGENTS.md").exists()
    assert "CLAUDE.md is a symlink to missing.md" in result.stderr


def test_init_unsafe_link_dangling_claude_md_beside_agents_md(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# Agents\n")
    (tmp_path / "CLAUDE.md").symlink_to("missing.md")

    result = _init(tmp_path)

    assert (tmp_path / "CLAUDE.md").is_symlink()
    assert not (tmp_path / "missing.md").exists()
    _block((tmp_path / "AGENTS.md").read_text())
    assert "CLAUDE.md is a symlink to missing.md" in result.stderr


def test_init_unsafe_link_claude_md_outside_repo(tmp_path: Path) -> None:
    repo, outside = _repo_and_outside(tmp_path)
    (outside / "theirs.md").write_text("# Theirs\n")
    (repo / "CLAUDE.md").symlink_to(outside / "theirs.md")
    (repo / "AGENTS.md").symlink_to(outside / "gone.md")

    result = _init(repo)

    assert result.exit_code == 0, result.output
    assert (outside / "theirs.md").read_text() == "# Theirs\n"
    assert not (outside / "gone.md").exists()
    assert (repo / "CLAUDE.md").is_symlink() and (repo / "AGENTS.md").is_symlink()
    assert f"CLAUDE.md is a symlink to {outside / 'theirs.md'}" in result.stderr
    assert f"AGENTS.md is a symlink to {outside / 'gone.md'}" in result.stderr


def test_init_unsafe_link_agents_md_with_no_claude_md(tmp_path: Path) -> None:
    repo, outside = _repo_and_outside(tmp_path)
    (outside / "agents.md").write_text("# Theirs\n")
    (repo / "AGENTS.md").symlink_to(outside / "agents.md")

    result = _init(repo)

    assert result.exit_code == 0, result.output
    assert (outside / "agents.md").read_text() == "# Theirs\n"
    assert not (repo / "CLAUDE.md").exists()
    assert "AGENTS.md is a symlink to" in result.stderr
    assert "wrote no CLAUDE.md" in result.stderr
    assert "fix the link, then run kmctl init again" in result.stderr
    assert (repo / ".okf" / "manifesto.md").is_file()


def test_init_unsafe_link_dangling_agents_md_with_no_claude_md(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").symlink_to("missing.md")

    result = _init(tmp_path)

    assert not (tmp_path / "CLAUDE.md").exists()
    assert not (tmp_path / "missing.md").exists()
    assert "AGENTS.md is a symlink to missing.md" in result.stderr
    assert "wrote no CLAUDE.md" in result.stderr


def test_init_unsafe_link_importing_claude_md_beside_dangling_agents_md(
    tmp_path: Path,
) -> None:
    (tmp_path / "CLAUDE.md").write_text("@AGENTS.md\n")
    (tmp_path / "AGENTS.md").symlink_to("missing.md")

    result = _init(tmp_path)

    assert (tmp_path / "CLAUDE.md").read_text() == "@AGENTS.md\n"
    assert not (tmp_path / "missing.md").exists()
    assert "AGENTS.md is a symlink to missing.md" in result.stderr


def test_init_unsafe_link_rule_writes_through_in_repo_link_once(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "docs").mkdir()
    (real / "docs" / "agents.md").write_text("# Agents\n")
    (real / "CLAUDE.md").symlink_to("docs/agents.md")
    (real / "AGENTS.md").symlink_to("CLAUDE.md")
    via = tmp_path / "via"
    via.symlink_to(real)

    result = _init(via)
    _init(via)

    assert result.exit_code == 0, result.output
    assert "symlink" not in result.stderr
    assert (real / "CLAUDE.md").is_symlink()
    _block((real / "docs" / "agents.md").read_text())


# This repository's record of the import rule (init-claude-md-always r4)


def test_init_agents_import_documented() -> None:
    adr = next((ROOT / ".okf" / "decisions").glob("0011-*.md")).read_text()
    corrections = adr.split("## Correction, 2026-10-15")[1:]
    assert any("@AGENTS.md" in c and "symlink" in c for c in corrections)

    help_text = CliRunner().invoke(app, ["init", "--help"], terminal_width=80).stdout
    assert "@AGENTS.md" in " ".join(help_text.split())
    for doc in (ScaffoldResult.__doc__, scaffold.__doc__):
        assert "@AGENTS.md" in " ".join((doc or "").split())
    reference = (ROOT / "docs" / "reference" / "commands.md").read_text()
    assert "@AGENTS.md" in reference
    log = (ROOT / ".okf" / "log.md").read_text()
    assert "@AGENTS.md" in log


# The first decision (r3)


def _sections(text: str) -> list[str]:
    return re.findall(r"^## (.+)$", text, re.MULTILINE)


def test_init_first_decision_in_a_fresh_repo(tmp_path: Path) -> None:
    result = _init(tmp_path)

    text = (tmp_path / DECISION).read_text()
    assert f'title: "ADR 0001: {FIRST_DECISION}"' in text
    assert _sections(text) == ["Context", "Decision", "Consequences"]
    decision = text.split("## Decision", 1)[1].split("## Consequences", 1)[0]
    for alternative in ("wiki", "README", "Nothing"):
        assert alternative in decision, alternative
    index = (tmp_path / ".okf" / "decisions" / "index.md").read_text()
    assert "(0001-keep-project-knowledge-in-an-okf-bundle.md)" in index
    log = (tmp_path / ".okf" / "log.md").read_text()
    assert "`decisions/0001-keep-project-knowledge-in-an-okf-bundle`" in log
    assert DECISION in result.stdout
    assert _invoke_check(tmp_path).exit_code == 0
    validate = okf_validate(tmp_path / ".okf")
    assert validate.returncode == 0, validate.stdout + validate.stderr


def _invoke_check(root: Path):
    return CliRunner().invoke(app, ["check", "--path", str(root)])


def test_init_first_decision_not_written_twice(tmp_path: Path) -> None:
    shutil.copytree(ROOT / ".okf", tmp_path / ".okf")
    _init(tmp_path)
    decisions = tmp_path / ".okf" / "decisions"
    written = sorted(decisions.glob("*-keep-project-knowledge-in-an-okf-bundle.md"))
    assert len(written) == 1
    snapshot = {p.name: p.read_bytes() for p in decisions.iterdir()}

    _init(tmp_path)

    assert {p.name: p.read_bytes() for p in decisions.iterdir()} == snapshot


def test_init_first_decision_kept_when_title_exists(tmp_path: Path) -> None:
    _init(tmp_path)
    decisions = tmp_path / ".okf" / "decisions"
    record = decisions / "0001-keep-project-knowledge-in-an-okf-bundle.md"
    moved = decisions / "0003-keep-project-knowledge-in-an-okf-bundle.md"
    record.rename(moved)
    index = decisions / "index.md"
    index.write_text(index.read_text().replace("0001-", "0003-"))
    for n in ("0001", "0002"):
        CliRunner().invoke(
            app,
            [
                "new",
                "decision",
                f"Other {n}",
                "--description",
                "x.",
                "--path",
                str(tmp_path),
            ],
        )
    before = _snapshot(tmp_path)

    _init(tmp_path)

    assert _snapshot(tmp_path) == before


# Next steps (r4)


def test_init_next_steps_in_order(tmp_path: Path) -> None:
    out = _init(tmp_path).stdout

    last = out.strip().splitlines()[-1]
    assert last.startswith("Next: ")
    steps = [
        last.find(s)
        for s in (".okf/manifesto.md", ".okf/architecture/", "kmctl new decision")
    ]
    assert -1 not in steps and steps == sorted(steps), last
    assert "operator" in last


# Twice (r5)


def test_init_twice_with_existing_agent_files_changes_nothing(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# Agents\n")
    (tmp_path / "CLAUDE.md").symlink_to("AGENTS.md")
    _init(tmp_path)
    before = _snapshot(tmp_path)

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        ".okf",
        "AGENTS.md",
        "CLAUDE.md",
        "docs",
    ]


# This repository's record of the change (r8)


def test_decision_record_for_seeding(tmp_path: Path) -> None:
    decisions = ROOT / ".okf" / "decisions"
    adr2 = "0002-briefing-and-rules-injected-by-the-cli.md"
    adr3 = "0003-claude-code-plugin-first-depends-on-okf.md"
    found = [
        p
        for p in sorted(decisions.glob("[0-9][0-9][0-9][0-9]-*.md"))
        if ".claude/rules/" in (t := p.read_text())
        and "CLAUDE.md" in t
        and f"({adr2})" in t
        and f"({adr3})" in t
    ]
    assert found, "no decision records why init writes rule files and the block"
    correction = (decisions / adr2).read_text().split("## Correction", 2)
    assert any(f"({found[0].name})" in part for part in correction[1:])

    help_text = CliRunner().invoke(app, ["init", "--help"], terminal_width=80).stdout
    flat = " ".join(help_text.split())
    assert "kmctl block" in flat and "first decision" in flat
    assert "never changed." not in flat
    doc = " ".join((ScaffoldResult.__doc__ or "").split())
    assert "kmctl block" in doc and "first decision" in doc


def test_init_first_decision_logged_as_init(tmp_path: Path) -> None:
    _init(tmp_path)

    log = (tmp_path / ".okf" / "log.md").read_text()
    assert (
        "`decisions/0001-keep-project-knowledge-in-an-okf-bundle` with `kmctl init`"
        in log
    )
    assert "with `kmctl new decision`" not in log


def test_init_reports_kept_files_it_changed_as_updated(tmp_path: Path) -> None:
    shutil.copytree(ROOT / ".okf", tmp_path / ".okf")
    for record in (tmp_path / ".okf" / "decisions").glob("*-keep-project-knowledge-*"):
        record.unlink()

    result = _init(tmp_path, "--json")
    data = json.loads(result.stdout)

    for rel in (".okf/log.md", ".okf/decisions/index.md"):
        assert rel in data["updated"], rel
        assert rel not in data["skipped"], rel


def test_init_broken_marker_warning_says_what_is_wrong(tmp_path: Path) -> None:
    cases = {
        "end-only": (f"# Mine\n{END}\n", f"has {END} with no {START} before it"),
        "two-starts": (f"{START}\na\n{START}\nb\n{END}\n", "markers, not one of each"),
        "start-only": (f"# Mine\n{START}\n", f"has {START} without a {END} after it"),
    }
    for name, (text, expected) in cases.items():
        root = tmp_path / name
        root.mkdir()
        (root / "CLAUDE.md").write_text(text)

        result = _init(root)

        assert (root / "CLAUDE.md").read_text() == text, name
        assert expected in result.stderr, name


def test_init_human_output_names_why_each_file_was_updated(tmp_path: Path) -> None:
    shutil.copytree(ROOT / ".okf", tmp_path / ".okf")
    for record in (tmp_path / ".okf" / "decisions").glob("*-keep-project-knowledge-*"):
        record.unlink()
    (tmp_path / "CLAUDE.md").write_text("# Mine\n")

    out = _init(tmp_path).stdout

    assert "updated CLAUDE.md (kmctl block)" in out
    for rel in (".okf/log.md", ".okf/decisions/index.md"):
        assert f"updated {rel} (first decision's entry)" in out, rel
        assert f"updated {rel} (kmctl block)" not in out, rel


def test_init_agents_only_folder_is_not_a_file(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").mkdir()

    result = _init(tmp_path)

    assert _block((tmp_path / "CLAUDE.md").read_text())
    assert "AGENTS.md is not a file" in result.stderr
    (tmp_path / "CLAUDE.md").write_text("@AGENTS.md\n")

    again = _init(tmp_path)

    assert _block((tmp_path / "CLAUDE.md").read_text()), (
        "an import of a folder loads nothing"
    )
    assert "AGENTS.md is not a file" in again.stderr


def test_init_block_names_freshness(tmp_path: Path) -> None:
    _init(tmp_path)

    block = _block((tmp_path / "CLAUDE.md").read_text())

    assert "--source" in block
    assert "--stale-after" in block


# consumer-surfaces r4: the block names each installed harness's rules folder (#23)

RULES_FOLDERS = {
    "claude": ".claude/rules/",
    "antigravity": ".agents/rules/",
    "opencode": ".opencode/rules/",
}


def _installed_for(root: Path, *harnesses: str) -> None:
    """Write the apm.yml ``apm install`` reads, naming kmctl's package for ``harnesses``."""
    (root / "apm.yml").write_text(
        json.dumps(
            {
                "name": "repo",
                "version": "0.1.0",
                "dependencies": {"apm": [plugin.new_entry()]},
                "targets": list(harnesses),
            }
        )
    )


@pytest.mark.parametrize(
    "harnesses",
    [("antigravity",), ("claude",), ("opencode",), ("claude", "antigravity")],
)
def test_update_block_names_the_rules_folder_of_each_installed_harness(
    tmp_path: Path, harnesses: tuple[str, ...]
) -> None:
    (tmp_path / "AGENTS.md").write_text("# Agents\n")
    _installed_for(tmp_path, *harnesses)

    result = CliRunner().invoke(app, ["update", "--path", str(tmp_path)])

    assert result.exit_code == 0, result.output
    block = _block((tmp_path / "AGENTS.md").read_text())
    for harness, folder in RULES_FOLDERS.items():
        assert (f"`{folder}`" in block) == (harness in harnesses), (harness, block)


def test_init_block_names_every_rules_folder_with_its_tool_when_none_is_found(
    tmp_path: Path,
) -> None:
    _init(tmp_path)

    block = _block((tmp_path / "CLAUDE.md").read_text())

    for folder, tool in zip(
        RULES_FOLDERS.values(), ("Claude Code", "Antigravity", "OpenCode"), strict=True
    ):
        assert f"`{folder}` ({tool})" in block, block


@pytest.mark.parametrize("name", ["apm.yml", "apm.lock.yaml"])
def test_init_over_a_non_utf8_apm_file_still_writes_the_rules_folder_block(
    tmp_path: Path, name: str
) -> None:
    """An apm.yml or apm.lock.yaml that is not UTF-8 counts as no harness found, not a crash."""
    (tmp_path / name).write_bytes(b"\xff\xfe targets: [antigravity]\n")

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    block = _block((tmp_path / "CLAUDE.md").read_text())
    assert all(f"`{folder}`" in block for folder in RULES_FOLDERS.values()), block
