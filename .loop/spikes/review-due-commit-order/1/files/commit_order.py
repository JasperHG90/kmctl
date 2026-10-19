"""Spike: does the commit-order rule for review due give the expected answers, and how fast is it?

Rule under test (plan review-due-commit-order):
  V = oldest commit in the file's history whose front matter holds the file's
      current (working tree) newest verified[].at. No V (entry not committed) -> no reason.
  source changed           when git diff V HEAD -- SOURCE is non-empty
                           (docs page without verified: V = page's last commit)
  edited after verification when file at V and at HEAD differ outside verified/stale_after

Run with uv run python from a worktree of kmctl: it runs that checkout's kmctl.
Exits 0 only when every case matches and the batched worst-case walk plus diffs\ntake <= LIMIT seconds on this repo.
"""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

WT = Path.cwd()
sys.path.insert(0, str(WT / "src"))
from kmctl.okf import as_datetime  # noqa: E402

KM = [sys.executable, "-c", "import sys; sys.argv[0] = 'kmctl'; from kmctl import main; main()"]
LIMIT = 0.28  # half the 0.56 s baseline
FAIL = []


def sh(cwd, *args, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"{args} failed in {cwd}: {p.stdout}{p.stderr}")
    return p.stdout


def git(cwd, *args, check=True):
    return sh(cwd, "git", *args, check=check)


def split(text):
    if not text.startswith("---\n"):
        return {}, text
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end]) or {}, text[end + 5 :]


def ats(meta):
    v = meta.get("verified") or []
    if isinstance(v, dict):
        v = [v]
    out = [as_datetime(e.get("at")) for e in v if isinstance(e, dict)]
    return [d for d in out if d is not None]


def show_many(cwd, specs):
    """Contents of each REV:PATH in one git cat-file --batch call."""
    if not specs:
        return []
    p = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=cwd,
        input="\n".join(specs).encode() + b"\n",
        capture_output=True,
        check=True,
    )
    data, out, i = p.stdout, [], 0
    for _ in specs:
        nl = data.index(b"\n", i)
        header = data[i:nl].split()
        if header[-1] == b"missing":
            out.append(None)
            i = nl + 1
            continue
        size = int(header[2])
        out.append(data[nl + 1 : nl + 1 + size].decode())
        i = nl + 1 + size + 1
    return out


def verification_commit(cwd, rel):
    """(V, head_text) per the rule, V None when the newest entry is not committed."""
    head = show_many(cwd, [f"HEAD:{rel}"])[0]
    if head is None:
        return None, None
    found = ats(split((Path(cwd) / rel).read_text())[0])  # the current (working tree) newest
    if not found:
        return None, head
    newest = max(found)
    commits = git(cwd, "log", "--format=%H", "--", rel).split()
    texts = show_many(cwd, [f"{c}:{rel}" for c in commits])
    holding = [c for c, t in zip(commits, texts) if t and newest in ats(split(t)[0])]
    return (holding[-1] if holding else None), head  # git log is newest first


def strip(text):
    meta, body = split(text)
    meta = {k: v for k, v in meta.items() if k not in ("verified", "stale_after")}
    return meta, body


def reasons(cwd, rel, sources):
    v, head = verification_commit(cwd, rel)
    out = []
    if v is None:
        if head is not None and not ats(split(head)[0]) and rel.startswith("docs/"):
            v = git(cwd, "log", "-1", "--format=%H", "--", rel).strip()
            for s in sources:
                if git(cwd, "diff", "--name-only", v, "HEAD", "--", s).strip():
                    out.append(f"source changed: {s}")
        return out
    for s in sources:
        if git(cwd, "diff", "--name-only", v, "HEAD", "--", s).strip():
            out.append(f"source changed: {s}")
    if strip(show_many(cwd, [f"{v}:{rel}"])[0]) != strip(head):
        out.append("edited after verification")
    return out


def check(name, got, want):
    ok = got == want
    print(f"{'ok  ' if ok else 'FAIL'} {name}: got {got}, want {want}")
    if not ok:
        FAIL.append(name)


def commit(cwd, msg):
    git(cwd, "add", "-A")
    git(cwd, "commit", "-qm", msg)


def new_repo():
    d = Path(tempfile.mkdtemp())
    git(d, "init", "-q", "-b", "main")
    git(d, "config", "user.email", "t@example.com")
    git(d, "config", "user.name", "t")
    sh(d, *KM, "init")
    return d


DEC = ".okf/decisions/0002-use-app.md"
DID = "decisions/0002-use-app"


