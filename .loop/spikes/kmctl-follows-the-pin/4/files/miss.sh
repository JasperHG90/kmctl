#!/usr/bin/env bash
# With a fresh, empty uv cache per case, does `uvx --offline --from git+...@SHA`
# fail fast (<2 s), nonzero, without opening network connections? Cases: source
# unreachable path, source on an unroutable host, the real GitHub URL, and a cache
# warm with another commit. Exit 0 only when every empty-cache case meets the bar.
set -u
unset GITHUB_TOKEN GH_TOKEN GITHUB_APM_PAT
SRC=/home/vscode/kmctl
W=$(mktemp -d)
COMMIT=$(git -C "$SRC" rev-list -n1 v0.6.0)
OTHER=$(git -C "$SRC" rev-list -n1 v0.5.1)
git clone -q --bare "$SRC" "$W/bare.git"
echo "commit=$COMMIT other=$OTHER"
export GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0
gitcfg() { printf '[url "%s"]\n\tinsteadOf = https://github.com/JasperHG90/kmctl.git\n\tinsteadOf = https://github.com/JasperHG90/kmctl\n' "$1" > "$W/gitconfig"; export GIT_CONFIG_GLOBAL="$W/gitconfig"; }
nogitcfg() { : > "$W/gitconfig"; export GIT_CONFIG_GLOBAL="$W/gitconfig"; }
URL=git+https://github.com/JasperHG90/kmctl
FROM="$URL@$COMMIT"
fresh() { export UV_CACHE_DIR="$W/cache$1" UV_TOOL_DIR="$W/tools$1" UV_TOOL_BIN_DIR="$W/bin$1"; }
t() {
  local label=$1; shift
  local s=$(date +%s%N)
  timeout 60 strace -f -qq -e trace=connect,execve -o "$W/trace" "$@" >"$W/out" 2>"$W/err" </dev/null
  local rc=$?; local ms=$(( ($(date +%s%N)-s)/1000000 ))
  local net=$(grep -c 'connect(.*AF_INET' "$W/trace")
  echo "== $label: ${ms} ms rc=$rc inet_connects=$net"
  echo "-- git subcommands run:"; grep -o 'execve("[^"]*/git", \["git", [^]]*' "$W/trace" | sed 's/.*\["git", //' | cut -c1-110 | sort | uniq -c | sort -rn | head -8
  echo "-- inet connect targets:"; grep -o 'sin6\?_addr=[^)]*)' "$W/trace" | sort | uniq -c | head -5
  echo "-- stdout:"; head -2 "$W/out"
  echo "-- stderr:"; head -12 "$W/err"
  LAST=$ms; LASTRC=$rc; LASTNET=$net
}
fail=0
bar() { [ $LASTRC != 0 ] && [ $LAST -lt 2000 ] && [ $LASTNET = 0 ] || { fail=1; echo "!! bar missed"; }; }

fresh A; gitcfg "file://$W/nonexistent.git"
t "A) empty cache, offline, source path missing" uvx --offline --from "$FROM" kmctl --version; bar
fresh B; gitcfg "http://10.255.255.1/kmctl.git"
t "B) empty cache, offline, source on unroutable host" uvx --offline --from "$FROM" kmctl --version; bar
fresh C; nogitcfg
t "C) empty cache, offline, real GitHub URL" uvx --offline --from "$FROM" kmctl --version; bar
fresh C2; nogitcfg
t "C2) empty cache, UV_OFFLINE=1, real GitHub URL" env UV_OFFLINE=1 uvx --from "$FROM" kmctl --version; bar

echo; echo "### cache warm with another commit ($OTHER), not this one"
fresh D; gitcfg "file://$W/bare.git"
t "D0) warm-up other commit, online" uvx --from "$URL@$OTHER" kmctl --version
gitcfg "file://$W/nonexistent.git"
t "D1) offline this commit, source path missing" uvx --offline --from "$FROM" kmctl --version
gitcfg "file://$W/bare.git"
t "D2) offline this commit, source reachable locally" uvx --offline --from "$FROM" kmctl --version
uv --version
echo "fail=$fail"
rm -rf "$W"
exit $fail
