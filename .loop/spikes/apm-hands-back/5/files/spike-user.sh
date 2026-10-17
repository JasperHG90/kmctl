#!/bin/bash
# At user scope (apm install -g --target claude, ~/.apm/apm.yml naming the split package over git): does APM resolve
# ./claude, write the SessionStart hook to $CLAUDE_CONFIG_DIR/settings.json and okf-bundle to $CLAUDE_CONFIG_DIR/.claude.json?
# Over a user install today's kmctl wrote, what does it leave? Does apm uninstall -g clean up?
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad
W=$(mktemp -d $S/user.XXXX); CACHE=${UV_CACHE_DIR:-$HOME/.cache/uv}
cd /home/vscode/kmctl && python3 - "$W" <<'PY'
import json,sys,pathlib,yaml
from kmctl import plugin
w=pathlib.Path(sys.argv[1]); P=w/"pkg"/"apm"
for d in ["claude/.apm/hooks","antigravity/.apm/instructions",".apm/skills/demo"]: (P/d).mkdir(parents=True)
(P/".apm/skills/demo/SKILL.md").write_text("---\nname: demo\ndescription: d\n---\nx\n")
mcp={"name":"okf-bundle","registry":False,"transport":"stdio","command":"sh","args":["-c",plugin.okf_mcp_launcher()]}
(P/"apm.yml").write_text(yaml.safe_dump({"name":"pkg","version":"0.0.1","dependencies":{"apm":["./claude","./antigravity"],"mcp":[mcp]}}))
(P/"claude/apm.yml").write_text("name: pkg-claude\nversion: 0.0.1\ntargets: [claude]\n")
(P/"claude/.apm/hooks/hooks.json").write_text(json.dumps({"hooks":{"SessionStart":[{"matcher":"*","hooks":[plugin.hook_entry()]}]}}))
(P/"antigravity/apm.yml").write_text("name: pkg-antigravity\nversion: 0.0.1\ntargets: [antigravity]\n"); (P/"antigravity/.apm/instructions/r.instructions.md").write_text("---\napplyTo: \"**/docs/**\"\n---\nAG rule.\n")
(w/"cmd").write_text(plugin.hook_entry()["command"]); (w/"launcher").write_text(plugin.okf_mcp_launcher())
PY
cd $W/pkg && git init -q -b main && git add -A && git -c user.email=t@e.invalid -c user.name=t commit -qm p && git tag v0.0.1
PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])'); URL=http://127.0.0.1:$PORT/o/pkg.git
mkdir -p $W/srv/o && git clone -q --bare $W/pkg $W/srv/o/pkg.git && git -C $W/srv/o/pkg.git update-server-info
python3 -I /home/vscode/kmctl/tests/fixtures/githttp.py $W/srv $PORT >/dev/null 2>&1 & SRV=$!; trap 'kill $SRV' EXIT
for _ in $(seq 50); do (exec 3<>/dev/tcp/127.0.0.1/$PORT) 2>/dev/null && break; sleep 0.1; done
export UV_CACHE_DIR=$CACHE HOME=$W/home XDG_DATA_HOME=$W/home/.local/share CLAUDE_CONFIG_DIR=$W/home/.claude
mkdir -p $CLAUDE_CONFIG_DIR $HOME/.apm
cd /home/vscode/kmctl && python3 - "$W" <<'PY'
import json,sys,pathlib
from kmctl import plugin
w=pathlib.Path(sys.argv[1]); c=w/"home/.claude"
(c/"settings.json").write_text(json.dumps({"theme":"dark","hooks":{"SessionStart":[{"hooks":[plugin.hook_entry()]}]}}))
old=plugin.okf_mcp_server(); old["args"]=["-c","exec uv run https://example.invalid/OLDPIN/okf_mcp.py .okf"]
(c/".claude.json").write_text(json.dumps({"mcpServers":{"okf-bundle":old,"mine":{"command":"x"}}}))
PY
printf "name: user\nversion: 0.0.1\ndependencies:\n  apm:\n    - {git: $URL, path: apm, ref: v0.0.1, allow_insecure: true}\n" > $HOME/.apm/apm.yml
cd $W && APM="uvx --from apm-cli==0.33.0 apm"
$APM install -g --target claude --allow-insecure > in.txt 2>&1; echo "install -g rc=$?"; grep -iE "error|okf-bundle|skip" in.txt | head -5
report() { python3 - "$W" "$1" <<'PY'
import json,sys,pathlib
w=pathlib.Path(sys.argv[1]); c=w/"home/.claude"; cmd=(w/"cmd").read_text(); l=(w/"launcher").read_text()
s=json.loads((c/"settings.json").read_text())
n=sum(h.get("command")==cmd for g in s.get("hooks",{}).get("SessionStart",[]) for h in g.get("hooks",[]))
side=(c/"apm-hooks.json").exists() and cmd in (c/"apm-hooks.json").read_text()
m=json.loads((c/".claude.json").read_text()).get("mcpServers",{})
print(sys.argv[2], "| kmctl hooks:", n, "| recorded by APM:", side, "| okf-bundle:", "package" if m.get("okf-bundle",{}).get("args",[0,0])[1]==l else ("stale" if "okf-bundle" in m else "none"), "| mine:", "mine" in m, "| skill:", (c/"skills/demo/SKILL.md").exists())
PY
}
report "over old kmctl"
python3 - "$W" <<'PY'
import json,sys,pathlib
c=pathlib.Path(sys.argv[1])/"home/.claude"
s=json.loads((c/"settings.json").read_text()); s["hooks"]["SessionStart"]=[g for g in s["hooks"]["SessionStart"] if "matcher" in g]; (c/"settings.json").write_text(json.dumps(s))
m=json.loads((c/".claude.json").read_text()); m["mcpServers"].pop("okf-bundle",None); (c/".claude.json").write_text(json.dumps(m))
PY
$APM install -g --target claude --allow-insecure > in2.txt 2>&1; echo "second install -g rc=$?"
report "after kmctl cleanup + reinstall"
$APM uninstall -g 127.0.0.1:$PORT/o/pkg/apm > un.txt 2>&1; echo "uninstall -g rc=$?"
report "after uninstall -g" 2>&1 | tail -1
