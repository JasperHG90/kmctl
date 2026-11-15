"""Tests for the project database."""

import pathlib as plb
import sqlite3

import alembic.command
import alembic.config
import sqlalchemy
from alembic.script import ScriptDirectory
from helpers import claim, make_chunk, note

from audit_cli.claims.models import ChunkResult
from audit_cli.claims.runner import stored_claims
from audit_cli.db import MIGRATIONS, Store


def head_of(path: plb.Path) -> str:
    """Return the Alembic revision a database file stands at."""
    return str(sqlite3.connect(path).execute("SELECT version_num FROM alembic_version").fetchone()[0])


def newest_revision() -> str:
    """Return the newest revision in the package's migrations."""
    return ScriptDirectory(str(MIGRATIONS)).get_current_head() or ""


def test_opening_twice_runs_each_migration_once(tmp_path: plb.Path) -> None:
    """A new database stands at the newest revision, and reopening changes nothing."""
    path = tmp_path / "a" / "audit.sqlite"
    with Store(path):
        pass
    with Store(path):
        pass
    assert head_of(path) == newest_revision() == "0008"


def test_a_chunk_that_is_gone_takes_its_claims(tmp_path: plb.Path) -> None:
    """replace_chunks keeps exactly the given chunks, and claims of a dropped chunk go with it."""
    one, two = make_chunk("c#one"), make_chunk("c#two")
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([one, two])
        store.replace_claims(two.id, stored_claims(two, [claim(1, "The CLI writes jobs.db")]))
        store.replace_chunks([one])
        assert [c.id for c in store.chunks()] == ["c#one"]
        assert store.counts().claims == 0  # the rows are gone, not only hidden by the join


def test_a_run_result_is_found_only_for_the_same_content_and_run(tmp_path: plb.Path) -> None:
    """A stored result comes back for the same chunk text, model, prompt and salt, and not otherwise."""
    chunk = make_chunk()
    with Store(tmp_path / "audit.sqlite") as store:
        verdicts = [note(1, "point"), note(2, "none")]
        result = ChunkResult(id=chunk.id, key=chunk.extraction_key, claims=[claim(1, "x")], verdicts=verdicts)
        store.save_extraction(result, "m", "p", "")
        found = store.extraction(chunk, "m", "p", "")
        assert found is not None and found.cached and found.claims[0].claim == "x"
        assert store.extraction(chunk, "m", "p", "2") is None
        assert store.extraction(chunk, "other", "p", "") is None
        changed = chunk.model_copy(update={"key": "new"})
        assert store.extraction(changed, "m", "p", "") is None


def test_a_changed_chunk_loses_its_claims(tmp_path: plb.Path) -> None:
    """Rechunking edited text drops the claims made from the old text; unchanged chunks keep theirs."""
    one, two = make_chunk("c#one"), make_chunk("c#two")
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([one, two])
        store.replace_claims(one.id, stored_claims(one, [claim(1, "kept")]))
        store.replace_claims(two.id, stored_claims(two, [claim(1, "dropped")]))
        store.replace_chunks([one, two.model_copy(update={"sentences": ["Edited."], "key": "edited"})])
        assert [c.claim for c in store.claims()] == ["kept"]


def test_replacing_one_concept_keeps_the_others(tmp_path: plb.Path) -> None:
    """Extracting one file replaces that concept's chunks and leaves every other concept alone."""
    one, two, other = make_chunk("c#one"), make_chunk("c#two"), make_chunk("d#one")
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([one, two, other])
        store.replace_chunks([one], {"c"})
        assert [c.id for c in store.chunks()] == ["c#one", "d#one"]


def test_an_old_database_is_brought_up_to_date(tmp_path: plb.Path) -> None:
    """A database at the first revision gets the reason columns and verdicts table when opened."""
    path = tmp_path / "audit.sqlite"
    config = alembic.config.Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    engine = sqlalchemy.create_engine(f"sqlite:///{path}")
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        alembic.command.upgrade(config, "0001")
    engine.dispose()
    with Store(path):
        pass
    db = sqlite3.connect(path)
    assert head_of(path) == newest_revision()
    assert "reason" in {row[1] for row in db.execute("PRAGMA table_info(claims)")}
    assert db.execute("SELECT COUNT(*) FROM sentence_verdicts").fetchone()[0] == 0


def test_an_in_memory_store_is_migrated() -> None:
    """The empty database diff reads from has every table too."""
    with Store(None) as store:
        assert store.counts().claims == 0
        assert store.verdicts("c#one") == []


def test_a_stored_result_with_a_sentence_missing_its_verdict_counts_as_not_made(tmp_path: plb.Path) -> None:
    """A result stored before gaps counted as failed is asked again: sentence 2 has no verdict."""
    chunk = make_chunk()
    with Store(tmp_path / "audit.sqlite") as store:
        result = ChunkResult(id=chunk.id, key=chunk.extraction_key, claims=[claim(1, "x")], verdicts=[note(1, "point")])
        store.save_extraction(result, "m", "p", "")
        assert store.extraction(chunk, "m", "p", "") is None


def test_a_new_check_replaces_the_old_one_with_its_result_and_triage(tmp_path: plb.Path) -> None:
    """Writing a claim's check again drops its last result and triage, which belonged to the old steps."""
    from audit_cli.db import CheckResult, StoredCheck, Triage

    with Store(tmp_path / "a.sqlite") as store:
        check = StoredCheck(
            claim_id="c1",
            kind="check",
            steps=[{"op": "file", "path": "x"}],
            strength="exact",
            writer="twocall:m",
            reads={"x": "abc"},
        )
        store.save_check(check)
        store.save_result(CheckResult(claim_id="c1", holds=False, results=[], reads_key="k"))
        store.save_triage(
            Triage(
                claim_id="c1",
                question="failure",
                asked_key="q",
                model="jev",
                score=0.9,
                verdict="claim_false",
                answers={},
            )
        )
        assert store.checks()["c1"].reads == {"x": "abc"}
        assert set(store.results()) == set(store.triage()) == {"c1"}
        store.save_check(check.model_copy(update={"steps": [{"op": "file", "path": "y"}], "reads": {"y": "def"}}))
        assert store.checks()["c1"].reads == {"y": "def"}
        assert store.results() == {} and store.triage() == {}


def test_checks_of_claims_that_are_gone_are_pruned(tmp_path: plb.Path) -> None:
    """A claim whose text changed has a new id; its old check is pruned, the others stay."""
    from audit_cli.db import StoredCheck

    with Store(tmp_path / "a.sqlite") as store:
        for claim_id in ("old", "kept"):
            store.save_check(StoredCheck(claim_id=claim_id, kind="reason", why="history", writer="twocall:m"))
        assert store.prune_checks({"kept", "new"}) == 1
        assert set(store.checks()) == {"kept"}


def test_cache_and_passes_round_trip(tmp_path: plb.Path) -> None:
    """A cached value and a recorded pass read back as written."""
    with Store(tmp_path / "a.sqlite") as store:
        assert store.cached("cli") is None
        store.cache("cli", {"kmctl": ["--by"]})
        store.record_pass("checks write", "2026-11-10T00:00:00+00:00", 1.5, {"model_calls": 3})
        assert store.cached("cli") == {"kmctl": ["--by"]}
        assert store.passes()[0]["report"] == {"model_calls": 3}
