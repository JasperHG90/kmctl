#!/usr/bin/env bash
# Does `claude plugin install` pull a cross-marketplace dependency when the
# dependency's marketplace (scaccogatto) has not been added?
# Exit 0 only if attempt A (scaccogatto not added) installs okf too.
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
echo "CLAUDE_CONFIG_DIR=$CLAUDE_CONFIG_DIR"
echo "== add local marketplace"; claude plugin marketplace add "$mkt" 2>&1; echo "exit $?"
echo "== marketplaces"; claude plugin marketplace list 2>&1
echo "== A: install tiny, scaccogatto NOT added"; claude plugin install tiny@spike-mkt --scope user 2>&1; a=$?; echo "exit $a"
echo "== list after A"; claude plugin list 2>&1
echo "== marketplaces after A"; claude plugin marketplace list 2>&1
okf_a=0; claude plugin list 2>&1 | grep -q 'okf@scaccogatto' && okf_a=1
echo "okf installed after A: $okf_a"
echo "== uninstall tiny (if present)"; claude plugin uninstall tiny@spike-mkt --scope user 2>&1; echo "exit $?"
echo "== add scaccogatto"; claude plugin marketplace add scaccogatto/okf-skills 2>&1; echo "exit $?"
echo "== list after marketplace add"; claude plugin list 2>&1
echo "== B: install tiny, scaccogatto added"; claude plugin install tiny@spike-mkt --scope user 2>&1; echo "exit $?"
echo "== list after B"; claude plugin list 2>&1
echo "== B2: reinstall (idempotence)"; claude plugin install tiny@spike-mkt --scope user 2>&1; echo "exit $?"
echo "== real config untouched check"; ls "$CLAUDE_CONFIG_DIR"
[ "$a" = 0 ] && [ "$okf_a" = 1 ]
