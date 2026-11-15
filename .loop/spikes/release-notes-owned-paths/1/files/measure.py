"""Count kmctl notes commits the current ownership rule keeps that touch only bookkeeping paths.

For each kmctl release range (previous tag to tag, and the last tag to the
given tip), walk the first-parent commits release_notes.py walks, skip the
ones it skips (loop: and release: subjects), and count how many the current
rule (kmctl owns packages/kmctl/ and everything outside packages/) keeps,
and how many of those touch nothing but .loop/, .okf/, .claude/ or uv.lock.
Run from the repository root: python3 measure.py TIP
"""

import subprocess
import sys

BOOKKEEPING = (".loop/", ".okf/", ".claude/")
FILES = ("uv.lock",)


def git(*args: str) -> str:
    """Run git and return its stdout."""
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def current(path: str) -> bool:
    """Today's rule for kmctl."""
    return path.startswith("packages/kmctl/") or not path.startswith("packages/")


def bookkeeping(path: str) -> bool:
    """A path that ships in no package."""
    return path.startswith(BOOKKEEPING) or path in FILES


def main() -> None:
    """Print one line per range and a total."""
    tip = sys.argv[1]
    tags = [t for t in git("tag", "--list", "v*", "--sort=v:refname").split() if "rc" not in t]
    ranges = list(zip(tags, tags[1:])) + [(tags[-1], tip)]
    total_kept = total_drop = 0
    for old, new in ranges[-6:]:
        kept = drop = 0
        names = []
        for sha in git("rev-list", "--first-parent", f"{old}..{new}").split():
            subject = git("log", "-1", "--format=%s", sha).strip()
            if subject.startswith(("loop: ", "release: ")):
                continue
            paths = [p for p in git("diff", "--name-only", f"{sha}^1", sha).split("\n") if p]
            if not any(current(p) for p in paths):
                continue
            kept += 1
            if all(bookkeeping(p) for p in paths if current(p)):
                drop += 1
                names.append(subject[:70])
        total_kept += kept
        total_drop += drop
        print(f"{old}..{new}: kept {kept}, bookkeeping-only {drop}: {names}")
    print(f"total: {total_drop} of {total_kept} kept commits touch only bookkeeping paths")


main()
