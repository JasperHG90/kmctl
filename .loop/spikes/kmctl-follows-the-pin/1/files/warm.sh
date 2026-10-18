#!/usr/bin/env bash
# Does a tag-pinned uvx / uv tool install warm the cache a commit-pinned uvx uses,
# and how long does a cold commit-pinned uvx take? Exit 0 only when both tag
# forms leave the commit form warm (<500 ms) and --offline works after warm-up.
set -u
unset GITHUB_TOKEN GH_TOKEN GITHUB_APM_PAT
SRC=/home/vscode/kmctl
W=$(mktemp -d)
COMMIT=$(git -C "$SRC" rev-list -n1 v0.6.0)
git clone -q --bare "$SRC" "$W/bare.git"
echo "commit=$COMMIT"
echo "bare clone size: $(du -sh "$W/bare.git" | cut -f1)"
printf '[url "file://%s"]\n\tinsteadOf = https://github.com/JasperHG90/kmctl.git\n\tinsteadOf = https://github.com/JasperHG90/kmctl\n' "$W/bare.git" > "$W/gitconfig"
export GIT_CONFIG_GLOBAL="$W/gitconfig" GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0
URL=git+https://github.com/JasperHG90/kmctl
fresh() { export UV_CACHE_DIR="$W/cache$1" UV_TOOL_DIR="$W/tools$1" UV_TOOL_BIN_DIR="$W/bin$1"; }
t() { local s=$(date +%s%N); "$@" >"$W/out" 2>&1; local rc=$?; local ms=$(( ($(date +%s%N)-s)/1000000 )); echo "$ms ms rc=$rc :: $* :: $(tail -1 "$W/out")"; LAST=$ms; LASTRC=$rc; }
fail=0
fresh a
echo "== a) cold commit form"; t uvx --from "$URL@$COMMIT" kmctl --version; COLD=$LAST
echo "== b) warm commit form"; t uvx --from "$URL@$COMMIT" kmctl --version
echo "== e) offline commit form"; t uvx --offline --from "$URL@$COMMIT" kmctl --version; [ $LASTRC = 0 ] || fail=1
fresh c
echo "== c) tag uvx, then commit form"; t uvx --from "$URL@v0.6.0" kmctl --version
t uvx --from "$URL@$COMMIT" kmctl --version; [ $LASTRC = 0 ] && [ $LAST -lt 500 ] || fail=1
t uvx --offline --from "$URL@$COMMIT" kmctl --version
fresh d
echo "== d) uv tool install tag, then commit form"; t uv tool install "$URL@v0.6.0"
t uvx --from "$URL@$COMMIT" kmctl --version; [ $LASTRC = 0 ] && [ $LAST -lt 500 ] || fail=1
t uvx --offline --from "$URL@$COMMIT" kmctl --version
echo "cache sizes: a=$(du -sh "$W/cachea"|cut -f1) c=$(du -sh "$W/cachec"|cut -f1) d=$(du -sh "$W/cached"|cut -f1)"
uv --version
rm -rf "$W"
echo "cold=${COLD}ms fail=$fail"
exit $fail
