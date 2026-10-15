#!/usr/bin/env bash
# At project scope, does `claude plugin install` pull the cross-marketplace
# okf dependency, is a second run a no-op, and does the project's
# .claude/settings.json carry both marketplaces and plugins for a teammate?
# Exit 0 only if okf installs at project scope, later runs leave the
# settings content and plugin list unchanged (key order may differ), and settings.json declares both marketplaces and both plugins.
set -u
work=$(mktemp -d)
export CLAUDE_CONFIG_DIR="$work/config"
mkdir -p "$CLAUDE_CONFIG_DIR"
mkt="$work/mkt"
mkdir -p "$mkt/.claude-plugin" "$mkt/tiny/.claude-plugin" "$work/proj"
cat > "$mkt/.claude-plugin/marketplace.json" <<'J'
{
  "name": "spike-mkt",
  "owner": {"name": "spike"},
  "allowCrossMarketplaceDependenciesOn": ["scaccogatto"],
  "plugins": [
    {"name": "tiny", "source": "./tiny",
     "dependencies": [{"name": "okf", "marketplace": "scaccogatto"}]}
  ]
}
J
echo '{"name": "tiny", "version": "0.0.1"}' > "$mkt/tiny/.claude-plugin/plugin.json"
cd "$work/proj"
git init -q . && git -c user.email=s@s -c user.name=s commit -q --allow-empty -m init
echo "CLAUDE_CONFIG_DIR=$CLAUDE_CONFIG_DIR"

run() { echo "== $*"; "$@" 2>&1; echo "exit $?"; }
snap() {
  { cat .claude/settings.json 2>/dev/null; echo ---;
    cat .claude/settings.local.json 2>/dev/null; echo ---;
    cat "$CLAUDE_CONFIG_DIR/settings.json" 2>/dev/null; echo ---;
    claude plugin list --json 2>&1; echo ---;
    claude plugin marketplace list --json 2>&1; } > "$1"
}

echo "##### (a) first run, everything at project scope"
run claude plugin marketplace add "$mkt" --scope project
run claude plugin marketplace add scaccogatto/okf-skills --scope project
run claude plugin install tiny@spike-mkt --scope project
run claude plugin list --json
run claude plugin marketplace list --json
okf=0
claude plugin list --json 2>&1 | grep -q '"okf@scaccogatto"' && okf=1
claude plugin list --json 2>&1 | python3 -c '
import json,sys
for p in json.load(sys.stdin):
    if p.get("id") == "okf@scaccogatto" and p.get("scope") != "project":
        print("okf scope is", p.get("scope")); sys.exit(1)
' || okf=0
echo "okf installed at project scope: $okf"
snap "$work/snap1"

echo "##### (b) second and third run, same commands"
again() {
  run claude plugin marketplace add "$mkt" --scope project
  run claude plugin marketplace add scaccogatto/okf-skills --scope project
  run claude plugin install tiny@spike-mkt --scope project
}
cp .claude/settings.json "$work/settings1"
again; snap "$work/snap2"; cp .claude/settings.json "$work/settings2"
again; snap "$work/snap3"; cp .claude/settings.json "$work/settings3"
echo "-- run 1 vs run 2, whole snapshot, bytes"; diff -u "$work/snap1" "$work/snap2"
echo "-- run 2 vs run 3, whole snapshot, bytes"; diff -u "$work/snap2" "$work/snap3"
same=0
python3 - "$work/settings1" "$work/settings2" "$work/settings3" <<'Q' && same=1
import json, sys
a, b, c = (json.load(open(f)) for f in sys.argv[1:])
print("settings content equal across runs 1-3:", a == b == c)
sys.exit(0 if a == b == c else 1)
Q
cmp -s "$work/settings2" "$work/settings3" && echo "settings.json bytes stable from run 2 to 3: yes" || echo "settings.json bytes stable from run 2 to 3: no"
cmp -s "$work/snap1" "$work/snap2" && echo "snapshot bytes equal run 1 to 2: yes" || echo "snapshot bytes equal run 1 to 2: no"
echo "second run changed nothing (content): $same"

echo "##### (c) what the project's settings files hold"
echo "-- .claude/settings.json"; cat .claude/settings.json 2>&1
echo "-- .claude/settings.local.json"; cat .claude/settings.local.json 2>&1
echo "-- user settings.json"; cat "$CLAUDE_CONFIG_DIR/settings.json" 2>&1
echo "-- git status"; git status --short
declared=0
python3 - .claude/settings.json <<'P' && declared=1
import json, sys
s = json.load(open(sys.argv[1]))
m = s.get("extraKnownMarketplaces", {})
e = s.get("enabledPlugins", {})
print("marketplaces:", sorted(m), "enabled:", sorted(e))
ok = {"spike-mkt", "scaccogatto"} <= set(m) and \
     e.get("tiny@spike-mkt") is True and e.get("okf@scaccogatto") is True
sys.exit(0 if ok else 1)
P
echo "settings.json declares both marketplaces and both plugins: $declared"

echo "##### teammate: clone with a fresh config dir"
git add -A && git -c user.email=s@s -c user.name=s commit -q -m settings
git clone -q "$work/proj" "$work/clone"
export CLAUDE_CONFIG_DIR="$work/config2"; mkdir -p "$CLAUDE_CONFIG_DIR"
cd "$work/clone"
run claude plugin marketplace list --json
run claude plugin list --json
echo "##### done"
[ "$okf" = 1 ] && [ "$same" = 1 ] && [ "$declared" = 1 ]
