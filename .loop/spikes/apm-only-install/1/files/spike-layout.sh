#!/usr/bin/env bash
# Risk 2 (apm-only-install): with the planned layout -- apm/apm.yml holding only
# the pinned okf-skills dependency (no `git: parent`), skills, agent and
# instructions under apm/.apm/ -- does APM 0.33.0 deliver to a consumer:
#   the 7 kmctl skills byte for byte, the auditor agent byte for byte,
#   the 4 rules in .claude/rules/ with paths: equal to today's and bodies equal,
#   okf's 4 skills;
# both (A) from a consumer apm.yml entry {git, path: apm} and
#      (B) `apm install <package> --target claude` in a git repo with no apm.yml?
# Exit 0 only when A and B both deliver everything.
set -u
KM=$(git rev-parse --show-toplevel)
SCR=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-apm-r2
W=$(mktemp -d "$SCR/run.XXXX")
export UV_CACHE_DIR="${UV_CACHE_DIR:-/home/vscode/.cache/uv}"
export HOME="$W/home"; mkdir -p "$HOME"
git config --global user.email spike@example.invalid
git config --global user.name spike
git config --global init.defaultBranch main
APM() { uvx -q --from apm-cli==0.33.0 apm "$@"; }
PY() { uv run -q --no-project --with pyyaml python -I "$@"; }
OKF=a8b96420de90d102c43cda1693d01ec4f925f2ab
echo "== kmctl HEAD $(git -C "$KM" rev-parse HEAD); $(APM --version 2>&1 | tail -1)"

