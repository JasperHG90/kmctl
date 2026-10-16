#!/usr/bin/env bash
# p3: with a scratch HOME/CLAUDE_CONFIG_DIR and a warm uv cache, do
#   uv tool run --offline --from apm-cli==0.33.0 apm --version
#   claude plugin list --json
# run without opening a network connection, and does claude plugin list leave
# every file under the scratch HOME unchanged? unshare -rn is not permitted in
# this container, so connections are observed with strace instead of blocked.
# Exit 0 iff both commands succeed, neither calls connect() on AF_INET/AF_INET6,
# and neither changes any file under the scratch HOME.
set -u
export UV_CACHE_DIR="$(uv cache dir)"
W=$(mktemp -d)
export HOME="$W/home" CLAUDE_CONFIG_DIR="$W/home/.claude"
mkdir -p "$CLAUDE_CONFIG_DIR" "$W/proj"
cd "$W/proj" && git init -q .
echo "UV_CACHE_DIR=$UV_CACHE_DIR HOME=$HOME CLAUDE_CONFIG_DIR=$CLAUDE_CONFIG_DIR"
echo "claude: $(command -v claude) $(claude --version 2>&1)"
snap() { (cd "$HOME" && find . -type f -printf '%T@ %s %p\n' | sort -k3 | while read -r t s p; do echo "$t $s $(sha256sum "$p" | cut -c1-16) $p"; done); }

echo "===== warm the cache (network allowed)"
uvx --from apm-cli==0.33.0 apm --version 2>&1 | tail -5; echo "--- exit ${PIPESTATUS[0]}"

fail=0
check() {
  local name=$1; shift
  echo "===== $name: $*"
  snap > "$W/$name.before"
  strace -f -qq -e trace=connect -o "$W/$name.strace" "$@" > "$W/$name.out" 2> "$W/$name.err"
  local rc=$?
  snap > "$W/$name.after"
  echo "--- exit $rc"; echo "--- stdout"; cat "$W/$name.out"; echo "--- stderr"; tail -20 "$W/$name.err"
  echo "--- all connect() calls"; cat "$W/$name.strace"
  local net; net=$(grep -cE 'sa_family=AF_INET6?,' "$W/$name.strace")
  echo "--- inet connects: $net"
  echo "--- HOME changes (diff before/after: mtime size sha path)"
  diff "$W/$name.before" "$W/$name.after"; local changed=$?
  echo "SUMMARY $name: exit=$rc inet_connects=$net home_changed=$([ $changed = 0 ] && echo no || echo yes)"
  [ "$rc" = 0 ] && [ "$net" = 0 ] && [ "$changed" = 0 ] || fail=1
}
check uv uv tool run --offline --from apm-cli==0.33.0 apm --version
check claude claude plugin list --json

for p in /home/vscode/.claude/agents /home/vscode/.claude/rules /home/vscode/.claude/skills/audit; do
  [ -e "$p" ] && { echo "REAL HOME TOUCHED: $p"; fail=3; }
done
echo "--- final exit $fail"; exit $fail
