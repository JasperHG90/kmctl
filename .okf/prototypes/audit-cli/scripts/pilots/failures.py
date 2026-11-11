"""Collect every failing check the pilots wrote, one per claim and check, to label and to ask a decision model about.

Run from the audit-cli folder: uv run python scripts/pilots/failures.py

Reads the saved one-call and agent results under results/pilots/ (a fix run's first, failing check counts too) and
writes results/pilots/failures.jsonl: per failing check the claim, its sentence, the steps, what each step saw and
the writer's why. Labels go in results/pilots/failure_labels.json, by hand: "drift" when what the steps saw shows the
claim is false, "check" when the check is wrong.
"""

import json
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path


def main() -> None:
    """Gather the failing checks, drop repeats, and save them."""
    sentences = {c.claim_id: c.sentence for c in common.claims()}
    found: dict[str, dict[str, object]] = {}
    for path in sorted(common.OUT.glob("*.json")):
        if not path.name.startswith(("oneshot-", "agent-spend-")):
            continue
        data = json.loads(path.read_text())
        entries = data.get("claims", {})
        for claim_id, entry in entries.items():
            for e in (entry.get("first"), entry):
                if not e or e.get("status") != "fails" or "check" not in e:
                    continue
                steps = e["check"]["steps"]
                key = f"{claim_id}|{json.dumps(steps, sort_keys=True)}"
                found.setdefault(
                    key,
                    {
                        "id": f"f{len(found) + 1}",
                        "claim_id": claim_id,
                        "claim": entry["claim"],
                        "sentence": sentences.get(claim_id, ""),
                        "steps": steps,
                        "saw": [{"holds": r["holds"], "detail": r["detail"][:300]} for r in e.get("results", [])],
                        "why": e["check"].get("why", ""),
                        "source": path.name,
                    },
                )
    out = common.OUT / "failures.jsonl"
    out.write_text("".join(json.dumps(v) + "\n" for v in found.values()))
    print(f"{len(found)} failing checks in {out.name}")


if __name__ == "__main__":
    main()
