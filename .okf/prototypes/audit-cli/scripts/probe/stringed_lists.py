"""Find model answers that sent a list as a quoted string, from LangSmith traces, and test whether they would parse.

Run from the audit-cli folder; the folder's .env holds the LangSmith settings:

    uv run python scripts/probe/stringed_lists.py MINUTES

Reads the LLM runs of the last MINUTES in the most recently active LangSmith project, keeps each tool call whose
``sentences`` or ``answers`` argument is a string, and checks that the string is complete JSON that the extractor's
``Verdicts`` model accepts. Writes the raw answers to results/probe/stringed-lists.json (git-ignored folder data).
"""

import argparse
import datetime as dt
import json
import pathlib as plb
from typing import Any

from dotenv import load_dotenv
from langsmith import Client
from pydantic import ValidationError

from audit_cli.claims.models import Verdicts

HERE = plb.Path(__file__).resolve().parents[2]
OUT = HERE / "results" / "probe" / "stringed-lists.json"


def tool_calls(run: Any) -> list[dict[str, Any]]:
    """Return the tool calls a traced model reply made, with their arguments."""
    found: list[dict[str, Any]] = []
    for generation in ((run.outputs or {}).get("generations") or [[]])[0]:
        found += (generation.get("message") or {}).get("kwargs", {}).get("tool_calls") or []
    return found


def verdict(text: str) -> str:
    """Say whether a stringed list is complete JSON the extractor's Verdicts model accepts, and if not, why."""
    try:
        items = json.loads(text)
    except json.JSONDecodeError as error:
        return f"not complete JSON: {error.msg} at {error.pos} of {len(text)}"
    try:
        Verdicts.model_validate({"sentences": items})
    except ValidationError as error:
        return f"JSON, but not the right shape: {error.error_count()} errors, first {error.errors()[0]['msg']}"
    return f"parses: {len(items)} sentences"


def main() -> None:
    """Print, per stringed answer, its run, its length and whether it parses; save the raw answers."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("minutes", type=int)
    args = parser.parse_args()
    load_dotenv(HERE / ".env", override=False)
    client = Client()
    since = dt.datetime.now(dt.UTC) - dt.timedelta(minutes=args.minutes)
    project = max(client.list_projects(), key=lambda p: p.last_run_start_time or dt.datetime.min.replace(tzinfo=dt.UTC))
    print(f"project: {project.name}")
    found = []
    for run in client.list_runs(project_id=project.id, run_type="llm", start_time=since):
        for call in tool_calls(run):
            for field in ("sentences", "answers"):
                value = (call.get("args") or {}).get(field)
                if isinstance(value, str):
                    found.append(
                        {"run": str(run.id), "trace": str(run.trace_id), "field": field, "raw": value}
                        | {"verdict": verdict(value) if field == "sentences" else "", "start": str(run.start_time)}
                    )
    for item in found:
        print(
            f"{item['start'][:19]}  {item['field']}  {len(item['raw'])} chars  {item['verdict']}  trace {item['trace']}"
        )
    print(f"{len(found)} stringed answers in {args.minutes} minutes")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(found, indent=2))


if __name__ == "__main__":
    main()
