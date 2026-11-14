"""What the ``kmaudit claims`` verbs do, callable without the CLI: todo, submit and list."""

import json
import re
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from kmaudit import AuditError
from kmaudit.feedback import (
    FEEDBACK_INSTRUCTIONS,
    FeedbackOut,
    is_open,
    latest,
    liked,
    take_in_section,
    wants_extraction,
)
from kmaudit.instructions import INSTRUCTIONS
from kmaudit.models import Claim, SectionAnswer, claim_id
from kmaudit.sections import cut, resolve_target
from kmaudit.store import StaleSection, Store, Verdict

_LABEL = re.compile(r"\[?\s*(?:(\d+)\.)?(\d+)\s*\]?")
_ANSWERS = TypeAdapter(list[object])


class Sentence(BaseModel):
    """One numbered sentence of a section handed out."""

    n: int = Field(description="The sentence number, from 1.")
    text: str = Field(description="The sentence.")


class TodoSection(BaseModel):
    """A section with no extraction for its current key, as ``todo`` hands it out."""

    id: str = Field(description="The section id to submit under.")
    key: str = Field(description="The key to submit with; a stale one is refused.")
    concept: str = Field(description="The concept id.")
    type: str = Field(description="The concept's type.")
    status: str | None = Field(description="The concept's status.")
    title: str = Field(description="The concept's title.")
    section: str = Field(description="The header path, joined with ' > '.")
    sentences: list[Sentence] = Field(description="The sentences to give verdicts for.")
    earlier: str = Field(
        description="Earlier sections' sentences, labelled [s.n], for context only."
    )
    corrections: str = Field(
        description="The record's corrections, for context only; a correction section gets only those after it."
    )
    feedback: list[FeedbackOut] = Field(
        default_factory=list,
        description="What people said about this section's claims (a thumbs down sends it back); extract it with that in mind.",
    )


class TodoCounts(BaseModel):
    """How the store's sections stand after a refresh."""

    up_to_date: int = Field(description="Sections extracted at their current key.")
    pending: int = Field(
        description="Sections with no extraction at their current key."
    )
    new: int = Field(description="Sections seen for the first time by this run.")
    changed: int = Field(
        description="Sections whose key moved since the last run; their claims were dropped."
    )
    removed: int = Field(
        description="Sections gone from the bundle; their claims were dropped."
    )


class PendingConcept(BaseModel):
    """A concept with sections to extract, so a caller can split the work by concept."""

    concept: str = Field(description="The concept id.")
    path: str = Field(description="The concept file, relative to the repository root.")
    sections: int = Field(
        description="Its sections with no extraction at their current key."
    )


class TodoResult(BaseModel):
    """What ``kmaudit claims todo`` hands out."""

    instructions: str | None = Field(
        default=None,
        description="How to give verdicts and the answer's shape; left out with brief.",
    )
    counts: TodoCounts
    concepts: list[PendingConcept] = Field(
        description="Every concept with pending sections, beyond the limit too."
    )
    sections: list[TodoSection] = Field(
        description="The pending sections, up to the limit."
    )
    feedback_instructions: str | None = Field(
        default=None,
        description="How to read feedback and examples; only when the output carries either.",
    )
    examples: list[FeedbackOut] = Field(
        default_factory=list,
        description="Claims people marked good, with their notes, to learn what works.",
    )
    namespace: str = Field(
        description="The namespace these sections belong to: the audited folder below the repository root; pass it as --path to submit."
    )
    next: str = Field(
        description="The verb that usually follows, with --path naming the namespace."
    )


class Stored(BaseModel):
    """One section ``submit`` stored."""

    section: str
    claims: int


class Refused(BaseModel):
    """One section ``submit`` refused, with the fix."""

    section: str | None
    reason: str


class SubmitResult(BaseModel):
    """What ``kmaudit claims submit`` stored and refused."""

    stored: list[Stored] = Field(default_factory=list)
    refused: list[Refused] = Field(default_factory=list)


class Document(BaseModel):
    """One concept's sections and claims per kind, as ``list`` shows it."""

    concept: str
    sections: int = Field(description="The concept's sections.")
    extracted: int = Field(description="Sections extracted at their current key.")
    claims: dict[str, int] = Field(description="Claims per kind.")


class ListResult(BaseModel):
    """What ``kmaudit claims list`` reads from the store."""

    documents: list[Document] | None = Field(
        default=None, description="Each concept, without --claims."
    )
    totals: dict[str, int] | None = Field(
        default=None,
        description="Claims per kind, over every document, without --claims.",
    )
    claims: list[Claim] | None = Field(
        default=None, description="Each claim, with --claims."
    )


