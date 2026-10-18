"""The document kinds kmctl knows, with their front matter and body sections, and their JSON Schema.

``KINDS`` is the one definition: ``kmctl new`` and ``kmctl new doc`` take their
skeletons from it, ``kmctl init`` the manifesto's and the summary's sections, ``kmctl decision
supersede`` the deprecated status, and ``kmctl schema`` prints a schema built
from it, so the schema is what kmctl writes. Field names come only from
``ALLOWED_FIELDS`` (invariant I4).
"""

from dataclasses import dataclass
from typing import Any

from kmctl.okf import ALLOWED_FIELDS

#: The OKF v0.2 status values (section 5.4).
DRAFT, STABLE, DEPRECATED = "draft", "stable", "deprecated"
STATUS_VALUES = (DRAFT, STABLE, DEPRECATED)

#: An architecture page's type, and the section every one ends with
#: (``apm/.apm/instructions/diagrams-stay-current.instructions.md``).
ARCHITECTURE = "architecture"
DEPICTS = "Depicts"

#: The summary's sections, each a theme of what the bundle knows (ADR 0027).
SUMMARY_SECTIONS = ["Decisions", "Architecture", "Open work", "Practices", "Known gaps"]

#: The heading ``kmctl decision supersede`` appends to a record, before its date.
CORRECTION = "Correction"


@dataclass(frozen=True)
class Last:
    """A body of free ``##`` sections whose last one is ``name``."""

    name: str


@dataclass(frozen=True)
class Pattern:
    """A body whose ``##`` headings each match the regular expression ``regex``."""

    regex: str
    meaning: str


#: A body: a fixed list of ``##`` sections in order, a heading pattern, free
#: sections with a fixed last one, or None for no fixed sections.
Body = list[str] | Pattern | Last | None


@dataclass(frozen=True)
class DocumentKind:
    """One kind of document: where it lives, its front matter and its body.

    Attributes
    ----------
    where : str
        The path it lives at, with placeholders such as ``SLUG``.
    purpose : str
        What it is for, in a few words, for the list.
    detail : str
        What only a rule says about it, for the schema's description.
    fields : tuple[str, ...]
        The top-level front matter fields it may carry, from ``ALLOWED_FIELDS``.
    required : tuple[str, ...]
        The fields kmctl always writes.
    type : str | None
        Its OKF ``type`` value, or None when it has no front matter type.
    status : str | None
        The ``status`` kmctl writes into a new one, or None for none.
    sections : Body
        Its body sections.
    then : Pattern | None
        Sections that may follow a fixed list, any number of them, or None.
    """

    where: str
    purpose: str
    detail: str
    fields: tuple[str, ...]
    required: tuple[str, ...]
    type: str | None
    status: str | None
    sections: Body
    then: Pattern | None = None


_CONCEPT = ("type", "title", "description", "tags", "generated", "status")
_REVIEWED = ("verified", "stale_after")
_WRITTEN = ("type", "title", "description", "tags", "generated")


def _concept(
    kind: str, where: str, purpose: str, detail: str, sections: list[str]
) -> DocumentKind:
    """A concept ``kmctl new KIND`` writes, which may name its sources."""
    return DocumentKind(
        where=where,
        purpose=purpose,
        detail=f"{detail} kmctl new {kind} writes it.",
        fields=(*_CONCEPT, *_REVIEWED, "sources"),
        required=_WRITTEN,
        type=kind,
        status=None,
        sections=sections,
    )


def _page(where: str, purpose: str, sections: Body) -> DocumentKind:
    """A file with no front matter."""
    return DocumentKind(
        where=where,
        purpose=purpose,
        detail="It has no front matter.",
        fields=(),
        required=(),
        type=None,
        status=None,
        sections=sections,
    )


#: The optional front matter of a docs/ page (ADR 0022).
_DOC_FIELDS = ("description", "stale_after", "verified", "sources")


