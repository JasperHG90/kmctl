"""Spike: which apm.yml forms of the adversarial-reviewer agent does APM 0.33.0 accept?

Exit 0 only when the pinned shorthand form (A) installs the agent for claude.
"""
import os, subprocess, sys, tempfile
from pathlib import Path

SHA = "09b7a0a844b86be4e9ba0973f6b1176defd83ce7"
FORMS = {
    "A pinned shorthand": f"    - jasperhg90/skills/agents/adversarial-reviewer.md#{SHA}",
    "B unpinned shorthand (README form)": "    - jasperhg90/skills/agents/adversarial-reviewer.md",
    "C git object with path and ref": f"    - git: https://github.com/jasperhg90/skills.git\n      path: agents/adversarial-reviewer.md\n      ref: {SHA}",
    "D control: pinned single-file rule": f"    - jasperhg90/skills/rules/adversarial-reviews.instructions.md#{SHA}",
}
env = {k: v for k, v in os.environ.items()
       if k not in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_APM_PAT", "GITHUB_COPILOT_PAT", "VIRTUAL_ENV")}
env["GIT_TERMINAL_PROMPT"] = "0"
root = Path(tempfile.mkdtemp(prefix="spike-forms-"))
accepted = {}
for i, (label, dep) in enumerate(FORMS.items()):
    d = root / str(i); d.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=d)
    (d / "apm.yml").write_text(f"name: demo\nversion: 0.1.0\ndependencies:\n  apm:\n{dep}\ntargets:\n  - claude\n")
    p = subprocess.run(["uvx", "--from", "apm-cli==0.33.0", "apm", "install"], cwd=d, env=env,
                       capture_output=True, text=True)
    out = p.stdout + p.stderr
    landed = sorted(str(f.relative_to(d)) for f in d.rglob("adversarial*") if "apm_modules" not in f.parts)
    print(f"\n== {label}: apm install exit {p.returncode}; landed: {landed}")
    for l in out.splitlines():
        if any(w in l.lower() for w in ("[x]", "[!]", "invalid", "error", "warn", "skip", "must end")):
            print("   ", l[:300])
    accepted[label] = p.returncode == 0 and bool(landed)
print("\naccepted:", accepted)
sys.exit(0 if accepted["A pinned shorthand"] else 1)
