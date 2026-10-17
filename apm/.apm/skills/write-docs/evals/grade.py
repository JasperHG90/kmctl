"""Grade write-docs runs: page in its type folder, listed in its folder's README.md, kmctl check passes, no stray pages.

Usage: python grade.py ITERATION_DIR, with ITERATION_DIR/<any-name>/<config>/repo as skill-creator lays
out runs; each eval folder's eval_metadata.json names its eval_id in evals.json. kmctl must be on PATH, or set KMCTL_BIN to the folder holding it. Writes grading.json per run.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ITER = Path(sys.argv[1])
BIN = Path(os.environ.get("KMCTL_BIN", "")) if os.environ.get("KMCTL_BIN") else None
EVALS = {
    e["id"]: e
    for e in json.loads((Path(__file__).parent / "evals.json").read_text())["evals"]
}
TYPE_FOLDER = {
    "tutorial": "tutorials",
    "how-to": "how-to",
    "reference": "reference",
    "explanation": "explanation",
}
TYPE_FOLDERS = {"tutorials", "how-to", "reference", "explanation"}

for eval_dir in sorted(p for p in ITER.iterdir() if p.is_dir()):
    meta_path = eval_dir / "eval_metadata.json"
    if not meta_path.is_file():
        print(eval_dir.name, "skipped: no eval_metadata.json")
        continue
    meta = json.loads(meta_path.read_text())
    spec = EVALS.get(meta.get("eval_id"))
    if spec is None or meta.get("prompt", spec["prompt"]) != spec["prompt"]:
        print(
            eval_dir.name,
            f"skipped: eval_id {meta.get('eval_id')} or its prompt does not match evals.json",
        )
        continue
    want = TYPE_FOLDER[spec["doc_type"]]
    for run in sorted(p for p in eval_dir.iterdir() if p.is_dir()):
        repo = run / "repo"
        docs = repo / "docs"
        pages = [p for p in docs.rglob("*.md") if p.name != "README.md"]
        in_type = [p for p in pages if p.relative_to(docs).parts[0] == want]
        stray = [p for p in pages if p.relative_to(docs).parts[0] not in TYPE_FOLDERS]
        folder_index = docs / want / "README.md"
        index = folder_index.read_text() if folder_index.exists() else ""
        listed = [
            p for p in in_type if f"({p.relative_to(docs / want).as_posix()})" in index
        ]
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
                "text": "The page is listed in its folder's README.md index",
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