def _doc_page(where: str, purpose: str, sections: Body) -> DocumentKind:
    """A docs/ page, whose front matter is optional and has no type."""
    return DocumentKind(
        where=where,
        purpose=purpose,
        detail=(
            "Its front matter is optional: kmctl new doc writes description, "
            "stale_after three months ahead and an empty sources, never "
            "verified. kmctl review due lists it once stale_after passes or a "
            "source changes; it is not an OKF concept."
        ),
        fields=_DOC_FIELDS,
        required=(),
        type=None,
        status=None,
        sections=sections,
    )


KINDS: dict[str, DocumentKind] = {
    "decision": DocumentKind(
        where=".okf/decisions/NNNN-SLUG.md",
        purpose="one choice and why it was made",
        detail=(
            "The Decision section names the alternative it rejected. A record is "
            "never rewritten: kmctl decision supersede sets status deprecated and "
            "appends a dated Correction section. kmctl new decision writes it."
        ),
        fields=(*_CONCEPT, *_REVIEWED, "sources"),
        required=(*_WRITTEN, "status"),
        type="decision",
        status=STABLE,
        sections=["Context", "Decision", "Consequences"],
        then=Pattern(
            rf"{CORRECTION}, \d{{4}}-\d{{2}}-\d{{2}}",
            f"then any number of dated {CORRECTION} sections, "
            f"{CORRECTION}, YYYY-MM-DD, that kmctl decision supersede appends",
        ),
    ),
    "practice": _concept(
        "practice",
        ".okf/practices/SLUG.md",
        "a lesson backed by evidence",
        "The Evidence section points at what showed the lesson.",
        ["What happened", "The lesson", "Evidence"],
    ),
    "proposal": _concept(
        "proposal",
        ".okf/proposals/SLUG.md",
        "a design not yet built",
        "It stays a proposal until it is built or dropped.",
        ["Problem", "Proposal", "Open questions"],
    ),
    "prototype": _concept(
        "prototype",
        ".okf/prototypes/SLUG/README.md",
        "a spike, with its scripts beside it",
        "Its scripts live in the same folder as the README.",
        ["Question", "Method", "Results", "Conclusion"],
    ),
    "handoff": DocumentKind(
        where=".okf/handoffs/SLUG.md",
        purpose="where work stopped, for the next session",
        detail=(
            "It is live until its stale_after (14 days unless set), then kmctl "
            "review due lists it as expired. It names no sources. kmctl new "
            "handoff writes it, and with --key updates it in place."
        ),
        fields=(*_CONCEPT, *_REVIEWED, "handoff_key"),
        required=(*_WRITTEN, "stale_after"),
        type="handoff",
        status=None,
        sections=["Summary", "Where it stands", "Next steps", "Key references"],
    ),
    "manifesto": DocumentKind(
        where=".okf/manifesto.md",
        purpose="what the project is for, its invariants and values",
        detail=(
            "Invariants carry ids such as I1 that other pages cite. The values "
            "are the operator's to write. kmctl init writes it with these "
            "sections, and the operator may change them."
        ),
        fields=(*_CONCEPT, *_REVIEWED),
        required=_WRITTEN,
        type="manifesto",
        status=None,
        sections=["What this is for", "Invariants", "Values"],
    ),
    "summary": DocumentKind(
        where=".okf/summary.md",
        purpose="the bundle's first page: its themes, each linking down to its concepts",
        detail=(
            "There is one, and kmctl init writes it. Its body is at most 500 "
            "words, which kmctl check enforces, and holds no counts or due "
            "lists. kmctl review due lists it, with the concepts that changed, "
            "when a concept changed after the summary's last commit; editing it "
            "or kmctl summary ack, which writes checked, clears that. It is "
            "never verified and has no stale_after."
        ),
        fields=(*_WRITTEN, "checked"),
        required=_WRITTEN,
        type="summary",
        status=None,
        sections=SUMMARY_SECTIONS,
    ),
    "index": DocumentKind(
        where=".okf/index.md",
        purpose="the bundle's root index, linking the summary, the manifesto and each section",
        detail=(
            "Its front matter carries only okf_version, and its body is a "
            "list of links, one per section. kmctl init writes it."
        ),
        fields=("okf_version",),
        required=("okf_version",),
        type=None,
        status=None,
        sections=None,
    ),
    "section-index": _page(
        ".okf/SECTION/index.md",
        "a section's index, one link per concept",
        None,
    ),
    "log": _page(
        ".okf/log.md",
        "the bundle's dated log of changes",
        Pattern(r"\d{4}-\d{2}-\d{2}", "one dated section per day, YYYY-MM-DD"),
    ),
    ARCHITECTURE: DocumentKind(
        where=".okf/architecture/SLUG.md",
        purpose="a diagram of the design, ending with what it depicts",
        detail=(
            f"Its sections are free except the last, {DEPICTS}, which lists the "
            "invariant ids, entry points and modules the diagram shows. No kmctl "
            "verb writes it."
        ),
        fields=(*_CONCEPT, *_REVIEWED, "sources"),
        required=("type", "title", "description"),
        type=ARCHITECTURE,
        status=None,
        sections=Last(DEPICTS),
    ),
    "tutorial": _doc_page(
        "docs/tutorials/SLUG.md",
        "a docs/ lesson that builds something",
        ["What you will build", "Before you start", "Steps", "What you learned"],
    ),
    "how-to": _doc_page(
        "docs/how-to/SLUG.md",
        "a docs/ page for one task",
        ["Before you start", "Steps", "Check it worked"],
    ),
    "reference": _doc_page(
        "docs/reference/SLUG.md",
        "a docs/ page of facts",
        ["Summary", "Details"],
    ),
    "explanation": _doc_page(
        "docs/explanation/SLUG.md",
        "a docs/ page on why",
        ["The question", "How it works", "Why it is this way"],
    ),
    "docs-index": _page(
        "docs/README.md",
        "the docs/ root index, written by hand: a link to each Diataxis folder's "
        "index and to any page outside those folders",
        None,
    ),
    "docs-folder-index": _page(
        "docs/FOLDER/README.md",
        "a Diataxis folder's index, one link per page, which kmctl check --fix "
        "generates from each page's title and description",
        None,
    ),
}

