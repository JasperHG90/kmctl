#!/usr/bin/env bash
# Risk 1 (layout): does APM 0.33.0 deploy kmctl's skills and agent from
# plugin/skills/*/SKILL.md and plugin/agents/*.md as they are, with no copy?
# Cases, each a git repo served over local HTTP and installed into a clean
# consumer:
#   A  repo root, no apm.yml anywhere          (git URL, no path)
#   B  plugin/ as is, no apm.yml               (git URL, path: plugin)
#   C  plugin/apm.yml added beside plugin.json (git URL, path: plugin)
# Exit 0 only when B deploys all 7 skill folders and the agent byte for byte
# (the layout needs no copy). C is reported because risks 2 and 3 need an
# apm.yml in plugin/.
PORT=8771
. /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/common.sh

check() {  # check NAME: compare consumer NAME's .claude to plugin/
  local n=$1 ok=0 s
  for s in "$KM"/plugin/skills/*/; do
    s=$(basename "$s")
    if diff -r "$KM/plugin/skills/$s" "$W/c-$n/.claude/skills/$s" >/dev/null 2>&1; then echo "   skill $s: identical"
    else echo "   skill $s: MISSING or DIFFERENT"; ok=1; fi
  done
  if cmp -s "$KM/plugin/agents/kmctl-auditor.md" "$W/c-$n/.claude/agents/kmctl-auditor.md"; then echo "   agent kmctl-auditor: identical"
  elif [ -f "$W/c-$n/.claude/agents/kmctl-auditor.md" ]; then echo "   agent kmctl-auditor: DIFFERENT"; diff "$KM/plugin/agents/kmctl-auditor.md" "$W/c-$n/.claude/agents/kmctl-auditor.md" | head; ok=1
  else echo "   agent kmctl-auditor: MISSING"; ok=1; fi
  return $ok
}

echo "== A: repo root, no apm.yml"
new_src a; publish a
consumer a "    - git: $GIT/a.git" "      allow_insecure: true"
files a

echo "== B: plugin/ as is, path: plugin"
new_src b; publish b
consumer b "    - git: $GIT/b.git" "      path: plugin" "      allow_insecure: true"
grep -E 'integrated|\[\+\]' "$W/c-b.log"
echo "-- files written:"; files b
check b; B=$?
echo "-- B result: $B"

echo "== C: plugin/apm.yml beside plugin.json, path: plugin"
new_src c; printf 'name: kmctl\nversion: 0.1.0\ndescription: kmctl skills\n' > "$W/c/plugin/apm.yml"; publish c
consumer c "    - git: $GIT/c.git" "      path: plugin" "      allow_insecure: true"
grep -E 'integrated|\[\+\]' "$W/c-c.log"
echo "-- files written:"; files c
check c; echo "-- C result: $?"
echo "-- C hook in settings.json:"; grep -c 'kmctl briefing' "$W/c-c/.claude/settings.json" 2>/dev/null

echo "== RESULT: $([ $B = 0 ] && echo 'risk does not hold: plugin/ deploys as is' || echo 'risk holds')"
exit $B
