"""List the changes since the newest decision record that may hold an unrecorded decision (ADR 0047).

``kmctl decision candidates`` calls no model and writes nothing. It splits
git history into changes, one per ticket merge, pull request or plain
commit, and gives each what a judge needs to say whether it made a decision
no record covers. The decision-gaps skill does the judging; the user
decides what becomes a record.

The split walks ``HEAD``'s first-parent line. A sync merge (``Merge
remote-tracking branch ...``) is followed into the commits it brought in,
and so is a pull request merge whose branch holds ticket merges, which is
listed as those tickets instead of as one change. Commits that only keep
the loop harness's state, release commits and placeholder commits are left
out (:data:`SKIPPED`).
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from kmctl.concepts import ConceptError

#: A ticket merge the loop harness writes: ``Merge loop/SLUG: SUMMARY``.
TICKET = re.compile(r"^Merge loop/(?P<slug>[a-z0-9-]+): (?P<summary>.+)$")
#: A pull request merge GitHub writes.
PULL = re.compile(r"^Merge pull request #(?P<number>\d+) from \S+$")
#: A merge that brought another line of history in, followed into what it brought.
SYNC = re.compile(r"^Merge remote-tracking branch ")
#: Subjects never listed: loop state, release commits and their pull
#: requests, syncs and merges of main into a branch, and placeholders.
SKIPPED = re.compile(
    r"^(loop: |release: "
    r"|Merge pull request #\d+ from \S+/release/(kmaudit-)?v"
    r"|Merge remote-tracking branch "
    r"|Merge (branch '?main'? |main )into "
    r"|operator: manual commits?$"
    r"|chore; manual commits?$)"
)
#: A decision record's path, with its number.
DECISION = re.compile(r"^\.okf/decisions/(?P<number>\d{4})-[^/]+\.md$")
#: Paths that keep knowledge or loop state; signals ignore them.
BOOKKEEPING = (".okf/", ".loop/")

#: Words in a change's text that often go with a choice.
_WORDS = re.compile(
    r"\b(instead of|rather than|replac\w*|switch\w* (to|from)|drop\w*|no longer|"
    r"stop\w*|move[sd]? (from|to|into)|only|rejected|in place of|deprecat\w*)\b",
    re.IGNORECASE,
)
_DEPENDENCY_FILE = re.compile(r"(^|/)pyproject\.toml$")
_DEPENDENCY_LINE = re.compile(r'^[+-]\s*"[A-Za-z0-9_.\-\[\]]+[<>=~!]')
_WORKFLOW = re.compile(r"^(\.github/workflows/|action\.ya?ml$)")
_CONFIG = re.compile(
    r"(^|/)(apm\.ya?ml|copier\.ya?ml|\.pre-commit-config\.yaml|config\.toml|[^/]*schema[^/]*\.json)$"
)
_SURFACE = re.compile(
    r"(^|/)\.apm/|(^|/)(hooks|skills|agents|instructions)/|^\.claude/rules/"
)
_SOURCE = re.compile(r"(^|/)src/.+\.py$|^scripts/.+\.py$")


@dataclass(frozen=True)
class Candidate:
    """One change in history, with what a judge needs to say whether it made a decision.

    Attributes
    ----------
    sha : str
        The change's commit.
    parent : str | None
        Its first parent, where the decision index stood before it; None for a root commit.
    kind : str
        ``ticket`` for a ticket merge, ``pull`` for a pull request merge, ``commit`` otherwise.
    subject : str
        The commit subject.
    message : str
        The commit body, stripped.
    slug : str | None
        The ticket's slug for a ticket merge.
    plan : str | None
        The ticket's plan, relative to the repository root, when it exists.
    files : list[list[str]]
        Each changed path against the first parent, as ``[status, path]``.
    recorded : list[str]
        The decision numbers the change added or amended.
    signals : dict[str, bool]
        Each decision-shaped signal and whether the change shows it.
    score : int
        How many signals the change shows.
    """

    sha: str
    parent: str | None
    kind: str
    subject: str
    message: str
    slug: str | None
    plan: str | None
    files: list[list[str]] = field(default_factory=list)
    recorded: list[str] = field(default_factory=list)
    signals: dict[str, bool] = field(default_factory=dict)
    score: int = 0


def _git(root: Path, *args: str) -> str:
    """Run git in ``root`` and return its stdout; raise ConceptError naming the fix when it fails."""
    proc = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise ConceptError(
            proc.stderr.strip().splitlines()[-1]
            if proc.stderr.strip()
            else "git failed"
        )
    return proc.stdout


def _commit(root: Path, ref: str) -> str:
    """The full sha ``ref`` names; raise ConceptError when it names no commit."""
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "-q", "--verify", f"{ref}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise ConceptError(
            f"--since {ref!r} names no commit; give a sha, tag or branch, e.g. --since v0.13.0"
        )
    return proc.stdout.strip()


def _walk(
    root: Path, tip: str, exclude: list[str]
) -> Iterator[tuple[str, list[str], str, str]]:
    """Yield (sha, parents, subject, body) of each change on ``tip``'s first-parent line, newest first.

    The walk stops at commits any of ``exclude`` reaches. A sync merge is
    followed by the commits it brought in. A pull request merge whose branch
    holds ticket merges yields that branch's commits in its place.
    """
    log = _git(
        root,
        "log",
        "--first-parent",
        "--format=%H%x1f%P%x1f%s%x1f%b%x1e",
        tip,
        *(f"^{ref}" for ref in exclude),
    )
    for record in log.split("\x1e")[:-1]:
        sha, parents, subject, body = record.lstrip("\n").split("\x1f")
        pair = parents.split()
        if len(pair) == 2 and PULL.match(subject) and not SKIPPED.match(subject):
            brought = list(_walk(root, pair[1], [*exclude, pair[0]]))
            if any(TICKET.match(change[2]) for change in brought):
                yield from brought
                continue
        yield sha, pair, subject, body
        if len(pair) == 2 and SYNC.match(subject):
            yield from _walk(root, pair[1], [*exclude, pair[0]])


def default_since(root: Path) -> str | None:
    """The commit that added the newest decision record committed in HEAD, or None when there is none.

    ``root`` is the repository's top level. Records only in the working tree
    or the index are not counted, so a record written but not yet committed
    does not move the start.
    """
    names = _git(root, "ls-tree", "--name-only", "HEAD", ".okf/decisions/").split()
    records = sorted(n for n in names if DECISION.match(n))
    if not records:
        return None
    added = _git(
        root, "log", "--follow", "--diff-filter=A", "--format=%H", "--", records[-1]
    ).split()
    return added[-1] if added else None


def _changes(root: Path, sha: str, parent: str | None) -> list[list[str]]:
    """Each path ``sha`` changes against ``parent`` as [status, path], renames as their new path."""
    if parent is None:
        out = _git(
            root, "diff-tree", "--root", "-r", "--name-status", "--no-commit-id", sha
        )
    else:
        out = _git(root, "diff", "--name-status", "-M", parent, sha)
    return [
        [line.split("\t")[0][0], line.split("\t")[-1]]
        for line in out.splitlines()
        if line
    ]


def _plan(root: Path, slug: str | None) -> str | None:
    """The ticket's plan, relative to ``root``, live or archived, when it exists."""
    if not slug:
        return None
    for plan in (
        Path(".loop") / "plans" / slug / "README.md",
        Path(".loop") / "archive" / slug / "plans" / slug / "README.md",
    ):
        if (root / plan).is_file():
            return plan.as_posix()
    return None


