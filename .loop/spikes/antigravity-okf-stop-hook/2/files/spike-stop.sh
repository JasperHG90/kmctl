#!/bin/bash
# In agy 1.4.0, does a plugin Stop hook that turns okf's "block" into "continue" re-enter the loop once, with executionNum telling the second stop apart?
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad
P=$S/live/tempconv; cd $P
git checkout -q -- . && git clean -qfd -e apm_modules
export PATH=$S/live/tools:$PATH GEMINI_API_KEY="$(bash -ic 'printf %s "$GEMINI_API_KEY"' 2>/dev/null)"; unset GOOGLE_API_KEY
# opt the bundle in and leave a tracked change outside .okf/
sed -i '0,/^---$/!{0,/^---$/s/^---$/upkeep: enforced\n---/}' .okf/index.md; git -c user.email=t@e.invalid -c user.name=t commit -qam "upkeep enforced"
echo "# changed" >> README.md
LOG=$S/stop-calls.log; : > $LOG
python3 - "$LOG" <<'PY'
import json,sys
log=sys.argv[1]
cmd=("in=$(cat); printf '%s\\n' \"$in\" >> " + log + "; "
     "printf '%s' \"$in\" | grep -Eq '\"executionNum\"[[:space:]]*:[[:space:]]*0[^0-9]' || { echo '{}'; exit 0; }; "
     "cd ../../.. 2>/dev/null || { echo '{}'; exit 0; }; "
     "out=$(printf '{}' | bash .agents/hooks/okf-skills/hooks/okf-stop-check.sh 2>/dev/null); "
     "[ -n \"$out\" ] || { echo '{}'; exit 0; }; "
     "printf '%s\\n' \"$out\" | sed 's/\"decision\":\"block\"/\"decision\":\"continue\"/'")
p='.agents/plugins/kmctl/hooks.json'
d=json.load(open(p)); d['kmctl-okf-stop']={'Stop':[{'type':'command','command':cmd,'timeout':15}]}
json.dump(d,open(p,'w'),indent=2)
PY
timeout 300 agy -p "Reply with the single word ready." --model gemini-3.8-flash-high --dangerously-skip-permissions --print-timeout 250s --output-format stream-json > $S/stop-run.jsonl 2>&1
echo "stop hook calls: $(wc -l < $LOG)"; cut -c1-300 $LOG
python3 - $S/stop-run.jsonl <<'PY'
import json,sys
for l in open(sys.argv[1]):
    try: e=json.loads(l)
    except: continue
    u=e.get('step_update') or {}
    if u.get('state')=='DONE' and u.get('step_type')!='agent_response' or e.get('event')=='result': print(str(u or e)[:300])
PY
n=$(wc -l < $LOG); git checkout -q -- . ; git reset -q --hard HEAD~1
[ "$n" -ge 2 ] && grep -q '"executionNum": *1[^0-9]\|"executionNum":1[^0-9]' $LOG
