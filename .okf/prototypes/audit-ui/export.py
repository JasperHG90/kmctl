"""Export the audit store as data.js for the audit UI prototype.

Run from the repository root, in the project environment:

    uv run python .okf/prototypes/audit-ui/export.py

It refreshes the stored sections from the bundle (as ``kmctl audit claims
todo`` does), reads every concept's sections, sentence verdicts, claims and
stored checks, and writes ``data.js`` next to this file as
``window.AUDIT = {...}`` so ``index.html`` opens straight from disk.
"""

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from kmctl.claims.check_store import check
from kmctl.claims.check_verbs import list_checks
from kmctl.claims.sections import cut, resolve_target
from kmctl.claims.store import Store
from kmctl.claims.verbs import todo

HERE = Path(__file__).resolve().parent

# How each claim status counts towards a sentence's coverage, worst first.
COVERAGE = [
    ("drift", {"drift", "fails"}),
    ("unchecked", {"no check", "stale reason", "not run", "skipped", "weak"}),
    ("reason", {"reason"}),
    ("checked", {"holds", "not measured"}),
]


def coverage(statuses: list[str]) -> str:
    """The worst coverage among a sentence's claim statuses."""
    for name, members in COVERAGE:
        if any(s in members for s in statuses):
            return name
    return "checked"


def check_detail(store: Store, claim_id: str) -> dict | None:
    """A claim's stored check or reason as plain data, or None when it has none."""
    found = check(store, claim_id)
    if found is None:
        return None
    q = found.quality
    return {
        "kind": found.kind,
        "strength": found.strength,
        "why": found.why,
        "drift": found.drift,
        "reason": found.reason,
        "by": found.submitted_by,
        "steps": [s.model_dump(mode="json") for s in found.steps],
        "results": [r.detail for r in found.results],
        "reads": sorted(found.reads),
        "quality": None
        if q is None
        else {"mutants": q.mutants, "killed": q.killed, "survived": q.survived},
    }


def main(root: Path) -> None:
    """Write data.js for the bundle under ``root``."""
    todo(root)  # refresh stored sections so pending ones show as outdated
    statuses = {r.claim: r for r in list_checks(root).claims}
    concepts: dict[str, dict] = {}
    with Store(root) as store:
        pending = store.pending_sections()
        verdicts = {
            (sid, n): (kind, reason)
            for sid, n, kind, reason in store.db.execute(
                "SELECT section_id, n, kind, reason FROM verdicts"
            )
        }
        claims: dict[tuple[str, int], list[dict]] = {}
        for c in store.claims():
            row = statuses.get(c.id)
            claims.setdefault((c.section, c.n), []).append(
                {
                    "id": c.id,
                    "text": c.claim,
                    "kind": c.kind,
                    "quantifier": c.quantifier,
                    "status": row.status if row else "not checkable",
                    "check": check_detail(store, c.id) if row else None,
                }
            )
        # The store appends new and renamed sections, so take document order from the cutter.
        order = {sec.id: i for i, sec in enumerate(cut(resolve_target(root)))}
        rows = sorted(
            store.db.execute(
                "SELECT id, concept, title, section, sentences FROM sections"
            ),
            key=lambda row: order.get(row[0], len(order)),
        )
        for sid, concept, title, section, sentences in rows:
            doc = concepts.setdefault(
                concept, {"concept": concept, "title": title, "sections": []}
            )
            out = []
            for n, text in enumerate(json.loads(sentences), start=1):
                kind, reason = verdicts.get((sid, n), (None, ""))
                found = claims.get((sid, n), [])
                checkable = [
                    c["status"] for c in found if c["status"] != "not checkable"
                ]
                out.append(
                    {
                        "n": n,
                        "text": text,
                        "kind": kind,
                        "reason": reason,
                        "claims": found,
                        "coverage": "pending"
                        if sid in pending
                        else "none"
                        if not found
                        else "not checkable"
                        if not checkable
                        else coverage(checkable),
                    }
                )
            doc["sections"].append(
                {
                    "id": sid,
                    "name": section,
                    "pending": sid in pending,
                    "sentences": out,
                }
            )
    for doc in concepts.values():
        cov = Counter(
            s["coverage"] for sec in doc["sections"] for s in sec["sentences"]
        )
        doc["counts"] = dict(cov)
        doc["outdated"] = any(sec["pending"] for sec in doc["sections"])
        doc["state"] = (
            "outdated"
            if doc["outdated"]
            else "drift"
            if cov["drift"]
            else "unchecked"
            if cov["unchecked"]
            else "ok"
        )
    data = {
        "generated": datetime.now(UTC).isoformat(timespec="seconds"),
        "concepts": sorted(concepts.values(), key=lambda d: d["concept"]),
    }
    (HERE / "data.js").write_text(
        "window.AUDIT = " + json.dumps(data, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {HERE / 'data.js'}: {len(concepts)} concepts")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd())
