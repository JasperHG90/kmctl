"""kmaudit briefing: each namespace's state and the next step, changing nothing (ADR 0043)."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from kmaudit import instructions
from kmaudit.cli import app
from typer.testing import CliRunner

from .fixtures.audit_repo import git, make_repo, store_claims

EXITS = "The CLI exits 1 when given more than one argument."
#: A check of EXITS that holds and notices a change to the code it matched.
CODE = {"op": "code", "pattern": "if len(sys.argv) > 2: $$$B", "paths": "src/tool.py"}


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The fixture repository, with claims stored for .okf."""
    root = make_repo(tmp_path / "repo")
    monkeypatch.chdir(root)
    store_claims(
        root,
        {"tool#parts": [(1, "point", EXITS), (2, "point", "The CLI writes out.txt.")]},
    )
    return root


def run(*args: str) -> tuple[int, str, str]:
    """Run kmaudit with ``args``; (exit code, stdout, stderr)."""
    result = CliRunner().invoke(app, list(args))
    return result.exit_code, result.stdout, result.stderr


def run_stdin(*args: str, stdin: str) -> tuple[int, str, str]:
    """Run kmaudit with ``args`` and ``stdin``; (exit code, stdout, stderr)."""
    result = CliRunner().invoke(app, list(args), input=stdin)
    return result.exit_code, result.stdout, result.stderr


def briefing() -> dict[str, dict]:
    """``kmaudit briefing --json``, by namespace."""
    code, out, err = run("briefing", "--json")
    assert code == 0, err
    return {b["namespace"]: b for b in json.loads(out)["namespaces"]}


def sqlite_bytes(root: Path) -> dict[str, str]:
    """Every .sqlite file under the repository, by path, with the hash of its bytes."""
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*.sqlite"))
    }


def test_counts_match_the_list_commands(repo: Path) -> None:
    from kmaudit.feedback import FeedbackIn
    from kmaudit.models import claim_id
    from kmaudit.ui import give_feedback

    exits = claim_id("tool", EXITS)
    answer = {"claim": exits, "steps": [CODE], "strength": "exact", "why": "w"}
    code, _, err = run_stdin("checks", "submit", "-", stdin=json.dumps([answer]))
    assert code == 0, err
    give_feedback(
        repo,
        FeedbackIn(claim=exits, target="check", vote="down", note="look again"),
        "human:t",
    )

    got = briefing()[".okf"]
    _, claims_out, _ = run("claims", "list", ".okf", "--json")
    _, checks_out, _ = run("checks", "list", ".okf", "--json")
    listed = json.loads(claims_out)
    checks = json.loads(checks_out)["counts"]

    assert got["sections"] == sum(d["sections"] for d in listed["documents"])
    assert got["claims"] == sum(listed["totals"].values())
    assert got["checks"] == checks
    assert set(got["checks"]) >= {"holds", "no check"}
    assert got["feedback"] == 1
    assert got["pending"] > 0
    assert got["next"].startswith("/extract-claims .okf")
    _, text, _ = run("briefing")
    assert "Next: /extract-claims .okf" in text


@pytest.mark.parametrize("step", range(1, 7))
def test_a_store_at_an_older_schema_step_still_briefs(repo: Path, step: int) -> None:
    """Rebuild the store at an earlier schema step, keeping its sections and claims."""
    import sqlite3

    from kmaudit.store import STEPS

    store = repo / ".kmaudit" / ".okf.sqlite"
    current = briefing()[".okf"]
    old = sqlite3.connect(store)
    old.row_factory = sqlite3.Row
    rebuilt = repo / "rebuilt.sqlite"
    new = sqlite3.connect(rebuilt)
    for part in STEPS[:step]:
        new.executescript(part)
    new.execute(f"PRAGMA user_version = {step}")
    for table in ("sections", "extractions", "claims"):
        cols = [c[1] for c in new.execute(f"PRAGMA table_info({table})")]
        for row in old.execute(f"SELECT * FROM {table}"):
            marks = ",".join("?" * len(cols))
            new.execute(
                f"INSERT INTO {table} ({','.join(cols)}) VALUES ({marks})",
                tuple(row[c] for c in cols),
            )
    new.commit()
    new.close()
    old.close()
    store.unlink()
    for side in store.parent.glob(".okf.sqlite-*"):
        side.unlink()
    rebuilt.rename(store)
    before = hashlib.sha256(store.read_bytes()).hexdigest()

    got = briefing()[".okf"]

    assert hashlib.sha256(store.read_bytes()).hexdigest() == before
    assert (got["sections"], got["claims"], got["pending"]) == (
        current["sections"],
        current["claims"],
        current["pending"],
    )
    assert got["checks"] == {"no check": 2}


