#!/usr/bin/env bash
# Spike plugin-remove risk 2: does dropping a target from apm.yml `targets:` and
# running `apm install --target REST` remove the dropped target's files?
# Exit 0 only when, in both directions (drop antigravity, drop claude), the
# dropped target's deployed files are all gone from disk.
set -uo pipefail

ROOT=$(pwd)                       # the throwaway worktree of HEAD
SCRATCH=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove-2
RUN=$(mktemp -d "$SCRATCH/run.XXXX")
REAL_UV_PY=$(uv python dir 2>/dev/null)
CACHE=${UV_CACHE_DIR:-$(uv cache dir)}
UVBIN=$(command -v uv); UVXBIN=$(command -v uvx)
APM=(uvx --from apm-cli==0.33.0 apm)

mkdir -p "$RUN/tools" "$RUN/home/.claude"
ln -s "$UVBIN" "$RUN/tools/uv"; ln -s "$UVXBIN" "$RUN/tools/uvx"
export HOME="$RUN/home" CLAUDE_CONFIG_DIR="$RUN/home/.claude" \
  XDG_DATA_HOME="$RUN/home/.local/share" UV_CACHE_DIR="$CACHE" \
  UV_PYTHON_INSTALL_DIR="$REAL_UV_PY" PATH="$RUN/tools:/usr/bin:/bin"
unset VIRTUAL_ENV
GIT=(git -c user.email=t@e.invalid -c user.name=t)
command -v claude && { echo "real claude on PATH, abort"; exit 2; }

VERSION=$(uv run --project "$ROOT" kmctl --version | awk '{print $2}')
echo "kmctl $VERSION"

# Serve the worktree's tree as o/kmctl.git tagged v$VERSION, as tests/conftest.py served does.
mkdir -p "$RUN/kmctl"
(cd "$ROOT" && git ls-files -z | xargs -0 cp --parents -t "$RUN/kmctl" 2>/dev/null)
(cd "$RUN/kmctl" && git init -q -b main && git add -A && "${GIT[@]}" commit -qm tree && git tag "v$VERSION")
mkdir -p "$RUN/srv/o"
git clone -q --bare "$RUN/kmctl" "$RUN/srv/o/kmctl.git"
git -C "$RUN/srv/o/kmctl.git" update-server-info
PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
python3 -I "$ROOT/tests/fixtures/githttp.py" "$RUN/srv" "$PORT" >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV' EXIT
for _ in $(seq 50); do (exec 3<>/dev/tcp/127.0.0.1/$PORT) 2>/dev/null && break; sleep 0.1; done
URL="http://127.0.0.1:$PORT/o/kmctl.git"

list() {  # files on disk under .claude/.agents, and the lock's view
  echo "--- files ($1)"
  find .claude .agents -type f 2>/dev/null | sort
  echo "--- apm.yml targets"; grep -A3 '^targets' apm.yml
  echo "--- lock deployed_files under .agents/ and .claude/"
  python3 -I - <<'EOF'
import re
t=open("apm.lock.yaml").read()
print("lock .agents/ entries:", len(re.findall(r"^\s*- \.agents/", t, re.M)))
print("lock .claude/ entries:", len(re.findall(r"^\s*- \.claude/", t, re.M)))
print("lock deployment targets:", sorted(set(re.findall(r"target: (\w+)", t))))
EOF
}

# Files under $1 that APM put there: everything except what kmctl itself writes
# (.agents/plugins/kmctl/ and .claude/settings.json, checked separately).
apm_files() {
  find "$1" -type f 2>/dev/null | grep -v -e '^.agents/plugins/kmctl/' -e '^.claude/settings.json$' | sort
}
lock_drop() {  # lock deployments still naming a path under $1, with their target
  python3 -I - "$1" <<'EOF2'
import sys, re
t = open("apm.lock.yaml").read()
for m in re.finditer(r"target: (\w+)\n  value: (\S+)", t):
    if m.group(2).startswith(sys.argv[1] + "/"):
        print("  lock deployment:", m.group(1), m.group(2))
EOF2
}

STATUS=0
for DROP in antigravity claude; do
  KEEP=$([ "$DROP" = antigravity ] && echo claude || echo antigravity)
  DIR=$([ "$DROP" = antigravity ] && echo .agents || echo .claude)
  C="$RUN/consumer-drop-$DROP"; mkdir -p "$C"; cd "$C"; git init -q
  echo; echo "===== drop $DROP, keep $KEEP"
  uv run --project "$ROOT" kmctl plugin install --harness claude,antigravity --source "$URL" 2>&1 | tail -5
  list "after install both"
  BEFORE=$(apm_files "$DIR" | wc -l)
  sed -i "/^targets:/,/^[^ -]/{/^- $DROP\$/d;/^  - $DROP\$/d}" apm.yml
  echo "--- apm.yml after edit"; cat apm.yml
  "${APM[@]}" install --target "$KEEP" --allow-insecure 2>&1 | tail -15
  list "after apm install --target $KEEP"
  AFTER=$(apm_files "$DIR" | wc -l)
  echo "RESULT drop=$DROP: $DIR APM files before=$BEFORE after=$AFTER"
  apm_files "$DIR" | sed 's/^/  left on disk: /'
  for f in $(apm_files "$DIR"); do echo "  $f content: $(head -c 120 "$f" | tr '\n' ' ')"; done
  lock_drop "$DIR"
  [ "$DROP" = claude ] && { echo "  settings.json hook events:"; python3 -I -c 'import json;print(" ",list(json.load(open(".claude/settings.json"))["hooks"]))'; }
  [ "$BEFORE" -gt 0 ] && [ "$AFTER" -eq 0 ] || STATUS=1
  if [ "$AFTER" -gt 0 ]; then  # other APM routes, for the record only
    echo "--- fallback: apm install --allow-insecure (targets from apm.yml)"
    "${APM[@]}" install --allow-insecure 2>&1 | tail -6
    echo "FALLBACK install-no-target drop=$DROP: $(apm_files "$DIR" | wc -l) left"
    echo "--- fallback: apm prune"
    "${APM[@]}" prune 2>&1 | tail -6
    echo "FALLBACK prune drop=$DROP: $(apm_files "$DIR" | wc -l) left"; lock_drop "$DIR"
    echo "--- apm targets"; "${APM[@]}" targets 2>&1 | tail -8
  fi
done
exit $STATUS
