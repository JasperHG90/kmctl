"""Split the audit's due list into batches, and merge each batch's findings.

Usage:

    audit-batches.py split DUE_JSON OUT_DIR
        Groups the concepts in DUE_JSON ({"due": [...]}) by kind and splits
        each kind into batches of at most ten, as the audit skill's step 2
        says. Writes batch N to OUT_DIR/N.json in the same shape and prints
        one line per batch: the file, the kind's review skill and the batch's
        name, separated by tabs.

    audit-batches.py add REPLY MERGED
        Reads the findings from the last fenced json block in REPLY, with the
        same checks audit-report.py makes, and adds them to MERGED, a file
        holding one fenced json block (created when missing). Exits 1 with the
        reason on stderr, leaving MERGED as it was, when REPLY has no usable
        findings.

Each Hermes run gets one batch, so no prompt nears Linux's 128 KiB limit on
one argument, and audit-report.py still reads one block for the whole audit.
"""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

BATCH_SIZE = 10
REVIEW_SKILLS = {
    "architecture": "architecture-review",
    "decisions": "decision-log-review",
    "practices": "practices-review",
}


def _report_module() -> ModuleType:
    """Load audit-report.py, which sits next to this file, to reuse its checks."""
    path = Path(__file__).with_name("audit-report.py")
    spec = importlib.util.spec_from_file_location("audit_report", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def batches(due: list[dict]) -> list[tuple[str, list[dict]]]:
    """Return ``(kind, concepts)`` batches of at most ten, grouped by kind in a fixed order.

    Concepts whose id does not start with a known kind are left out.
    """
    out: list[tuple[str, list[dict]]] = []
    for kind in REVIEW_SKILLS:
        group = [c for c in due if c["id"].startswith(f"{kind}/")]
        for start in range(0, len(group), BATCH_SIZE):
            out.append((kind, group[start : start + BATCH_SIZE]))
    return out


def split(due_json: Path, out_dir: Path) -> list[str]:
    """Write each batch to ``out_dir`` and return one tab-separated line per batch."""
    found = batches(json.loads(due_json.read_text())["due"])
    totals = {kind: sum(k == kind for k, _ in found) for kind in REVIEW_SKILLS}
    seen = dict.fromkeys(REVIEW_SKILLS, 0)
    lines = []
    for n, (kind, concepts) in enumerate(found, start=1):
        seen[kind] += 1
        path = out_dir / f"{n}.json"
        path.write_text(json.dumps({"due": concepts}))
        name = f"{kind} batch {seen[kind]} of {totals[kind]}"
        lines.append(f"{path}\t{REVIEW_SKILLS[kind]}\t{name}")
    return lines


def add(reply: Path, merged: Path) -> None:
    """Add the findings in ``reply`` to the block in ``merged``.

    Raises
    ------
    ValueError, TypeError
        If ``reply`` (or ``merged``) holds no usable findings block.
    """
    findings = _report_module()._findings
    earlier = findings(merged.read_text()) if merged.exists() else []
    new = findings(reply.read_text())
    # Escape backticks so a finding's text can never close the fence early.
    body = json.dumps(earlier + new, indent=2).replace("`", "\\u0060")
    merged.write_text("```json\n" + body + "\n```\n")


def main() -> int:
    """Run the subcommand named on the command line; return the exit code."""
    command, *args = sys.argv[1:]
    if command == "split":
        for line in split(Path(args[0]), Path(args[1])):
            print(line)
        return 0
    if command == "add":
        try:
            add(Path(args[0]), Path(args[1]))
        except (ValueError, TypeError) as err:
            print(f"kmctl audit: no usable findings: {err}", file=sys.stderr)
            return 1
        return 0
    print(f"audit-batches.py: unknown command {command!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
