"""Pilot: mutation-test every stored check that holds, free, and print how many changes each one noticed.

Run from the audit-cli folder: uv run python scripts/pilots/mutation.py

Reads kmctl's database (the checks audit checks write stored), runs scripts' mutation tester
(src/audit_cli/checks/mutate.py) on each holding check, and writes results/pilots/mutation.json: per check the claim,
its steps, mutants tried, killed and the ones it missed.
"""

import json
import pathlib as plb
import sys
import time
from collections import Counter
from typing import Any

from pydantic import TypeAdapter

from audit_cli.checks.mutate import measure
from audit_cli.checks.steps import Repository, Step
from audit_cli.config import load_config
from audit_cli.db import Store

sys.path.insert(0, str(plb.Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path

STEPS = TypeAdapter(list[Step])


def main() -> None:
    """Mutation-test each holding check and save the scores."""
    config = load_config(common.HERE / "audit.toml")
    repo = Repository(common.REPO, config.files)
    started = time.monotonic()
    rows: list[dict[str, Any]] = []
    with Store(config.database_path(common.REPO)) as store:
        claims = {c.claim_id: c.claim for c in store.claims()}
        results = store.results()
        for claim_id, check in store.checks().items():
            result = results.get(claim_id)
            if check.kind != "check" or result is None or not result.holds:
                continue
            q = measure(repo, STEPS.validate_python(check.steps), [r["detail"] for r in result.results])
            rows.append(
                {
                    "claim": claims.get(claim_id, ""),
                    "strength": check.strength,
                    "steps": check.steps,
                    "mutants": q.mutants,
                    "killed": q.killed,
                    "survived": q.survived[:5],
                }
            )
    scored = [r for r in rows if r["mutants"]]
    summary = {
        "checks": len(rows),
        "with_mutants": len(scored),
        "killed_none": sum(r["killed"] == 0 for r in scored),
        "killed_all": sum(r["killed"] == r["mutants"] for r in scored),
        "mean_score": round(sum(int(r["killed"]) / int(r["mutants"]) for r in scored) / max(len(scored), 1), 2),
        "by_strength_killed_none": dict(Counter(r["strength"] for r in scored if r["killed"] == 0)),
        "seconds": round(time.monotonic() - started, 1),
    }
    (common.OUT / "mutation.json").write_text(json.dumps({"summary": summary, "checks": rows}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
