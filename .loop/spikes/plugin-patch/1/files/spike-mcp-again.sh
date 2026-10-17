#!/bin/bash
# Over a stale okf-bundle (older pin) in .mcp.json: apm install skips it; after deleting it from .mcp.json and .agents/mcp_config.json, does a second plain apm install write the package server back to both?
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
old=plugin.okf_mcp_server(); old["args"]=["-c","exec uv run https://example.invalid/OLDPIN/okf_mcp.py .okf"]
(w/"old_mcp.json").write_text(json.dumps({"mcpServers":{"okf-bundle":old,"mine":{"command":"x"}}}))
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
echo "first: $(grep -c OLDPIN .mcp.json) stale lines in .mcp.json"
python3 - <<'PY'
import json
for f in [".mcp.json", ".agents/mcp_config.json"]:
    try: d=json.load(open(f))
    except FileNotFoundError: continue
    d["mcpServers"].pop("okf-bundle", None); json.dump(d, open(f,"w"))
PY
uvx --from apm-cli==0.33.0 apm install --target claude,antigravity > in2.txt 2>&1; echo "second install rc=$?"; grep -i "okf-bundle" in2.txt | head -3
python3 - "$W" <<'PY'
import json,sys,pathlib
w=pathlib.Path(sys.argv[1]); c=w/"c"; want=(w/"launcher").read_text(); ok=True
for f in [".mcp.json", ".agents/mcp_config.json"]:
    s=json.load(open(c/f))["mcpServers"].get("okf-bundle")
    good = bool(s) and s.get("args",[None,None])[1]==want
    print(f, "okf-bundle back with the package launcher:", good); ok = ok and good
print("mine kept:", "mine" in json.load(open(c/".mcp.json"))["mcpServers"])
sys.exit(0 if ok else 1)
PY
