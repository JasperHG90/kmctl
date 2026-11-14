"""Drive every kmaudit verb with Target.bundle pointing at a plain markdown folder.

Exit 0 when nothing breaks outside the plan's touched files (sections, steps,
cli, store, verbs, check_verbs, ui, coverage); exit 1 when some assumption
lives elsewhere (lines.py, anchors.py, ui.html, check_instructions.py, ...).
"""

import json
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

WS = Path("/home/vscode/workspace")
sys.path.insert(0, str(WS / "packages/kmaudit"))
from tests.fixtures.audit_repo import git, make_repo  # noqa: E402

import kmaudit.check_verbs as check_verbs  # noqa: E402
import kmaudit.coverage as coverage_mod  # noqa: E402
import kmaudit.sections as sections  # noqa: E402
import kmaudit.ui as ui  # noqa: E402
import kmaudit.verbs as verbs  # noqa: E402
from kmaudit.sections import Target  # noqa: E402
from kmaudit.steps import Repository  # noqa: E402

PLAIN = """# Guide

## Retries

The tool stops after `MAX_RETRIES` attempts in `src/tool.py`. The CLI writes out.txt.

## Exit

The CLI exits 1 when given more than one argument.
"""

TOUCHED = {"sections.py", "steps.py", "cli.py", "store.py", "verbs.py",
           "check_verbs.py", "ui.py", "coverage.py", "instructions.py"}
findings: list[tuple[str, str, str]] = []  # (site, what, kind: raise|wrong|ok)


def note(site, what, kind):
    findings.append((site, what, kind))
    print(f"[{kind}] {site}: {what}")


