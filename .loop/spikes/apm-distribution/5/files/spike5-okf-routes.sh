#!/usr/bin/env bash
# Risk 3 follow-up. Spike 4 showed that a plugin/apm.yml that declares
# dependencies turns plugin/ into an APM-format package, and APM then drops
# plugin/agents/kmctl-auditor.md (it reads agents only from .apm/agents/).
# Which route gets everything into a consumer with plugin/ unchanged (no
# apm.yml in it)?
#   M  a meta package apm/apm.yml in the same repo, depending on
#      {git: parent, path: plugin} and scaccogatto/okf-skills; consumer
#      installs path: apm
#   D  the consumer lists both: path: plugin and scaccogatto/okf-skills
# "Everything": 7 kmctl skills and the agent byte for byte, the kmctl
# SessionStart hook in .claude/settings.json, the 4 okf skills; and for the
# first route that has them, kmctl --version, kmctl briefing --path and the
# deployed hook command run from the consumer.
# Exit 0 only when M or D gets everything.
PORT=8775
. /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/common.sh
OKF=a8b96420de90d102c43cda1693d01ec4f925f2ab

everything() {  # everything NAME
  local n=$1 ok=0 s C="$W/c-$1"
  [ "$CEXIT" = 0 ] || ok=1
  for s in "$KM"/plugin/skills/*/; do s=$(basename "$s")
    diff -r "$KM/plugin/skills/$s" "$C/.claude/skills/$s" >/dev/null 2>&1 || { echo "   kmctl skill $s: MISSING or DIFFERENT"; ok=1; }
  done
  cmp -s "$KM/plugin/agents/kmctl-auditor.md" "$C/.claude/agents/kmctl-auditor.md" && echo "   kmctl agent: identical" || { echo "   kmctl agent: MISSING or DIFFERENT"; ok=1; }
  grep -q 'kmctl briefing' "$C/.claude/settings.json" 2>/dev/null && echo "   kmctl hook in settings.json: yes" || { echo "   kmctl hook: NO"; ok=1; }
  for s in okf validate backfill visualize; do
    [ -f "$C/.claude/skills/$s/SKILL.md" ] || { echo "   okf skill $s: NO"; ok=1; }
  done
  echo "   agents: $(ls "$C/.claude/agents" 2>/dev/null | tr '\n' ' ')"
  echo "   skills: $(ls "$C/.claude/skills" 2>/dev/null | tr '\n' ' ')"
  echo "   lock: $(grep -E 'repo_url|virtual_path' "$C/apm.lock.yaml" | tr -s ' \n' ' ')"
  return $ok
}

echo "== M: meta package apm/apm.yml"
new_src m; mkdir "$W/m/apm"
printf 'name: kmctl\nversion: 0.1.0\ndependencies:\n  apm:\n    - git: parent\n      path: plugin\n    - scaccogatto/okf-skills#%s\n' "$OKF" > "$W/m/apm/apm.yml"
publish m
consumer m "    - git: $GIT/m.git" "      path: apm" "      allow_insecure: true"
grep -E '\[\+\]|integrated|\[!\]' "$W/c-m.log"
everything m; M=$?; echo "-- M result: $M"

echo "== D: consumer lists plugin and okf"
new_src d; publish d
consumer d "    - git: $GIT/d.git" "      path: plugin" "      allow_insecure: true" "    - scaccogatto/okf-skills#$OKF"
grep -E '\[\+\]|integrated|\[!\]' "$W/c-d.log"
everything d; D=$?; echo "-- D result: $D"

C=""; [ $M = 0 ] && C="$W/c-m"; [ -z "$C" ] && [ $D = 0 ] && C="$W/c-d"
if [ -n "$C" ]; then
  echo "== kmctl from consumer $C"
  UV_TOOL_DIR="$W/tools" UV_TOOL_BIN_DIR="$W/bin" uv tool install -q "$KM" || exit 3
  export PATH="$W/bin:$PATH"; cd "$C"
  kmctl --version; v=$?
  kmctl briefing --path "$C" > "$W/brief.txt" 2>&1; b=$?; head -2 "$W/brief.txt"
  HOOK=$("$W/venv/bin/python" -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print([h["command"] for g in d["hooks"]["SessionStart"] for h in g["hooks"] if "kmctl" in h["command"]][0])' "$C/.claude/settings.json")
  sh -c "$HOOK" > "$W/hook.txt" 2>&1; h=$?; head -2 "$W/hook.txt"
  echo "   kmctl --version exit $v, briefing exit $b, hook exit $h"
  grep -q 'not installed\|briefing failed' "$W/hook.txt" && h=1
  [ $v = 0 ] && [ $b = 0 ] && [ $h = 0 ] || { M=1; D=1; }
fi
echo "== RESULT: M=$M D=$D (0 = everything reached the consumer)"
[ $M = 0 ] || [ $D = 0 ]