_DATE = {
    "anyOf": [
        {"type": "string", "format": "date-time"},
        {"type": "string", "format": "date"},
    ],
}
_BY_AT = {
    "type": "object",
    "additionalProperties": False,
    "required": ["by", "at"],
    "properties": {
        "by": {
            "type": "string",
            "description": "Who: process:NAME/VERSION for a tool, human:ID for a person.",
        },
        "at": {
            **_DATE,
            "description": (
                "When: a date (2026-10-15) or a UTC timestamp (2026-10-15T08:00:00Z)."
            ),
        },
    },
}

#: What each front matter field means, beside where ``ALLOWED_FIELDS`` says it comes from.
_FIELD_SCHEMAS: dict[str, dict[str, Any]] = {
    "okf_version": {"const": "0.2", "description": "The OKF version, quoted."},
    "type": {"type": "string", "description": "The kind of concept."},
    "title": {"type": "string", "description": "The title, as the page's # heading."},
    "description": {
        "type": "string",
        "description": "One sentence, the same as the index entry's.",
    },
    "tags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Words to find it by; kmctl writes the kind.",
    },
    "generated": {**_BY_AT, "description": "Who wrote it and when."},
    "verified": {
        "anyOf": [{"type": "array", "items": _BY_AT}, _BY_AT],
        "description": (
            "Who checked it against the code and when, newest last; one mapping "
            "also reads as a list of one."
        ),
    },
    "sources": {
        "type": "array",
        "items": {
            "anyOf": [
                {"type": "string"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["resource"],
                    "properties": {
                        "id": {"type": "string", "description": "A short name."},
                        "resource": {
                            "type": "string",
                            "description": (
                                "A file or folder from the repository root, or "
                                "from .okf/ with a leading /."
                            ),
                        },
                    },
                },
            ]
        },
        "description": (
            "What it describes; kmctl review due lists it when one changes "
            "after the last verified date. kmctl new writes --source as resource mappings."
        ),
    },
    "status": {
        "enum": list(STATUS_VALUES),
        "description": "How far to trust it.",
    },
    "stale_after": {
        **_DATE,
        "description": "When kmctl review due lists it as due, or a handoff as expired.",
    },
    "handoff_key": {
        "type": "string",
        "description": "The session key kmctl new handoff --key updates it by.",
    },
    "checked": {
        "type": "object",
        "additionalProperties": False,
        "required": ["at", "against"],
        "properties": {
            "at": {
                **_DATE,
                "description": "When kmctl summary ack ran, a UTC timestamp to the second.",
            },
            "against": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The ids of the concepts that had changed, which it was checked against.",
            },
        },
        "description": (
            "An agent's word, from kmctl summary ack, that the summary still "
            "holds after the concepts that changed; not a person's review."
        ),
    },
}