def run(folder: str) -> None:
    print(f"\n===== audited folder: {folder} =====")
    root = make_repo(Path(tempfile.mkdtemp()) / "repo").resolve()
    (root / folder).mkdir(parents=True, exist_ok=True)
    (root / folder / "guide.md").write_text(PLAIN)
    (root / folder / "sub").mkdir(exist_ok=True)
    (root / folder / "sub" / "index.md").write_text("# Sub index\n\nThe CLI writes out.txt.\n")
    git(root, "add", ".")
    git(root, "-c", "user.name=t", "-c", "user.email=t@e", "commit", "-qm", "plain")
    target = Target(bundle=(root / folder).resolve(), files=None, root=root)
    fake = lambda path: target  # noqa: E731
    for mod in (sections, verbs, check_verbs, coverage_mod, ui):
        mod.resolve_target = fake

    def step(name, fn):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            note(name, f"raised {type(e).__name__}: {e}", "raise")
            traceback.print_exc()
            return None

    # 1 cut
    secs = step("sections.cut", lambda: list(sections.cut(target)))
    if secs is not None:
        ids = sorted({s.id for s in secs})
        print("sections:", ids)
        if not any(i.startswith("sub/index") for i in ids):
            note("sections.py:18 SKIP_NAMES", f"{folder}/sub/index.md skipped in a plain folder", "wrong")
        if not any(i.startswith("guide") for i in ids):
            note("sections.cut", "guide.md not cut", "wrong")

    # 2 claims todo / submit
    td = step("verbs.todo", lambda: verbs.todo(root))
    if td is not None:
        print("claims todo concepts:", [(c.concept, c.path) for c in td.concepts])
        answers = []
        for s in td.sections:
            answers.append({"section": s.id, "key": s.key, "sentences": [
                {"n": x.n, "how_to_check": "open", "reason": "r", "kind": "point",
                 "claims": [{"claim": f"{s.id} {x.n}: " + x.text, "quantifier": "exists"}]}
                for x in s.sentences]})
        res = step("verbs.submit", lambda: verbs.submit(root, json.dumps(answers)))
        if res is not None and res.refused:
            note("verbs.submit", f"refused {res.refused}", "wrong")
        lc = step("verbs.list_claims", lambda: verbs.list_claims(root))
        if lc is not None:
            print("list documents:", [d.concept for d in lc.documents or []])

    # 3 checks todo (anchors + lines)
    repo = Repository(root)
    inside = [f for f in repo.files if f.startswith(folder + "/")]
    if inside:
        note("steps.py:59 EXCLUDE_DIRS / Repository", f"checks may read audited files {inside}", "wrong")
    ct = step("check_verbs.todo", lambda: check_verbs.todo(root))
    claim_ids = []
    if ct is not None:
        print("checks todo concepts:", [(c.concept, c.path) for c in ct.concepts])
        for c in ct.claims:
            claim_ids.append(c.id)
            shown = c.lines.files if hasattr(c.lines, "files") else []
            print(f"  {c.id} anchors={[(a.text, a.status) for a in c.anchors]} lines.source={c.lines.source} files={shown}")
            bad = [f for f in shown if f.startswith(folder + "/")]
            if bad:
                note("lines.py LineFinder", f"lines for {c.id} come from audited folder {bad}", "wrong")
        if not ct.claims:
            note("check_verbs.todo", "no checkable claims handed out", "wrong")
        src_lines = [c for c in ct.claims if "src/tool.py" in (c.lines.files or [])]
        print("claims with lines in src/tool.py:", len(src_lines))

    # 4 checks try / submit
    if claim_ids:
        cid = next((i for i in claim_ids), None)
        good = {"claim": cid, "steps": [{"op": "grep", "pattern": "MAX_RETRIES = 3", "paths": "src/tool.py"}],
                "strength": "exact", "why": "w"}
        self_read = {"claim": cid, "steps": [{"op": "grep", "pattern": "MAX_RETRIES", "paths": f"{folder}/guide.md"}],
                     "strength": "exact", "why": "w"}
        tried = step("check_verbs.try_answers", lambda: check_verbs.try_answers(root, json.dumps([good, self_read])))
        if tried is not None:
            for t in tried:
                print("  try:", t.kind, t.holds, [s.detail for s in t.steps][:2])
            if tried[1].holds:
                note("steps.py Repository", f"a check read {folder}/guide.md and held", "wrong")
        sub = step("check_verbs.submit", lambda: check_verbs.submit(root, json.dumps([good])))
        if sub is not None:
            print("  checks submit:", sub.model_dump_json()[:300])

    # 5 coverage
    cov = step("coverage.coverage", lambda: coverage_mod.coverage(root))
    if cov is not None:
        cf = [f.path for f in cov.by_file]
        print("coverage files:", cf, "covered", cov.covered, "/", cov.lines)
        bad = [f for f in cf if f.startswith(folder + "/")]
        if bad:
            note("coverage.code_files (via Repository)", f"audited files counted as code {bad}", "wrong")

    # 6 ui
    view = step("ui.build", lambda: ui.build(root))
    if view is not None:
        print("ui concepts:", [d.concept for d in view.concepts])
        if not any(d.concept == "guide" for d in view.concepts):
            note("ui.build", "page does not list guide", "wrong")
        bad = [f.path for f in view.code.files if f.path.startswith(folder + "/")]
        if bad:
            note("ui.build code view", f"audited files in code view {bad}", "wrong")
    ft = step("ui.file_text(src)", lambda: ui.file_text(root, "src/tool.py"))
    print("file_text src ok:", ft is not None)
    try:
        ui.file_text(root, f"{folder}/guide.md")
        note("ui.file_text", f"serves audited {folder}/guide.md as code", "wrong")
    except Exception as e:  # noqa: BLE001
        print(f"file_text {folder}/guide.md refused: {e}")
    shutil.rmtree(root.parent, ignore_errors=True)


for folder in ("docs", "handbook"):
    run(folder)

# static: page hard-codes the .okf/ prefix for a document's path
html = (WS / "packages/kmaudit/src/kmaudit/ui.html").read_text()
for n, line in enumerate(html.splitlines(), 1):
    if "`.okf/${" in line:
        note(f"ui.html:{n}", "document path shown as .okf/<concept>.md whatever the folder", "wrong")
ci = (WS / "packages/kmaudit/src/kmaudit/check_instructions.py").read_text()
for n, line in enumerate(ci.splitlines(), 1):
    if ".okf/ and docs/" in line:
        note(f"check_instructions.py:{n}", "check prompt says only .okf/ and docs/ are never read", "wrong")

print("\n===== summary =====")
outside = []
for site, what, kind in findings:
    file = site.split(":")[0].split(" ")[0].split(".")[0] + ".py" if not site.startswith("ui.html") else "ui.html"
    if site.startswith(("sections.", "verbs.", "check_verbs.", "coverage.", "ui.build", "ui.file_text", "steps.py", "lines.py")):
        file = {"sections": "sections.py", "verbs": "verbs.py", "check_verbs": "check_verbs.py",
                "coverage": "coverage.py", "ui": "ui.py", "steps": "steps.py", "lines": "lines.py"}[site.split(".")[0].split(":")[0]]
    flag = "in plan" if file in TOUCHED else "OUTSIDE plan"
    if file not in TOUCHED:
        outside.append(site)
    print(f"{kind:6} {flag:12} {site}: {what}")
print("outside plan:", outside)
sys.exit(1 if outside else 0)