def verify(d, cid, *extra):
    sh(d, *KM, "verify", cid, "--by", "human:tester", *extra)
    time.sleep(1.1)  # verified at has second resolution


def issue17(how):
    d = new_repo()
    (d / "app.py").write_text("print(1)\n")
    commit(d, "init")
    git(d, "switch", "-qc", "feature")
    sh(d, *KM, "new", "decision", "Use app", "--description", "One sentence.", "--source", "app.py")
    (d / "app.py").write_text("print(2)\n")
    commit(d, "change source")
    verify(d, DID)
    commit(d, "verify")
    git(d, "switch", "-q", "main")
    (d / "other.txt").write_text("main moved on\n")
    commit(d, "main moves")  # so rebase and squash write new commits
    time.sleep(1.1)
    if how == "squash":
        git(d, "merge", "-q", "--squash", "feature")
        commit(d, "squash merge")
    elif how == "rebase":
        git(d, "switch", "-q", "feature")
        git(d, "rebase", "-q", "main")
        git(d, "switch", "-q", "main")
        git(d, "merge", "-q", "--ff-only", "feature")
    else:
        git(d, "merge", "-q", "--no-ff", "-m", "merge feature", "feature")
    return d


def after_landing(d, how):
    landed = git(d, "rev-parse", "HEAD").strip()
    src = ["app.py"]
    check(f"{how}: landed, nothing after verify", reasons(d, DEC, src), [])

    def reset():
        git(d, "reset", "-q", "--hard", landed)

    (d / "app.py").write_text("print(3)\n")
    commit(d, "source after")
    check(f"{how}: source commit after", reasons(d, DEC, src), ["source changed: app.py"])
    reset()
    with open(d / DEC, "a") as f:
        f.write("\nEdited after verification.\n")
    commit(d, "body edit")
    check(f"{how}: body edit after", reasons(d, DEC, src), ["edited after verification"])
    reset()
    t = (d / DEC).read_text().replace('description: "One sentence."', 'description: "Two sentences."', 1)
    assert t != (d / DEC).read_text(), "description line not found"
    (d / DEC).write_text(t)
    commit(d, "fm edit")
    check(f"{how}: other front matter edit", reasons(d, DEC, src), ["edited after verification"])
    reset()
    verify(d, DID)
    commit(d, "reverify")
    check(f"{how}: re-verify only", reasons(d, DEC, src), [])
    reset()
    verify(d, DID, "--stale-after", "6m")
    commit(d, "reverify stale")
    check(f"{how}: re-verify with --stale-after", reasons(d, DEC, src), [])
    reset()
    # source changed then re-verified in a later commit: covered
    (d / "app.py").write_text("print(4)\n")
    commit(d, "source")
    verify(d, DID)
    commit(d, "verify again")
    check(f"{how}: source change then re-verify", reasons(d, DEC, src), [])
    reset()
    # uncommitted verify after a committed source change: nothing counts (plan)
    (d / "app.py").write_text("print(5)\n")
    commit(d, "source")
    verify(d, DID)
    check(f"{how}: uncommitted re-verify, nothing counts", reasons(d, DEC, src), [])


def issue18():
    d = new_repo()
    sh(d, *KM, "new", "decision", "Use cache", "--description", "One sentence.")
    commit(d, "add decision")
    verify(d, "decisions/0002-use-cache")
    commit(d, "verify")
    rel = ".okf/decisions/0002-use-cache.md"
    check("issue18: verified, untouched", reasons(d, rel, []), [])
    with open(d / rel, "a") as f:
        f.write("Edited after verification.\n")
    commit(d, "edit")
    check("issue18: appended line", reasons(d, rel, []), ["edited after verification"])


def uncommitted_first():
    d = new_repo()
    (d / "app.py").write_text("print(1)\n")
    commit(d, "init")
    sh(d, *KM, "new", "decision", "Use app", "--description", "One sentence.", "--source", "app.py")
    commit(d, "decision")
    verify(d, DID)
    check("never-committed verify: nothing counts", reasons(d, DEC, ["app.py"]), [])


