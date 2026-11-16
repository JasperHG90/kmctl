"""Ask a model whether each unit made a decision that no existing decision covers.

The judge runs ``claude -p`` from an empty temporary folder with no tools, no MCP servers and no project or
user settings, so neither this repository's CLAUDE.md nor any session hook
reaches it. It sees what the skill would: the unit's subject and body, its
plan's intent when the ticket has one (both with any sentence naming an ADR
or a decision stripped), the files it changed outside .okf/ and .loop/,
and the decision index as it stood in the unit's first parent. A unit that
already has a result in the output file is skipped, so a stopped run resumes.

Usage::

    python3 scripts/judge.py REPO results/units.jsonl results/judge.jsonl [MODEL]
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hide import intent, strip, visible_files

MODEL = "sonnet"
#: An empty folder to run the judge in, so no CLAUDE.md or project settings are found.
EMPTY = tempfile.mkdtemp(prefix="decision-gaps-judge-")
MAX_FILES = 60
MAX_PLAN_WORDS = 1200

INSTRUCTIONS = """You review one change to a software repository and decide whether it made a decision that deserves a decision record (an ADR) and whether an existing record already covers it.

A change deserves a record when it commits the project to one option among real alternatives that a later contributor could reasonably question or reverse: architecture, module or package boundaries, dependencies, interfaces and formats, how the project is distributed, installed or released, and working process. It does not when it fixes a bug, refactors without choosing anything, edits docs or tests, or adds a feature the way an existing decision already says to.

Answer with one JSON object and nothing else:
{"verdict": "missing" | "covered" | "none", "choice": "<the choice made, one sentence, or empty>", "rejected": "<the alternative it turned down, if the change shows one, or empty>", "covered_by": "<ADR number that covers it, or empty>"}

"missing": the change made such a decision and none of the existing records covers it.
"covered": it made one, and an existing record already covers it.
"none": it made no decision that deserves a record."""


def git(repo: Path, *args: str) -> str:
    """Run git in ``repo`` and return its stdout, or '' when the command fails."""
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else ""


def prompt(repo: Path, unit: dict) -> str:
    """The judge's input for ``unit``."""
    plan = " ".join(strip(intent(repo, unit["slug"])).split()[:MAX_PLAN_WORDS])
    files = visible_files(unit["files"])
    listed = "\n".join(f"{s} {p}" for s, p in files[:MAX_FILES])
    if len(files) > MAX_FILES:
        listed += f"\n... and {len(files) - MAX_FILES} more"
    index = git(repo, "show", f"{unit['parent']}:.okf/decisions/index.md") if unit["parent"] else ""
    return (
        f"{INSTRUCTIONS}\n\n## The change\n\nSubject: {strip(unit['subject'])}\n\n"
        f"Message: {strip(unit['body']) or '(none)'}\n\n"
        f"Plan intent: {plan or '(no plan)'}\n\nFiles changed:\n{listed or '(none)'}\n\n"
        f"## Existing decision records\n\n{index or '(none)'}\n"
    )


def ask(text: str, model: str) -> dict:
    """Run the judge once and return its parsed answer with cost and time."""
    started = time.monotonic()
    done = subprocess.run(
        [
            "claude", "-p", "--model", model, "--output-format", "json",
            "--tools", "", "--strict-mcp-config", "--setting-sources", "",
            "--no-session-persistence",
        ],
        input=text, capture_output=True, text=True, timeout=600, cwd=EMPTY,
    )
    seconds = round(time.monotonic() - started, 1)
    envelope = json.loads(done.stdout)
    raw = envelope.get("result", "")
    start, end = raw.find("{"), raw.rfind("}")
    answer = json.loads(raw[start : end + 1]) if start != -1 else {"verdict": "unparsed", "raw": raw}
    return {**answer, "cost_usd": envelope.get("total_cost_usd"), "seconds": seconds}


def main() -> int:
    """Judge every unit not yet in the output file."""
    repo, units_path, out_path = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), Path(sys.argv[3])
    model = sys.argv[4] if len(sys.argv) > 4 else MODEL
    done = set()
    if out_path.exists():
        done = {json.loads(line)["sha"] for line in out_path.read_text().splitlines() if line}
    with out_path.open("a") as out:
        for line in units_path.read_text().splitlines():
            unit = json.loads(line)
            if unit["sha"] in done:
                continue
            result = ask(prompt(repo, unit), model)
            out.write(json.dumps({"sha": unit["sha"], "model": model, **result}) + "\n")
            out.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
