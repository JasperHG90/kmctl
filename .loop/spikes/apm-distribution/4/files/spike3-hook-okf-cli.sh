#!/usr/bin/env bash
# Risk 3 (hook and okf): installed as path: plugin with a plugin/apm.yml that
# declares okf as a dependency, does APM 0.33.0 put (a) kmctl's SessionStart
# hook into the consumer's .claude/settings.json, (b) the okf plugin's skills
# into the consumer, and (c) with kmctl on PATH, do `kmctl --version`,
# `kmctl briefing --path <consumer>` and the deployed hook command run from
# the consumer?
# okf is pinned to scaccogatto/okf-skills main at spike time (a8b96420).
# Exit 0 only when (a), (b) and (c) all hold.
PORT=8773
. /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/common.sh
OKF=a8b96420de90d102c43cda1693d01ec4f925f2ab
echo "== okf-skills main now: $(git ls-remote https://github.com/scaccogatto/okf-skills refs/heads/main | cut -f1)"
ok=0

new_src k
printf 'name: kmctl\nversion: 0.1.0\ndependencies:\n  apm:\n    - scaccogatto/okf-skills#%s\n' "$OKF" > "$W/k/plugin/apm.yml"
publish k
consumer k "    - git: $GIT/k.git" "      path: plugin" "      allow_insecure: true"
grep -E 'integrated|\[\+\]|\[!\]|trust|MCP|mcp' "$W/c-k.log"
echo "-- files written:"; files k
C="$W/c-k"

echo "== (a) hook"
if [ -f "$C/.claude/settings.json" ] && grep -q 'kmctl briefing' "$C/.claude/settings.json"; then echo "   kmctl SessionStart hook in .claude/settings.json: yes"
else echo "   kmctl SessionStart hook in .claude/settings.json: NO"; ok=1; fi
"$W/venv/bin/python" -I -c 'import json,sys; d=json.load(open(sys.argv[1])); [print("   settings.json", ev, "->", h.get("command","")[:90]) for ev,gs in d.get("hooks",{}).items() for g in gs for h in g["hooks"]]' "$C/.claude/settings.json"

echo "== (b) okf"
for s in okf validate backfill visualize; do
  if [ -f "$C/.claude/skills/$s/SKILL.md" ]; then echo "   okf skill $s: yes"; else echo "   okf skill $s: NO"; ok=1; fi
done
ls "$C/.claude/agents" 2>/dev/null | sed 's/^/   agent: /'
[ -f "$C/.mcp.json" ] && echo "   .mcp.json:" && cat "$C/.mcp.json"
echo "-- lock deps:"; grep -E 'repo_url|resolved_commit|virtual_path|depth' "$C/apm.lock.yaml"

echo "== (c) kmctl from the consumer"
UV_TOOL_DIR="$W/tools" UV_TOOL_BIN_DIR="$W/bin" uv tool install -q "$KM" || { echo "   uv tool install failed"; exit 3; }
export PATH="$W/bin:$PATH"
cd "$C"
kmctl --version; v=$?; echo "   kmctl --version exit $v"
kmctl briefing --path "$C" > "$W/brief.txt" 2>&1; b=$?; echo "   kmctl briefing --path exit $b"; head -15 "$W/brief.txt"
HOOK=$("$W/venv/bin/python" -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print([h["command"] for g in d["hooks"]["SessionStart"] for h in g["hooks"] if "kmctl" in h["command"]][0])' "$C/.claude/settings.json")
sh -c "$HOOK" > "$W/hook.txt" 2>&1; h=$?; echo "   deployed hook command exit $h; first lines:"; head -5 "$W/hook.txt"
grep -q 'kmctl is not installed\|briefing failed' "$W/hook.txt" && { echo "   hook fell back"; ok=1; }
[ $v = 0 ] && [ $b = 0 ] && [ $h = 0 ] || ok=1

echo "== RESULT: $([ $ok = 0 ] && echo 'risk does not hold' || echo 'risk holds')"
exit $ok