def docs_page():
    d = new_repo()
    (d / "app.py").write_text("print(1)\n")
    commit(d, "init")
    sh(d, *KM, "new", "doc", "reference", "App ref", "--description", "x")
    rel = "docs/reference/app-ref.md"
    (d / rel).write_text((d / rel).read_text().replace("sources: []", "sources:\n- resource: app.py", 1))
    commit(d, "page")
    check("docs unverified: nothing after page", reasons(d, rel, ["app.py"]), [])
    base = git(d, "rev-parse", "HEAD").strip()
    (d / "app.py").write_text("print(2)\n")
    commit(d, "src")
    check("docs unverified: source after page", reasons(d, rel, ["app.py"]), ["source changed: app.py"])
    git(d, "reset", "-q", "--hard", base)
    verify(d, "docs/reference/app-ref")
    commit(d, "verify page")
    landed = git(d, "rev-parse", "HEAD").strip()
    check("docs verified: nothing after", reasons(d, rel, ["app.py"]), [])
    (d / "app.py").write_text("print(3)\n")
    commit(d, "src")
    check("docs verified: source after", reasons(d, rel, ["app.py"]), ["source changed: app.py"])
    git(d, "reset", "-q", "--hard", landed)
    with open(d / rel, "a") as f:
        f.write("More.\n")
    commit(d, "edit page")
    check("docs verified: body edit", reasons(d, rel, ["app.py"]), ["edited after verification"])
    git(d, "reset", "-q", "--hard", landed)
    verify(d, "docs/reference/app-ref", "--stale-after", "6m")
    commit(d, "reverify")
    check("docs verified: re-verify only", reasons(d, rel, ["app.py"]), [])


def parse_versions(texts):
    for t in texts:  # parse every version, as the rule must when no version holds the entry
        if t:
            ats(split(t)[0])


def timing():
    """Worst case on this repo: every concept and docs page walks its whole history.

    Two designs: (a) one git log per file, as a first cut would; (b) one git log
    for all files plus one cat-file batch. The limit applies to (b).
    """
    files = [
        p.relative_to(WT).as_posix()
        for base in ("docs", ".okf")
        for p in sorted((WT / base).rglob("*.md"))
        if p.name not in ("README.md", "index.md", "log.md")
        and "/handoffs/" not in p.as_posix()
        and not p.as_posix().endswith(".okf/summary.md")
    ]
    t0 = time.perf_counter()
    walked = 0
    for rel in files:
        commits = git(WT, "log", "--format=%H", "--", rel).split()
        walked += len(commits)
        parse_versions(show_many(WT, [f"{c}:{rel}" for c in commits]))
    per_file = time.perf_counter() - t0

    t0 = time.perf_counter()
    history, current = {}, None
    for line in git(WT, "log", "--format=@%H", "--name-only", "--", *files).splitlines():
        if line.startswith("@"):
            current = line[1:]
        elif line:
            history.setdefault(line, []).append(current)
    specs = [f"{c}:{rel}" for rel in files for c in history.get(rel, [])]
    texts = show_many(WT, specs)
    parse_versions(texts)
    batched = time.perf_counter() - t0

    t0 = time.perf_counter()
    for rel in files:  # one git diff per source, V = the file's first commit
        meta = split((WT / rel).read_text())[0]
        v = history.get(rel, ["HEAD"])[-1]
        for src in meta.get("sources") or []:
            r = src.get("resource") if isinstance(src, dict) else src
            if isinstance(r, str) and "://" not in r:
                git(WT, "diff", "--quiet", v, "HEAD", "--", r.lstrip("/"), check=False)
    diffs = time.perf_counter() - t0

    verified = [rel for rel in files if ats(split((WT / rel).read_text())[0])]
    t0 = time.perf_counter()
    for rel in verified:
        verification_commit(WT, rel)
    real = time.perf_counter() - t0

    t0 = time.perf_counter()
    sh(WT, *KM, "review", "due", check=False)
    base = time.perf_counter() - t0
    commits_total = git(WT, "rev-list", "--count", "HEAD").strip()
    print(
        f"timing: repo {commits_total} commits, {len(files)} concepts and docs pages, {walked} file versions; "
        f"kmctl review due now {base:.3f} s\n"
        f"  (a) per-file git log, whole history parsed: {per_file:.3f} s\n"
        f"  (b) one git log + one cat-file batch, whole history parsed: {batched:.3f} s ({len(specs)} versions)\n"
        f"  per-source git diff for all sources: {diffs:.3f} s\n"
        f"  real walk today ({len(verified)} verified: {verified}): {real:.3f} s"
    )
    if batched + diffs > LIMIT:
        FAIL.append(f"batched walk + diffs {batched + diffs:.3f} s > {LIMIT} s")


for how in ("squash", "rebase", "merge"):
    after_landing(issue17(how), how)
issue18()
uncommitted_first()
docs_page()
timing()
print("FAILED:", FAIL if FAIL else "none")
sys.exit(1 if FAIL else 0)
