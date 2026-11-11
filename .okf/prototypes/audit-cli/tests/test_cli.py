"""Tests for the audit command, run against a temporary repository."""

import json
import os
import pathlib as plb

import pytest
from helpers import claim
from typer.testing import CliRunner

from audit_cli.claims.models import CorrectionLink
from audit_cli.claims.runner import stored_claims
from audit_cli.cli import REFUSED, app
from audit_cli.config import load_config
from audit_cli.db import Store
from audit_cli.processing.chunker import BundleChunker, SentenceSplitter
from audit_cli.processing.target import resolve_target

runner = CliRunner()
FILE = ".okf/decisions/0001-use-a-queue.md"


@pytest.fixture(autouse=True)
def no_key(repo: plb.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run from the repository with no provider key and no .env file above it."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.chdir(repo)


def test_only_claims_and_init_are_offered() -> None:
    """The top level offers claims and init, and claims offers extract and diff."""
    top = runner.invoke(app, ["--help"]).output
    assert "claims" in top and "init" in top and "files" not in top
    sub = runner.invoke(app, ["claims", "--help"]).output
    assert "extract" in sub and "diff" in sub and "list" in sub


def test_init_writes_once(tmp_path: plb.Path) -> None:
    """init writes audit.toml, then refuses to overwrite it without --force."""
    assert runner.invoke(app, ["init", "--path", str(tmp_path)]).exit_code == 0
    again = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert again.exit_code == REFUSED and "--force" in again.output


def test_init_refuses_a_folder_that_does_not_exist(tmp_path: plb.Path) -> None:
    """init names the missing folder instead of failing with a traceback."""
    result = runner.invoke(app, ["init", "--path", str(tmp_path / "nowhere")])
    assert result.exit_code == REFUSED and "is not a folder" in result.output


@pytest.mark.parametrize(("path", "chunks"), [(".", 3), (".okf", 3), (FILE, 3)])
def test_diff_before_extraction_needs_every_run(repo: plb.Path, path: str, chunks: int) -> None:
    """A bundle, its repository or one file diff as new, with one call per section per run, and no key needed."""
    result = runner.invoke(app, ["claims", "diff", path, "--json"])
    assert result.exit_code == 1, result.output
    report = json.loads(result.output)
    # Two runs per section, plus one call to judge the decision's correction.
    assert report["up_to_date"] is False and report["pending_calls"] == chunks * 2 + 1
    assert [c["status"] for c in report["concepts"]] == ["new"]


def test_diff_writes_no_database(repo: plb.Path, data_dir: plb.Path) -> None:
    """diff reads only: a project with no database still has none afterwards."""
    runner.invoke(app, ["claims", "diff", "."])
    assert not (data_dir / "projects").exists()


def test_extract_without_a_key_is_refused(repo: plb.Path) -> None:
    """A missing provider key stops extract before any call and names the variable."""
    result = runner.invoke(app, ["claims", "extract", "."])
    assert result.exit_code == REFUSED and "OPENAI_API_KEY" in result.output


def test_a_missing_model_is_refused(repo: plb.Path) -> None:
    """Without a model set, both verbs refuse and say which setting to fill in."""
    (repo / "audit.toml").unlink()
    result = runner.invoke(app, ["claims", "diff", "."])
    assert result.exit_code == REFUSED and "agents.extractor.model" in result.output


def test_init_writes_no_provider_specific_setup(tmp_path: plb.Path) -> None:
    """audit init writes a generic endpoint and leaves the model blank."""
    runner.invoke(app, ["init", "--path", str(tmp_path)])
    text = (tmp_path / "audit.toml").read_text()
    assert 'model = ""' in text and "api.openai.com" in text and "bifrost" not in text


@pytest.mark.parametrize("path", ["nowhere", "src/worker.py", "src", ".okf/decisions/0002-old.md"])
def test_paths_that_name_no_concept_are_refused(repo: plb.Path, path: str) -> None:
    """A missing path, a code file, a folder with no bundle and a deprecated concept are refused with exit 2."""
    result = runner.invoke(app, ["claims", "diff", path])
    assert result.exit_code == REFUSED and "refused" in result.output


def stored(repo: plb.Path) -> None:
    """Store the repository's chunks with one point and one subjective claim, as an extraction would."""
    target = resolve_target(repo)
    chunks = list(BundleChunker(SentenceSplitter()).chunks(target.bundle))
    with Store(load_config(repo / "audit.toml").database_path(target.project_root)) as store:
        store.replace_chunks(chunks)
        first = chunks[0]
        claims = [claim(1, "The CLI writes jobs.db"), claim(2, "Workers should be simple", "subjective")]
        claims = [c.model_copy(update={"reason": f"why {c.claim_type}"}) for c in claims]
        store.replace_claims(first.id, stored_claims(first, claims))


def test_list_with_nothing_extracted_lists_nothing(repo: plb.Path, data_dir: plb.Path) -> None:
    """A project with no database lists no documents, exits 0 and creates no database."""
    result = runner.invoke(app, ["claims", "list", ".", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["documents"] == []
    assert not (data_dir / "projects").exists()


def test_list_counts_documents_and_shows_claims_for_one_file(repo: plb.Path) -> None:
    """The bundle lists counts per document; one file lists each claim with its reason."""
    stored(repo)
    bundle = json.loads(runner.invoke(app, ["claims", "list", "--json"]).output)
    (doc,) = bundle["documents"]
    assert doc["concept"] == "decisions/0001-use-a-queue" and doc["sections"] == 3
    assert doc["claims_by_kind"] == {"point": 1, "subjective": 1} and doc["claims"] == []
    single = runner.invoke(app, ["claims", "list", FILE])
    assert "[1] point: The CLI writes jobs.db" in single.output and "why: why point" in single.output


def test_list_filters_by_kind(repo: plb.Path) -> None:
    """--kind keeps only claims of the named kinds."""
    stored(repo)
    result = json.loads(runner.invoke(app, ["claims", "list", "--claims", "--kind", "subjective", "--json"]).output)
    assert [c["claim"] for c in result["documents"][0]["claims"]] == ["Workers should be simple"]


def test_list_shows_superseded_claims_and_hides_them_with_current(repo: plb.Path) -> None:
    """A claim a correction overturns is marked with its link, and --current leaves it out."""
    stored(repo)
    target = resolve_target(repo)
    with Store(load_config(repo / "audit.toml").database_path(target.project_root)) as store:
        decision = next(c for c in store.claims() if c.claim == "The CLI writes jobs.db")
        link = CorrectionLink(
            correction_chunk="decisions/0001-use-a-queue#correction-2026-01-02",
            correction_n=1,
            target_chunk=decision.chunk_id,
            target_n=1,
            claim_id=decision.claim_id,
            reason="the file moved",
        )
        store.save_correction(link.correction_chunk, "k", "test-model", [link])
    single = runner.invoke(app, ["claims", "list", FILE]).output
    assert "point [superseded]: The CLI writes jobs.db" in single and "the file moved" in single
    current = json.loads(runner.invoke(app, ["claims", "list", "--current", "--claims", "--json"]).output)
    assert [c["claim"] for c in current["documents"][0]["claims"]] == ["Workers should be simple"]
    assert current["documents"][0]["superseded"] == 1


@pytest.mark.parametrize(("enabled", "tracing"), [("true", "true"), ("false", "false")])
def test_telemetry_enabled_switches_langsmith_tracing(repo: plb.Path, enabled: str, tracing: str) -> None:
    """telemetry.enabled sets LANGSMITH_TRACING and nothing else; LangSmith reads the rest from its own variables."""
    (repo / "audit.toml").write_text(
        f'[agents.extractor]\nprovider = "openai"\nmodel = "test-model"\n\n[telemetry]\nenabled = {enabled}\n'
    )
    runner.invoke(app, ["claims", "diff", "."])
    assert os.environ["LANGSMITH_TRACING"] == tracing and "LANGSMITH_PROJECT" not in os.environ


def test_list_takes_any_folder_in_the_repository(repo: plb.Path) -> None:
    """list reads stored claims, so a folder with no bundle names its repository rather than being refused."""
    (repo / "src" / "deep").mkdir()
    result = runner.invoke(app, ["claims", "list", "src/deep"])
    assert result.exit_code == 0, result.output
