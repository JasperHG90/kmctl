#!/usr/bin/env bash
# Spike plugin-remove risk 1: does `apm uninstall` on kmctl's entry remove
# every deployed file, okf's transitive skills and the lock entries?
# Exits 0 only when nothing kmctl- or okf-related remains after uninstall.
set -u
SRC=$(pwd)                      # the throwaway worktree of HEAD
PROJ=/home/vscode/kmctl         # project uv runs kmctl from
S=$(mktemp -d -p /tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove-1)
echo "scratch: $S"
CACHE=${UV_CACHE_DIR:-$(uv cache dir)}
UVBIN=$(dirname "$(command -v uv)")
mkdir -p "$S/home/.claude" "$S/tools"
ln -s "$(command -v uv)" "$S/tools/uv"
ln -s "$(command -v uvx)" "$S/tools/uvx"
VER=$(cd "$PROJ" && uv run --project "$PROJ" kmctl --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+[^ ]*' | head -1)
echo "kmctl version: $VER"

# Serve this tree as o/kmctl.git tagged v$VER, as tests/conftest.py served does.
mkdir -p "$S/kmctl"
git -C "$SRC" ls-files -z --cached --others --exclude-standard | (cd "$SRC" && xargs -0 cp --parents -t "$S/kmctl" 2>/dev/null)
git -C "$S/kmctl" init -q -b main && git -C "$S/kmctl" add -A
git -C "$S/kmctl" -c user.email=t@e.invalid -c user.name=t commit -qm tree
git -C "$S/kmctl" tag "v$VER"
mkdir -p "$S/srv/o"
git clone -q --bare "$S/kmctl" "$S/srv/o/kmctl.git"
git -C "$S/srv/o/kmctl.git" update-server-info
PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
python3 -I "$SRC/tests/fixtures/githttp.py" "$S/srv" "$PORT" >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV' EXIT
for _ in $(seq 50); do (exec 3<>/dev/tcp/127.0.0.1/$PORT) 2>/dev/null && break; sleep 0.1; done
URL="http://127.0.0.1:$PORT/o/kmctl.git"

export UV_CACHE_DIR="$CACHE" HOME="$S/home" CLAUDE_CONFIG_DIR="$S/home/.claude" \
  XDG_DATA_HOME="$S/home/.local/share" PATH="$S/tools:/usr/bin:/bin"
unset VIRTUAL_ENV
C="$S/consumer"; mkdir -p "$C"; cd "$C"; git init -q
echo 'keep me' > README.md

snapshot() {
  echo "=== $1: files under .claude/ and .agents/"
  find .claude .agents -type f 2>/dev/null | sort
  echo "=== $1: apm_modules entries (depth 3)"
  find apm_modules -mindepth 1 -maxdepth 3 -type d 2>/dev/null | sort
  echo "=== $1: apm.yml"; cat apm.yml 2>/dev/null || echo "(no apm.yml)"
  echo "=== $1: lock dependencies"
  python3 -I -c 'import re,sys
t=open("apm.lock.yaml").read() if __import__("os").path.exists("apm.lock.yaml") else ""
print(t if t else "(no apm.lock.yaml)")' | sed -n '/^dependencies:/,/^[a-z_]*:/p' | grep -E 'repo_url|^- |^  - |virtual_path|path:' | grep -vE 'deployed|sha' || true
  echo "=== $1: full lock"; cat apm.lock.yaml 2>/dev/null || echo "(none)"
}

uv run --project "$PROJ" kmctl plugin install --harness claude,antigravity --source "$URL" || { echo "INSTALL FAILED"; exit 2; }
snapshot BEFORE
echo "=== apm deps list"; uvx --from apm-cli==0.33.0 apm deps list 2>&1

# Try candidate names for kmctl's entry; stop at the first one that drops
# kmctl's entry from apm.yml.
WORKED=""
for arg in "$URL" "127.0.0.1:$PORT/o/kmctl/apm" "o/kmctl/apm" "o/kmctl"; do
  echo "=== apm uninstall '$arg'"
  uvx --from apm-cli==0.33.0 apm uninstall "$arg" 2>&1; rc=$?
  echo "exit $rc"
  if [ $rc -eq 0 ] && ! grep -q 'kmctl' apm.yml 2>/dev/null; then WORKED="$arg"; break; fi
done
echo "=== uninstall argument that worked: ${WORKED:-none}"
snapshot AFTER

echo "=== left over (kmctl or okf related)"
LEFT=$( { find .claude .agents -type f 2>/dev/null | grep -vE '^\.claude/settings\.json$'; \
          find apm_modules -mindepth 1 -maxdepth 3 2>/dev/null; \
          grep -n -iE 'kmctl|okf' apm.yml apm.lock.yaml 2>/dev/null; \
          grep -n -iE 'okf' .claude/settings.json 2>/dev/null | sed 's/^/settings.json:/'; } )
echo "${LEFT:-(nothing)}"
echo "=== settings.json / .mcp.json (kmctl writes these itself, not APM)"
cat .claude/settings.json 2>/dev/null; cat .mcp.json 2>/dev/null
[ -n "$WORKED" ] && [ -z "$LEFT" ]