def todo(path: Path, limit: int | None = None, brief: bool = False) -> TodoResult:
    """Refresh the store from the bundle at ``path`` and list the sections with no extraction for their current key.

    With ``brief``, the instructions are left out, for a caller that already
    has them from an earlier round.

    Raises
    ------
    AuditError
        If ``path`` names no bundle, or a concept's front matter does not read.
    """
    target = resolve_target(path)
    sections = list(cut(target))
    with Store(target.root, target.namespace) as store:
        refresh = store.refresh(sections, target.concepts)
        extracted = store.extracted()
        said: dict[str, list[FeedbackOut]] = {}
        flags: set[str] = set()
        for f in latest(store).values():
            if f.target == "claim" and is_open(f):
                said.setdefault(f.section, []).append(f.out())
                if wants_extraction(f):
                    flags.add(f.section)
        examples = liked(store, "claim")
    stale = [s for s in sections if extracted.get(s.id) != s.key]
    flagged = [s for s in sections if s.id in flags and extracted.get(s.id) == s.key]
    pending = flagged + stale
    shown = pending if limit is None else pending[:limit]
    per = Counter(s.concept for s in pending)
    root = target.root.resolve()
    concepts = [
        PendingConcept(
            concept=concept,
            path=(target.bundle.resolve() / f"{concept}.md")
            .relative_to(root)
            .as_posix(),
            sections=count,
        )
        for concept, count in per.items()
    ]
    return TodoResult(
        concepts=concepts,
        instructions=None if brief else INSTRUCTIONS,
        counts=TodoCounts(
            up_to_date=len(sections) - len(pending),
            pending=len(pending),
            new=len(refresh.new),
            changed=len(refresh.changed),
            removed=len(refresh.removed),
        ),
        sections=[
            TodoSection(
                id=s.id,
                key=s.key,
                concept=s.concept,
                type=s.type,
                status=s.status,
                title=s.title,
                section=s.section,
                sentences=[Sentence(n=n, text=t) for n, t in enumerate(s.sentences, 1)],
                earlier=s.earlier,
                corrections=s.corrections,
                feedback=said.get(s.id, []),
            )
            for s in shown
        ],
        feedback_instructions=FEEDBACK_INSTRUCTIONS
        if examples or any(s.id in said for s in shown)
        else None,
        examples=examples,
        namespace=target.namespace,
        next=f"kmaudit claims submit - --path {target.namespace}",
    )


def _refers_to(
    labels: list[str], section_id: str, count: int, earlier_ids: list[str], own: int
) -> list[str]:
    """Turn ``s.n`` and ``n`` labels into 'section id|n', dropping the claim's own sentence and labels that name nothing."""
    found: list[str] = []
    for label in labels:
        match = _LABEL.fullmatch(label.strip())
        if not match:
            continue
        part, n = match.group(1), int(match.group(2))
        if part is None:
            if 1 <= n <= count and n != own:
                found.append(f"{section_id}|{n}")
        elif 1 <= int(part) <= len(earlier_ids):
            found.append(f"{earlier_ids[int(part) - 1]}|{n}")
    return found


def _first_error(error: ValidationError) -> str:
    """The first validation error as 'field: message'."""
    first = error.errors()[0]
    where = ".".join(str(p) for p in first["loc"]) or "answer"
    return f"{where}: {first['msg']}"


