"""Read back what recent DeepSeek calls spent from their LangSmith traces: free, no model calls.

Run from the audit-cli folder, with the shell's keys loaded:

    uv run python scripts/pilots/from_traces.py MINUTES [--name NAME]

Lists the LLM runs of the last MINUTES in the project the settings name (LANGSMITH_PROJECT, else kmctl-local),
grouped by trace: per trace the calls, input, output and cached input tokens, and the tool calls the model asked
for. Used when a pilot stopped before saving its own numbers. Writes results/pilots/from-traces.json.
"""

import argparse
import datetime as dt
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any

from langsmith import Client

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path


def usage(run: Any) -> tuple[int, int, int]:
    """Return a traced LLM run's input, output and cached input tokens."""
    outputs = run.outputs or {}
    for generation in (outputs.get("generations") or [[]])[0]:
        meta = (generation.get("message") or {}).get("kwargs", {}).get("usage_metadata") or {}
        if meta:
            cached = (meta.get("input_token_details") or {}).get("cache_read") or 0
            return meta.get("input_tokens", 0), meta.get("output_tokens", 0), cached
    return run.prompt_tokens or 0, run.completion_tokens or 0, 0


def calls(run: Any) -> list[dict[str, Any]]:
    """Return the tool calls a traced reply made, with their arguments."""
    outputs = run.outputs or {}
    found: list[dict[str, Any]] = []
    for generation in (outputs.get("generations") or [[]])[0]:
        found += (generation.get("message") or {}).get("kwargs", {}).get("tool_calls") or []
    return found


def main() -> None:
    """Print and save the spend of the recent traces."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("minutes", type=int)
    parser.add_argument("--out", default="from-traces", help="Results file name, without .json.")
    parser.add_argument("--run-type", default="llm", help="llm (model calls) or chain (the CLI's own spans).")
    args = parser.parse_args()
    common.settings()
    project = os.environ.get("LANGSMITH_PROJECT", "kmctl-local")
    since = dt.datetime.now(dt.UTC) - dt.timedelta(minutes=args.minutes)
    runs = list(Client().list_runs(project_name=project, run_type=args.run_type, start_time=since))
    by_trace: dict[str, list[Any]] = defaultdict(list)
    for run in runs:
        by_trace[str(run.trace_id)].append(run)
    out = []
    for trace, items in by_trace.items():
        items.sort(key=lambda r: r.start_time)
        spent = [usage(r) for r in items]
        out.append(
            {
                "trace": trace,
                "start": items[0].start_time.isoformat(),
                "calls": len(items),
                "in": sum(s[0] for s in spent),
                "out": sum(s[1] for s in spent),
                "cached": sum(s[2] for s in spent),
                "in_per_call": [s[0] for s in spent],
                "cached_per_call": [s[2] for s in spent],
                "tools": dict(Counter(c.get("name", "?") for r in items for c in calls(r))),
                "submits": [c.get("args") for r in items for c in calls(r) if c.get("name") == "Submit"],
                "asked": [f"{c.get('name')} {json.dumps(c.get('args'))[:300]}" for r in items for c in calls(r)],
            }
        )
    out.sort(key=lambda t: t["start"])
    (common.OUT / f"{args.out}.json").write_text(json.dumps(out, indent=1))
    print(f"{len(out)} traces, {sum(t['calls'] for t in out)} calls")


if __name__ == "__main__":
    main()
