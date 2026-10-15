"""Turn claude -p's JSON output into the audit's job summary and issue body.

Usage: audit-report.py CLAUDE_OUTPUT SUMMARY_OUT BODY_OUT. Reads the last fenced
json block in the result text, checks it is the auditor's findings list, and
writes a Markdown table to both files. Exits 1, writing nothing, when there is
no findings block or it has the wrong shape.
"""

import json
import re
import sys
from pathlib import Path

REVIEWS = {"architecture", "decision", "practice"}
VERDICTS = ("drifted", "unsure", "holds")
KEYS = {"concept", "path", "review", "verdict", "summary", "evidence"}


def _findings(output: str) -> list[dict]:
    result = json.loads(output).get("result") or ""
    blocks = re.findall(r"```json\s*\n(.*?)```", result, re.DOTALL)
    if not blocks:
        raise ValueError("the audit printed no findings block")
    findings = json.loads(blocks[-1])
    if not isinstance(findings, list):
        raise TypeError("the findings block is not a list")
    for item in findings:
        if not isinstance(item, dict) or not KEYS <= item.keys():
            raise ValueError(f"a finding lacks one of {sorted(KEYS)}: {item!r}")
        if item["review"] not in REVIEWS or item["verdict"] not in VERDICTS:
            raise ValueError(f"a finding has an unknown review or verdict: {item!r}")
        if not isinstance(item["evidence"], list):
            raise TypeError(f"a finding's evidence is not a list: {item!r}")
    return findings


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _report(findings: list[dict]) -> str:
    counts = {v: sum(f["verdict"] == v for f in findings) for v in VERDICTS}
    lines = [
        "## Knowledge audit",
        "",
        "Report only: nothing was changed and no `verified` entry was written.",
        "",
        ", ".join(f"{counts[v]} {v}" for v in VERDICTS) + ".",
        "",
        "| Concept | Verdict | Summary | Evidence |",
        "|---|---|---|---|",
    ]
    for f in sorted(findings, key=lambda f: VERDICTS.index(f["verdict"])):
        evidence = ", ".join(f"`{e}`" for e in f["evidence"])
        lines.append(
            f"| `{_cell(f['concept'])}` | {f['verdict']} | {_cell(f['summary'])} | {_cell(evidence)} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    output, summary_out, body_out = (Path(a) for a in sys.argv[1:4])
    try:
        findings = _findings(output.read_text())
    except (ValueError, TypeError) as err:
        print(f"kmctl audit: no usable findings: {err}", file=sys.stderr)
        return 1
    report = _report(findings)
    with summary_out.open("a") as summary:
        summary.write(report)
    body_out.write_text(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
