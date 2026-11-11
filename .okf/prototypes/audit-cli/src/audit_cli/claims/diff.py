"""Compare a bundle's current text with what the database holds: what is extracted and what would change."""

import difflib
from typing import Literal

from pydantic import BaseModel, Field

from audit_cli.claims.corrections import pending_corrections
from audit_cli.claims.runner import PROMPT_HASH
from audit_cli.db import Store
from audit_cli.processing.chunker import Chunk

Status = Literal["up to date", "new", "changed", "incomplete", "removed"]


class ChunkDiff(BaseModel):
    """One section: whether its claims in the database match its current text."""

    id: str = Field(description="The chunk id: concept id plus section slug.")
    status: Status = Field(
        description="up to date: extracted from this text by every run; new: never extracted; changed: extracted "
        "from older text; incomplete: same text, but some runs are missing; removed: the section is gone."
    )
    sentences_added: int = Field(default=0, description="Sentences in the current text and not in the stored one.")
    sentences_removed: int = Field(default=0, description="Sentences in the stored text and not in the current one.")
    pending_runs: list[str] = Field(default_factory=list, description="Runs that would call a model for this text.")


class ConceptDiff(BaseModel):
    """One concept file and its sections."""

    concept: str
    status: Status = Field(description="up to date only when every section is; otherwise what best sums them up.")
    chunks: list[ChunkDiff]


class DiffReport(BaseModel):
    """What extracting the path would change."""

    up_to_date: bool = Field(description="True when extracting would change no claim and call no model.")
    pending_calls: int = Field(description="Run results that would need a model call; a follow-up call may add more.")
    concepts: list[ConceptDiff]


def _sentence_changes(old: list[str], new: list[str]) -> tuple[int, int]:
    """Return how many sentences were added and removed between two versions of a section."""
    added = removed = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        if tag in {"replace", "delete"}:
            removed += i2 - i1
        if tag in {"replace", "insert"}:
            added += j2 - j1
    return added, removed


def _concept_status(chunks: list[ChunkDiff]) -> Status:
    """Sum up a concept's sections in one status: a status all of them share, else incomplete or changed."""
    statuses = {c.status for c in chunks}
    if len(statuses) == 1:
        return statuses.pop()
    return "incomplete" if statuses == {"incomplete", "up to date"} else "changed"


def diff(
    store: Store,
    current: list[Chunk],
    concepts: set[str] | None,
    runs: list[tuple[str, str, str]],
    corrections_model: str | None = None,
) -> DiffReport:
    """Compare the current chunks with the stored ones, without writing anything or calling a model.

    Parameters
    ----------
    store :
        The project's database.
    current :
        The chunks the path holds now.
    concepts :
        The concepts the path covers, so stored chunks of other concepts are not called removed; None for a whole
        bundle.
    runs :
        Each configured run's label, model and salt.
    corrections_model :
        The model that judges corrections; a correction section not judged for the current text and claims needs
        one more call. None leaves corrections out.
    """
    stored = {c.id: c for c in store.chunks(concepts)}
    by_concept: dict[str, list[ChunkDiff]] = {}
    pending_calls = 0
    for chunk in current:
        missing = [label for label, model, salt in runs if store.extraction(chunk, model, PROMPT_HASH, salt) is None]
        pending_calls += len(missing)
        before = stored.pop(chunk.id, None)
        if before is None:
            entry = ChunkDiff(id=chunk.id, status="new", sentences_added=len(chunk.sentences), pending_runs=missing)
        elif before.extraction_key != chunk.extraction_key:
            added, removed = _sentence_changes(before.sentences, chunk.sentences)
            entry = ChunkDiff(
                id=chunk.id, status="changed", sentences_added=added, sentences_removed=removed, pending_runs=missing
            )
        else:
            entry = ChunkDiff(id=chunk.id, status="incomplete" if missing else "up to date", pending_runs=missing)
        by_concept.setdefault(chunk.concept, []).append(entry)
    for gone in stored.values():
        removed_entry = ChunkDiff(id=gone.id, status="removed", sentences_removed=len(gone.sentences))
        by_concept.setdefault(gone.concept, []).append(removed_entry)
    if corrections_model is not None:
        entries = {e.id: e for es in by_concept.values() for e in es}
        stale = {cid for cid, e in entries.items() if e.status != "up to date"}
        for cid in pending_corrections(store, current, corrections_model, stale):
            entry = entries[cid]
            entry.pending_runs.append("corrections")
            pending_calls += 1
            if entry.status == "up to date":
                entry.status = "incomplete"
    reports = [
        ConceptDiff(concept=concept, status=_concept_status(chunks), chunks=chunks)
        for concept, chunks in sorted(by_concept.items())
    ]
    return DiffReport(
        up_to_date=all(r.status == "up to date" for r in reports), pending_calls=pending_calls, concepts=reports
    )
