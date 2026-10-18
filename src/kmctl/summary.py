"""The bundle summary, ``.okf/summary.md``: when it is behind its concepts, and ``ack`` (ADR 0027).

The summary is the bundle's first page: what the knowledge says as a whole,
citing its concepts. It is behind when a concept changed in a commit after
the last commit that changed the summary, or is changed (or new and
untracked) in the working tree while the summary is not. Commit order, not
dates, decides, so a concept committed together with the summary is
covered. The concepts are the manifesto, decisions, practices, proposals,
prototype READMEs and architecture pages; indexes, ``log.md``, handoffs and
the summary itself never count. Without git history (no repository, or a
shallow clone) the rule cannot be checked, the way ``review_due`` skips its
history reason.

``ack`` is how an agent says the summary is still right after a change: it
writes ``checked`` into the summary's front matter, which is an edit to the
summary, so the same rule clears it. It claims no person's review; that is
``kmctl verify`` (ADR 0023).

``nudge`` is what Claude Code's PostToolUse hook prints right after a tool
call: the concepts the summary is behind and both ways out. It uses the same
rule, so git only, and it remembers the last set it named as a hash under the
git directory, so later calls on the same set stay quiet. It never writes
``.okf/``.
"""

import hashlib
import re
import subprocess
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from kmctl.concepts import _STAMP, ConceptError
from kmctl.okf import BadFrontMatter, field, front_matter
from kmctl.verify import _block

#: The summary's path from the repository root, and its concept id.
SUMMARY = ".okf/summary.md"
SUMMARY_ID = "summary"
#: The most words the summary's body may hold, outside its front matter.
WORD_LIMIT = 500

#: Where the last nudged set's hash goes, as ``git rev-parse --git-path`` takes it.
NUDGE_STATE = "kmctl/summary-nudge"

#: A path, from the repository root, of a concept whose change the summary follows.
_CONCEPT = re.compile(
    r"\.okf/(manifesto\.md|(decisions|practices|proposals|architecture)/[^/]+\.md"
    r"|prototypes/[^/]+/README\.md)"
)


@dataclass(frozen=True)
class Acked:
    """What ``ack`` wrote: the summary's path, the time, and the concepts it was checked against.

    Attributes
    ----------
    path : str
        The summary's path from the repository root.
    at : str | None
        The UTC time written as ``checked.at``, to the second, or None when
        nothing was written because the summary was not behind.
    against : list[str]
        The concept ids written as ``checked.against``: the ones that had
        changed since the summary.
    """

    path: str
    at: str | None
    against: list[str]


def _git(root: Path, *args: str) -> str | None:
    """The output of ``git -C root ARGS``, or None when it fails."""
    proc = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    return proc.stdout if proc.returncode == 0 else None


def is_concept(rel: str) -> bool:
    """True when ``rel``, a path from the repository root, is a concept the summary follows."""
    return bool(_CONCEPT.fullmatch(rel)) and not rel.endswith("/index.md")


def concept_id(rel: str) -> str:
    """The concept id of ``rel``, as ``kmctl review due`` prints it.

    A prototype's id is its folder, as ``kmctl new prototype`` names it.
    """
    cid = Path(rel).relative_to(".okf").with_suffix("").as_posix()
    return cid.removesuffix("/README") if cid.startswith("prototypes/") else cid


def _status_paths(output: str) -> set[str]:
    """The paths ``git status --porcelain -z`` names, the new one for a rename or copy."""
    paths = set()
    entries = iter(output.split("\0"))
    for entry in entries:
        if len(entry) < 4:
            continue
        paths.add(entry[3:])
        if "R" in entry[:2] or "C" in entry[:2]:
            next(entries, None)  # the old path of a rename or copy
    return paths


def changed_concepts(root: Path) -> list[str] | None:
    """The concepts the summary in ``root`` is behind, by the rule in the module docstring.

    Parameters
    ----------
    root : Path
        The repository root, holding .okf/summary.md.

    Returns
    -------
    list[str] | None
        The changed concepts' ids, sorted; empty when the summary is current.
        None when there is no summary, or no git history to check it with
        (not a git repository, or a shallow clone).
    """
    if not (root / SUMMARY).is_file():
        return None
    shallow = _git(root, "rev-parse", "--is-shallow-repository")
    prefix = _git(root, "rev-parse", "--show-prefix")
    if shallow is None or shallow.strip() == "true" or prefix is None:
        return None
    prefix = prefix.strip()
    status = _git(
        root, "status", "--porcelain", "-z", "--untracked-files=all", "--", ".okf"
    )
    working = _status_paths(status or "")
    if prefix + SUMMARY in working:
        return []  # an uncommitted edit to the summary covers everything so far
    base = (_git(root, "log", "-1", "--format=%H", "--", SUMMARY) or "").strip()
    if base:
        listed = _git(root, "diff", "--name-only", "-z", f"{base}..HEAD", "--", ".okf")
    else:
        listed = _git(root, "ls-files", "-z", "--full-name", "--", ".okf")
    changed = set(filter(None, (listed or "").split("\0"))) | working
    rels = {p.removeprefix(prefix) for p in changed if p.startswith(prefix)}
    return sorted({concept_id(p) for p in rels if is_concept(p)})


