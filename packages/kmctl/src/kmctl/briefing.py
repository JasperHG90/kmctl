"""The session briefing: where knowledge lives, which skill to use, what is due, and one reading rule (ADR 0002).

The SessionStart hook in kmctl's APM package relays it, so it is read
at the start of every session in every harness. It reads state and writes
nothing, and stays within ``TOKEN_BUDGET`` (invariant I3). The rules for
writing knowledge are not in it: kmctl's APM package installs them in each
harness's rules folder, which reaches the system prompt anyway. It carries only
``RULES``, the guidance those files do not.
"""

import json
import re
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Protocol
from urllib.parse import unquote, urlparse

import yaml
from pydantic import BaseModel, Field, ValidationError

from kmctl import plugin
from kmctl.handoffs import live_handoffs
from kmctl.kinds import ARCHITECTURE
from kmctl.review_due import review_due
from kmctl.summary import changed_concepts

#: The most tokens the briefing may take, estimated at CHARS_PER_TOKEN.
TOKEN_BUDGET = 500
CHARS_PER_TOKEN = 4

#: Guidance the knowledge rules kmctl's package installs do not carry.
RULES = [
    (
        "unverified-is-a-lead",
        (
            "Treat a concept with no verified entry, or past its stale_after, "
            "as a lead to check, not a fact."
        ),
    )
]

ROUTING = """\
Knowledge in this repository:
- docs/: pages for people who use the project, one folder per Diataxis type,
  each with a generated README.md.
- .okf/: an OKF v0.2 bundle for people and agents working on it. Start at
  .okf/summary.md. manifesto.md is the design; decisions/ records each choice and
  what it rejected; architecture/ the design as diagrams; practices/ lessons;
  proposals/ designs not yet built; prototypes/ spikes; handoffs/ notes on
  where work stopped.
- Skills do repeatable tasks; the rules your tool loads cover writing knowledge.
Verbs: kmctl new decision|practice|proposal|prototype|handoff to add a concept;
kmctl new doc tutorial|how-to|reference|explanation for a docs/ page;
kmctl check when done (--fix writes docs indexes; never edit one);
kmctl handoffs for live handoffs; kmctl schema KIND for a document's shape. All take --help and --json."""

#: ROUTING for a bundle with no .okf/summary.md yet (kmctl update writes one).
ROUTING_NO_SUMMARY = ROUTING.replace(
    "Start at\n  .okf/summary.md.", "Start at\n  .okf/index.md."
)

EMPTY = "No .okf/ bundle here. Run kmctl init to start docs/ and .okf/."

_FIRST_SENTENCE = re.compile(r"\.\s| - ")
#: Words kept from a skill's description or the newest handoff's title, so
#: neither can break TOKEN_BUDGET.
_SUMMARY_WORDS = 12


@dataclass(frozen=True)
class State:
    """Counts only, so the briefing stays the same size however big the bundle grows."""

    due: int
    live_handoffs: int
    newest_handoff: str | None
    #: How many concepts changed after .okf/summary.md (0 when it is current),
    #: or None when there is no summary or no git history to tell (ADR 0027).
    summary_behind: int | None


@dataclass(frozen=True)
class Setup:
    """Whether the repository's knowledge is set up, which the agent settles with the user first.

    Attributes
    ----------
    initialized : bool
        ``kmctl init`` has run: there is an ``.okf/`` folder.
    manifesto_written : bool
        ``.okf/manifesto.md`` has text under its headings, not only init's scaffold.
    architecture_detailed : bool
        ``.okf/architecture/`` has a page other than its index.
    """

    initialized: bool
    manifesto_written: bool
    architecture_detailed: bool


@dataclass(frozen=True)
class Briefing:
    """The parts of the briefing."""

    routing: str
    setup: Setup
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
    first = _FIRST_SENTENCE.split(description.strip(), maxsplit=1)[0].rstrip(".")
    clipped = _clip(first)
    return clipped if clipped.endswith("...") else clipped + "."


def _clip(text: str) -> str:
    """``text`` cut at _SUMMARY_WORDS words, ending in "..." when cut."""
    words = text.split()
    if len(words) > _SUMMARY_WORDS:
        return " ".join(words[:_SUMMARY_WORDS]).rstrip(",;:") + "..."
    return " ".join(words)


def load_skills() -> list[tuple[str, str]]:
    """Each skill folder kmctl's package ships, as (name, when to use it), read at run time."""
    folder = plugin.skills_dir()
    if not folder.is_dir():
        return []
    return [
        (p.name, _skill_summary(p / "SKILL.md"))
        for p in sorted(folder.iterdir())
        if p.is_dir()
    ]


