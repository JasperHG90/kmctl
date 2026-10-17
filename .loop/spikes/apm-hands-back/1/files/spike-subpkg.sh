#!/bin/bash
# Can one consumer entry {git, path: apm} pull per-harness sub-packages (targets: claude / antigravity)
# from the same repo, by a relative path (VARIANT=rel) or the repo's own git URL (VARIANT=git)?
set -u
VARIANT=${1:-rel}
S=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad
W=$(mktemp -d $S/subpkg-$VARIANT.XXXX); CACHE=${UV_CACHE_DIR:-$HOME/.cache/uv}
export UV_CACHE_DIR=$CACHE HOME=$W/home XDG_DATA_HOME=$W/home/.local/share CLAUDE_CONFIG_DIR=$W/home/.claude; mkdir -p $CLAUDE_CONFIG_DIR
PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
URL=http://127.0.0.1:$PORT/o/pkg.git
P=$W/pkg; mkdir -p $P/apm/.apm/skills/demo $P/apm/claude/.apm/instructions $P/apm/claude/.apm/hooks $P/apm/antigravity/.apm/instructions $P/apm/antigravity/.apm/hooks
if [ $VARIANT = rel ]; then C="./claude"; A="./antigravity"; else C="{git: $URL, path: apm/claude, ref: v0.0.1, allow_insecure: true}"; A="{git: $URL, path: apm/antigravity, ref: v0.0.1, allow_insecure: true}"; fi
cat > $P/apm/apm.yml <<Y
name: pkg
version: 0.0.1
dependencies:
  apm:
    - $C
    - $A
  mcp:
    - {name: okf-bundle, registry: false, transport: stdio, command: sh, args: ["-c", "echo okf"]}
Y
printf -- '---\nname: demo\ndescription: a demo skill\n---\nDemo.\n' > $P/apm/.apm/skills/demo/SKILL.md
printf 'name: pkg-claude\nversion: 0.0.1\ntargets: [claude]\n' > $P/apm/claude/apm.yml
printf -- '---\napplyTo: "docs/**, .okf/**"\n---\nClaude rule.\n' > $P/apm/claude/.apm/instructions/r.instructions.md
printf '{"hooks":{"SessionStart":[{"matcher":"*","hooks":[{"type":"command","command":"echo claude-start","timeout":10}]}]}}\n' > $P/apm/claude/.apm/hooks/hooks.json
printf 'name: pkg-antigravity\nversion: 0.0.1\ntargets: [antigravity]\n' > $P/apm/antigravity/apm.yml
printf -- "---\napplyTo: '**/docs/**\\\\, **/.okf/**'\n---\nAG rule.\n" > $P/apm/antigravity/.apm/instructions/r.instructions.md
printf '{"hooks":{"SessionStart":[{"matcher":"*","hooks":[{"type":"command","command":"echo ag-start","timeout":10}]}]}}\n' > $P/apm/antigravity/.apm/hooks/hooks.json
cat $P/apm/antigravity/.apm/instructions/r.instructions.md
git -C $P init -q -b main && git -C $P add -A && git -C $P -c user.email=t@e.invalid -c user.name=t commit -qm p && git -C $P tag v0.0.1
mkdir -p $W/srv/o && git clone -q --bare $P $W/srv/o/pkg.git && git -C $W/srv/o/pkg.git update-server-info
python3 -I /home/vscode/kmctl/tests/fixtures/githttp.py $W/srv $PORT >/dev/null 2>&1 & SRV=$!; trap 'kill $SRV' EXIT
for _ in $(seq 50); do (exec 3<>/dev/tcp/127.0.0.1/$PORT) 2>/dev/null && break; sleep 0.1; done
mkdir -p $W/c/.agents && cd $W/c && git init -q
printf "name: c\nversion: 0.0.1\ndependencies:\n  apm:\n    - {git: $URL, path: apm, ref: v0.0.1, allow_insecure: true}\ntargets: [claude, antigravity]\n" > apm.yml
APM="uvx --from apm-cli==0.33.0 apm"
$APM install --target claude,antigravity --allow-insecure > in.txt 2>&1; rc=$?; echo "install rc=$rc"; grep -iE "error|reject|warn|not allowed" in.txt | head -5
echo "--- files"; find .claude .agents -type f | sort
echo "--- .claude rule"; cat .claude/rules/r.md 2>/dev/null; echo "--- .agents rule"; cat .agents/rules/r.md 2>/dev/null
echo "--- hooks"; grep -o 'echo [a-z-]*' .claude/settings.json .agents/hooks.json 2>/dev/null
echo "--- mcp"; grep -l okf-bundle .mcp.json .agents/mcp_config.json 2>/dev/null
ok=1
[ $rc = 0 ] || ok=0
grep -q "Claude rule" .claude/rules/r.md 2>/dev/null || ok=0
grep -q 'globs: "\*\*/docs/\*\*, \*\*/.okf/\*\*"' .agents/rules/r.md 2>/dev/null || ok=0
grep -q "AG rule" .claude/rules/r.md 2>/dev/null && ok=0
grep -q "claude-start" .claude/settings.json 2>/dev/null || ok=0
grep -q "ag-start" .agents/hooks.json 2>/dev/null || ok=0
grep -q "ag-start" .claude/settings.json 2>/dev/null && ok=0
grep -q "claude-start" .agents/hooks.json 2>/dev/null && ok=0
[ -f .claude/skills/demo/SKILL.md ] && [ -f .agents/skills/demo/SKILL.md ] || ok=0
grep -q okf-bundle .mcp.json 2>/dev/null && grep -q okf-bundle .agents/mcp_config.json 2>/dev/null || ok=0
$APM uninstall 127.0.0.1:$PORT/o/pkg/apm > un.txt 2>&1; echo "uninstall rc=$?"; left=$(find .claude/rules .claude/skills .agents/rules .agents/skills -type f 2>/dev/null | wc -l); echo "left after uninstall: $left"; cat .agents/hooks.json 2>/dev/null; grep -c "echo claude-start" .claude/settings.json 2>/dev/null
[ "$left" = 0 ] || ok=0
echo "ok=$ok"; [ $ok = 1 ]