def reason(changed: list[str]) -> str:
    """The ``kmctl review due`` reason for a summary behind the concepts ``changed``."""
    return "concepts changed: " + ", ".join(changed)


def body_words(text: str) -> int:
    """How many words ``text``, a page, holds outside its front matter."""
    text = text.replace("\r\n", "\n")
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            text = text[end + 4 :]
    return len(text.split())


def _with_checked(head: list[str], at: str, against: list[str]) -> list[str]:
    """``head`` (the front matter lines) with ``checked`` set to ``at`` and ``against``, replacing any old one."""
    block = ["checked:", f"  at: {at}", "  against:"]
    block += [f"    - {cid}" for cid in against]
    for i, line in enumerate(head):
        if line.startswith("checked:"):
            return [*head[:i], *block, *head[_block(head, i) :]]
    return [*head, *block]


def ack(root: Path, now: datetime | None = None) -> Acked:
    """Record that the summary still holds after the concepts that changed since it.

    It writes ``checked.at`` (the UTC time, to the second) and
    ``checked.against`` (the ids
    ``changed_concepts`` lists) into the summary's front matter, replacing an
    older ``checked``, and changes no other line and no other file. When the
    summary is not behind, it writes nothing.

    Parameters
    ----------
    root : Path
        The repository root, holding .okf/summary.md.
    now : datetime | None
        The time written, in UTC; now when omitted. When that would leave the
        file as it is (a second ack in the same second, against the same
        ids), it is a second later, so the summary always changes.

    Returns
    -------
    Acked
        The summary's path, the time written (None when nothing was) and the
        concept ids it was checked against.

    Raises
    ------
    ConceptError
        When there is no summary, its front matter is unreadable or lacks
        ``type: summary``, or there is no git history to tell what changed.
        Nothing is written.
    """
    now = (now or datetime.now(UTC)).astimezone(UTC)
    path = root / SUMMARY
    if not path.is_file():
        raise ConceptError(f"there is no {SUMMARY}; run kmctl init to write one")
    try:
        meta = front_matter(path)
    except BadFrontMatter as error:
        raise ConceptError(f"{error}; fix its front matter first") from error
    if field(meta, "type") != "summary":
        raise ConceptError(
            f"{SUMMARY} has no front matter with type: summary; kmctl schema "
            "summary gives its shape"
        )
    changed = changed_concepts(root)
    if changed is None:
        raise ConceptError(
            "there is no git history to tell which concepts changed (not a git "
            "repository, or a shallow clone); run it in a full clone"
        )
    if not changed:
        return Acked(path=SUMMARY, at=None, against=[])
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 4)
    at = now.strftime(_STAMP)
    head = _with_checked(text[4:end].split("\n"), at, changed)
    if "---\n" + "\n".join(head) + text[end:] == text:
        # An ack in the same second as the last one, against the same ids:
        # step a second on, so the summary always changes and the rule clears it.
        at = (now + timedelta(seconds=1)).strftime(_STAMP)
        head = _with_checked(text[4:end].split("\n"), at, changed)
    try:
        yaml.safe_load("\n".join(head))
    except yaml.YAMLError as error:
        raise ConceptError(
            f"{SUMMARY}'s front matter would not parse with checked added; "
            "rewrite its checked field as a block mapping"
        ) from error
    new = "---\n" + "\n".join(head) + text[end:]
    path.write_text(new, encoding="utf-8")
    return Acked(path=SUMMARY, at=at, against=changed)


class _HookPayload(BaseModel):
    """The JSON object Claude Code sends a PostToolUse hook on stdin, with the field kmctl reads."""

    cwd: str | None = Field(
        default=None, description="The folder the session runs in: the repository."
    )