def test_read_only_even_with_only_the_old_store_and_a_changed_page(repo: Path) -> None:
    old = repo / ".kmctl" / "audit.sqlite"
    old.parent.mkdir()
    shutil.move(repo / ".kmaudit" / ".okf.sqlite", old)
    shutil.rmtree(repo / ".kmaudit")
    before_pending = briefing()[".okf"]["pending"]
    tool = repo / ".okf" / "tool.md"
    tool.write_text(
        tool.read_text().replace("It reads `config.toml`", "It reads `settings.toml`")
    )
    before = sqlite_bytes(repo)

    after_pending = briefing()[".okf"]["pending"]

    assert sqlite_bytes(repo) == before
    assert not (repo / ".kmaudit").exists()
    assert after_pending == before_pending + 1


def test_a_store_keyed_under_previous_guidance_reads_as_up_to_date(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from kmaudit.sections import cut, resolve_target
    from kmaudit.store import Store
    from kmaudit.verbs import todo

    current = instructions.instructions_hash
    shutil.rmtree(repo / ".kmaudit")
    monkeypatch.setattr(instructions, "instructions_hash", lambda: "0ld0ld0ld0ld")
    store_claims(repo, {"tool#parts": [(1, "point", "The CLI writes out.txt.")]})
    target = resolve_target(repo / ".okf")
    with Store(target.root, target.namespace) as store:
        extracted = len(store.extracted())
    every = len(list(cut(target)))
    monkeypatch.setattr(instructions, "instructions_hash", current)
    stale = briefing()[".okf"]["pending"]
    monkeypatch.setattr(instructions, "PREVIOUS_HASHES", ("0ld0ld0ld0ld",))

    carried = briefing()[".okf"]["pending"]

    assert extracted > 0
    assert stale == every
    assert carried == every - extracted
    assert todo(repo / ".okf").counts.pending == carried


def test_never_fails_with_no_namespace_or_a_broken_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    git(empty, "init", "-q")
    monkeypatch.chdir(empty)
    code, out, err = run("briefing")
    assert (code, out, err) == (0, "", "")
    assert json.loads(run("briefing", "--json")[1]) == {"namespaces": []}

    (empty / ".kmaudit").mkdir()
    (empty / ".kmaudit" / "docs.sqlite").write_text("not a database")
    (empty / "docs").mkdir()
    (empty / "docs" / "a.md").write_text("# A\n\nText.\n")
    code, out, _ = run("briefing")
    json_code, json_out, _ = run("briefing", "--json")

    assert code == 0
    assert out.startswith("kmaudit briefing: unavailable")
    assert len(out.splitlines()) == 1
    assert json_code == 0
    assert json.loads(json_out)["namespaces"] == []
    assert json.loads(json_out)["unavailable"]


def test_a_nested_namespace_briefs(repo: Path) -> None:
    """briefing opens a nested namespace's store, named handbook%2Fguides.sqlite."""
    guides = repo / "handbook" / "guides"
    guides.mkdir(parents=True)
    (guides / "a.md").write_text("# A\n\n## Part\n\nThe tool writes out.txt.\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "handbook")
    code, _, err = run("claims", "todo", "handbook/guides", "--json")
    assert code == 0, err

    rows = briefing()

    assert "handbook/guides" in rows
    assert rows["handbook/guides"]["pending"] == 1