def _intent(root: Path, plan: str | None) -> str:
    """The plan's Intent section, or '' when there is no plan or no such section."""
    if not plan:
        return ""
    text = (root / plan).read_text(encoding="utf-8")
    return (
        text.split("## Intent", 1)[1].split("\n## ", 1)[0]
        if "## Intent" in text
        else ""
    )


def _dependency_changed(
    root: Path, sha: str, parent: str | None, files: list[list[str]]
) -> bool:
    """Whether the change adds or removes a dependency line in a pyproject.toml."""
    paths = [p for _, p in files if _DEPENDENCY_FILE.search(p)]
    if not paths or parent is None:
        return False
    diff = _git(root, "diff", "-U0", parent, sha, "--", *paths)
    return any(_DEPENDENCY_LINE.match(line) for line in diff.splitlines())


def _signals(
    root: Path, sha: str, parent: str | None, files: list[list[str]], text: str
) -> dict[str, bool]:
    """The decision-shaped signals of one change, read outside .okf/ and .loop/."""
    shipped = [(s, p) for s, p in files if not p.startswith(BOOKKEEPING)]
    return {
        "dependency": _dependency_changed(root, sha, parent, files),
        "new_module": any(s == "A" and _SOURCE.search(p) for s, p in shipped),
        "deleted": any(s == "D" for s, _ in shipped),
        "workflow": any(_WORKFLOW.search(p) for _, p in shipped),
        "config": any(_CONFIG.search(p) for _, p in shipped),
        "surface": any(_SURFACE.search(p) for _, p in shipped),
        "words": bool(_WORDS.search(" ".join(text.split()))),
        "broad": len({p.split("/")[0] for _, p in shipped}) >= 4,
    }


def candidates(root: Path, since: str | None = None) -> list[Candidate]:
    """List every change after ``since`` (default: the newest decision's commit), highest score first.

    Parameters
    ----------
    root :
        A folder inside the repository to read; the list is read from the
        repository's top level, and nothing in it is written.
    since :
        A commit, tag or branch; the list starts after it. None starts after
        the commit that added the newest decision record, or at the first
        commit when there is none.

    Returns
    -------
    list[Candidate]
        One per change, highest score first, newest first among equal scores.

    Raises
    ------
    ConceptError
        When ``root`` is not in a git repository, the repository has no
        commits, or ``since`` names no commit.
    """
    top = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if top.returncode:
        raise ConceptError(
            f"{root} is not a git repository; run it inside one or pass --path"
        )
    root = Path(top.stdout.strip())
    if subprocess.run(
        ["git", "-C", str(root), "rev-parse", "-q", "--verify", "HEAD"],
        capture_output=True,
        check=False,
    ).returncode:
        raise ConceptError(
            f"{root} has no commits yet; commit something, then list the candidates"
        )
    start = _commit(root, since) if since else default_since(root)
    found: list[Candidate] = []
    for sha, parents, subject, body in _walk(root, "HEAD", [start] if start else []):
        if SKIPPED.match(subject):
            continue
        parent = parents[0] if parents else None
        files = _changes(root, sha, parent)
        ticket = TICKET.match(subject)
        slug = ticket["slug"] if ticket else None
        plan = _plan(root, slug)
        recorded = sorted(
            {m["number"] for s, p in files if s != "D" and (m := DECISION.match(p))}
        )
        text = " ".join([subject, body, _intent(root, plan)])
        signals = _signals(root, sha, parent, files, text)
        found.append(
            Candidate(
                sha=sha,
                parent=parent,
                kind="ticket"
                if ticket
                else "pull"
                if PULL.match(subject)
                else "commit",
                subject=subject,
                message=body.strip(),
                slug=slug,
                plan=plan,
                files=files,
                recorded=recorded,
                signals=signals,
                score=sum(signals.values()),
            )
        )
    order = {c.sha: i for i, c in enumerate(found)}
    return sorted(found, key=lambda c: (-c.score, order[c.sha]))
