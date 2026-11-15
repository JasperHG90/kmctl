"""How much of a repository's code the bundle's claims cover, line by line.

A line is covered when the last run of a stored check matched it: a grep
line, a code pattern's whole node, a definition or an import. A file that a
check only reads (a file, query or help step) is "read", not covered, and is
counted apart. A run whose files changed since is stale: its lines are not
counted until a rerun (the ``checks_run`` MCP tool or the audit page) runs it again. Only answers to
claims now in the store count, as in ``kmaudit checks list``. The code is every
file a check may read that is on disk, without tests, fixtures, evals, lock
files and the folders harnesses install packages into (ADR 0042).
"""

import fnmatch
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel, Field

from kmaudit.check_store import check, check_ids
from kmaudit.check_verbs import CHECKABLE
from kmaudit.sections import resolve_target
from kmaudit.steps import Repository, is_test
from kmaudit.store import Store

#: Generated files that are code in name only (``*.lock`` is never read at all).
LOCK_FILES = ("*-lock.json", "*.lock.json", "*lock.yaml")
#: Folders harnesses install packages into: other people's skills and agents, not this repository's code.
INSTALLED_DIRS = (".github/skills/", ".github/agents/", ".agents/", ".opencode/")


class LineHit(BaseModel):
    """The claims whose checks matched one line, and whether any of them fails."""

    claims: list[str] = Field(description="Claim ids, which are also check ids.")
    drift: bool = Field(
        description="True when a check matching the line fails on its last run (drift, or fails); "
        "a run skipped for a missing extra does not count."
    )


class FileCoverage(BaseModel):
    """One code file: its size, the lines checks matched, and the checks that read it."""

    path: str
    lines: int = Field(description="Non-blank lines.")
    covered: int = Field(description="Non-blank lines a check matched.")
    hits: dict[int, LineHit] = Field(
        description="Matched lines, by 1-based line number."
    )
    read_by: list[str] = Field(
        description="Claim ids whose checks read the file, matched lines or not."
    )


class Coverage(BaseModel):
    """Line coverage of a repository's code by the claims' checks."""

    lines: int = Field(description="Non-blank lines of code.")
    covered: int = Field(description="Of those, lines a check matched.")
    files: int = Field(description="Code files.")
    files_read: int = Field(description="Code files at least one check reads.")
    stale: int = Field(
        description="Checks whose files changed since their last run; their lines are not counted."
    )
    by_file: list[FileCoverage]

    @property
    def share(self) -> float:
        """Covered lines over all lines, 0 when there is no code."""
        return self.covered / self.lines if self.lines else 0.0


def code_files(repo: Repository) -> list[str]:
    """The files that count as code: what a check may read and is on disk, without tests, fixtures, evals, lock files and installed packages."""
    return [
        f
        for f in repo.files
        if not is_test(f)
        and not f.startswith(INSTALLED_DIRS)
        and not any(fnmatch.fnmatchcase(f.rsplit("/", 1)[-1], p) for p in LOCK_FILES)
        and repo.sha(f) != "missing"
    ]


def coverage(path: Path) -> Coverage:
    """Measure which lines of the repository's code the stored checks matched on their last run.

    Raises
    ------
    AuditError
        If ``path`` names no bundle, or the repository is not a git repository.
    """
    target = resolve_target(path)
    repo = Repository(target.root, target.bundle)
    files = code_files(repo)
    wanted = set(files)
    hits: dict[str, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
    failing: dict[str, set[int]] = defaultdict(set)
    read_by: dict[str, set[str]] = defaultdict(set)
    stale = 0
    with Store(target.root, target.namespace) as store:
        live = {c.id for c in store.claims() if c.kind in CHECKABLE}
        for claim_id in check_ids(store):
            if claim_id not in live:
                continue  # its section waits for extraction; claims_todo hands it out
            stored = check(store, claim_id)
            if stored is None or stored.kind != "check" or stored.holds is None:
                continue
            for read in stored.reads:
                if read in wanted:
                    read_by[read].add(claim_id)
            if any(repo.sha(p) != h for p, h in stored.reads.items()):
                stale += 1  # its lines may have moved; checks_run reruns it
                continue
            fails = not stored.holds and not stored.skipped
            for result in stored.results:
                for span in result.spans:
                    if span.path not in wanted:
                        continue
                    for n in range(span.start, span.end + 1):
                        hits[span.path][n].add(claim_id)
                        if fails:
                            failing[span.path].add(n)
    by_file: list[FileCoverage] = []
    for f in files:
        text = repo.text(f).splitlines()
        real = {n for n, line in enumerate(text, 1) if line.strip()}
        matched = {n: ids for n, ids in hits.get(f, {}).items() if n in real}
        by_file.append(
            FileCoverage(
                path=f,
                lines=len(real),
                covered=len(matched),
                hits={
                    n: LineHit(claims=sorted(ids), drift=n in failing[f])
                    for n, ids in sorted(matched.items())
                },
                read_by=sorted(read_by.get(f, set())),
            )
        )
    return Coverage(
        lines=sum(f.lines for f in by_file),
        covered=sum(f.covered for f in by_file),
        files=len(by_file),
        files_read=sum(1 for f in by_file if f.read_by),
        stale=stale,
        by_file=by_file,
    )
