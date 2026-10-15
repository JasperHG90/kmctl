import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from kmctl import app, plugin
from kmctl.briefing import WORD_BUDGET


def _invoke(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _repo(root: Path) -> Path:
    """A repository with a bundle, one concept due (unverified) and two live handoffs."""
    assert _invoke("init", "--path", str(root)).exit_code == 0
    for title in ("Earlier work", "Latest work"):
        result = _invoke(
            "new",
            "handoff",
            title,
            "--description",
            f"Where {title} stands.",
            "--path",
            str(root),
        )
        assert result.exit_code == 0, result.output
    return root


def _briefing(root: Path, *args: str) -> Result:
    return _invoke("briefing", "--path", str(root), *args)


def test_briefing_has_three_parts(tmp_path: Path) -> None:
    out = _briefing(_repo(tmp_path)).stdout

    assert "Knowledge in this repository" in out
    assert "Verbs:" in out
    assert "due for review" in out
    assert "every-touched-concept-is-logged" in out


def test_briefing_state_counts(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    due = json.loads(_invoke("review", "due", "--path", str(root), "--json").stdout)[
        "due"
    ]
    live = json.loads(_invoke("handoffs", "--path", str(root), "--json").stdout)

    state = json.loads(_briefing(root, "--json").stdout)["state"]

    assert state["due"] == len(due)
    assert state["live_handoffs"] == len(live) == 2
    assert state["newest_handoff"] == live[0]["title"]
    assert "manifesto" not in json.dumps(state)


def test_briefing_word_budget(tmp_path: Path) -> None:
    out = _briefing(_repo(tmp_path)).stdout

    assert len(out.split()) <= WORD_BUDGET, len(out.split())


def test_briefing_empty_repository(tmp_path: Path) -> None:
    result = _briefing(tmp_path)

    assert result.exit_code == 0
    assert "kmctl init" in result.stdout


def test_briefing_writes_nothing(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}

    _briefing(root)
    _briefing(root, "--json")

    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before


def test_briefing_json(tmp_path: Path) -> None:
    data = json.loads(_briefing(_repo(tmp_path), "--json").stdout)

    assert {"routing", "state", "rules"} <= data.keys()


def test_briefing_state_line_reads_right_for_one(tmp_path: Path) -> None:
    assert _invoke("init", "--path", str(tmp_path)).exit_code == 0
    # Verify init's first decision, so the manifesto is the one concept due.
    decision = (
        tmp_path / ".okf/decisions/0001-keep-project-knowledge-in-an-okf-bundle.md"
    )
    decision.write_text(
        decision.read_text().replace(
            "status: stable\n",
            "status: stable\nverified:\n  - by: human:test\n    at: 2026-10-15T00:00:00Z\n",
            1,
        )
    )
    _invoke(
        "new",
        "handoff",
        "Only one",
        "--description",
        "Where it stands.",
        "--path",
        str(tmp_path),
    )

    out = _briefing(tmp_path).stdout

    assert "1 concept due for review" in out
    assert "1 live handoff," in out


def _skill_names(plugin_dir: Path) -> list[str]:
    return sorted(p.name for p in (plugin_dir / "skills").iterdir() if p.is_dir())


def test_briefing_names_every_skill(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    out = _briefing(_repo(root)).stdout
    names = _skill_names(plugin._payload()[0])

    assert names
    assert [n for n in names if f"- {n}:" not in out] == []


def test_briefing_skills_are_read_at_run_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin_dir, marketplace = plugin._payload()
    copy = tmp_path / "payload"
    shutil.copytree(plugin_dir, copy)
    extra = copy / "skills" / "extra-skill"
    extra.mkdir()
    (extra / "SKILL.md").write_text(
        "---\nname: extra-skill\ndescription: Do one extra thing. Use when asked.\n---\n"
    )
    monkeypatch.setattr(plugin, "_payload", lambda: (copy, marketplace))
    root = tmp_path / "repo"
    root.mkdir()

    out = _briefing(_repo(root)).stdout

    assert "- extra-skill: Do one extra thing." in out
    assert [n for n in _skill_names(copy) if f"- {n}:" not in out] == []


def test_briefing_unchanged_by_the_seeded_files(tmp_path: Path) -> None:
    """The rule files, agent-file block and first decision init writes leave the briefing's text alone."""
    seeded, plain = tmp_path / "seeded", tmp_path / "plain"
    seeded.mkdir()
    assert _invoke("init", "--path", str(seeded)).exit_code == 0
    for rel in ("docs/README.md", ".okf/index.md", ".okf/log.md", ".okf/manifesto.md"):
        (plain / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(seeded / rel, plain / rel)
    assert (seeded / ".claude" / "rules").is_dir()

    with_seed = json.loads(_briefing(seeded, "--json").stdout)
    without = json.loads(_briefing(plain, "--json").stdout)

    for key in ("routing", "rules", "skills"):
        assert with_seed[key] == without[key], key
    assert [r["name"] for r in with_seed["rules"]] == [
        "audience-picks-the-folder",
        "docs-sorted-by-reader-intent",
        "docs-describe-what-exists",
        "prototypes-hold-their-scripts",
        "start-at-the-index",
        "kmctl-writes-the-structure",
        "every-touched-concept-is-logged",
        "decisions-are-never-rewritten",
        "trust-is-recorded",
    ]