class _Context(BaseModel):
    """What a PostToolUse hook hands Claude Code to add to the model's context."""

    model_config = ConfigDict(populate_by_name=True)

    event: str = Field(
        default="PostToolUse",
        alias="hookEventName",
        description="The hook event this output answers.",
    )
    context: str = Field(
        alias="additionalContext", description="The text the model reads next."
    )


class _HookOutput(BaseModel):
    """The JSON object a Claude Code PostToolUse hook prints to add context."""

    model_config = ConfigDict(populate_by_name=True)

    specific: _Context = Field(
        alias="hookSpecificOutput", description="The event's own output."
    )


def as_claude(text: str | None) -> str:
    """``text`` as the JSON a Claude Code PostToolUse hook prints, or ``{}`` for no nudge."""
    if text is None:
        return "{}"
    return _HookOutput(specific=_Context(context=text)).model_dump_json(by_alias=True)


class BadPayload(ValueError):
    """Hook input on stdin that is empty, not a JSON object, or names no folder."""


def payload_cwd(text: str) -> Path | None:
    """The folder a PostToolUse payload names as ``cwd``, or None when it names none.

    Raises
    ------
    BadPayload
        When ``text`` is empty, not a JSON object, or its ``cwd`` is not a
        string naming a folder.
    """
    try:
        payload = _HookPayload.model_validate_json(text)
    except ValidationError as error:
        raise BadPayload("the hook input is not a JSON object") from error
    if payload.cwd is None:
        return None
    path = Path(payload.cwd)
    if not path.is_dir():
        raise BadPayload(f"the hook input's cwd {payload.cwd!r} is not a folder")
    return path


def find_root(start: Path) -> Path:
    """The folder holding the summary for ``start``: it or a parent, up to the one holding ``.git``.

    It stops at the first folder holding ``.okf/summary.md`` or ``.git``, so a
    hook run in a subfolder finds the repository, and never reads a parent
    project's bundle. When neither is found, it is ``start``.
    """
    folder = start.resolve()
    for candidate in (folder, *folder.parents):
        if (candidate / SUMMARY).is_file() or (candidate / ".git").exists():
            return candidate
    return folder


def nudge_text(changed: list[str]) -> str:
    """The nudge for a summary behind the concepts ``changed``: what changed and both ways out."""
    return (
        f"kmctl: {SUMMARY} is behind concepts that changed since it: "
        f"{', '.join(changed)}. If they change what the summary says, update "
        f"{SUMMARY}; if it still holds, run kmctl summary ack."
    )


@dataclass(frozen=True)
class Nudge:
    """What ``nudge`` found: the concepts the summary is behind, and the nudge to give now.

    ``kmctl summary nudge --json`` prints it as is.

    Attributes
    ----------
    concepts : list[str]
        The changed concepts' ids, sorted; empty when the summary is current
        or the rule cannot be checked.
    nudge : str | None
        The nudge, or None to stay quiet: nothing changed, or this set was
        already named.
    behind : bool
        Whether the summary is behind a changed concept: ``concepts`` is not
        empty.
    """

    concepts: list[str]
    nudge: str | None
    behind: bool = dataclass_field(init=False)

    def __post_init__(self) -> None:
        """Derive ``behind`` from ``concepts``."""
        object.__setattr__(self, "behind", bool(self.concepts))


def nudge(root: Path) -> Nudge:
    """What to tell the agent about the summary in ``root`` now.

    It nudges when ``changed_concepts`` lists concepts and this set, against
    this summary text, is not the one it last nudged about. It then writes
    the set's hash to ``kmctl/summary-nudge`` under the git directory, so the
    same set stays quiet and a set that grows, or comes back after the
    summary changed, nudges again. It reads git and the summary only and
    writes nothing under ``.okf/``.

    Parameters
    ----------
    root : Path
        The repository root, holding .okf/summary.md.

    Returns
    -------
    Nudge
        The changed concepts, and the nudge text: None when the summary is
        current, there is no summary or git history, or this set was
        already named.
    """
    changed = changed_concepts(root)
    if not changed:
        return Nudge(concepts=[], nudge=None)
    quiet = Nudge(concepts=changed, nudge=None)
    where = _git(root, "rev-parse", "--git-path", NUDGE_STATE)
    if where is None:
        return quiet
    state = root / where.strip()
    key = hashlib.sha256((root / SUMMARY).read_bytes())
    key.update("\0".join(changed).encode())
    digest = key.hexdigest()
    try:
        if state.read_text(encoding="utf-8").strip() == digest:
            return quiet
    except OSError:
        pass  # no set nudged yet
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(digest + "\n", encoding="utf-8")
    return Nudge(concepts=changed, nudge=nudge_text(changed))
