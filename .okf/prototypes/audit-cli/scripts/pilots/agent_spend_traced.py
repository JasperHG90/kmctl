"""Rebuild the "after" agent-spend run from its LangSmith traces: what each batch spent and the checks it submitted.

Run from the audit-cli folder, after scripts/pilots/from_traces.py wrote results/pilots/traces-agent-spend.json:

    uv run python scripts/pilots/agent_spend_traced.py SINCE UNTIL BATCHES   # ISO times (UTC), batches it ran

The run on 2026-11-10 stopped at the spending cap before it saved its own results; every call was traced. Batches
ran one after another and labels repeat across batches (c1 to c4), so the rebuild only accepts a run it can split
without guessing: each batch ends with one call whose Submits cover exactly its labels, and the number of batches
is the one given. Anything else (a batch submitted over several calls, a check sent back, an unreadable Submit,
calls left over) stops the script. Each batch's submitted checks are run again against the repository. Writes
results/pilots/agent-spend-after-traced.json.
"""

import json
import sys
from collections import Counter
from typing import Any

from pydantic import ValidationError

from audit_cli.checks.steps import Repository, run_check
from audit_cli.checks.writer import Submit

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import agent_spend, common  # the scripts folder is not a package on the path


def main(since: str, until: str, expected: int) -> None:
    """Split the traced calls into batches, rerun each batch's checks and save both."""
    traces = json.loads((common.OUT / "traces-agent-spend.json").read_text())
    calls = sorted((t for t in traces if since <= t["start"] <= until), key=lambda t: t["start"])
    repo = Repository(common.REPO)
    groups = agent_spend.batches(agent_spend.sample())
    out: dict[str, Any] = {"batches": [], "claims": {}}
    current: list[dict[str, Any]] = []
    covered: set[str] = set()
    for call in calls:
        current.append(call)
        if not call["submits"]:
            continue
        if len(out["batches"]) == len(groups):
            raise SystemExit(f"a Submit after the last batch, at {call['start']}")
        batch = groups[len(out["batches"])]
        by_label = {f"c{i}": c for i, c in enumerate(batch, 1)}
        submissions = []
        for args in call["submits"]:
            try:
                submissions.append(Submit.model_validate(args))
            except ValidationError as error:
                raise SystemExit(f"an unreadable Submit at {call['start']}: rebuild this run by hand") from error
        for submission in submissions:
            for label in [c.claim for c in submission.checks] + [n.claim for n in submission.no_checks]:
                if label not in by_label:
                    raise SystemExit(f"{label} at {call['start']} is not a label of batch {len(out['batches']) + 1}")
                covered.add(label)
        if covered != set(by_label):
            raise SystemExit(
                f"the Submit at {call['start']} covers {sorted(covered)}, not all of batch {len(out['batches']) + 1}"
            )
        for submission in submissions:
            for check in submission.checks:
                holds, results = run_check(repo, check.steps)
                out["claims"][by_label[check.claim].claim_id] = {
                    "claim": by_label[check.claim].text,
                    "status": "holds" if holds else "fails",
                    "check": check.model_dump(mode="json"),
                    "results": [r.model_dump() for r in results],
                }
            for no in submission.no_checks:
                out["claims"][by_label[no.claim].claim_id] = {
                    "claim": by_label[no.claim].text,
                    "status": "no check",
                    "reason": no.reason,
                }
        out["batches"].append(
            {
                "claims": len(batch),
                "calls": len(current),
                "in": sum(c["in"] for c in current),
                "out": sum(c["out"] for c in current),
                "cached": sum(c["cached"] for c in current),
                "tools": dict(sum((Counter(c["tools"]) for c in current), Counter())),
            }
        )
        current, covered = [], set()
    if current or len(out["batches"]) != expected:
        raise SystemExit(f"{len(out['batches'])} batches rebuilt and {len(current)} calls left, not {expected} batches")
    (common.OUT / "agent-spend-after-traced.json").write_text(json.dumps(out, indent=1))
    for b in out["batches"]:
        print(b)
    for e in out["claims"].values():
        print(f"\n[{e['status']}] {e['claim']}")
        for step, result in zip(e.get("check", {}).get("steps", []), e.get("results", []), strict=True):
            print("   ", "ok" if result["holds"] else "X ", json.dumps(step)[:170])
        if "reason" in e:
            print("    reason:", e["reason"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
