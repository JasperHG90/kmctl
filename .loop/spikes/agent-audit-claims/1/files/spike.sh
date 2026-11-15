#!/usr/bin/env bash
# Risk 1 of agent-audit-claims: can a subagent's shell be limited to
# `kmctl claims ...` in Claude Code and in Antigravity, and can kmctl's
# Antigravity translation carry such a limit?
# Exits 0 only when every check says the limit is possible (risk does not hold).
set -u
REPO_PY=/Users/jasperginn/Documents/code_projects/kmctl/.venv/bin/python
AGY=$(command -v agy)
T=$(mktemp -d)
fail=0

echo "== 1. kmctl translate_agent on tools: Read, Bash(kmctl claims:*)"
PYTHONPATH="$PWD/src" "$REPO_PY" -I -c '
import sys; sys.path.insert(0, sys.argv[1])
from kmctl.antigravity import translate_agent, PluginError
text = "---\nname: claims-runner\ndescription: d\ntools: Read, Bash(kmctl claims:*)\n---\nbody\n"
try:
    print(translate_agent(text, "claims-runner.md")); print("TRANSLATED")
except PluginError as e:
    print("REFUSED:", e); sys.exit(1)
' "$PWD/src" || { echo "-> translation refuses the scoped Bash entry"; fail=1; }

echo; echo "== 2. agy $("$AGY" --version | head -1): agent commandExecutionPolicy values"
P=$T/plug; mkdir -p "$P/agents"; echo '{"name":"kmctl","version":"1.0.0"}' > "$P/plugin.json"
probe() {  # $1 = extra front matter; prints agents loaded and agent findings
  printf -- '---\nname: claims-runner\ndescription: probe\n%s\n---\nYou probe.\n' "$1" > "$P/agents/claims-runner.md"
  "$AGY" plugin validate --json "$P" 2>/dev/null | "$REPO_PY" -I -c '
import json, sys
d = json.loads(sys.stdin.read().split("\n}\n")[0] + "\n}")
msgs = [f["message"] for f in d["findings"] if f["file"].startswith("agents/")]
print("agents loaded:", d["components"]["agents"], "|", "; ".join(msgs) or "no agent findings")'
}
for v in off auto eager '"kmctl claims"' '"kmctl claims:*"'; do
  printf '  commandExecutionPolicy: %-18s -> ' "$v"; probe "tools: [view_file, run_command]
commandExecutionPolicy: $v"
done
echo "  (only off/auto/eager load: the policy is all-or-nothing, not a command allowlist)"
fail=1

echo; echo "== 3. agy validator on unknown tool and key spellings (silently accepted => no evidence they work)"
printf '  tools: run_command(kmctl claims:*) -> '; probe 'tools: [view_file, "run_command(kmctl claims:*)"]'
printf '  allowedCommands: [kmctl claims]    -> '; probe 'tools: [view_file, run_command]
allowedCommands: ["kmctl claims"]'

echo; echo "== 4. agy binary: YAML keys mentioning allow/deny/permission/command"
strings -n 6 "$(readlink -f "$AGY")" | grep -oE 'yaml:"[a-zA-Z]+' | sort -u \
  | grep -iE 'allow|deny|perm|command|polic' | sed 's/^/  /'

echo; echo "== 5. Claude Code $(claude --version 2>/dev/null): live subagent run"
if claude auth status 2>/dev/null | grep -q '"loggedIn": true'; then
  echo "  logged in, but this script does not run the live check"
else
  echo "  SKIPPED: claude is not logged in from this sandbox, so no live run"
fi
echo; echo "fail=$fail"
exit $fail
