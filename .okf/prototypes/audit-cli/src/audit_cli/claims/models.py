"""What the extractor asks the model for, and the claims it keeps."""

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from audit_cli.jsontext import read_list

Kind = Literal["point", "structural", "broad", "subjective", "external", "none"]
Quantifier = Literal["exists", "all", "none"]


def _labels_as_text(value: Any) -> Any:
    """Read sentence labels a model wrote as numbers (``2.7``, ``3``) as the text labels they stand for."""
    if isinstance(value, list):
        return [str(v) if isinstance(v, int | float) and not isinstance(v, bool) else v for v in value]
    return value


class ClaimText(BaseModel):
    """One claim and how many places settle it, as the model writes it.

    A label sent as a number is read as text; a float cannot tell ``2.10`` from ``2.1``, so that one reads as the
    first sentence of section 2.
    """

    claim: str
    quantifier: Quantifier = Field(
        description="exists: one place proves it; all: every instance must comply; none: no instance may exist."
    )
    refers_to: list[str] = Field(
        default=[], description="Labels of the sentences this claim needs to be understood, like [2.4] or [3]."
    )

    @field_validator("refers_to", mode="before")
    @classmethod
    def _from_numbers(cls, value: Any) -> Any:
        """Read labels sent as numbers as text."""
        return _labels_as_text(value)


class SentenceVerdict(BaseModel):
    """The claims one numbered sentence makes, with the check reasoned out before the kind."""

    n: int = Field(description="The sentence number.")
    how_to_check: str = Field(
        description="What to open or run in this repository to confirm it; empty if nothing would."
    )
    reason: str = Field(
        default="", description="One short sentence: why this kind, naming what settles it or why nothing does."
    )
    kind: Kind
    claims: list[ClaimText] = Field(
        description="Each claim the sentence makes, standalone and in the present tense; empty for none."
    )


class Verdicts(BaseModel):
    """One verdict per numbered sentence, in order."""

    sentences: list[SentenceVerdict]

    @field_validator("sentences", mode="before")
    @classmethod
    def _from_text(cls, value: Any) -> Any:
        """Read a list sent as JSON text, as some models send it."""
        return read_list(value)


class TokenCounts(BaseModel):
    """Tokens the model calls for one chunk used."""

    input: int = Field(default=0, description="Tokens sent to the model.")
    output: int = Field(default=0, description="Tokens the model returned.")


class Claim(BaseModel):
    """One claim from a sentence verdict."""

    evidence: list[int] = Field(description="The number of the sentence the verdict is for.")
    claim_type: str = Field(description="The verdict's kind; never none.")
    claim: str = Field(description="The claim; empty when the verdict listed none.")
    how_to_check: str = Field(description="What the model would open or run to confirm it.")
    quantifier: Quantifier = Field(default="exists", description="How many places settle the claim.")
    refers_to: list[str] = Field(default=[], description="Other sentences the claim needs, as 'chunk id|n'.")
    run: str = Field(default="", description="The extraction run that produced the claim.")
    reason: str = Field(default="", description="The model's reason for the kind.")


class SentenceNote(BaseModel):
    """One sentence's verdict: its kind and the model's reason, kept for sentences with no claim too."""

    n: int = Field(description="The sentence number.")
    kind: str = Field(description="The verdict's kind, none included.")
    reason: str = Field(default="", description="The model's reason for the kind.")
    run: str = Field(default="", description="The extraction run the verdict came from.")


class ChunkResult(BaseModel):
    """One chunk's extraction by one run."""

    id: str = Field(description="The chunk id.")
    key: str = Field(description="The chunk's cache key when it was extracted.")
    claims: list[Claim]
    verdicts: list[SentenceNote] = Field(default_factory=list, description="Every sentence's verdict, in order.")
    error: str | None = Field(default=None, description="Why the model's answer could not be read, if it could not.")
    tokens: TokenCounts = Field(default_factory=TokenCounts)
    cached: bool = Field(default=False, description="Whether the result came from the database; not stored.")


class CorrectionLink(BaseModel):
    """A correction sentence tied to a sentence it corrects and, when one is named, a claim it overturns."""

    correction_chunk: str = Field(description="The correction section's chunk id.")
    correction_n: int = Field(description="The correction sentence's number.")
    target_chunk: str = Field(description="The corrected sentence's chunk id.")
    target_n: int = Field(description="The corrected sentence's number.")
    claim_id: str | None = Field(default=None, description="The overturned claim; None when no claim is overturned.")
    reason: str = Field(default="", description="The model's one-sentence reason.")


def claim_id(concept: str, claim: str) -> str:
    """Return a claim's stable id: a hash of its concept and text, the same as the audit-agent notebook's."""
    return hashlib.sha256(json.dumps([concept, claim]).encode()).hexdigest()[:12]


def merge_runs(first: ChunkResult, second: ChunkResult) -> ChunkResult:
    """Return the first run's claims plus the second's for each sentence the first gave no claim (a run skips some)."""
    covered = {n for claim in first.claims for n in claim.evidence}
    extra = [claim for claim in second.claims if claim.evidence and claim.evidence[0] not in covered]
    tokens = TokenCounts(
        input=first.tokens.input + second.tokens.input, output=first.tokens.output + second.tokens.output
    )
    # A sentence's verdict comes from the run whose claims it keeps: a later run's when it added claims, else the first.
    added = {claim.evidence[0] for claim in extra}
    verdicts = {v.n: v for v in first.verdicts}
    verdicts.update({v.n: v for v in second.verdicts if v.n in added or v.n not in verdicts})
    merged = [verdicts[n] for n in sorted(verdicts)]
    return first.model_copy(update={"claims": first.claims + extra, "tokens": tokens, "verdicts": merged})
