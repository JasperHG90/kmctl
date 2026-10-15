#!/usr/bin/env python3
"""Make github.com unresolvable for git only, then check kmctl's install error and
pytest's failure report both name the network error. Runs in the spike worktree."""
import os, re, subprocess, sys, tempfile
from pathlib import Path

WT = Path.cwd()
PATTERNS = ["could not resolve host", "resolve", "connection", "timed out", "name resolution"]

def found(text):
    low = text.lower()
    return [p for p in PATTERNS if p in low]

# Venv for this worktree, built with the normal environment.
subprocess.run(["uv", "sync", "--frozen", "-q"], cwd=WT, check=True)
py = str(WT / ".venv/bin/python")

scratch = Path(tempfile.mkdtemp(prefix="spike-ntr-"))
gitcfg = scratch / "gitconfig"
gitcfg.write_text('[url "https://unresolvable.invalid/"]\n\tinsteadOf = https://github.com/\n'
                  '[url "https://unresolvable.invalid/"]\n\tinsteadOf = git@github.com:\n')

def env_for(tag):
    e = dict(os.environ)
    e["HOME"] = str(scratch / tag / "home")
    e["CLAUDE_CONFIG_DIR"] = str(scratch / tag / "claude-config")
    e["XDG_DATA_HOME"] = str(scratch / tag / "data")
    e["GIT_CONFIG_GLOBAL"] = str(gitcfg)
    Path(e["HOME"]).mkdir(parents=True)
    return e

def repo(tag):
    p = scratch / tag / "proj"
    p.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=p, check=True)
    return p

def show(title, text):
    print(f"===== {title} =====\n{text.rstrip()}\n")

# 1. claude raw
e = env_for("raw"); p = repo("raw")
r = subprocess.run(["claude", "plugin", "marketplace", "add", "scaccogatto/okf-skills", "--scope", "project"],
                   cwd=p, env=e, capture_output=True, text=True, timeout=180)
show(f"claude marketplace add exit={r.returncode} STDOUT", r.stdout)
show("claude marketplace add STDERR", r.stderr)
detail = (r.stderr or r.stdout).strip().splitlines()
show("what _require keeps (last line)", detail[-1] if detail else "no output")

# 2. kmctl CLI
e = env_for("cli"); p = repo("cli")
k = subprocess.run([str(WT / ".venv/bin/kmctl"), "plugin", "install", "--scope", "project"],
                   cwd=p, env=e, capture_output=True, text=True, timeout=300)
kmsg = k.stdout + k.stderr
show(f"kmctl plugin install exit={k.returncode} OUTPUT", kmsg)

# 3. pytest, with the install in test_update_after_bump asserted (scratch worktree only)
tf = WT / "tests/test_plugin_install.py"
src = tf.read_text()
old = ('def test_update_after_bump(isolated: Path, monkeypatch: pytest.MonkeyPatch) -> None:\n'
       '    _kmctl("plugin", "install", "--scope", "project")\n')
new = ('def test_update_after_bump(isolated: Path, monkeypatch: pytest.MonkeyPatch) -> None:\n'
       '    result = _kmctl("plugin", "install", "--scope", "project")\n'
       '    assert result.exit_code == 0, result.output\n')
assert old in src, "test_update_after_bump install line not found"
tf.write_text(src.replace(old, new))
reports = {}
for test in ["test_install_pulls_okf", "test_update_after_bump"]:
    e = env_for("pt-" + test)
    t = subprocess.run([py, "-m", "pytest", "-x", "-p", "no:cacheprovider", "-o", "addopts=",
                        f"tests/test_plugin_install.py::{test}"],
                       cwd=WT, env=e, capture_output=True, text=True, timeout=300)
    reports[test] = (t.returncode, t.stdout + t.stderr)
    show(f"pytest {test} exit={t.returncode}", t.stdout + t.stderr)

# Verdict
print("===== VERDICT =====")
ok = True
print(f"raw claude stderr: {found(r.stderr)}; raw stdout: {found(r.stdout)}")
print(f"kmctl message (exit {k.returncode}): {found(kmsg)}")
ok &= k.returncode != 0 and bool(found(kmsg))
for test, (rc, out) in reports.items():
    fail = re.search(r"(?s)=+ FAILURES =+(.*)", out)
    fr = fail.group(1) if fail else ""
    print(f"pytest {test} (exit {rc}) failure report: {found(fr)}")
    ok &= rc != 0 and bool(found(fr))
print("PASS: network error reaches both" if ok else "FAIL: network error missing somewhere")
sys.exit(0 if ok else 1)
