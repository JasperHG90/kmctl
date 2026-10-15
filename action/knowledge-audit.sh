#!/usr/bin/env bash
# The kmctl GitHub Action's audit mode, in one script the tests run locally
# (ADR 0005, I2). Runs headless Claude Code with only read tools on the concepts
# kmctl review due lists, writes the findings to $GITHUB_STEP_SUMMARY and the
# issue body to $RUNNER_TEMP/kmctl-audit-body.md. It reports; it never edits or
# pushes. knowledge-audit-issue.sh, a later step, posts the body.
#
# Needs: kmctl and claude on PATH; ANTHROPIC_API_KEY for the real run;
# KMCTL_PLUGIN_DIR, the plugin folder from the action's checkout. No GitHub
# token may be reachable: the model's Read tool could open it.
set -u

summary="${GITHUB_STEP_SUMMARY:-/dev/stdout}"
here="$(cd "$(dirname "$0")" && pwd)"
body="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/kmctl-audit-body.md"
rm -f "$body"

# The key reaches a model, so code from a pull request or fork must never run here.
case "${GITHUB_EVENT_NAME:-}" in
  workflow_dispatch | schedule) ;;
  *)
    echo "kmctl audit: refused for event '${GITHUB_EVENT_NAME:-}'; audit mode runs only on workflow_dispatch or schedule." >&2
    exit 1
    ;;
esac

# A token anywhere in this process's environment stays readable in
# /proc/PID/environ, and checkout's persisted credentials sit in git config
# (directly, or in a file it includes). Refuse rather than hand either to a model.
for name in GH_TOKEN GITHUB_TOKEN; do
  if [ -n "${!name:-}" ]; then
    echo "kmctl audit: refused: $name is set, and the model could read the token. Set it only for the issue step, not for the job." >&2
    exit 1
  fi
done
if git config --get-regexp '^http\..*\.extraheader$' > /dev/null 2>&1; then
  echo "kmctl audit: refused: git config holds checkout's token (an extraheader), and the model could read it. Check out with persist-credentials: false." >&2
  exit 1
fi

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
mv "$work/body.md" "$body"
