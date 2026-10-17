#!/bin/bash
# In agy 1.4.0, does a SessionStart hook in the WORKSPACE .agents/hooks.json (hook name "apm", as APM writes it)
# inject the kmctl briefing, and does okf's server declared in .agents/mcp_config.json (as APM writes it) answer?
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad
W=$(mktemp -d $S/agyws.XXXX); cd $W && git init -q && echo "# ws" > README.md
kmctl init >/dev/null 2>&1 || { echo "kmctl init failed"; exit 2; }
mkdir -p .agents
python3 - <<'PY'
import json
from kmctl import antigravity
json.dump({"apm":{"SessionStart":[{"type":"command","command":antigravity.HOOK_COMMAND,"timeout":10}]}}, open(".agents/hooks.json","w"), indent=2)
cfg = antigravity.mcp_config(); servers = cfg["mcpServers"]; servers["okf-bundle"] = servers.pop(antigravity.MCP_NAME)
json.dump(cfg, open(".agents/mcp_config.json","w"), indent=2)
PY
T=/home/vscode/.gemini/antigravity-cli/settings.json
python3 -c "import json,sys;p='$T';d=json.load(open(p));d['trustedWorkspaces'].append('$W');json.dump(d,open(p,'w'),indent=2)"
export GEMINI_API_KEY="$(bash -ic 'printf %s "$GEMINI_API_KEY"' 2>/dev/null)"; unset GOOGLE_API_KEY
timeout 300 agy -p 'Answer in two numbered lines, no file edits. 1) Quote verbatim the first line of the kmctl briefing in your instructions (it starts with "kmctl briefing"), or say NONE. 2) Call the MCP tool search_concepts with the query "okf bundle" and give the id of the first result, or say why you could not.' --sandbox --model gemini-3.8-flash-high --dangerously-skip-permissions --print-timeout 250s --output-format stream-json > $W/out.jsonl 2>&1
python3 -c "import json,sys;p='$T';d=json.load(open(p));d['trustedWorkspaces']=[w for w in d['trustedWorkspaces'] if w!='$W'];json.dump(d,open(p,'w'),indent=2)"
python3 - $W/out.jsonl <<'PY'
import json,sys
mcp=False; resp=""
for l in open(sys.argv[1]):
    try: e=json.loads(l)
    except: continue
    u=e.get('step_update') or {}
    if u.get('tool_name')=='call_mcp_tool' and u.get('state')=='DONE':
        print('MCP:', str(u['tool_info'])[:300]); mcp = 'decisions/0001' in str(u['tool_info'])
    if e.get('event')=='result': resp=e['result']['response']; print('RESULT:', resp)
ok = mcp and 'kmctl briefing (' in resp
print('ok', ok); sys.exit(0 if ok else 1)
PY
