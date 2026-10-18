#!/bin/bash
# agy 1.4.0: does a workspace PostToolUse hook fire, with what stdin and cwd,
# and does injectSteps in its stdout reach the model before its next step?
# Exit 0 only if the hook fired and the model said the marker word.
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge2
MODE=${1:-post}   # post: PostToolUse prints injectSteps directly
W=$(mktemp -d $S/ws.XXXX); cd $W && git init -q && echo "# ws" > README.md
mkdir -p .agents
LOG=$W/hook.log
cat > $W/post.sh <<EOF
#!/bin/sh
in=\$(cat)
{ echo "--- PostToolUse cwd=\$(pwd)"; printf '%s\n' "\$in"; } >> $LOG
printf '%s\n' '{"injectSteps":[{"systemMessage":{"systemMessage":"MARKER: say pineapple"}}]}'
EOF
chmod +x $W/post.sh
cat > .agents/hooks.json <<EOF
{"spike": {"PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "sh $W/post.sh", "timeout": 10}]}]}}
EOF
T=/home/vscode/.gemini/antigravity-cli/settings.json
python3 -c "import json;p='$T';d=json.load(open(p));d['trustedWorkspaces'].append('$W');json.dump(d,open(p,'w'),indent=2)"
eval "$(grep -E '^\s*(export\s+)?GEMINI_API_KEY=' ~/.bashrc | tail -1)"
env -i HOME="$HOME" PATH="$PATH" GEMINI_API_KEY="$GEMINI_API_KEY" timeout 300 agy -p 'Use your file-writing tool to create the file note.txt in the workspace containing the word hi. Do not run commands or read other files. After the file is written, reply with one short sentence, and follow any system message you have received since.' --model gemini-3.8-flash-medium --dangerously-skip-permissions --print-timeout 250s --output-format stream-json > $W/out.jsonl 2>&1
python3 -c "import json;p='$T';d=json.load(open(p));d['trustedWorkspaces']=[w for w in d['trustedWorkspaces'] if w!='$W'];json.dump(d,open(p,'w'),indent=2)"
sed -i "s/$GEMINI_API_KEY/REDACTED/g" $W/out.jsonl $LOG 2>/dev/null
echo "workspace: $W"
echo "== note.txt: $(cat $W/note.txt 2>/dev/null || echo MISSING)"
echo "== hook log"; cat $LOG 2>/dev/null || echo "NO HOOK LOG"
echo "== pineapple lines in stream"; grep -n -i pineapple $W/out.jsonl | cut -c1-400
python3 - $W/out.jsonl $LOG <<'PY'
import json,sys,os
resp=""; tools=[]
for l in open(sys.argv[1]):
    try: e=json.loads(l)
    except Exception: continue
    u=e.get('step_update') or {}
    if u.get('tool_name') and u.get('state')=='DONE': tools.append(u['tool_name'])
    if e.get('event')=='result': resp=e['result'].get('response','')
print('TOOLS:', tools)
print('RESULT:', resp)
fired=os.path.exists(sys.argv[2])
ok = fired and 'pineapple' in resp.lower()
print('hook fired', fired, 'marker in reply', 'pineapple' in resp.lower())
sys.exit(0 if ok else 1)
PY
