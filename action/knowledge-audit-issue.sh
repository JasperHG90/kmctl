#!/usr/bin/env bash
# The kmctl GitHub Action's audit issue step (ADR 0005). Runs after
# knowledge-audit.sh, in a step of its own so the GitHub token never shares a
# process with the model. Posts $RUNNER_TEMP/kmctl-audit-body.md to the one open
# issue titled "Knowledge audit", creating it if none is open. With no body
# (nothing was due, or the audit failed) it does nothing.
#
# Needs: gh on PATH and GH_TOKEN.
set -euo pipefail

body="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/kmctl-audit-body.md"
title="Knowledge audit"

if [ ! -f "$body" ]; then
  echo "kmctl audit: no report to post; no issue was written."
  exit 0
fi

if ! issues="$(gh issue list --state open --search "\"$title\" in:title" --json number,title)"; then
  echo "kmctl audit: could not look up the open \"$title\" issue, so none was written; rerun the job." >&2
  exit 1
fi
number="$(printf '%s' "$issues" | python3 -c '
import json, sys
title = sys.argv[1]
print(next((str(i["number"]) for i in json.load(sys.stdin) if i["title"] == title), ""))
' "$title")"
if [ -n "$number" ]; then
  gh issue edit "$number" --body-file "$body"
else
  gh issue create --title "$title" --body-file "$body"
fi