# 1. Restructured copy of the committed tree.
T="$W/kmctl"; mkdir "$T"; git -C "$KM" archive HEAD | tar -x -C "$T"
mkdir -p "$T/apm/.apm/skills" "$T/apm/.apm/agents" "$T/apm/.apm/instructions"
mv "$T"/plugin/skills/* "$T/apm/.apm/skills/"
mv "$T/plugin/agents/kmctl-auditor.md" "$T/apm/.apm/agents/"
rm -rf "$T/plugin" "$T/.claude-plugin/marketplace.json"
cat > "$W/conv.py" <<'EOF'
import sys, yaml, pathlib
src, dst = map(pathlib.Path, sys.argv[1:3])
for f in sorted(src.glob("*.md")):
    t = f.read_text(); end = t.find("\n---\n", 4)
    paths = yaml.safe_load(t[4:end])["paths"]
    out = '---\napplyTo: "' + ", ".join(paths) + '"\n---\n' + t[end + 5:]
    (dst / f"{f.stem}.instructions.md").write_text(out)
    print("  ", f.stem, "applyTo:", ", ".join(paths))
EOF
PY "$W/conv.py" "$T/src/kmctl/repo_rules" "$T/apm/.apm/instructions" || exit 3
rm -rf "$T/src/kmctl/repo_rules"
printf 'name: kmctl\nversion: 0.3.0\ndescription: spike\ndependencies:\n  apm:\n    - scaccogatto/okf-skills#%s\n' "$OKF" > "$T/apm/apm.yml"
echo "== package tree:"; (cd "$T/apm" && find . -type f | sort | sed 's/^/   /' | grep -v '/evals/')
( cd "$T" && git init -q && git add -A && git commit -qm tree ) || exit 3
mkdir -p "$W/srv/o"; git clone -q --bare "$T" "$W/srv/o/kmctl.git" && git -C "$W/srv/o/kmctl.git" update-server-info

PORT=$(PY -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')
python3 -I "$KM/tests/fixtures/githttp.py" "$W/srv" "$PORT" >/dev/null 2>&1 &
SRV=$!; trap 'kill "$SRV" 2>/dev/null' EXIT; sleep 1
URL="http://127.0.0.1:$PORT/o/kmctl.git"

cat > "$W/check.py" <<'EOF'
import sys, yaml, pathlib, filecmp
km, c = map(pathlib.Path, sys.argv[1:3]); ok = True
def split(t):
    if not t.startswith("---\n"): return None, t.lstrip("\n")
    e = t.find("\n---\n", 4); return yaml.safe_load(t[4:e]) or {}, t[e + 5:].lstrip("\n")
def same_tree(a, b):
    d = filecmp.dircmp(a, b)
    if d.left_only or d.right_only or d.diff_files or d.funny_files: return False
    _, mism, err = filecmp.cmpfiles(a, b, d.common_files, shallow=False)
    return not mism and not err and all(same_tree(a / s, b / s) for s in d.common_dirs)
for s in sorted(p for p in (km / "plugin/skills").iterdir()):
    good = (c / ".claude/skills" / s.name).is_dir() and same_tree(s, c / ".claude/skills" / s.name)
    ok &= good; print(f"   skill {s.name}: {'identical' if good else 'MISSING/DIFFERENT'}")
a = c / ".claude/agents/kmctl-auditor.md"
good = a.is_file() and filecmp.cmp(km / "plugin/agents/kmctl-auditor.md", a, shallow=False)
ok &= good; print(f"   agent kmctl-auditor: {'identical' if good else 'MISSING/DIFFERENT'}")
for r in sorted((km / "src/kmctl/repo_rules").glob("*.md")):
    wfm, wbody = split(r.read_text()); g = c / ".claude/rules" / r.name
    if not g.is_file(): ok = False; print(f"   rule {r.stem}: MISSING"); continue
    gfm, gbody = split(g.read_text())
    pg = (gfm or {}).get("paths"); bg = gbody == wbody
    good = pg == wfm["paths"] and bg; ok &= good
    print(f"   rule {r.stem}: paths {'equal' if pg == wfm['paths'] else 'DIFF ' + repr(pg)}, body {'equal' if bg else 'DIFF'}")
for s in ("okf", "validate", "backfill", "visualize"):
    good = (c / ".claude/skills" / s / "SKILL.md").is_file(); ok &= good
    print(f"   okf skill {s}: {'present' if good else 'MISSING'}")
print("   other files:", sorted(str(p.relative_to(c)) for p in c.rglob("*") if p.is_file()
      and not any(x in p.parts for x in (".git", "apm_modules", "skills", "rules", "agents"))))
sys.exit(0 if ok else 1)
EOF

# A: consumer apm.yml entry.
A="$W/c-a"; mkdir "$A"; (cd "$A" && git init -q)
printf 'name: c-a\nversion: 0.1.0\ndependencies:\n  apm:\n    - git: %s\n      path: apm\n      allow_insecure: true\n' "$URL" > "$A/apm.yml"
(cd "$A" && APM install --target claude --allow-insecure > "$W/a.log" 2>&1); AE=$?
echo "== A (apm.yml entry): apm install exit $AE"; grep -E '\[\+\]|\[x\]|\[!\]|integrated' "$W/a.log" | head -20
PY "$W/check.py" "$KM" "$A"; AR=$?; [ $AE = 0 ] || AR=1

# B: no apm.yml, package on the command line. APM 0.33.0 cannot take a subpath
# of a repo on a non-GitHub host in the CLI form (it says to use git:+path: in
# apm.yml), so B1 records that against the served tree and B2 runs the CLI form
# kmctl would run, against the released v0.3.0 tag on GitHub (old layout: it
# still has git: parent). B passes when B2 creates apm.yml and deploys the 7
# kmctl skills and the agent.
B="$W/c-b1"; mkdir "$B"; (cd "$B" && git init -q)
(cd "$B" && APM install "$URL/apm" --target claude --allow-insecure > "$W/b1.log" 2>&1)
echo "== B1 (no apm.yml, CLI '$URL/apm'): exit $?"; grep -A2 -E '\[x\]' "$W/b1.log" | head -6
B="$W/c-b2"; mkdir "$B"; (cd "$B" && git init -q)
PKG=JasperHG90/Knowledge-management/apm#v0.3.0
(cd "$B" && APM install "$PKG" --target claude > "$W/b2.log" 2>&1); BE=$?
echo "== B2 (no apm.yml, CLI '$PKG'): exit $BE"; grep -E '\[\+\]|\[x\]|integrated|Created' "$W/b2.log" | head -20
echo "   apm.yml written:"; sed 's/^/     /' "$B/apm.yml" 2>/dev/null
BR=$BE
grep -q 'Knowledge-management/apm' "$B/apm.yml" 2>/dev/null || { echo "   apm.yml lacks the package"; BR=1; }
for s in "$KM"/plugin/skills/*/; do [ -f "$B/.claude/skills/$(basename "$s")/SKILL.md" ] || { echo "   skill $(basename "$s") MISSING"; BR=1; }; done
[ -f "$B/.claude/agents/kmctl-auditor.md" ] && echo "   agent present" || { echo "   agent MISSING"; BR=1; }
echo "== RESULT: A=$AR B=$BR (0 = everything delivered)"
[ $AR = 0 ] && [ $BR = 0 ]
