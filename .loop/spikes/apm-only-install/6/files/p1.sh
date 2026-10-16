#!/usr/bin/env bash
# Risk 4 (apm-only-install), plan review finding p1 (ADR 0013 users).
# A consumer installed the old package JasperHG90/Knowledge-management/apm#v0.3.0
# (string entry in apm.yml; APM wrote skills, agent and a SessionStart hook).
# kmctl then swaps that entry for {git: <new-layout tree>, path: apm} and adds a
# plain SessionStart entry to .claude/settings.json, and runs apm install.
# Does APM drop the old package's files and hook, land the new files, and keep
# exactly one kmctl SessionStart entry across a second install? If the plain
# route leaves leftovers, try `apm prune` and record it.
# Exit 0 only when the end state (with the recorded steps) is right.
set -u
KM=$(git rev-parse --show-toplevel)
SCR=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-migrate
mkdir -p "$SCR"; W=$(mktemp -d "$SCR/p1.XXXX")
export UV_CACHE_DIR="${UV_CACHE_DIR:-/home/vscode/.cache/uv}"
REAL=/home/vscode/.claude
IP_BEFORE=$(sha256sum "$REAL/plugins/installed_plugins.json" 2>/dev/null || echo none)
export HOME="$W/home" CLAUDE_CONFIG_DIR="$W/home/.claude"; mkdir -p "$CLAUDE_CONFIG_DIR"
git config --global user.email spike@example.invalid
git config --global user.name spike
git config --global init.defaultBranch main
APM() { uvx -q --from apm-cli==0.33.0 apm "$@"; }
PY() { uv run -q --no-project --with pyyaml python -I "$@"; }
OKF=a8b96420de90d102c43cda1693d01ec4f925f2ab
echo "== kmctl HEAD $(git -C "$KM" rev-parse HEAD); $(APM --version 2>&1 | tail -1)"

