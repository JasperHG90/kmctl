"""The bundle summary, ``.okf/summary.md``: when it is behind its concepts, and ``ack`` (ADR 0027, ADR 0048).

The summary is the bundle's first page: what the knowledge says as a whole,
citing its concepts. It is behind when a concept changed in a commit after
the last commit that changed the summary or an ack file, or is changed (or
new and untracked) in the working tree while neither the summary nor an ack
file is. Commit order, not dates, decides, so a concept committed together
with the summary is covered. The concepts are the manifesto, decisions,
practices, proposals, prototype READMEs and architecture pages; indexes,
``log.md``, handoffs and the summary itself never count. Without git history
(no repository, or a shallow clone) the rule cannot be checked, the way
``review_due`` skips its history reason.

``ack`` is how an agent says the summary is still right after a change: it
writes one ack file under ``.okf/.acks/``, with a name no other ack has, so
two branches that both ack never change the same bytes and merge without a
conflict (ADR 0048). It claims no person's review; that is ``kmctl verify``
(ADR 0023).
"""

import hashlib
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from kmctl.concepts import _STAMP, ConceptError
from kmctl.okf import BadFrontMatter, field, front_matter
from kmctl.verify import _block

#: The summary's path from the repository root, and its concept id.
SUMMARY = ".okf/summary.md"
SUMMARY_ID = "summary"
#: The folder of ack files, from the repository root. Its name starts with a dot,
#: so the bundle checks, which read sections, leave it alone.
ACKS = ".okf/.acks"
#: The most words the summary's body may hold, outside its front matter.
WORD_LIMIT = 500

#: A path, from the repository root, of a concept whose change the summary follows.
_CONCEPT = re.compile(
    r"\.okf/(manifesto\.md|(decisions|practices|proposals|architecture)/[^/]+\.md"
    r"|prototypes/[^/]+/README\.md)"
)


@dataclass(frozen=True)
class Acked:
    """What ``ack`` wrote: the summary's path, the time, the concepts it was checked against, and the ack file.

    Attributes
    ----------
    path : str
        The summary's path from the repository root.
    at : str | None
        The UTC time written as ``at``, to the second, or None when nothing
        was written because the summary was not behind.
    against : list[str]
        The concept ids written as ``against``: the ones that had changed
        since the summary and are still in the bundle.
    file : str | None
        The ack file's path from the repository root, or None when nothing
        was written.
    """

    path: str
    at: str | None
    against: list[str]
    file: str | None = None


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


def in_bundle(root: Path, cid: str) -> bool:
    """True when ``cid`` is the id of a concept the summary follows, and it is in ``root``'s bundle."""
    rel = f".okf/{cid}/README.md" if cid.startswith("prototypes/") else f".okf/{cid}.md"
    return is_concept(rel) and (root / rel).is_file()


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
    acks = prefix + ACKS + "/"
    if prefix + SUMMARY in working or any(p.startswith(acks) for p in working):
        # an uncommitted edit to the summary, or an ack, covers everything so far
        return []
    base = (_git(root, "log", "-1", "--format=%H", "--", SUMMARY, ACKS) or "").strip()
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


def _without_checked(head: list[str]) -> list[str]:
    """``head`` (the front matter lines) without a ``checked`` block, which kmctl wrote before ADR 0048."""
    for i, line in enumerate(head):
        if line.startswith("checked:"):
            return [*head[:i], *head[_block(head, i) :]]
    return head


def ack(root: Path, now: datetime | None = None) -> Acked:
    """Record that the summary still holds after the concepts that changed since it.

    It writes one ack file under ``.okf/.acks/`` that holds ``at`` (the UTC
    time, to the second) and ``against`` (the ids ``changed_concepts`` lists,
    less those no longer in the bundle, such as a deleted concept). The
    file's name is the time and a digest of ``HEAD`` and those ids, so two
    branches write different files. It removes the ack files that were there,
    which this one replaces, and a ``checked`` block in the summary's front
    matter, which kmctl wrote before ADR 0048. It changes no other line and
    no other file. When the summary is not behind, it writes nothing.

    Parameters
    ----------
    root : Path
        The repository root, holding .okf/summary.md.
    now : datetime | None
        The time written, in UTC; now when omitted.

    Returns
    -------
    Acked
        The summary's path, the time written and the ack file's path (both
        None when nothing was written) and the concept ids it was checked
        against, which may be none when every changed concept was deleted.

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
    changed = [cid for cid in changed if in_bundle(root, cid)]
    at = now.strftime(_STAMP)
    head_commit = (_git(root, "rev-parse", "HEAD") or "").strip()
    digest = hashlib.sha256("\n".join([head_commit, *changed]).encode()).hexdigest()
    folder = root / ACKS
    folder.mkdir(exist_ok=True)
    for old in folder.glob("*.yaml"):
        old.unlink()
    file = f"{ACKS}/{now.strftime('%Y%m%dT%H%M%SZ')}-{digest[:8]}.yaml"
    lines = [
        "# kmctl summary ack: .okf/summary.md was read against these concepts and still holds.",
        f"at: {at}",
        "against:" if changed else "against: []",
        *[f"  - {cid}" for cid in changed],
    ]
    (root / file).write_text("\n".join(lines) + "\n", encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 4)
    head = text[4:end].split("\n")
    if _without_checked(head) != head:
        new = "---\n" + "\n".join(_without_checked(head)) + text[end:]
        path.write_text(new, encoding="utf-8")
    return Acked(path=SUMMARY, at=at, against=changed, file=file)
