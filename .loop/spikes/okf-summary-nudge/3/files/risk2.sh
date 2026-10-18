#!/usr/bin/env bash
# Does APM 0.33.0 deploy a PostToolUse entry with matcher Write|Edit|MultiEdit|Bash from a
# package's .apm/hooks/hooks.json into .claude/settings.json, keep one copy on reinstall,
# record it (lock names the package; APM tracks hooks in .claude/apm-hooks.json), and remove it on uninstall? Exits 0 only when all hold.
set -u
unset GITHUB_TOKEN GH_TOKEN GITHUB_APM_PAT
SRC=/home/vscode/kmctl/apm/claude
W=$(mktemp -d); CACHE=${UV_CACHE_DIR:-$HOME/.cache/uv}
export UV_CACHE_DIR=$CACHE HOME=$W/home CLAUDE_CONFIG_DIR=$W/home/.claude; mkdir -p $CLAUDE_CONFIG_DIR
P=$W/c/pkg; mkdir -p $W/c; cp -r $SRC $P   # mirror apm/claude (apm.yml, .apm/instructions, .apm/hooks)
python3 -I - "$P/.apm/hooks/hooks.json" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p))
d["hooks"]["PostToolUse"]=[{"matcher":"Write|Edit|MultiEdit|Bash","hooks":[{"type":"command",
  "description":"kmctl: nudge to summarise new OKF concepts. Never blocks.",
  "command":"command -v kmctl >/dev/null 2>&1 && kmctl nudge || true; exit 0","timeout":10}]}]
json.dump(d,open(p,"w"),indent=2)
PY
cd $W/c && git init -q
printf 'name: c\nversion: 0.0.1\ndependencies:\n  apm:\n    - ./pkg\ntargets: [claude]\n' > apm.yml
APM="uvx --from apm-cli==0.33.0 apm"
check() {
  python3 -I - .claude/settings.json <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
h=d.get("hooks",{})
print("events:", sorted(h))
post=h.get("PostToolUse",[])
print("PostToolUse:", json.dumps(post))
ss=h.get("SessionStart",[])
n=sum(1 for e in post if e.get("matcher")=="Write|Edit|MultiEdit|Bash")
print("matching entries:", n, "| SessionStart entries:", len(ss))
sys.exit(0 if n==1 and len(post)==1 and len(ss)==1 else 1)
PY
}
ok=1
$APM install --target claude > in1.txt 2>&1; rc=$?; echo "install 1 rc=$rc"; tail -15 in1.txt
[ $rc = 0 ] || ok=0
echo "--- after install 1"; check || ok=0
$APM install --target claude > in2.txt 2>&1; rc=$?; echo "install 2 rc=$rc"; tail -5 in2.txt
[ $rc = 0 ] || ok=0
echo "--- after install 2"; check || ok=0
echo "--- apm.lock.yaml"; cat apm.lock.yaml
grep -q "name: kmctl-claude" apm.lock.yaml || { echo "FAIL: lock lacks the package"; ok=0; }
grep -q "PostToolUse\|settings.json" apm.lock.yaml && echo "lock names the hook or settings.json" || echo "lock does not name the hook or settings.json"
echo "--- .claude/apm-hooks.json"; cat .claude/apm-hooks.json 2>/dev/null || echo "(none)"
grep -q "Write|Edit|MultiEdit|Bash" .claude/apm-hooks.json 2>/dev/null || { echo "FAIL: apm-hooks.json lacks the PostToolUse entry"; ok=0; }
$APM uninstall ./pkg > un.txt 2>&1; echo "uninstall rc=$?"; tail -5 un.txt
echo "--- settings.json after uninstall"; cat .claude/settings.json 2>/dev/null || echo "(none)"
grep -q "PostToolUse" .claude/settings.json 2>/dev/null && { echo "FAIL: PostToolUse left after uninstall"; ok=0; }
echo "ok=$ok"; [ $ok = 1 ]
