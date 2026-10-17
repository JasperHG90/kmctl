#!/bin/bash
# With a consumer already holding kmctl-written pieces (SessionStart hook in .claude/settings.json, okf-bundle in .mcp.json),
# what does APM 0.33.0 do when kmctl's package declares the same hook and server? And does it keep kmctl's real hook
# commands (claude guard, agy briefing, agy okf Stop wrapper) byte for byte?
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad
W=$(mktemp -d $S/migrate.XXXX); CACHE=${UV_CACHE_DIR:-$HOME/.cache/uv}
cd /home/vscode/kmctl && python3 - "$W" <<'PY'
import json,sys,pathlib
from kmctl import plugin, antigravity
w=pathlib.Path(sys.argv[1])
claude_cmd=plugin.hook_entry()["command"]
stop=antigravity.STOP_COMMAND.replace("cd ../../..","cd ..")
cmds={"claude":claude_cmd,"ag_start":antigravity.HOOK_COMMAND,"ag_stop":stop}
(w/"cmds.json").write_text(json.dumps(cmds))
(w/"launcher").write_text(plugin.okf_mcp_launcher())
(w/"old_settings.json").write_text(json.dumps({"theme":"dark","hooks":{"SessionStart":[{"hooks":[plugin.hook_entry()]}]}}))
(w/"old_mcp.json").write_text(json.dumps({"mcpServers":{"okf-bundle":plugin.okf_mcp_server(),"mine":{"command":"x"}}}))
P=w/"pkg"/"apm"
for d in ["claude/.apm/hooks","antigravity/.apm/hooks",".apm/skills/demo"]: (P/d).mkdir(parents=True)
(P/".apm/skills/demo/SKILL.md").write_text("---\nname: demo\ndescription: d\n---\nx\n")
mcp={"name":"okf-bundle","registry":False,"transport":"stdio","command":"sh","args":["-c",plugin.okf_mcp_launcher()]}
import yaml
(P/"apm.yml").write_text(yaml.safe_dump({"name":"pkg","version":"0.0.1","dependencies":{"apm":["./claude","./antigravity"],"mcp":[mcp]}}))
(P/"claude/apm.yml").write_text("name: pkg-claude\nversion: 0.0.1\ntargets: [claude]\n")
(P/"claude/.apm/hooks/hooks.json").write_text(json.dumps({"hooks":{"SessionStart":[{"matcher":"*","hooks":[plugin.hook_entry()]}]}}))
(P/"antigravity/apm.yml").write_text("name: pkg-antigravity\nversion: 0.0.1\ntargets: [antigravity]\n")
(P/"antigravity/.apm/hooks/hooks.json").write_text(json.dumps({"hooks":{
  "SessionStart":[{"matcher":"*","hooks":[{"type":"command","command":cmds["ag_start"],"timeout":10}]}],
  "Stop":[{"matcher":"*","hooks":[{"type":"command","command":cmds["ag_stop"],"timeout":10}]}]}}))
PY
export UV_CACHE_DIR=$CACHE HOME=$W/home XDG_DATA_HOME=$W/home/.local/share CLAUDE_CONFIG_DIR=$W/home/.claude; mkdir -p $CLAUDE_CONFIG_DIR
mkdir -p $W/c/.claude $W/c/.agents && cd $W/c && git init -q
cp $W/old_settings.json .claude/settings.json; cp $W/old_mcp.json .mcp.json
printf "name: c\nversion: 0.0.1\ndependencies:\n  apm:\n    - $W/pkg/apm\ntargets: [claude, antigravity]\n" > apm.yml
uvx --from apm-cli==0.33.0 apm install --target claude,antigravity > in.txt 2>&1; rc=$?; echo "install rc=$rc"; grep -iE "error|warn|skip|conflict|exist" in.txt | head -8
python3 - "$W" <<'PY'
import json,sys,pathlib
w=pathlib.Path(sys.argv[1]); c=w/"c"; cmds=json.loads((w/"cmds.json").read_text())
s=json.loads((c/".claude/settings.json").read_text())
hooks=[h["command"] for g in s.get("hooks",{}).get("SessionStart",[]) for h in g.get("hooks",[])]
print("claude SessionStart kmctl hooks:", sum(cmds["claude"]==h for h in hooks), "theme kept:", s.get("theme"))
m=json.loads((c/".mcp.json").read_text())["mcpServers"]
print("mcp names:", sorted(m)); print("okf-bundle args kept:", m.get("okf-bundle",{}).get("args",[None,None])[1]==(w/"launcher").read_text())
a=json.loads((c/".agents/hooks.json").read_text())
flat=[h["command"] for ev in a.values() for hs in ev.values() for h in hs]
print("ag start kept:", cmds["ag_start"] in flat, "ag stop kept:", cmds["ag_stop"] in flat)
am=json.loads((c/".agents/mcp_config.json").read_text())["mcpServers"]
print("ag mcp args kept:", am.get("okf-bundle",{}).get("args",[None,None])[1]==(w/"launcher").read_text())
PY
