"""The audit store: where it lives, that git ignores it, schema steps and parallel writers."""

import sqlite3
import threading
from pathlib import Path

import pytest
from kmaudit import store as store_module
from kmaudit.models import Claim
from kmaudit.sections import cut, resolve_target
from kmaudit.store import STEPS, Store, Verdict

from .fixtures.audit_repo import git, make_repo


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return make_repo(tmp_path / "repo")


def test_store_at_the_repository_root_and_ignored(repo: Path) -> None:
    target = resolve_target(repo / ".okf" / "tool.md")
    with Store(target.root) as store:
        store.refresh(cut(target), target.concepts)

    assert (repo / ".kmctl" / "audit.sqlite").is_file()
    assert (repo / ".kmctl" / ".gitignore").read_text() == "*\n"
    assert git(repo, "status", "--porcelain") == ""


def test_fresh_database_opens_at_the_newest_step(repo: Path) -> None:
    with Store(repo) as store:
        assert store.version == len(STEPS)


def test_older_database_is_brought_up(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (repo / ".kmctl").mkdir()
    db = sqlite3.connect(repo / ".kmctl" / "audit.sqlite")
    db.execute("CREATE TABLE marker (x INTEGER)")
    db.execute("PRAGMA user_version = 0")
    db.commit()
    db.close()
    monkeypatch.setattr(store_module, "STEPS", [*STEPS, "CREATE TABLE later (y TEXT)"])

    with Store(repo) as store:
        tables = {r[0] for r in store.db.execute("SELECT name FROM sqlite_master")}
        assert store.version == len(STEPS) + 1
    assert {"marker", "sections", "claims", "later"} <= tables


def test_two_writers_at_once(repo: Path) -> None:
    target = resolve_target(repo)
    sections = list(cut(target))
    with Store(target.root) as store:
        store.refresh(sections, None)
    errors: list[BaseException] = []

    def write(section_id: str, key: str) -> None:
        try:
            with Store(target.root) as store:
                for _ in range(20):
                    store.save(section_id, key, [Verdict(1, "none", "", "")], [], "t")
        except BaseException as error:  # noqa: BLE001  # collected for the assert
            errors.append(error)

    threads = [threading.Thread(target=write, args=(s.id, s.key)) for s in sections[:2]]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    with Store(target.root) as store:
        assert set(store.extracted()) == {s.id for s in sections[:2]}


def test_saved_claims_read_back(repo: Path) -> None:
    target = resolve_target(repo)
    sections = {s.id: s for s in cut(target)}
    parts = sections["tool#parts"]
    claim = Claim(
        id="abc",
        section=parts.id,
        concept="tool",
        n=1,
        sentence="",
        kind="point",
        claim="The CLI writes out.txt.",
        quantifier="exists",
        how_to_check="read src/tool.py",
        reason="names a file",
    )
    with Store(target.root) as store:
        store.refresh(sections.values(), None)
        store.save(parts.id, parts.key, [Verdict(1, "point", "", "")], [claim], "t")
        back = store.claims()

    assert [c.claim for c in back] == ["The CLI writes out.txt."]
    assert back[0].sentence == "The CLI writes `out.txt`."


def test_a_section_keyed_under_previous_guidance_keeps_its_answer(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A store written before the submit text left the hash keeps its claims (PREVIOUS_HASHES)."""
    from kmaudit import instructions

    target = resolve_target(repo)
    claim = Claim(
        id="abc",
        section="tool#parts",
        concept="tool",
        n=1,
        sentence="",
        kind="point",
        claim="The CLI writes out.txt.",
        quantifier="exists",
        how_to_check="read src/tool.py",
        reason="names a file",
    )
    monkeypatch.setattr(instructions, "instructions_hash", lambda: "0ld0ld0ld0ld")
    old = {s.id: s for s in cut(target)}
    with Store(target.root) as store:
        store.refresh(old.values(), None)
        parts = old["tool#parts"]
        store.save(parts.id, parts.key, [Verdict(1, "point", "", "")], [claim], "t")
    monkeypatch.undo()
    monkeypatch.setattr(instructions, "PREVIOUS_HASHES", ("0ld0ld0ld0ld",))
    new = {s.id: s for s in cut(target)}

    with Store(target.root) as store:
        refresh = store.refresh(new.values(), None)
        back = store.claims()
        waiting = store.pending_sections()

    assert new["tool#parts"].key != parts.key
    assert refresh.changed == []
    assert [c.claim for c in back] == ["The CLI writes out.txt."]
    assert "tool#parts" not in waiting


def test_a_section_keyed_under_unknown_guidance_is_handed_out_again(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the hashes in PREVIOUS_HASHES carry an answer over; any other key moves."""
    from kmaudit import instructions

    target = resolve_target(repo)
    monkeypatch.setattr(instructions, "instructions_hash", lambda: "0ld0ld0ld0ld")
    old = {s.id: s for s in cut(target)}
    with Store(target.root) as store:
        store.refresh(old.values(), None)
    monkeypatch.undo()
    monkeypatch.setattr(instructions, "PREVIOUS_HASHES", ())

    with Store(target.root) as store:
        refresh = store.refresh(cut(target), None)

    assert "tool#parts" in refresh.changed
