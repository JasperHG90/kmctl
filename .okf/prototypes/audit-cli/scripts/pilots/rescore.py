"""Run the checks a pilot saved again with the current step runner, with no model, and update their status.

Run from the audit-cli folder after a runner fix: uv run python scripts/pilots/rescore.py results/pilots/X.json ...
"""

import json
import pathlib as plb
import sys
from collections import Counter

from pydantic import TypeAdapter

from audit_cli.checks.steps import Repository, Step, run_check

sys.path.insert(0, str(plb.Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path

STEPS = TypeAdapter(list[Step])


def main() -> None:
    """Rescore each named results file in place and print its statuses before and after."""
    repo = Repository(common.REPO)
    for name in sys.argv[1:]:
        path = plb.Path(name)
        data = json.loads(path.read_text())
        claims = data.get("claims", data)
        before = Counter(e["status"] for e in claims.values())
        for entry in claims.values():
            if "check" in entry:
                holds, results = run_check(repo, STEPS.validate_python(entry["check"]["steps"]))
                entry["status"] = "holds" if holds else "fails"
                entry["results"] = [r.model_dump() for r in results]
        after = Counter(e["status"] for e in claims.values())
        if "summary" in data:
            data["summary"]["status"] = dict(after)
        path.write_text(json.dumps(data, indent=1))
        print(path.name, dict(before), "->", dict(after))


if __name__ == "__main__":
    main()
