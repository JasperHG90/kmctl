#!/bin/bash
# Does apm uninstall of kmctl's entry, then kmctl plugin install for the harnesses kept, leave
# nothing of the removed harness from APM and the kept harness whole?
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad
URL=http://127.0.0.1:18765/o/kmctl.git
W=$(mktemp -d $S/spike-remove3.XXXX); CACHE=${UV_CACHE_DIR:-$HOME/.cache/uv}
mkdir -p $W/tools; for t in uv uvx git; do ln -s "$(command -v $t)" $W/tools/$t; done; ln -s $S/live/tools/kmctl $W/tools/kmctl
export UV_CACHE_DIR=$CACHE HOME=$W/home CLAUDE_CONFIG_DIR=$W/home/.claude XDG_DATA_HOME=$W/home/.local/share PATH=$W/tools:/usr/bin:/bin
mkdir -p $CLAUDE_CONFIG_DIR $W/c && cd $W/c && git init -q && echo keep > README.md
apmfiles() { find .claude/skills .claude/agents .claude/rules .claude/hooks .agents/skills .agents/rules .agents/hooks -type f 2>/dev/null | sort; }
kmctl plugin install --harness claude,antigravity --source $URL >/dev/null || { echo install failed; exit 2; }
echo "installed: $(apmfiles | wc -l) APM files"
uvx --from apm-cli==0.33.0 apm uninstall 127.0.0.1:18765/o/kmctl/apm > un.txt 2>&1; rc=$?
echo "uninstall rc=$rc"; left=$(apmfiles); echo "APM files left: ${left:-none}"
hj=$(cat .agents/hooks.json 2>/dev/null || echo absent); echo ".agents/hooks.json: $hj"; [ -f apm.lock.yaml ] && echo "lock remains" || echo "no lock"
ok1=0; [ $rc = 0 ] && [ -z "$left" ] && [ ! -f apm.lock.yaml ] && { [ "$hj" = absent ] || [ "$(echo $hj | tr -d ' \n')" = "{}" ]; } && ok1=1
kmctl plugin install --harness claude --source $URL > re.txt 2>&1 || { echo reinstall failed; cat re.txt; exit 3; }
ag=$(find .agents/skills .agents/rules .agents/hooks -type f 2>/dev/null); cl=$(find .claude/skills -name SKILL.md | wc -l)
echo "after reinstall for claude: .agents APM files: ${ag:-none}; claude skills: $cl"
grep -o "^targets:.*\|^  - [a-z]*$" apm.yml | head -4
lockag=$(grep -c "\.agents/" apm.lock.yaml); echo "lock .agents paths: $lockag"
[ $ok1 = 1 ] && [ -z "$ag" ] && [ "$cl" -ge 11 ] && [ "$lockag" = 0 ]
