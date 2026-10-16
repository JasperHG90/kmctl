# Shared setup for the apm-distribution spikes. Sourced, not run.
# - APM 0.33.0 from pip in a throwaway venv, isolated HOME.
# - Source packages are published as bare git repos served over plain HTTP on
#   127.0.0.1 by git http-backend (githttp.py). APM 0.33.0 rejects file:// git
#   URLs and its shallow clone fails on dumb HTTP; smart HTTP keeps the git +
#   `path:` subdirectory route a GitHub install would use.
set -u
KM=$(git rev-parse --show-toplevel)
export UV_CACHE_DIR="${UV_CACHE_DIR:-$HOME/.cache/uv}"
W=$(mktemp -d)
export HOME="$W/home"; mkdir -p "$HOME"
git config --global user.email spike@example.invalid
git config --global user.name spike
git config --global init.defaultBranch main
echo "== kmctl HEAD: $(git -C "$KM" rev-parse HEAD)"
uv venv -q "$W/venv" && VIRTUAL_ENV="$W/venv" uv pip install -q apm-cli==0.33.0 || exit 3
APM="$W/venv/bin/apm"; "$APM" --version

mkdir -p "$W/srv/o"
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/githttp.py "$W/srv" "$PORT" >/dev/null 2>&1 &
SRV=$!
trap 'kill "$SRV" 2>/dev/null; rm -rf "$W"' EXIT
sleep 1
GIT="http://127.0.0.1:$PORT/o"

# new_src NAME: a work tree at $W/NAME holding a copy of kmctl's plugin/.
new_src() { rm -rf "$W/$1"; mkdir "$W/$1"; cp -r "$KM/plugin" "$W/$1/plugin"; }

# publish NAME: commit $W/NAME and serve it as $GIT/NAME.git.
publish() {
  ( cd "$W/$1" && git init -q && git add -A && git commit -qm "$1" )
  rm -rf "$W/srv/o/$1.git"
  git clone -q --bare "$W/$1" "$W/srv/o/$1.git" && git -C "$W/srv/o/$1.git" update-server-info
}

# consumer NAME DEPLINES...: a fresh git repo at $W/c-NAME whose apm.yml lists
# DEPLINES (already-indented YAML) under dependencies.apm; runs apm install.
consumer() {
  local n=$1; shift
  rm -rf "$W/c-$n"; mkdir "$W/c-$n"; ( cd "$W/c-$n" && git init -q )
  { echo "name: c-$n"; echo "version: 0.1.0"; echo "targets: [claude]"
    echo "dependencies:"; echo "  apm:"; printf '%s\n' "$@"; } > "$W/c-$n/apm.yml"
  ( cd "$W/c-$n" && "$APM" install --allow-insecure > "$W/c-$n.log" 2>&1 ); CEXIT=$?
  echo "-- consumer $n: apm install exit $CEXIT"
  if [ "$CEXIT" != 0 ]; then grep -A3 -E '\[x\]' "$W/c-$n.log" | head -12; fi
}

# files NAME: the files apm wrote in consumer NAME (not .git, apm_modules).
files() {
  ( cd "$W/c-$1" && find . -path ./.git -prune -o -path ./apm_modules -prune -o -type f -print | sort | grep -v -E '^\./(apm\.yml|apm\.lock\.yaml|\.gitignore)$' )
}
