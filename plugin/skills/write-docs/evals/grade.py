"""Grade write-docs runs: page in its type folder, listed in docs/README.md, kmctl check passes, no stray pages.

Usage: python grade.py ITERATION_DIR, with ITERATION_DIR/<eval-name>/<config>/repo as skill-creator lays
out runs. kmctl must be on PATH, or set KMCTL_BIN to the folder holding it. Writes grading.json per run.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ITER = Path(sys.argv[1])
BIN = Path(os.environ.get("KMCTL_BIN", "")) if os.environ.get("KMCTL_BIN") else None
FOLDER = {
    "tutorial-getting-started": "tutorials",
    "howto-supersede": "how-to",
    "reference-commands": "reference",
    "explanation-one-hook": "explanation",
}
TYPE_FOLDERS = {"tutorials", "how-to", "reference", "explanation"}

for eval_dir in sorted(p for p in ITER.iterdir() if p.is_dir()):
    want = FOLDER[eval_dir.name]
    for run in sorted(p for p in eval_dir.iterdir() if p.is_dir()):
        repo = run / "repo"
        docs = repo / "docs"
        pages = [p for p in docs.rglob("*.md") if p.name != "README.md"]
        in_type = [p for p in pages if p.relative_to(docs).parts[0] == want]
        stray = [p for p in pages if p.relative_to(docs).parts[0] not in TYPE_FOLDERS]
        index = (
            (docs / "README.md").read_text() if (docs / "README.md").exists() else ""
        )
        listed = [p for p in in_type if f"({p.relative_to(docs).as_posix()})" in index]
        env = os.environ | ({"PATH": f"{BIN}:{os.environ['PATH']}"} if BIN else {})
        check = subprocess.run(
            ["kmctl", "check"],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        expectations = [
            {
                "text": f"A page is created under docs/{want}/",
                "passed": bool(in_type),
                "evidence": ", ".join(str(p.relative_to(repo)) for p in pages)
                or "no pages",
            },
            {
                "text": "The page is listed in docs/README.md",
                "passed": bool(listed),
                "evidence": index.strip().splitlines()[-1]
                if index.strip()
                else "empty index",
            },
            {
                "text": "kmctl check passes afterwards",
                "passed": check.returncode == 0,
                "evidence": (check.stdout.strip().splitlines() or [""])[-1],
            },
            {
                "text": "No page sits outside a Diataxis type folder",
                "passed": not stray,
                "evidence": ", ".join(str(p.relative_to(repo)) for p in stray)
                or "none",
            },
        ]
        passed = sum(e["passed"] for e in expectations)
        grading = {
            "expectations": expectations,
            "summary": {
                "passed": passed,
                "failed": len(expectations) - passed,
                "total": len(expectations),
                "pass_rate": passed / len(expectations),
            },
        }
        (run / "grading.json").write_text(json.dumps(grading, indent=2))
        print(eval_dir.name, run.name, f"{passed}/{len(expectations)}")
