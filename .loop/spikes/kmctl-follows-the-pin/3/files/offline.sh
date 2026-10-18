#!/usr/bin/env bash
# Does `uvx --offline --from git+...@SHA` with an empty cache fail fast (<2 s),
# nonzero, without touching the network, and in a way kmctl can tell apart from
# the pinned command itself failing? Exit 0 only when all bars hold.
set -u
unset GITHUB_TOKEN GH_TOKEN GITHUB_APM_PAT
SRC=/home/vscode/kmctl
W=$(mktemp -d)
COMMIT=$(git -C "$SRC" rev-list -n1 v0.6.0)
git clone -q --bare "$SRC" "$W/bare.git"
echo "commit=$COMMIT"
gitcfg() { printf '[url "file://%s"]\n\tinsteadOf = https://github.com/JasperHG90/kmctl.git\n\tinsteadOf = https://github.com/JasperHG90/kmctl\n' "$1" > "$W/gitconfig"; }
gitcfg "$W/bare.git"
export GIT_CONFIG_GLOBAL="$W/gitconfig" GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0
URL=git+https://github.com/JasperHG90/kmctl
FROM="$URL@$COMMIT"
fresh() { export UV_CACHE_DIR="$W/cache$1" UV_TOOL_DIR="$W/tools$1" UV_TOOL_BIN_DIR="$W/bin$1"; }
# t LABEL CMD...: run under strace, print time, rc, stderr, network connects and git execs
t() {
  local label=$1; shift
  local s=$(date +%s%N)
  strace -f -qq -e trace=connect,execve -o "$W/trace" "$@" >"$W/out" 2>"$W/err" </dev/null
  local rc=$?; local ms=$(( ($(date +%s%N)-s)/1000000 ))
  local net=$(grep -c 'connect(.*AF_INET' "$W/trace"); local gits=$(grep -c 'execve("[^"]*/git"' "$W/trace")
  echo "== $label: ${ms} ms rc=$rc inet_connects=$net git_execs=$gits"
  echo "-- stdout (first 3 lines):"; head -3 "$W/out"
  echo "-- stderr:"; cat "$W/err"
  LAST=$ms; LASTRC=$rc; LASTNET=$net; LASTGIT=$gits
}
fail=0
fresh a
t "a1) empty cache, offline --version" uvx --offline --from "$FROM" kmctl --version
[ $LASTRC != 0 ] && [ $LAST -lt 2000 ] && [ $LASTNET = 0 ] || fail=1
MISSRC=$LASTRC
gitcfg "$W/nonexistent.git"
t "a2) empty cache, offline, bare clone unreachable" uvx --offline --from "$FROM" kmctl --version
[ $LASTRC != 0 ] && [ $LAST -lt 2000 ] && [ $LASTNET = 0 ] || fail=1
t "a3) empty cache, uv tool run --offline, bare clone unreachable" uv tool run --offline --from "$FROM" kmctl --version
t "a4) empty cache, offline -q" uvx -q --offline --from "$FROM" kmctl --version
t "a5) control: empty cache, ONLINE, bare clone unreachable" uvx --from "$FROM" kmctl --version
ls "$UV_CACHE_DIR" 2>/dev/null | sed 's/^/cache entry after misses: /'
gitcfg "$W/bare.git"
t "b0) warm-up, online" uvx --from "$FROM" kmctl --version
gitcfg "$W/nonexistent.git"
t "b1) warm, offline --version, bare clone unreachable" uvx --offline --from "$FROM" kmctl --version
[ $LASTRC = 0 ] || fail=1
E=$(mktemp -d)
t "c1) warm, offline briefing --format text in empty dir" bash -c "cd '$E' && uvx --offline --from '$FROM' kmctl briefing --format text"
t "c2) warm, offline kmctl nosuchcommand" uvx --offline --from "$FROM" kmctl nosuchcommand
[ $LASTRC = 2 ] || fail=1
t "c3) warm, offline kmctl --help" uvx --offline --from "$FROM" kmctl --help
t "c4) child exits 7 via python -c" uvx --offline --from "$FROM" python -c 'import sys; sys.exit(7)'
t "c5) child exits 1" uvx --offline --from "$FROM" python -c 'import sys; sys.exit(1)'
t "c6) child exits 2" uvx --offline --from "$FROM" python -c 'import sys; sys.exit(2)'
uv --version
echo "miss_rc=$MISSRC fail=$fail"
rm -rf "$W" "$E"
exit $fail
