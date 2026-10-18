"""Spike: does a pinned single-file agent dep install cleanly per harness set in a starter project?

Exit 0 only when every harness set installs the agent with apm install, plugin patch,
kmctl init and doctor showing no failure beyond the unpassable ones.
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path("/home/vscode/kmctl")
AGENT = "jasperhg90/skills/agents/adversarial-reviewer.md#09b7a0a844b86be4e9ba0973f6b1176defd83ce7"
UNPASSABLE = {"dep.claude", "dep.agy", "dep.opencode", "antigravity.trust"}
SETS = ["[claude]", "[opencode]", "[antigravity]", "[claude, antigravity, opencode]"]
KMCTL_GIT = "https://github.com/JasperHG90/kmctl.git"

root = Path(tempfile.mkdtemp(prefix="spike-reviewer-"))
bare = root / "srv" / "kmctl.git"
subprocess.run(["git", "clone", "-q", "--bare", str(SRC), str(bare)], check=True)
gitconfig = root / "gitconfig"
gitconfig.write_text(
    f'[url "file://{bare}"]\n\tinsteadOf = {KMCTL_GIT}\n\tinsteadOf = {KMCTL_GIT.removesuffix(".git")}\n'
    "[user]\n\temail = t@e.invalid\n\tname = t\n"
)
copier_py = subprocess.run(
    ["uv", "run", "--project", str(SRC), "python", "-c", "import sys; print(sys.executable)"],
    capture_output=True, text=True, check=True).stdout.strip()

def run(cmd, cwd, env):
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr

all_ok = True
for hs in SETS:
    name = hs.strip("[]").replace(", ", "+")
    case = root / name
    home = case / "home"; (home / ".claude").mkdir(parents=True)
    tools = case / "tools"; tools.mkdir()
    for t in ("uv", "uvx", "just"):
        (tools / t).symlink_to(shutil.which(t))
    env = {k: v for k, v in os.environ.items()
           if k not in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_APM_PAT", "GITHUB_COPILOT_PAT", "VIRTUAL_ENV")}
    env.update(HOME=str(home), CLAUDE_CONFIG_DIR=str(home / ".claude"),
               XDG_DATA_HOME=str(home / ".local/share"),
               PATH=f"{home}/.local/bin:{tools}:/usr/bin:/bin",
               GIT_CONFIG_GLOBAL=str(gitconfig), GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0",
               UV_CACHE_DIR=os.environ.get("UV_CACHE_DIR", str(Path.home() / ".cache/uv")))
    proj = case / "demo"
    print(f"\n===== harnesses={hs} =====", flush=True)
    rc, out = run([copier_py, "-m", "copier", "copy", "--defaults", "--vcs-ref", "HEAD",
                   "-d", "project_name=demo", "-d", "codeowners=@octocat", "-d", f"harnesses={hs}",
                   "git+file://" + str(SRC), str(proj)], root, env)
    print("copier exit", rc)
    if rc:
        print(out[-2000:]); all_ok = False; continue
    apm = proj / "apm.yml"
    text = apm.read_text().replace("targets:", f"    - {AGENT}\ntargets:", 1)
    apm.write_text(text)
    run(["git", "init", "-q"], proj, env)
    rc, out = run(["just", "bootstrap"], proj, env)
    print("just bootstrap exit", rc)
    lines = [l for l in out.splitlines() if "adversarial" in l.lower() or "warn" in l.lower()
             or "error" in l.lower() or "skip" in l.lower()]
    print("bootstrap lines mentioning adversarial/warn/error/skip:")
    for l in lines: print("   ", l[:300])
    if rc:
        print("bootstrap tail:\n" + out[-3000:]); all_ok = False
    found = sorted(str(p.relative_to(proj)) for p in proj.rglob("adversarial-reviewer*"))
    print("adversarial-reviewer files:", found)
    deployed = [f for f in found if not f.startswith("apm_modules")]
    lock = proj / "apm.lock.yaml"
    if lock.exists():
        lt = lock.read_text()
        i = lt.find("adversarial-reviewer")
        print("lock entry:", lt[max(0, i-400):i+400] if i >= 0 else "MISSING")
    rc_check, out_check = run(["kmctl", "check"], proj, env)
    print("kmctl check exit", rc_check)
    if rc_check: print(out_check[-1500:])
    rc_d, out_d = run(["kmctl", "doctor", "--json"], proj, env)
    print("kmctl doctor exit", rc_d)
    try:
        rep = json.loads(out_d[: out_d.rfind("}") + 1])
        failed = {c["id"] for c in rep["checks"] if not c["ok"]}
        other = failed - UNPASSABLE
        print("doctor failing:", sorted(failed), "| beyond unpassable:", sorted(other))
        for c in rep["checks"]:
            if c["id"] in other: print("   ", json.dumps(c)[:500])
    except Exception as e:
        print("doctor output unparsed:", e, out_d[-1500:]); other = {"unparsed"}
    # No failure anywhere; with claude in the set the agent must also land (shows the pinned ref is accepted).
    ok = rc == 0 and rc_check == 0 and not other and (bool(deployed) or "claude" not in hs)
    print(f"RESULT {hs}: {'OK' if ok else 'FAIL'} (agent deployed to: {deployed or 'nowhere'})")
    all_ok &= ok
print("\nALL OK" if all_ok else "\nNOT ALL OK")
sys.exit(0 if all_ok else 1)
