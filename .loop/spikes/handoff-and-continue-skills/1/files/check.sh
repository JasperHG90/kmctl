#!/usr/bin/env bash
# Exit 0 when a skill can read the session id: the Bash tool env carries it,
# and the skills docs list the ${CLAUDE_SESSION_ID} substitution.
set -u
rc=0
echo "CLAUDE_CODE_SESSION_ID=${CLAUDE_CODE_SESSION_ID:-<unset>}"
if [[ "${CLAUDE_CODE_SESSION_ID:-}" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
  echo "env: OK, UUID session id visible to Bash subprocess"
else
  echo "env: FAIL"; rc=1
fi
docs=$(curl -sfL --max-time 20 https://code.claude.com/docs/en/skills.md) || { echo "docs: fetch failed"; exit 2; }
if grep -F '| `${CLAUDE_SESSION_ID}` |' <<<"$docs"; then
  echo "docs: OK, skills substitution table lists \${CLAUDE_SESSION_ID}"
else
  echo "docs: FAIL"; rc=1
fi
envdocs=$(curl -sfL --max-time 20 https://code.claude.com/docs/en/env-vars.md) || { echo "env docs: fetch failed"; exit 2; }
grep -F '| `CLAUDE_CODE_SESSION_ID` |' <<<"$envdocs" | cut -c1-400
exit $rc
