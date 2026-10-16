import json
import re
import shutil
from pathlib import Path

from conftest import okf_validate
from typer.testing import CliRunner

from kmctl import app
from kmctl.scaffold import FIRST_DECISION, RULE_FILES, ScaffoldResult, scaffold

ROOT = Path(__file__).resolve().parents[1]
BASE_FILES = ("docs/README.md", ".okf/index.md", ".okf/log.md", ".okf/manifesto.md")
RULES = tuple(f".claude/rules/{name}" for name in RULE_FILES)
DECISION = ".okf/decisions/0001-keep-project-knowledge-in-an-okf-bundle.md"
FILES = (
    *BASE_FILES,
    *RULES,
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
    assert sorted(second["skipped"]) == sorted([*BASE_FILES, *RULES, "CLAUDE.md"])


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


def test_init_warns_when_kept_index_misses_new_manifesto(tmp_path: Path) -> None:
    index = _partial_bundle(tmp_path)

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    # The one change to the kept index: the first decision's section link.
    assert (tmp_path / ".okf" / "index.md").read_text() == (
        index + "- [Decisions](decisions/index.md): the decisions.\n"
    )
    assert "index.md does not link the new manifesto" in result.stderr
    assert "log.md has no line for the new manifesto" in result.stderr


def test_init_json_lists_warnings(tmp_path: Path) -> None:
    _partial_bundle(tmp_path)

    data = json.loads(_init(tmp_path, "--json").stdout)

    assert len(data["warnings"]) == 2, data["warnings"]


def test_init_no_warning_when_kept_index_already_links_manifesto(
    tmp_path: Path,
) -> None:
    (tmp_path / ".okf").mkdir()
    index = '---\nokf_version: "0.2"\n---\n\n- [Manifesto](manifesto.md): the design.\n'
    (tmp_path / ".okf" / "index.md").write_text(index)
    (tmp_path / ".okf" / "log.md").write_text("# Log\n\n- Wrote `manifesto`.\n")

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


# Rule files (r1)


def test_init_writes_rule_files_for_any_repository(tmp_path: Path) -> None:
    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    for rel in RULES:
        text = (tmp_path / rel).read_text()
        assert rel in result.stdout, rel
        assert re.match(r"---\npaths: \[[^\]]+\]\n---\n", text), rel
        assert "<constraint name=" in text and "WHY:" in text, rel
        assert not re.search(r"loopctl|ticket|\.loop/", text, re.IGNORECASE), rel


def _packaged(name: str) -> str:
    return (ROOT / "src" / "kmctl" / "repo_rules" / name).read_text()


def test_init_overwrites_edited_rule(tmp_path: Path) -> None:
    _init(tmp_path)
    mine = tmp_path / ".claude" / "rules" / "okf-bundle.md"
    mine.write_text("my own rule\n")

    result = _init(tmp_path, "--json")

    assert result.exit_code == 0, result.output
    assert mine.read_text() == _packaged("okf-bundle.md")
    report = json.loads(result.stdout)
    assert ".claude/rules/okf-bundle.md" in report["updated"]
    assert ".claude/rules/okf-bundle.md" not in report["skipped"]


def test_init_names_a_replaced_rule(tmp_path: Path) -> None:
    _init(tmp_path)
    (tmp_path / ".claude" / "rules" / "okf-bundle.md").write_text("old\n")

    result = _init(tmp_path)

    assert (
        "updated .claude/rules/okf-bundle.md (replaced with kmctl's rule)"
        in result.stdout
    )


def test_init_skips_current_rule(tmp_path: Path) -> None:
    _init(tmp_path)
    rule = tmp_path / ".claude" / "rules" / "okf-bundle.md"
    before = rule.stat().st_mtime_ns

    result = _init(tmp_path, "--json")

    report = json.loads(result.stdout)
    assert ".claude/rules/okf-bundle.md" in report["skipped"]
    assert ".claude/rules/okf-bundle.md" not in report["updated"] + report["created"]
    assert rule.stat().st_mtime_ns == before


def test_init_leaves_other_rules(tmp_path: Path) -> None:
    other = tmp_path / ".claude" / "rules" / "my-rule.md"
    other.parent.mkdir(parents=True)
    other.write_text("mine\n")
    before = other.stat().st_mtime_ns

    for _ in range(2):
        report = json.loads(_init(tmp_path, "--json").stdout)
        listed = report["created"] + report["updated"] + report["skipped"]
        assert ".claude/rules/my-rule.md" not in listed

    assert other.read_text() == "mine\n"
    assert other.stat().st_mtime_ns == before


def test_init_leaves_a_rule_symlink_outside_the_repo(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("not ours\n")
    repo = tmp_path / "repo"
    rule = repo / ".claude" / "rules" / "okf-bundle.md"
    rule.parent.mkdir(parents=True)
    rule.symlink_to(outside)

    report = json.loads(_init(repo, "--json").stdout)

    assert outside.read_text() == "not ours\n"
    assert ".claude/rules/okf-bundle.md" in report["skipped"]
    assert any(
        ".claude/rules/okf-bundle.md is a symlink" in w for w in report["warnings"]
    )


def test_init_leaves_a_folder_at_a_rule_path(tmp_path: Path) -> None:
    folder = tmp_path / ".claude" / "rules" / "okf-bundle.md"
    folder.mkdir(parents=True)

    result = _init(tmp_path, "--json")

    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert folder.is_dir()
    assert ".claude/rules/okf-bundle.md" in report["skipped"]
    assert any(
        ".claude/rules/okf-bundle.md is not a file" in w for w in report["warnings"]
    )


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
        ".claude",
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
