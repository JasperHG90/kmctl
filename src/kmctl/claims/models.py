"""The claim schema: what an agent submits for a section, and the claims the store keeps."""

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Kind = Literal["point", "structural", "broad", "subjective", "external", "none"]
Quantifier = Literal["exists", "all", "none"]
KINDS: tuple[str, ...] = ("point", "structural", "broad", "subjective", "external")


def _labels_as_text(value: Any) -> Any:
    """Read sentence labels written as numbers (``2.7``, ``3``) as the text labels they stand for."""
    if isinstance(value, list):
        return [
            str(v) if isinstance(v, int | float) and not isinstance(v, bool) else v
            for v in value
        ]
    return value


class ClaimText(BaseModel):
    """One claim a sentence makes and how many places settle it."""

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(
        min_length=1,
        description="The claim, standalone and in the present tense.",
    )
    quantifier: Quantifier = Field(
        default="exists",
        description=(
            "exists: one place proves it; all: every instance must comply; "
            "none: no instance may exist."
        ),
    )
    refers_to: list[str] = Field(
        default_factory=list,
        description="Labels of the sentences this claim needs, like 2.4 (earlier section 2) or 3 (this section).",
    )

    @field_validator("refers_to", mode="before")
    @classmethod
    def _from_numbers(cls, value: Any) -> Any:
        """Read labels sent as numbers as text."""
        return _labels_as_text(value)


class SentenceVerdict(BaseModel):
    """The verdict on one numbered sentence: how to check it, why this kind, and its claims."""

    model_config = ConfigDict(extra="forbid")

    n: int = Field(ge=1, description="The sentence number, from 1.")
    how_to_check: str = Field(
        default="",
        description="What to open or run in this repository to confirm it; empty if nothing would.",
    )
    reason: str = Field(
        default="",
        description="One short sentence: why this kind, naming what settles it or why nothing does.",
    )
    kind: Kind = Field(
        description="How the sentence's claims are checked; none for no claim."
    )
    claims: list[ClaimText] = Field(
        default_factory=list,
        description="Each claim the sentence makes; empty when kind is none.",
    )


class SectionAnswer(BaseModel):
    """One section's answer, as ``kmctl audit claims submit`` reads it."""

    model_config = ConfigDict(extra="forbid")

    section: str = Field(
        description="The section id that kmctl audit claims todo gave, like manifesto#parts."
    )
    key: str = Field(description="The section's key that kmctl audit claims todo gave.")
    sentences: list[SentenceVerdict] = Field(
        description="One verdict per numbered sentence, in order."
    )


class Claim(BaseModel):
    """One stored claim, read back by ``kmctl audit claims list``."""

    id: str = Field(description="The claim's id: a hash of its concept and text.")
    section: str = Field(description="The id of the section the claim came from.")
    concept: str = Field(
        description="The concept id: its path in the bundle without .md."
    )
    n: int = Field(description="The number of the sentence that makes the claim.")
    sentence: str = Field(description="The sentence that makes the claim.")
    kind: str = Field(description="The verdict's kind; never none.")
    claim: str = Field(description="The claim.")
    quantifier: Quantifier = Field(description="How many places settle the claim.")
    how_to_check: str = Field(description="What to open or run to confirm it.")
    reason: str = Field(description="Why the sentence is this kind.")
    refers_to: list[str] = Field(
        default_factory=list,
        description="Other sentences the claim needs, as 'section id|n'.",
    )


def claim_id(concept: str, claim: str) -> str:
    """Return a claim's stable id: a hash of its concept and text."""
    return hashlib.sha256(json.dumps([concept, claim]).encode()).hexdigest()[:12]
