#!/usr/bin/env bash
# Risk 4 (apm-only-install), plan review finding p2 (old claude-plugin users).
# In a scratch repo, install the old way (kmctl plugin install --scope project,
# today's code), then `claude plugin uninstall kmctl@kmctl --scope project`.
# Is okf@scaccogatto still installed/enabled? What stays in .claude/settings.json
# and the marketplace list? Then uninstall okf@scaccogatto and remove the kmctl
# marketplace. Exit 0 only when, after those three commands, no kmctl or okf
# plugin is enabled for the repo.
set -u
KM=$(git rev-parse --show-toplevel)
SCR=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-migrate
mkdir -p "$SCR"; W=$(mktemp -d "$SCR/p2.XXXX")
export UV_CACHE_DIR="${UV_CACHE_DIR:-$(uv cache dir)}" UV_PYTHON_INSTALL_DIR="$(uv python dir)"
CLAUDE=$(command -v claude)
REAL=/home/vscode/.claude
IP_BEFORE=$(sha256sum "$REAL/plugins/installed_plugins.json" 2>/dev/null || echo none)
export HOME="$W/home" CLAUDE_CONFIG_DIR="$W/home/.claude" XDG_DATA_HOME="$W/home/.local/share"
mkdir -p "$CLAUDE_CONFIG_DIR"
git config --global user.email spike@example.invalid
git config --global user.name spike
git config --global init.defaultBranch main
echo "== kmctl HEAD $(git -C "$KM" rev-parse HEAD); claude $("$CLAUDE" --version)"
R="$W/repo"; mkdir "$R"; (cd "$R" && git init -q && git commit -q --allow-empty -m init)
cd "$R"
state() {
  echo "-- claude plugin list --json (from repo):"
  "$CLAUDE" plugin list --json 2>&1 | uv run -q --no-project python -I -c '
import json, sys
t = sys.stdin.read()
try: d = json.loads(t)
except Exception: print("   unparsed:", t[:400]); sys.exit()
d = d if isinstance(d, list) else d.get("plugins", d)
for p in d: print("  ", json.dumps({k: p.get(k) for k in ("id", "scope", "enabled", "version", "projectPath")}))
if not d: print("   (none)")'
  echo "-- .claude/settings.json:"; cat "$R/.claude/settings.json" 2>/dev/null | sed 's/^/   /' || echo "   (missing)"
  echo "-- claude plugin marketplace list --json:"
  "$CLAUDE" plugin marketplace list --json 2>&1 | head -c 1500 | sed 's/^/   /'; echo
}
enabled_any() {  # exit 0 when kmctl or okf is enabled for the repo
  "$CLAUDE" plugin list --json 2>/dev/null | uv run -q --no-project python -I -c '
import json, sys
d = json.load(sys.stdin); d = d if isinstance(d, list) else d.get("plugins", d)
hit = [p.get("id") for p in d if p.get("enabled") and p.get("id") in ("kmctl@kmctl", "okf@scaccogatto")]
print("   enabled kmctl/okf per plugin list:", hit); sys.exit(0 if hit else 1)'
  local a=$?
  uv run -q --no-project python -I -c '
import json, sys, pathlib
p = pathlib.Path(sys.argv[1])
e = json.loads(p.read_text()).get("enabledPlugins", {}) if p.exists() else {}
hit = [k for k, v in e.items() if v and k in ("kmctl@kmctl", "okf@scaccogatto")]
print("   enabled kmctl/okf per settings.json enabledPlugins:", hit); sys.exit(0 if hit else 1)' "$R/.claude/settings.json"
  local b=$?
  [ $a = 0 ] || [ $b = 0 ]
}

echo "######## 1. old install: kmctl plugin install --scope project"
uv run -q --project "$KM" kmctl plugin install --scope project; echo "== exit $?"
state
echo "######## 2. claude plugin uninstall kmctl@kmctl --scope project"
"$CLAUDE" plugin uninstall kmctl@kmctl --scope project; echo "== exit $?"
state
echo "######## 3. claude plugin uninstall okf@scaccogatto --scope project"
"$CLAUDE" plugin uninstall okf@scaccogatto --scope project; echo "== exit $?"
echo "######## 4. claude plugin marketplace remove kmctl"
"$CLAUDE" plugin marketplace remove kmctl; echo "== exit $?"
state
enabled_any; E=$?   # 0 means something still enabled

SAFE=0
for p in "$REAL/agents" "$REAL/rules" "$REAL/skills/audit"; do [ -e "$p" ] && { echo "   REAL $p EXISTS"; SAFE=1; }; done
IP_AFTER=$(sha256sum "$REAL/plugins/installed_plugins.json" 2>/dev/null || echo none)
[ "$IP_BEFORE" = "$IP_AFTER" ] || { echo "   REAL installed_plugins.json CHANGED"; SAFE=1; }
echo "== RESULT: kmctl/okf still enabled=$([ $E = 0 ] && echo yes || echo no); real ~/.claude untouched=$([ $SAFE = 0 ] && echo yes || echo NO)"
[ $E != 0 ] && [ $SAFE = 0 ]
