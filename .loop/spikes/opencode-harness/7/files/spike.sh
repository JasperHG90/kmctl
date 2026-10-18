#!/usr/bin/env bash
# Spike opencode-harness risk 3, changed plan: patch re-runs after every
# apm install (plain and --frozen) and lands on identical bytes, and
# `plugin patch --undo` (delete translated agents) lets apm uninstall finish
# clean. Exits 0 only when every assertion holds.
set -u
SRC=$(pwd)   # throwaway worktree of HEAD
APM=/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm/venv/bin/apm
S=$(mktemp -d -p /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/3b)
echo "scratch: $S"; "$APM" --version
FAIL=0
ok()   { echo "PASS: $*"; }
bad()  { echo "FAIL: $*"; FAIL=1; }
check() { local d="$1"; shift; if "$@"; then ok "$d"; else bad "$d"; fi; }

# Same fixture as spike 4: subfolder apm/, two Claude-format agents, one skill.
P="$S/pkg"; mkdir -p "$P/apm/.apm/agents" "$P/apm/.apm/skills/s1"
printf 'name: pkg\nversion: 0.1.0\ndescription: spike package\n' > "$P/apm/apm.yml"
cp "$SRC/apm/.apm/agents/kmctl-auditor.md" "$P/apm/.apm/agents/"
printf -- '---\nname: other\ndescription: second agent\ntools: Read\n---\nbody\n' > "$P/apm/.apm/agents/other.md"
printf -- '---\nname: s1\ndescription: a skill\n---\nskill\n' > "$P/apm/.apm/skills/s1/SKILL.md"
git -C "$P" init -q -b main && git -C "$P" add -A
git -C "$P" -c user.email=t@e.invalid -c user.name=t commit -qm pkg && git -C "$P" tag v0.1.0
mkdir -p "$S/srv/o"; git clone -q --bare "$P" "$S/srv/o/pkg.git"; git -C "$S/srv/o/pkg.git" update-server-info
PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
python3 -I "$SRC/tests/fixtures/githttp.py" "$S/srv" "$PORT" >/dev/null 2>&1 &
SRV=$!; trap 'kill $SRV' EXIT
for _ in $(seq 50); do (exec 3<>/dev/tcp/127.0.0.1/$PORT) 2>/dev/null && break; sleep 0.1; done
URL="http://127.0.0.1:$PORT/o/pkg.git"
NAME="127.0.0.1:$PORT/o/pkg/apm"

export HOME="$S/home"; mkdir -p "$HOME"
C="$S/consumer"; mkdir -p "$C/.opencode"; cd "$C"; git init -q
cat > apm.yml <<EOF
name: consumer
version: 0.0.1
targets: [opencode]
dependencies:
  apm:
    - git: $URL
      path: apm
      ref: v0.1.0
      allow_insecure: true
EOF

AG=".opencode/agents"
patch() {  # deterministic translation: tools string -> mapping, plus a marker
  for f in "$AG"/*.md; do
    python3 -I - "$f" <<'PY'
import sys,re
p=sys.argv[1]; t=open(p).read()
if 'PATCHED-MARKER' not in t:
    def m(x):
        names=[n.strip().lower() for n in x.group(1).split(',') if n.strip()]
        return 'tools:\n' + ''.join(f'  {n}: true\n' for n in names).rstrip('\n')
    t=re.sub(r'(?m)^tools: (.*)$', m, t, count=1)
    open(p,'w').write(t+"\nPATCHED-MARKER\n")
PY
  done
}
agents_hash() { sha256sum "$AG"/*.md | sha256sum | cut -c1-16; }
tree_hash() {   # every file under .opencode/ and .agents/, plus opencode.json if any
  { find .opencode .agents -type f 2>/dev/null; [ -f opencode.json ] && echo opencode.json; } \
    | sort | xargs -r sha256sum | sha256sum | cut -c1-16
}
show() { echo "--- $1"; sha256sum "$AG"/*.md 2>/dev/null | cut -c1-12,64-; echo "agents=$(agents_hash) tree=$(tree_hash) files=$({ find .opencode .agents -type f 2>/dev/null; [ -f opencode.json ] && echo opencode.json; } | sort | tr '\n' ' ')"; }
run() {  # run LABEL CMD...
  echo; echo "=== $1: ${*:2}"; "${@:2}" 2>&1 | grep -vE 'experimental resolver|lockfile reconciliation\.|tools as str|requires a mapping|load time|rewrite the frontmatter'
  rc=${PIPESTATUS[0]}; echo "=== $1 exit $rc"; check "$1 exits 0" [ "$rc" = 0 ]
}

echo; echo "##### step 1: install, patch"
run step1-install "$APM" install --allow-insecure
RAW=$(agents_hash); show "after install (raw APM bytes)"
patch; H=$(agents_hash); T=$(tree_hash); show "after patch (H)"
check "patch changed the agents" [ "$H" != "$RAW" ]
grep -q 'PATCHED-MARKER' "$AG"/other.md && grep -q '^  read: true' "$AG"/other.md && ok "other.md translated" || bad "other.md not translated"
patch; check "patch is idempotent on its own output" [ "$(agents_hash)" = "$H" ]
LOCK1=$(sha256sum apm.lock.yaml | cut -c1-16)

echo; echo "##### step 2: plain install again, re-patch"
run step2-install "$APM" install --allow-insecure; show "after install"
check "install reverted agents to raw APM bytes" [ "$(agents_hash)" = "$RAW" ]
patch; show "after re-patch"
check "re-patched agents equal H" [ "$(agents_hash)" = "$H" ]
check "whole tree equals state after step 1" [ "$(tree_hash)" = "$T" ]
check "apm.lock.yaml unchanged by install" [ "$(sha256sum apm.lock.yaml | cut -c1-16)" = "$LOCK1" ]

echo; echo "##### step 3: install --frozen, re-patch"
run step3-frozen "$APM" install --frozen --allow-insecure; show "after frozen install"
patch; show "after re-patch"
check "re-patched agents equal H after --frozen" [ "$(agents_hash)" = "$H" ]
check "whole tree equals state after step 1 after --frozen" [ "$(tree_hash)" = "$T" ]
check "apm.lock.yaml unchanged by --frozen" [ "$(sha256sum apm.lock.yaml | cut -c1-16)" = "$LOCK1" ]

echo; echo "##### step 4: undo (delete translated agents only), then uninstall"
for f in "$AG"/*.md; do grep -q PATCHED-MARKER "$f" && rm -f "$f"; done
show "after undo"
run step4-uninstall "$APM" uninstall "$NAME"; show "after uninstall"
if ls "$AG"/*.md >/dev/null 2>&1; then bad "agent files left"; else ok "no .opencode/agents/*.md left"; fi
if [ -f apm.lock.yaml ] && grep -qE 'pkg|opencode/agents|skills' apm.lock.yaml; then bad "lock still names the dependency"; cat apm.lock.yaml; else ok "no lock dependency entry (lock present: $([ -f apm.lock.yaml ] && echo yes || echo no))"; fi
LEFT=$(find .agents -type f 2>/dev/null)
check "no leftover skill files" [ -z "$LEFT" ]
if grep -q "$URL" apm.yml; then bad "apm.yml still lists the dependency"; else ok "apm.yml no longer lists the dependency"; fi
echo "=== apm.yml after uninstall"; cat apm.yml
echo "=== files left under .opencode/ .agents/ apm_modules/"; find .opencode .agents apm_modules -type f 2>/dev/null

echo; echo "RESULT FAIL=$FAIL"; exit $FAIL
