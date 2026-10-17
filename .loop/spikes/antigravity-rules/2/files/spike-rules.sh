#!/bin/bash
# Does deleting APM-deployed kmctl rules from .agents/rules/ break a later apm install or apm uninstall?
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad
W=$(mktemp -d $S/spike-rules.XXXX); export UV_CACHE_DIR=${UV_CACHE_DIR:-$HOME/.cache/uv}
export HOME=$W/home CLAUDE_CONFIG_DIR=$W/home/.claude XDG_DATA_HOME=$W/home/.local/share; mkdir -p $CLAUDE_CONFIG_DIR
git clone -q $S/live/tempconv $W/p && cd $W/p
APM="uvx --from apm-cli==0.33.0 apm"
rules() { ls .agents/rules/ 2>/dev/null | tr '\n' ' '; echo; }
cp -r $S/live/tempconv/apm_modules . 
echo "before: $(rules)"
rm -f .agents/rules/{okf-bundle,docs-layout,diagrams-stay-current,manifesto-invariants}.md
echo "deleted: $(rules)"
$APM install --target claude,antigravity --allow-insecure > out1.txt 2>&1; rc1=$?
echo "apm install rc=$rc1; skip lines: $(grep -ci "local files exist" out1.txt)"; echo "after install: $(rules)"
rm -f .agents/rules/{okf-bundle,docs-layout,diagrams-stay-current,manifesto-invariants}.md
$APM uninstall 127.0.0.1:18765/o/kmctl/apm > out2.txt 2>&1; rc2=$?
echo "apm uninstall rc=$rc2"; tail -5 out2.txt
left=$(find .claude/skills .claude/rules .agents/skills .agents/rules -type f 2>/dev/null | wc -l); echo "left files: $left"; ls apm.lock.yaml 2>&1
[ $rc1 = 0 ] && [ $rc2 = 0 ] && [ "$(grep -ci "local files exist" out1.txt)" = 0 ] && [ $left = 0 ]