def estimate_tokens(text: str) -> int:
    """About how many tokens ``text`` takes, at CHARS_PER_TOKEN characters each."""
    return -(-len(text) // CHARS_PER_TOKEN)


def _manifesto_written(manifesto: Path) -> bool:
    """Whether ``manifesto`` has a line of text that is not front matter, a heading or blank."""
    if not manifesto.is_file():
        return False
    text = manifesto.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        text = text[end + 4 :] if end != -1 else ""
    return any(
        line.strip() and not line.lstrip().startswith("#") for line in text.splitlines()
    )


def read_setup(root: Path) -> Setup:
    """Whether ``root`` has kmctl initialized, a written manifesto and an architecture page."""
    okf = root / ".okf"
    architecture = okf / ARCHITECTURE
    return Setup(
        initialized=okf.is_dir(),
        manifesto_written=_manifesto_written(okf / "manifesto.md"),
        architecture_detailed=architecture.is_dir()
        and any(p.name != "index.md" for p in architecture.glob("*.md")),
    )


def build_briefing(root: Path) -> Briefing:
    """Build the briefing for the repository at ``root``.

    Parameters
    ----------
    root : Path
        The repository root.

    Returns
    -------
    Briefing
        Routing (starting at .okf/summary.md, or at .okf/index.md when there
        is no summary), setup, state (None when there is no .okf/), RULES and
        the package's skills (empty when there is no .okf/).
    """
    setup = read_setup(root)
    if not setup.initialized:
        return Briefing(routing=EMPTY, setup=setup, state=None, rules=RULES, skills=[])
    handoffs = live_handoffs(root)
    changed = changed_concepts(root)
    state = State(
        due=len(review_due(root).due),
        live_handoffs=len(handoffs),
        newest_handoff=_clip(handoffs[0].title) if handoffs else None,
        summary_behind=None if changed is None else len(changed),
    )
    routing = (
        ROUTING if (root / ".okf" / "summary.md").is_file() else ROUTING_NO_SUMMARY
    )
    return Briefing(
        routing=routing, setup=setup, state=state, rules=RULES, skills=load_skills()
    )


def setup_line(setup: Setup) -> str:
    """The briefing's setup line: all done, or what is missing and that it comes first."""
    if not setup.initialized:
        return (
            "Setup first: kmctl is not initialized. Ask the user to run kmctl "
            "init, then write the manifesto and architecture with you."
        )
    missing = [
        text
        for done, text in (
            (setup.manifesto_written, "manifesto not written"),
            (setup.architecture_detailed, "no architecture pages"),
        )
        if not done
    ]
    if not missing:
        return "Setup: kmctl initialized, manifesto written, architecture detailed."
    return (
        f"Setup first: {'; '.join(missing)}. Ask the user to fill these in "
        "with you now."
    )


def render(briefing: Briefing) -> str:
    """The briefing as text for the session start."""
    lines = [
        f"kmctl briefing (kmctl {version('kmctl')})",
        setup_line(briefing.setup),
        briefing.routing,
    ]
    if briefing.skills:
        lines.append("kmctl skills:")
        lines += [f"- {name}: {summary}" for name, summary in briefing.skills]
    if briefing.state is not None:
        s = briefing.state
        concepts = "concept" if s.due == 1 else "concepts"
        handoffs = "handoff" if s.live_handoffs == 1 else "handoffs"
        line = (
            f"State: {s.due} {concepts} due for review (kmctl review due); "
            f"{s.live_handoffs} live {handoffs}"
        )
        if s.newest_handoff:
            line += f", newest: {s.newest_handoff}"
        if s.summary_behind == 0:
            line += "; summary current"
        elif s.summary_behind is not None:
            changed = "concept" if s.summary_behind == 1 else "concepts"
            line += f"; summary behind: {s.summary_behind} {changed} changed"
        lines.append(line + ".")
    lines.append("Reading knowledge:")
    lines += [f"- {name}: {text}" for name, text in briefing.rules]
    return "\n".join(lines)


def as_dict(briefing: Briefing) -> dict:
    """The briefing as one JSON-ready object."""
    data = asdict(briefing)
    data["rules"] = [{"name": n, "text": t} for n, t in briefing.rules]
    data["skills"] = [{"name": n, "summary": s} for n, s in briefing.skills]
    return data


class _Stdin(Protocol):
    """What ``hook_workspace`` uses of standard input."""

    def isatty(self) -> bool:
        """Whether it is a terminal."""
        ...

    def read(self) -> str:
        """All of it."""
        ...


class _HookInput(BaseModel):
    """The JSON object Antigravity sends a hook on stdin, with the field kmctl reads."""

    workspace_paths: list[str] = Field(
        default_factory=list,
        alias="workspacePaths",
        description="The open workspaces' folders; the first is the repository.",
    )


def hook_workspace(stdin: _Stdin | None) -> Path | None:
    """The repository an Antigravity hook names on stdin, or None.

    Antigravity sends every hook a JSON object whose ``workspacePaths`` lists
    the open workspaces; the first is the repository. A terminal is never
    read, so a person running the command by hand is not left waiting. Empty
    input, input that is not that JSON, and a path that is not a folder all
    give None, and the caller falls back to ``--path``. A ``file://`` URI is
    read as its path.
    """
    if stdin is None or stdin.isatty():
        return None
    try:
        paths = _HookInput.model_validate_json(stdin.read()).workspace_paths
    except ValidationError:
        return None
    first = paths[0] if paths else ""
    if not first:
        return None
    if first.startswith("file://"):
        first = unquote(urlparse(first).path)
    path = Path(first)
    return path if path.is_dir() else None


def as_antigravity(text: str) -> str:
    """The briefing ``text`` in the JSON an Antigravity SessionStart hook prints to inject it."""
    return json.dumps({"injectSteps": [{"systemMessage": {"systemMessage": text}}]})
