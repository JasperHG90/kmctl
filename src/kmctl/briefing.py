"""The session briefing: where knowledge lives, which skill to use, what is due, and the rules (ADR 0002).

The plugin's SessionStart hook relays it, so it is read at the start of every
session in every harness. It reads state and writes nothing, and stays within
``WORD_BUDGET`` (invariant I3).
"""

import re
from dataclasses import asdict, dataclass
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

import yaml

from kmctl.handoffs import live_handoffs
from kmctl.plugin import skills_dir
from kmctl.review_due import review_due

WORD_BUDGET = 600
RULE_FILES = ("docs-layout.md", "okf-bundle.md")

ROUTING = """\
Knowledge in this repository:
- docs/: pages for people who use the project, one folder per Diataxis type
  (tutorials, how-to, reference, explanation), each page listed in docs/README.md.
- .okf/: an OKF v0.2 bundle for people and agents working on it. Start at
  .okf/index.md. manifesto.md is the design; decisions/ records each choice and
  what it rejected; architecture/ the design as diagrams; practices/ lessons
  backed by evidence; proposals/ designs not yet built; prototypes/ spikes with
  their scripts; handoffs/ notes on where work stopped.
- Skills do repeatable tasks; the rules below are standing guidance.
Verbs: kmctl new decision|practice|proposal|prototype|handoff to add a concept;
kmctl new doc tutorial|how-to|reference|explanation for a docs/ page;
kmctl check after editing an index; kmctl review due for what needs review;
kmctl handoffs for live handoffs; kmctl schema KIND for a document's expected
shape. Each takes --help and --json."""

EMPTY = "No .okf/ bundle here. Run kmctl init to start docs/ and .okf/."

_FIRST_SENTENCE = re.compile(r"\.\s| - ")
#: Words kept from a skill's description, so new skills cannot break WORD_BUDGET.
_SUMMARY_WORDS = 12
_CONSTRAINT = re.compile(r'<constraint name="([^"]+)">\n(.*?)</constraint>', re.DOTALL)


@dataclass(frozen=True)
class State:
    """Counts only, so the briefing stays the same size however big the bundle grows."""

    due: int
    live_handoffs: int
    newest_handoff: str | None


@dataclass(frozen=True)
class Briefing:
    """The parts of the briefing."""

    routing: str
    state: State | None
    rules: list[tuple[str, str]]
    skills: list[tuple[str, str]]


def _skill_summary(skill_md: Path) -> str:
    """The first sentence of a SKILL.md description, cut at 12 words, or a pointer to the file.

    SKILL.md front matter is Claude Code's skill format, not an OKF concept, so
    it is parsed here rather than read through ``okf.front_matter`` (I4 covers OKF).
    """
    text = skill_md.read_text(encoding="utf-8") if skill_md.is_file() else ""
    end = text.find("\n---", 4)
    try:
        data = (
            yaml.safe_load(text[4:end])
            if text.startswith("---\n") and end != -1
            else None
        )
    except yaml.YAMLError:
        data = None
    description = data.get("description") if isinstance(data, dict) else None
    if not isinstance(description, str) or not description.strip():
        return "see its SKILL.md."
    words = (
        _FIRST_SENTENCE.split(description.strip(), maxsplit=1)[0].rstrip(".").split()
    )
    if len(words) > _SUMMARY_WORDS:
        return " ".join(words[:_SUMMARY_WORDS]).rstrip(",;:") + "..."
    return " ".join(words) + "."


def load_skills() -> list[tuple[str, str]]:
    """Each skill folder the packaged plugin ships, as (name, when to use it), read at run time."""
    folder = skills_dir()
    if not folder.is_dir():
        return []
    return [
        (p.name, _skill_summary(p / "SKILL.md"))
        for p in sorted(folder.iterdir())
        if p.is_dir()
    ]


def load_rules() -> list[tuple[str, str]]:
    """The packaged knowledge rules as (name, text), each without its WHY paragraph."""
    rules = []
    for name in RULE_FILES:
        text = files("kmctl").joinpath("rules", name).read_text(encoding="utf-8")
        for rule, body in _CONSTRAINT.findall(text):
            paragraphs = [
                p for p in body.strip().split("\n\n") if not p.startswith("WHY:")
            ]
            rules.append((rule, " ".join(" ".join(paragraphs).split())))
    return rules


def build_briefing(root: Path) -> Briefing:
    """Build the briefing for the repository at ``root``.

    Parameters
    ----------
    root : Path
        The repository root.

    Returns
    -------
    Briefing
        Routing, state (None when there is no .okf/), the rules and the
        plugin's skills (empty when there is no .okf/).
    """
    if not (root / ".okf").is_dir():
        return Briefing(routing=EMPTY, state=None, rules=load_rules(), skills=[])
    handoffs = live_handoffs(root)
    state = State(
        due=len(review_due(root).due),
        live_handoffs=len(handoffs),
        newest_handoff=handoffs[0].title if handoffs else None,
    )
    return Briefing(
        routing=ROUTING, state=state, rules=load_rules(), skills=load_skills()
    )


def render(briefing: Briefing) -> str:
    """The briefing as text for the session start."""
    lines = [f"kmctl briefing (kmctl {version('kmctl')})", briefing.routing]
    if briefing.skills:
        lines.append("Skills in the kmctl plugin:")
        lines += [f"- {name}: {summary}" for name, summary in briefing.skills]
    if briefing.state is not None:
        s = briefing.state
        concepts = "concept" if s.due == 1 else "concepts"
        handoffs = "handoff" if s.live_handoffs == 1 else "handoffs"
        line = (
            f"State: {s.due} {concepts} due for review (kmctl review due); "
            f"{s.live_handoffs} live {handoffs}"
        )
        lines.append(
            line + (f", newest: {s.newest_handoff}." if s.newest_handoff else ".")
        )
    lines.append("Rules for writing knowledge:")
    lines += [f"- {name}: {text}" for name, text in briefing.rules]
    return "\n".join(lines)


def as_dict(briefing: Briefing) -> dict:
    """The briefing as one JSON-ready object."""
    data = asdict(briefing)
    data["rules"] = [{"name": n, "text": t} for n, t in briefing.rules]
    data["skills"] = [{"name": n, "summary": s} for n, s in briefing.skills]
    return data
