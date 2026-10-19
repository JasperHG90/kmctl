#!/usr/bin/env bash
# Spike: does `apm audit --ci` (APM 0.33.0) fail drift on .agents/hooks.json and
# config-consistency on `bundle` after apm install --target antigravity +
# kmctl plugin patch, and pass for --target claude alone?
# Runs in a worktree of kmctl HEAD ($PWD). Exits 0 only when the issue's
# account holds: antigravity fails exactly drift + config-consistency, claude passes.
set -u
TREE=$PWD
apm() { uvx --from apm-cli==0.33.0 apm "$@"; }
kmctl() { uv run --project "$TREE" kmctl "$@"; }
VER=$(python3 -c "import re,sys;print(re.search(r'^version:\s*(\S+)',open('$TREE/apm/apm.yml').read(),re.M).group(1))")
TAG="v$VER"
URL=https://github.com/JasperHG90/kmctl.git
W=$(mktemp -d)
echo "kmctl tree $TREE at $(git -C "$TREE" rev-parse HEAD), tag $TAG, work $W"
apm --version

# A tagged bare clone of this tree; git rewrites the GitHub URL to it.
git clone -q --bare "$TREE" "$W/kmctl.git"
git -C "$W/kmctl.git" tag -f "$TAG" HEAD >/dev/null
cat > "$W/gitconfig" <<EOF
[url "file://$W/kmctl.git"]
	insteadOf = $URL
	insteadOf = ${URL%.git}
[user]
	email = t@e.invalid
	name = t
EOF
export GIT_CONFIG_GLOBAL=$W/gitconfig GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0
unset GITHUB_TOKEN GH_TOKEN GITHUB_APM_PAT GITHUB_COPILOT_PAT

audit() { # name, extra args
  local name=$1; shift
  echo "----- [$P] apm audit --ci $* -----"
  apm audit --ci "$@" > "$W/$P.$name.txt" 2>&1
  local rc=$?
  cat "$W/$P.$name.txt"
  echo "----- exit $rc -----"
  echo $rc > "$W/$P.$name.rc"
}

project() { # target
  P=$1
  local d=$W/$P
  mkdir -p "$d" && cd "$d" && git init -q -b main
  cat > apm.yml <<EOF
name: demo
version: 0.1.0
dependencies:
  apm:
    - git: $URL
      path: apm
      ref: $TAG
targets:
  - $P
EOF
  echo "===== [$P] apm install --target $P ====="
  apm install --target "$P" 2>&1 | tail -15
  git add -A && git commit -qm install
  audit before_patch --no-fail-fast
  echo "===== [$P] kmctl plugin patch ====="
  kmctl plugin patch 2>&1 | tail -10
  git add -A && git commit -qm patch
  echo "hooks.json:"; cat .agents/hooks.json 2>/dev/null || echo "(none)"
  audit plain
  audit all --no-fail-fast
  audit nodrift --no-drift --no-fail-fast
  apm audit --ci --no-fail-fast -f json > "$W/$P.json" 2>/dev/null
  echo "json summary:"; python3 - "$W/$P.json" <<'PY'
import json,sys
t=open(sys.argv[1]).read(); d=json.loads(t[t.index('{'):])
for c in d.get("checks",[]): print(" ", c.get("name"), "passed" if c.get("passed") else "FAILED", "|", c.get("message",""), c.get("details",""))
PY
  cd "$W"
}

project antigravity
project claude

for p in antigravity claude; do echo "SUMMARY $p: before_patch=$(cat $W/$p.before_patch.rc) plain=$(cat $W/$p.plain.rc) all=$(cat $W/$p.all.rc) nodrift=$(cat $W/$p.nodrift.rc)"; done
ok=1
grep -qi drift "$W/antigravity.all.txt" && grep -q hooks.json "$W/antigravity.all.txt" || { echo "MISS: drift on hooks.json"; ok=0; }
grep -qi config-consistency "$W/antigravity.all.txt" && grep -q bundle "$W/antigravity.all.txt" || { echo "MISS: config-consistency on bundle"; ok=0; }
[ "$(cat $W/antigravity.all.rc)" != 0 ] || { echo "MISS: antigravity audit passed"; ok=0; }
[ "$(cat $W/claude.all.rc)" = 0 ] || { echo "MISS: claude audit failed"; ok=0; }
[ $ok = 1 ] && { echo "ISSUE CONFIRMED"; exit 0; }
exit 1
