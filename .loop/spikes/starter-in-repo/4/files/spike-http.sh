#!/usr/bin/env bash
# Does uv and APM 0.33.0 follow a git insteadOf rewrite of
# https://github.com/JasperHG90/kmctl to a local smart-HTTP server?
# Run from a checkout of kmctl (cwd). Exit 0 only if (a), (b), (c) all come
# from the local server.
set -u
SRC=$(pwd)
VER=$(sed -n 's/^version: *\([^ #]*\).*/\1/p' "$SRC/apm/apm.yml")
T=$(mktemp -d)
UVC=$(uv cache dir)
unset GITHUB_TOKEN GH_TOKEN GITHUB_APM_PAT GITHUB_COPILOT_PAT ADO_APM_PAT
echo "version=$VER scratch=$T"

# Served copy: committed+untracked files, a marker, tagged v$VER.
mkdir -p "$T/work"
git -C "$SRC" ls-files -z --cached --others --exclude-standard |
  while IFS= read -r -d '' f; do
    [ -f "$SRC/$f" ] && mkdir -p "$T/work/$(dirname "$f")" && cp -p "$SRC/$f" "$T/work/$f"
  done
echo served-copy > "$T/work/src/kmctl/_spike_marker.txt"
git -C "$T/work" init -q -b main
git -C "$T/work" add -A
git -C "$T/work" -c user.email=t@e.invalid -c user.name=t commit -qm tree
git -C "$T/work" tag "v$VER"
SHA=$(git -C "$T/work" rev-parse HEAD)
mkdir -p "$T/srv/o"
git clone -q --bare "$T/work" "$T/srv/o/kmctl.git"
git -C "$T/srv/o/kmctl.git" update-server-info

# Server: the test fixture, with its request log written to a file.
sed 's|"""Keep the request log off stderr."""|sys.stderr.write("REQ %s %s\\n" % (self.command, self.path)); sys.stderr.flush()|' \
  "$SRC/tests/fixtures/githttp.py" > "$T/githttp.py"
PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
python3 -I "$T/githttp.py" "$T/srv" "$PORT" 2>> "$T/server.log" &
SRV=$!
trap 'kill $SRV 2>/dev/null; rm -rf "$T"' EXIT
for _ in $(seq 50); do (exec 3<>/dev/tcp/127.0.0.1/$PORT) 2>/dev/null && break; sleep 0.1; done

# Scratch HOME and git config with the rewrite.
export HOME="$T/home" XDG_DATA_HOME="$T/home/.local/share" XDG_CONFIG_HOME="$T/home/.config" \
  XDG_CACHE_HOME="$T/home/.cache" UV_TOOL_DIR="$T/home/uvtools" UV_TOOL_BIN_DIR="$T/home/bin" \
  UV_CACHE_DIR="$UVC" GIT_CONFIG_GLOBAL="$T/gitconfig" GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0
mkdir -p "$HOME" "$UV_TOOL_BIN_DIR"
B="http://127.0.0.1:$PORT/o/kmctl.git"
git config --global "url.$B.insteadOf" https://github.com/JasperHG90/kmctl.git
git config --global --add "url.$B.insteadOf" https://github.com/JasperHG90/kmctl
git config --global user.email t@e.invalid
git config --global user.name t
echo "--- gitconfig"; cat "$GIT_CONFIG_GLOBAL"
export PATH="$UV_TOOL_BIN_DIR:$PATH"
URL="git+https://github.com/JasperHG90/kmctl@v$VER"
ok=0

mark() { echo "REQ-MARK $1" >> "$T/server.log"; }

echo "=== (a) uv tool install"
mark a
if uv tool install --force --refresh "$URL" && kmctl --version &&
   m=$(find "$UV_TOOL_DIR" -name _spike_marker.txt | head -1) && [ -n "$m" ]; then
  echo "(a) PASS marker=$m"
else echo "(a) FAIL"; ok=1; fi

echo "=== (b) uvx --from"
mark b
if uvx --refresh --from "$URL" kmctl --version &&
   uvx --from "$URL" python -c 'import kmctl,pathlib;print((pathlib.Path(kmctl.__file__).parent/"_spike_marker.txt").read_text().strip())' | grep -qx served-copy; then
  echo "(b) PASS marker found"
else echo "(b) FAIL"; ok=1; fi

echo "=== (c) apm install"
mark c
C="$T/consumer"; mkdir -p "$C"; git -C "$C" init -q -b main
cat > "$C/apm.yml" <<EOF
name: consumer
version: 0.0.1
targets: [claude]
dependencies:
  apm:
    - git: https://github.com/JasperHG90/kmctl.git
      path: apm
      ref: v$VER
EOF
( cd "$C" && uvx --from apm-cli==0.33.0 apm install ); rc=$?
echo "apm rc=$rc"
echo "--- apm.lock.yaml"; cat "$C/apm.lock.yaml" 2>/dev/null | grep -v -i token
echo "served sha=$SHA"
if [ $rc -eq 0 ] && grep -q "$SHA" "$C/apm.lock.yaml" 2>/dev/null; then
  echo "(c) PASS lock holds served sha"
else echo "(c) FAIL"; ok=1; fi

echo "--- server request log"
grep -E '^REQ' "$T/server.log" | sed 's/\?.*//' | sort | uniq -c
echo "result=$ok"
exit $ok