def _sub_path(path: str, name: str) -> str:
    """The ``ALLOWED_FIELDS`` path of key ``name`` under ``path``.

    A path ending in ``[].`` is a list item's; ``verified`` written as one
    mapping has its keys under ``verified[].``, the way ``okf.field`` reads it.
    """
    if path.endswith("[]."):
        return f"{path}{name}"
    nested = f"{path}.{name}"
    return nested if nested in ALLOWED_FIELDS else f"{path}[].{name}"


def _cited(schema: dict[str, Any], path: str) -> dict[str, Any]:
    """``schema`` with each description at or under ``path`` ending in its OKF source."""
    out = dict(schema)
    if "description" in out:
        out["description"] = f"{out['description']} ({ALLOWED_FIELDS[path]})"
    if "properties" in out:
        out["properties"] = {
            name: _cited(sub, _sub_path(path, name))
            for name, sub in out["properties"].items()
        }
    if "items" in out:
        out["items"] = _cited(out["items"], f"{path}[].")
    if "anyOf" in out:
        out["anyOf"] = [_cited(alt, path) for alt in out["anyOf"]]
    return out


def _sections_json(body: Body) -> Any:
    """``body`` as the JSON value of ``x-kmctl-sections``."""
    if isinstance(body, Pattern):
        return {"pattern": body.regex}
    if isinstance(body, Last):
        return {"last": body.name}
    return body


def _body_text(body: Body, then: Pattern | None = None) -> str:
    """One sentence on ``body``, and the sections that may follow it, for the schema's description."""
    if isinstance(body, list):
        after = f", {then.meaning}" if then else ""
        return (
            "Body: these ## sections, in this order: " + ", ".join(body) + after + "."
        )
    if isinstance(body, Pattern):
        return f"Body: {body.meaning}."
    if isinstance(body, Last):
        return f"Body: any ## sections, the last one {body.name}."
    return "Body: no fixed ## sections."


def schema(name: str) -> dict[str, Any]:
    """The JSON Schema (draft 2020-12) of kind ``name``'s front matter, with its body in ``x-kmctl-sections`` and ``x-kmctl-then``.

    Raises
    ------
    KeyError
        When ``name`` is not in ``KINDS``.
    """
    kind = KINDS[name]
    properties = {}
    for f in kind.fields:
        sub = _cited(_FIELD_SCHEMAS[f], f)
        if f == "type" and kind.type is not None:
            sub = {**sub, "const": kind.type}
        properties[f] = sub
    out: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": name,
        "description": f"{kind.where}: {kind.purpose}. {kind.detail} {_body_text(kind.sections, kind.then)}",
        "type": "object",
        "properties": properties,
        "required": list(kind.required),
        "additionalProperties": False,
        "x-kmctl-sections": _sections_json(kind.sections),
    }
    if kind.then is not None:
        out["x-kmctl-then"] = {"pattern": kind.then.regex}
    return out


def skeleton(name: str) -> list[str]:
    """The fixed ``##`` sections of kind ``name``, which kmctl writes as its skeleton.

    Raises
    ------
    TypeError
        When the kind's body is not a fixed list of sections.
    """
    sections = KINDS[name].sections
    if not isinstance(sections, list):
        raise TypeError(f"kind {name!r} has no fixed list of sections")
    return sections
