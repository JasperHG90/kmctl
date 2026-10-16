#!/usr/bin/env bash
# Does hatchling's regex version source, reading plugin/.claude-plugin/plugin.json,
# give 0.2.0 on every kmctl install path? Exit 0 only when every path prints 0.2.0.
set -u
W=$(mktemp -d)
export UV_TOOL_DIR="$W/tools" UV_TOOL_BIN_DIR="$W/bin"
fail=0
check() { # name, got
  if [ "$2" = "0.2.0" ] || echo "$2" | grep -q '0\.2\.0'; then echo "PASS $1: $2"; else echo "FAIL $1: $2"; fail=1; fi
}

git clone -q /home/vscode/kmctl "$W/repo"
cd "$W/repo"
python3 - <<'EOF'
import re, pathlib
p = pathlib.Path("pyproject.toml"); t = p.read_text()
t = t.replace('version = "0.1.0"\n', 'dynamic = ["version"]\n', 1)
t = t.replace('[tool.hatch.build.targets.wheel]',
  '[tool.hatch.version]\nsource = "regex"\npath = "plugin/.claude-plugin/plugin.json"\n'
  'pattern = \'"version": "(?P<version>[^"]+)"\'\n\n[tool.hatch.build.targets.wheel]', 1)
p.write_text(t)
m = pathlib.Path("plugin/.claude-plugin/plugin.json")
m.write_text(m.read_text().replace('"version": "0.1.0"', '"version": "0.2.0"', 1))
EOF
git diff --stat
git -c user.name=s -c user.email=s@s commit -qam "version from manifest" && git tag v0.2.0

echo "== (a) uv build"
uv build -q -o "$W/dist" . 2>&1 | tail -3
ls "$W/dist"
whl=$(ls "$W/dist"/*.whl 2>/dev/null | head -1); sd=$(ls "$W/dist"/*.tar.gz 2>/dev/null | head -1)
check "wheel name" "$(basename "$whl")"
check "sdist name" "$(basename "$sd")"
echo "-- sdist holds manifest:"; tar tzf "$sd" | grep 'plugin/.claude-plugin/plugin.json' || { echo "FAIL sdist missing plugin.json"; fail=1; }
uv tool install -q "$whl" && check "wheel install --version" "$("$UV_TOOL_BIN_DIR/kmctl" --version 2>&1)"
uv tool uninstall -q kmctl

echo "== (a2) build wheel from sdist"
mkdir "$W/sx" && tar xzf "$sd" -C "$W/sx"
uv build -q --wheel -o "$W/dist2" "$W/sx"/kmctl-*/ 2>&1 | tail -3
check "wheel from sdist" "$(ls "$W/dist2")"

echo "== (b) git+file bare remote at tag"
git clone -q --bare "$W/repo" "$W/remote.git"
uv tool install -q "git+file://$W/remote.git@v0.2.0" && check "git tag install --version" "$("$UV_TOOL_BIN_DIR/kmctl" --version 2>&1)"
uv tool uninstall -q kmctl

echo "== (c) git archive folder, no .git"
mkdir "$W/arch" && git archive v0.2.0 | tar x -C "$W/arch"
test -e "$W/arch/.git" && echo "unexpected .git"
uv tool install -q "$W/arch" && check "archive folder install --version" "$("$UV_TOOL_BIN_DIR/kmctl" --version 2>&1)"
uv tool uninstall -q kmctl

echo "fail=$fail"
exit $fail
