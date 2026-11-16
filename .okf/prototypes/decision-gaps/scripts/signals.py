"""Score each unit by decision-shaped signals, with any decision it added hidden.

Each signal is 0 or 1; a unit's score is their sum. Signals read the unit's
visible changes (every path under .okf/ and .loop/ dropped, for every unit
alike) and its stripped subject, body and plan intent, so a positive unit
is scored as if its decision had never been written.

Usage::

    python3 scripts/signals.py REPO results/units.jsonl > results/signals.jsonl
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hide import intent, strip, visible_files

WORDS = re.compile(
    r"\b(instead of|rather than|replac\w*|switch\w* (to|from)|drop\w*|no longer|"
    r"stop\w*|move[sd]? (from|to|into)|only|rejected|in place of|deprecat\w*)\b",
    re.I,
)
DEPENDENCY_FILES = re.compile(r"(^|/)(pyproject\.toml|uv\.lock|package\.json|requirements[^/]*\.txt)$")
WORKFLOW = re.compile(r"^(\.github/workflows/|action\.ya?ml$)")
CONFIG = re.compile(
    r"(^|/)(apm\.ya?ml|copier\.ya?ml|\.pre-commit-config\.yaml|config\.toml|[^/]*schema[^/]*\.json)$"
)
SURFACE = re.compile(r"(^|/)\.apm/|(^|/)(hooks|skills|agents|instructions)/|^\.claude/rules/")
SOURCE = re.compile(r"(^|/)src/.+\.py$|^scripts/.+\.py$")


def git(repo: Path, *args: str) -> str:
    """Run git in ``repo`` and return its stdout."""
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout


def dependency_changed(repo: Path, unit: dict) -> bool:
    """Whether the unit adds or removes a line in a pyproject's dependency lists."""
    paths = [p for s, p in unit["files"] if p.endswith("pyproject.toml")]
    if not paths or not unit["parent"]:
        return False
    diff = git(repo, "diff", "-U0", unit["parent"], unit["sha"], "--", *paths)
    return any(
        re.match(r'^[+-]\s*"[A-Za-z0-9_.\-\[\]]+[<>=~!]', line) for line in diff.splitlines()
    )


def score(repo: Path, unit: dict) -> dict:
    """The unit's signals and total score."""
    files = visible_files(unit["files"])
    text = strip(" ".join([unit["subject"].split(":", 1)[-1], unit["body"], intent(repo, unit["slug"])]))
    signals = {
        "dependency": dependency_changed(repo, unit),
        "new_module": any(s == "A" and SOURCE.search(p) for s, p in files),
        "deleted": any(s == "D" and not p.startswith((".loop/", ".okf/")) for s, p in files),
        "workflow": any(WORKFLOW.search(p) for s, p in files),
        "config": any(CONFIG.search(p) for s, p in files),
        "surface": any(SURFACE.search(p) for s, p in files),
        "words": bool(WORDS.search(text)),
        "broad": len({p.split("/")[0] for s, p in files if not p.startswith((".loop/", ".okf/"))}) >= 4,
    }
    return {
        "sha": unit["sha"],
        "positive": bool(unit["adds_decisions"]),
        "signals": signals,
        "score": sum(signals.values()),
    }


def main() -> int:
    """Print one JSON line of signals per unit."""
    repo = Path(sys.argv[1]).resolve()
    for line in open(sys.argv[2]):
        print(json.dumps(score(repo, json.loads(line))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