# 1. New-layout tree, built as in spike:apm-only-install/1, served over http.
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
EOF
PY "$W/conv.py" "$T/src/kmctl/repo_rules" "$T/apm/.apm/instructions" || exit 3
rm -rf "$T/src/kmctl/repo_rules"
printf 'name: kmctl\nversion: 0.4.0\ndescription: spike\ndependencies:\n  apm:\n    - scaccogatto/okf-skills#%s\n' "$OKF" > "$T/apm/apm.yml"
( cd "$T" && git init -q && git add -A && git commit -qm tree ) || exit 3
mkdir -p "$W/srv/o"; git clone -q --bare "$T" "$W/srv/o/kmctl.git" && git -C "$W/srv/o/kmctl.git" update-server-info
PORT=$(PY -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')
python3 -I "$KM/tests/fixtures/githttp.py" "$W/srv" "$PORT" >/dev/null 2>&1 &
SRV=$!; trap 'kill "$SRV" 2>/dev/null' EXIT; sleep 1
URL="http://127.0.0.1:$PORT/o/kmctl.git"

cat > "$W/check.py" <<'EOF'
# check.py KM CONSUMER OLDLIST -> exit 0 when the migration end state is right
import sys, json, yaml, pathlib, filecmp
km, c, oldlist = map(pathlib.Path, sys.argv[1:4]); ok = True
def say(good, msg):
    global ok; ok &= good; print(f"   [{'ok' if good else 'BAD'}] {msg}")
def same_tree(a, b):
    d = filecmp.dircmp(a, b)
    if d.left_only or d.right_only or d.diff_files or d.funny_files: return False
    _, mism, err = filecmp.cmpfiles(a, b, d.common_files, shallow=False)
    return not mism and not err and all(same_tree(a / s, b / s) for s in d.common_dirs)
for s in sorted((km / "plugin/skills").iterdir()):
    say((c / ".claude/skills" / s.name).is_dir() and same_tree(s, c / ".claude/skills" / s.name),
        f"skill {s.name} equals new package")
a = c / ".claude/agents/kmctl-auditor.md"
say(a.is_file() and filecmp.cmp(km / "plugin/agents/kmctl-auditor.md", a, shallow=False), "agent equals new package")
for r in sorted((km / "src/kmctl/repo_rules").glob("*.md")):
    say((c / ".claude/rules" / r.name).is_file(), f"rule {r.name} present")
for s in ("okf", "validate", "backfill", "visualize"):
    say((c / ".claude/skills" / s / "SKILL.md").is_file(), f"okf skill {s} present")
lock = yaml.safe_load((c / "apm.lock.yaml").read_text())
deps = lock.get("dependencies") or []
print("   lock deps:", [(d.get("repo_url"), d.get("virtual_path"), d.get("host")) for d in deps])
say(not any("knowledge-management" in str(d.get("repo_url", "")).lower() for d in deps), "no old github kmctl dep in lock")
now = {f for d in deps for f in d.get("deployed_files") or []}
old = [l for l in oldlist.read_text().split() if l]
left = sorted(f for f in old if f not in now and (c / f).exists())
say(not left, f"old-only files left on disk: {left}")
hooks = json.loads((c / ".claude/settings.json").read_text()).get("hooks", {})
ss = hooks.get("SessionStart", [])
km_ss = [e for e in ss if any("kmctl briefing" in h.get("command", "") for h in e.get("hooks", []))]
print("   settings SessionStart entries:", json.dumps(ss)[:400])
say(len(km_ss) == 1, f"kmctl SessionStart entries in settings.json: {len(km_ss)}")
side = c / ".claude/apm-hooks.json"
st = json.loads(side.read_text()) if side.exists() else {}
srcs = [e.get("_apm_source") for v in st.values() for e in v]
print("   apm-hooks.json sources:", srcs)
say(not any("knowledge-management" in str(s) for s in srcs), "no old kmctl source in apm-hooks.json")
print("   Stop hooks (okf):", len(hooks.get("Stop", [])))
sys.exit(0 if ok else 1)
EOF

old_install() {  # $1 consumer dir
  local C=$1; mkdir "$C"; (cd "$C" && git init -q)
  printf 'name: consumer\nversion: 0.1.0\ndependencies:\n  apm:\n    - JasperHG90/Knowledge-management/apm#v0.3.0\n' > "$C/apm.yml"
  (cd "$C" && APM install --target claude > "$C.old.log" 2>&1); echo "== old install: exit $?"
  grep -E '\[\+\]|integrated|\[x\]' "$C.old.log" | sed 's/^/   /'
  PY -c '
import sys, yaml
l = yaml.safe_load(open(sys.argv[1]))
for d in l["dependencies"]:
    if "knowledge-management" in d["repo_url"].lower():
        print("\n".join(d.get("deployed_files") or []))' "$C/apm.lock.yaml" > "$C.oldfiles.txt"
  echo "   old kmctl deployed_files: $(wc -l < "$C.oldfiles.txt")"
}
ss_count() { PY -c 'import json,sys; print(len(json.load(open(sys.argv[1])).get("hooks",{}).get("SessionStart",[])))' "$1/.claude/settings.json"; }
migrate() {  # $1 consumer dir: swap the apm.yml entry, add a plain SessionStart entry
  local C=$1
  printf 'name: consumer\nversion: 0.1.0\ndependencies:\n  apm:\n    - git: %s\n      path: apm\n      allow_insecure: true\n' "$URL" > "$C/apm.yml"
  PY -c '
import json, sys
s = json.load(open(sys.argv[1])); h = json.load(open(sys.argv[2]))["hooks"]["SessionStart"][0]
s.setdefault("hooks", {}).setdefault("SessionStart", []).append(h)
json.dump(s, open(sys.argv[1], "w"), indent=2)' "$C/.claude/settings.json" "$KM/plugin/hooks/hooks.json"
  echo "   SessionStart entries in settings.json before new install: $(ss_count "$C")"
}
inst() { (cd "$1" && APM install --target claude --allow-insecure > "$1.$2.log" 2>&1); echo "== apm install ($2): exit $?"
  grep -E '\[\+\]|hook|\[x\]' "$1.$2.log" | sed 's/^/   /'; }
check() { echo "== check: $2"; PY "$W/check.py" "$KM" "$1" "$1.oldfiles.txt"; }

# Route A: plain. Old install, swap, apm install, re-install.
echo "######## Route A: swap entry, apm install"
A="$W/a"; old_install "$A"; migrate "$A"; inst "$A" new
check "$A" "A after apm install"; RA=$?
inst "$A" re; check "$A" "A after second apm install"; RA2=$?
# Route P: A plus apm prune.
echo "######## Route P: then apm prune, apm install"
(cd "$A" && APM prune > "$A.prune.log" 2>&1); echo "== apm prune: exit $?"; sed 's/^/   /' "$A.prune.log" | tail -8
inst "$A" afterprune; check "$A" "P after prune + apm install"; RP=$?
# Route U: apm uninstall the old package before the swap.
echo "######## Route U: apm uninstall old package first, then swap, apm install"
U="$W/u"; old_install "$U"
(cd "$U" && APM uninstall JasperHG90/Knowledge-management/apm > "$U.uninst.log" 2>&1); echo "== apm uninstall JasperHG90/Knowledge-management/apm: exit $?"
sed 's/^/   /' "$U.uninst.log" | tail -12
echo "   SessionStart entries after uninstall: $(ss_count "$U"); apm-hooks.json: $(cat "$U/.claude/apm-hooks.json" 2>/dev/null | tr -d ' \n' | head -c 300)"
echo "   kmctl skills left after uninstall: $(ls "$U/.claude/skills" 2>/dev/null | tr '\n' ' ')"
migrate "$U"; inst "$U" new; check "$U" "U after apm install"; RU=$?
inst "$U" re; check "$U" "U after second apm install"; RU2=$?
echo "== routes (0 = right end state): A=$RA A-reinstall=$RA2 prune=$RP uninstall-first=$RU uninstall-first-reinstall=$RU2"
if [ $RA = 0 ] && [ $RA2 = 0 ]; then STEPS="plain apm install"; R=0
elif [ $RP = 0 ]; then STEPS="apm install; apm prune; apm install"; R=0
elif [ $RU = 0 ] && [ $RU2 = 0 ]; then STEPS="apm uninstall OLD; swap; apm install"; R=0
else STEPS="none worked"; R=1; fi
RR=$R

# Safety: real ~/.claude untouched.
SAFE=0
for p in "$REAL/agents" "$REAL/rules" "$REAL/skills/audit"; do [ -e "$p" ] && { echo "   REAL $p EXISTS"; SAFE=1; }; done
IP_AFTER=$(sha256sum "$REAL/plugins/installed_plugins.json" 2>/dev/null || echo none)
[ "$IP_BEFORE" = "$IP_AFTER" ] || { echo "   REAL installed_plugins.json CHANGED"; SAFE=1; }
echo "== RESULT: steps '$STEPS'; after steps=$R, after re-install=$RR, real ~/.claude untouched=$([ $SAFE = 0 ] && echo yes || echo NO)"
[ $R = 0 ] && [ $RR = 0 ] && [ $SAFE = 0 ]
