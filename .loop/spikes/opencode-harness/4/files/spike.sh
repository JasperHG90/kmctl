#!/usr/bin/env bash
# Spike opencode-harness risk 3: after hand-editing APM-deployed
# .opencode/agents/*.md, do apm install, install --frozen, install --force and
# uninstall still exit 0, what do they do to each edited file, and does
# uninstall remove the edited files and their lock entries?
# Exits 0 only when every command exits 0 and uninstall leaves no agent file
# and no lock entry behind.
set -u
SRC=$(pwd)   # throwaway worktree of HEAD
APM=/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm/venv/bin/apm
S=$(mktemp -d -p /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/3)
echo "scratch: $S"; "$APM" --version
FAIL=0

# A small package shaped like kmctl's: subfolder apm/, two Claude-format agents
# (kmctl's real auditor plus one more) and a skill, served over git http, tagged.
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
edit() {  # what patch would do: tools string -> mapping, plus a marker line
  for f in "$AG"/*.md; do
    python3 -I - "$f" <<'PY'
import sys,re
p=sys.argv[1]; t=open(p).read()
t=re.sub(r'(?m)^tools: .*$', 'tools:\n  read: true\n  grep: true', t, count=1)
open(p,'w').write(t+"\nPATCHED-MARKER\n")
PY
  done
}
state() {
  echo "--- state after $1"
  for f in "$AG"/kmctl-auditor.md "$AG"/other.md; do
    if [ -f "$f" ]; then
      m=$(grep -c PATCHED-MARKER "$f"); tl=$(grep -m1 -A1 '^tools:' "$f" | tr '\n' '|')
      echo "$f: present, marker=$m, tools=[$tl] sha=$(sha256sum "$f" | cut -c1-12)"
    else echo "$f: ABSENT"; fi
  done
  echo "lock hashes:"; grep -E '^\s+\.opencode/agents/.*sha256' apm.lock.yaml 2>/dev/null | sed 's/sha256:\(.\{12\}\).*/sha256:\1/' || echo "  (no lock or no entries)"
}
run() {  # run LABEL CMD...
  echo; echo "=== $1: ${*:2}"; "${@:2}" 2>&1 | grep -vE 'experimental resolver|lockfile reconciliation\.'
  rc=${PIPESTATUS[0]}; echo "=== $1 exit $rc"; [ "$rc" = 0 ] || FAIL=1
}

run install1 "$APM" install --allow-insecure
state install1
edit; state edit1
run install2-plain "$APM" install --allow-insecure; state install2-plain
edit; state edit2
run install3-frozen "$APM" install --frozen --allow-insecure; state install3-frozen
edit; state edit3
run install4-force "$APM" install --force --allow-insecure; state install4-force
edit; state edit4
run audit "$APM" audit
echo; echo "=== apm deps list"; "$APM" deps list 2>&1
NAME="127.0.0.1:$PORT/o/pkg/apm"
run uninstall "$APM" uninstall "$NAME"; state uninstall
echo "=== apm.yml after uninstall"; cat apm.yml
echo "=== lock after uninstall"; cat apm.lock.yaml 2>/dev/null || echo "(no apm.lock.yaml)"
echo "=== files left under .opencode/ and .agents/"; find .opencode .agents -type f 2>/dev/null
if ls "$AG"/*.md >/dev/null 2>&1; then echo "LEFTOVER agent files"; FAIL=1; fi
if grep -q 'opencode/agents' apm.lock.yaml 2>/dev/null; then echo "LEFTOVER lock entries"; FAIL=1; fi
RESULT=$FAIL

# Informational recovery paths (do not change the exit code).
echo; echo "##### recovery A: plain apm install (reverts edits), then uninstall"
cp apm.yml apm.yml.keep; cp apm.lock.yaml apm.lock.keep
run recA-install "$APM" install --allow-insecure; state recA-install
run recA-uninstall "$APM" uninstall "$NAME"; state recA-uninstall
echo "apm.yml deps:"; sed -n '/^dependencies:/,$p' apm.yml
echo "files left:"; find .opencode .agents apm_modules -type f 2>/dev/null; ls apm.lock.yaml 2>/dev/null || echo "(no apm.lock.yaml)"

echo; echo "##### recovery B: fresh install, edit, delete the edited agent files, then uninstall"
cp apm.yml.keep apm.yml; run recB-install "$APM" install --allow-insecure; edit; state recB-edit
rm -f "$AG"/kmctl-auditor.md "$AG"/other.md
run recB-uninstall "$APM" uninstall "$NAME"; state recB-uninstall
echo "apm.yml deps:"; sed -n '/^dependencies:/,$p' apm.yml
echo "files left:"; find .opencode .agents apm_modules -type f 2>/dev/null; ls apm.lock.yaml 2>/dev/null || echo "(no apm.lock.yaml)"

echo "RESULT (main path) FAIL=$RESULT"; exit $RESULT
