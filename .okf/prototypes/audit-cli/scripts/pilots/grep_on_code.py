"""Count the grep steps the one-call pilots pinned to source code, where a code step could stand in: free, no calls.

Run from the audit-cli folder: uv run python scripts/pilots/grep_on_code.py

For each saved one-call run, counts checks, grep steps, grep steps over source files (the code step's languages),
and how those checks ended. Writes results/pilots/grep_on_code.json.
"""

import json
import pathlib as plb
import sys
from collections import Counter

from audit_cli.checks.steps import LANGUAGES

sys.path.insert(0, str(plb.Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path

RUNS = ("oneshot-lines-grouped-low", "oneshot-lines-single-low", "oneshot-lines-grouped-low-code")


def on_code(step: dict[str, object]) -> bool:
    """Whether a grep step searches source files a code step could read."""
    paths = str(step.get("paths", ""))
    return step.get("op") == "grep" and any(paths.endswith(suffix) for suffix in LANGUAGES)


def main() -> None:
    """Print, per run, how many checks lean on grep over code and how they ended."""
    out = {}
    for run in RUNS:
        claims = json.loads((common.OUT / f"{run}.json").read_text())["claims"]
        checks = [e for e in claims.values() if "check" in e]
        steps = [s for e in checks for s in e["check"]["steps"]]
        leaning = [e for e in checks if any(on_code(s) for s in e["check"]["steps"])]
        out[run] = {
            "checks": len(checks),
            "steps_by_op": dict(Counter(s["op"] for s in steps)),
            "grep_steps_on_code": sum(on_code(s) for s in steps),
            "checks_with_grep_on_code": len(leaning),
            "their_status": dict(Counter(e["status"] for e in leaning)),
        }
    (common.OUT / "grep_on_code.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
