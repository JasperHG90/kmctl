#!/bin/bash
# Which name does apm 0.33.0 uninstall accept for kmctl's entry installed from GitHub?
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad
W=$(mktemp -d $S/spike-remove4.XXXX); CACHE=${UV_CACHE_DIR:-$HOME/.cache/uv}
export UV_CACHE_DIR=$CACHE HOME=$W/home CLAUDE_CONFIG_DIR=$W/home/.claude XDG_DATA_HOME=$W/home/.local/share
mkdir -p $CLAUDE_CONFIG_DIR $W/c && cd $W/c && git init -q
APM="uvx --from apm-cli==0.33.0 apm"
cat > apm.yml <<'Y'
name: c
version: 0.0.1
dependencies:
  apm:
    - git: https://github.com/JasperHG90/Knowledge-management.git
      path: apm
      ref: v0.3.0
targets:
  - claude
Y
$APM install --target claude > in.txt 2>&1 || { echo install failed; tail -5 in.txt; exit 2; }
echo "lock entry:"; grep -E "repo_url|host|port|virtual_path|resolved_ref" apm.lock.yaml | head -12
echo "deps list:"; $APM deps list 2>&1 | grep -i knowledge | head -3
for name in "github.com/JasperHG90/Knowledge-management/apm" "JasperHG90/Knowledge-management/apm"; do
  cp apm.yml apm.yml.bak; cp apm.lock.yaml lock.bak
  out=$($APM uninstall --dry-run "$name" 2>&1); rc=$?
  echo "== $name: dry-run rc=$rc"; echo "$out" | grep -iE "not found|remov|would" | head -3
done
$APM uninstall "github.com/JasperHG90/Knowledge-management/apm" > un.txt 2>&1; rc=$?
echo "real uninstall rc=$rc"; tail -3 un.txt
left=$(find .claude -type f 2>/dev/null | wc -l); echo "files left: $left"
[ $rc = 0 ] && [ $left = 0 ] && ! grep -q Knowledge apm.yml
