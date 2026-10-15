#!/usr/bin/env bash
# The kmctl GitHub Action's audit mode, in one script the tests run locally
# (ADR 0005, I2). Runs headless Claude Code with only read tools on the concepts
# kmctl review due lists, writes the findings to $GITHUB_STEP_SUMMARY and to one
# open issue titled "Knowledge audit". It reports; it never edits or pushes.
#
# Needs: kmctl, claude and gh on PATH; ANTHROPIC_API_KEY and GH_TOKEN for the
# real run; KMCTL_PLUGIN_DIR, the plugin folder from the action's checkout.
set -u

summary="${GITHUB_STEP_SUMMARY:-/dev/stdout}"
here="$(cd "$(dirname "$0")" && pwd)"
title="Knowledge audit"

# The key reaches a model, so code from a pull request or fork must never run here.
case "${GITHUB_EVENT_NAME:-}" in
  workflow_dispatch | schedule) ;;
  *)
    echo "kmctl audit: refused for event '${GITHUB_EVENT_NAME:-}'; audit mode runs only on workflow_dispatch or schedule." >&2
    exit 1
    ;;
esac

# review due reads git history, and actions/checkout fetches one commit by default.
if [ "$(git rev-parse --is-shallow-repository 2>/dev/null)" = "true" ]; then
  git fetch --quiet --unshallow || echo "note: could not fetch full history." >&2
fi

if ! due="$(kmctl review due --json)"; then
  echo "kmctl audit: kmctl review due failed; run it locally to see why." >&2
  exit 1
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Only architecture, decisions and practices are audited (the audit skill's step 1).
# With none of them due there is nothing to ask a model, so stop here.
if ! printf '%s' "$due" | python3 -c '
import json, sys
due = json.load(sys.stdin)["due"]
kept = [c for c in due if c["id"].startswith(("architecture/", "decisions/", "practices/"))]
json.dump({"due": kept}, sys.stdout)
' > "$work/due.json"; then
  echo "kmctl audit: could not read the due list." >&2
  exit 1
fi
if grep -q '"due": \[\]' "$work/due.json"; then
  {
    echo "## Knowledge audit"
    echo
    echo "Nothing in scope is due: no architecture page, decision or practice needs review."
  } >> "$summary"
  exit 0
fi

skills="${KMCTL_PLUGIN_DIR}/skills"
cat > "$work/prompt" <<EOF
Audit this repository ($PWD) by following the audit skill. Read it first, with
the Read tool, at $skills/audit/SKILL.md. Its review skills are next to it:
$skills/architecture-review/SKILL.md, $skills/decision-log-review/SKILL.md and
$skills/practices-review/SKILL.md; read the ones the batches need.

Bash is not available, so for the skill's step 1 use this due list, already
filtered to architecture, decisions and practices, instead of running kmctl:

$(cat "$work/due.json")

Dispatch the kmctl:kmctl-auditor agent for each batch, passing the review
skill's text. End your reply with the combined findings as one fenced json
block, and nothing after it.
EOF

# --tools sets the tool list; --allowedTools alone does not narrow it
# (spike:ci-audit/2). Agent is there only to dispatch the read-only auditor.
# The prompt goes on stdin: the tool flags take any number of values.
claude -p \
  --plugin-dir "${KMCTL_PLUGIN_DIR}" \
  --setting-sources project \
  --strict-mcp-config \
  --tools Read,Grep,Glob,Agent \
  --allowedTools Read,Grep,Glob,Agent \
  --disallowedTools Bash,Edit,Write,NotebookEdit \
  --output-format json \
  < "$work/prompt" > "$work/claude.json"
claude_status=$?
if [ "$claude_status" -ne 0 ]; then
  echo "kmctl audit: claude exited $claude_status." >&2
  exit 1
fi

if ! python3 "$here/audit-report.py" "$work/claude.json" "$summary" "$work/body.md"; then
  echo "kmctl audit: the run gave no findings; no issue was written." >> "$summary"
  exit 1
fi

number="$(gh issue list --state open --search "\"$title\" in:title" --json number,title \
  | python3 -c "import json,sys; print(next((str(i['number']) for i in json.load(sys.stdin) if i['title'] == '$title'), ''))")"
if [ -n "$number" ]; then
  gh issue edit "$number" --body-file "$work/body.md"
else
  gh issue create --title "$title" --body-file "$work/body.md"
fi