def _check_answer(
    store: Store, answer: SectionAnswer
) -> tuple[list[Verdict], list[Claim]]:
    """The verdicts and claims of one valid answer, or a refusal naming what is wrong and the fix.

    Raises
    ------
    AuditError
        If the section is unknown or its key stale, or a sentence has no verdict, two, or one out of range.
    """
    row = store.section(answer.section)
    if row is None:
        raise AuditError(
            f"unknown section {answer.section!r}; run kmaudit claims todo for the current section ids"
        )
    if row["key"] != answer.key:
        raise AuditError(
            f"stale key {answer.key!r} for {answer.section} (the section or its context changed); "
            "run kmaudit claims todo and answer the section again"
        )
    sentences: list[str] = json.loads(row["sentences"])
    earlier_ids: list[str] = json.loads(row["earlier_ids"])
    numbers = [v.n for v in answer.sentences]
    extra = sorted({n for n in numbers if n > len(sentences)})
    if extra:
        raise AuditError(
            f"{answer.section} has {len(sentences)} sentences, but the answer gives verdicts for {extra}; "
            "drop them and submit again"
        )
    twice = sorted(n for n, c in Counter(numbers).items() if c > 1)
    if twice:
        raise AuditError(
            f"{answer.section}: sentences {twice} have more than one verdict; give each one verdict and submit again"
        )
    missing = sorted(set(range(1, len(sentences) + 1)) - set(numbers))
    if missing:
        raise AuditError(
            f"{answer.section}: no verdict for sentences {missing} of {len(sentences)}; "
            "add a verdict for each (kind none for no claim) and submit again"
        )
    verdicts: list[Verdict] = []
    claims: list[Claim] = []
    for v in sorted(answer.sentences, key=lambda v: v.n):
        if v.kind == "none" and v.claims:
            raise AuditError(
                f"{answer.section}: sentence {v.n} is kind none but lists claims; "
                "give it a kind or drop its claims, then submit again"
            )
        if v.kind != "none" and not v.claims:
            raise AuditError(
                f"{answer.section}: sentence {v.n} is kind {v.kind} but lists no claim; "
                "list its claims or mark it none, then submit again"
            )
        verdicts.append(
            Verdict(n=v.n, kind=v.kind, how_to_check=v.how_to_check, reason=v.reason)
        )
        if v.kind == "none":
            continue
        for text in v.claims:
            claims.append(
                Claim(
                    id=claim_id(row["concept"], text.claim),
                    section=answer.section,
                    concept=row["concept"],
                    n=v.n,
                    sentence=sentences[v.n - 1],
                    kind=v.kind,
                    claim=text.claim,
                    quantifier=text.quantifier,
                    how_to_check=v.how_to_check,
                    reason=v.reason,
                    refers_to=_refers_to(
                        text.refers_to, answer.section, len(sentences), earlier_ids, v.n
                    ),
                )
            )
    return verdicts, claims


def submit(path: Path, text: str, by: str = "agent") -> SubmitResult:
    """Validate an agent's answers and store each good one; one bad section does not undo the others.

    Parameters
    ----------
    path :
        The repository, bundle or a path inside it; names the store.
    text :
        JSON: one section answer, or a list of them.
    by :
        Who submitted the answers, recorded with each extraction.

    Raises
    ------
    AuditError
        If ``text`` is not JSON, or ``path`` names no bundle.
    """
    target = resolve_target(path)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise AuditError(
            f"the answer is not JSON ({error.msg} at line {error.lineno}); "
            "pipe a list of section answers, as kmaudit claims todo --json describes"
        ) from error
    items = _ANSWERS.validate_python(data if isinstance(data, list) else [data])
    if not items:
        raise AuditError(
            "the answer list is empty; pipe the section answers, "
            "as kmaudit claims todo --json describes"
        )
    result = SubmitResult()
    with Store(target.root, target.namespace) as store:
        for item in items:
            section = item.get("section") if isinstance(item, dict) else None
            label = section if isinstance(section, str) else None
            try:
                answer = SectionAnswer.model_validate(item)
            except ValidationError as error:
                result.refused.append(
                    Refused(
                        section=label,
                        reason=f"malformed answer for {label or 'a section'}: {_first_error(error)}; "
                        "fix it to the shape kmaudit claims todo --json gives and submit again",
                    )
                )
                continue
            try:
                verdicts, claims = _check_answer(store, answer)
            except AuditError as error:
                result.refused.append(Refused(section=label, reason=str(error)))
                continue
            try:
                count = store.save(answer.section, answer.key, verdicts, claims, by)
            except StaleSection:
                result.refused.append(
                    Refused(
                        section=label,
                        reason=f"{answer.section} changed while the answer was checked; "
                        "run kmaudit claims todo and answer it again",
                    )
                )
                continue
            take_in_section(store, answer.section)
            result.stored.append(Stored(section=answer.section, claims=count))
    return result


def list_claims(path: Path, kind: str | None = None, each: bool = False) -> ListResult:
    """Read the store's documents and claims per kind, or each claim with ``each``; ``kind`` filters claims.

    Raises
    ------
    AuditError
        If ``path`` names no bundle.
    """
    target = resolve_target(path)
    concepts = target.concepts
    with Store(target.root, target.namespace) as store:
        claims = [c for c in store.claims(concepts) if kind is None or c.kind == kind]
        documents = store.documents()
    if each:
        return ListResult(claims=claims)
    per: dict[str, Counter[str]] = {}
    for c in claims:
        per.setdefault(c.concept, Counter())[c.kind] += 1
    totals: Counter[str] = Counter(c.kind for c in claims)
    return ListResult(
        documents=[
            Document(
                concept=concept,
                sections=s,
                extracted=e,
                claims=dict(per.get(concept, {})),
            )
            for concept, (s, e) in documents.items()
            if concepts is None or concept in concepts
        ],
        totals=dict(totals),
    )
