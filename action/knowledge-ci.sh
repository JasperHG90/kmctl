#!/usr/bin/env bash
# The kmctl GitHub Action's checks, in one script the tests run locally (ADR 0005).
# Runs in the repository to check. Writes both reports to $GITHUB_STEP_SUMMARY
# (or stdout), fails when kmctl check fails or kmctl review due crashes, and never
# fails because concepts are due.
set -u

summary="${GITHUB_STEP_SUMMARY:-/dev/stdout}"
status=0

# review due reads git history, and actions/checkout fetches one commit by default.
if [ "$(git rev-parse --is-shallow-repository 2>/dev/null)" = "true" ]; then
  if ! git fetch --quiet --unshallow; then
    echo "note: could not fetch full history; review due will skip its history reason." >&2
  fi
fi

{
  echo "## kmctl check"
  echo
  echo '```'
} >> "$summary"
kmctl check >> "$summary" 2>&1
check_status=$?
echo '```' >> "$summary"
if [ "$check_status" -ne 0 ]; then
  status=$check_status
fi

{
  echo
  echo "## kmctl review due"
  echo
  echo '```'
} >> "$summary"
if ! kmctl review due >> "$summary" 2>&1; then
  echo '```' >> "$summary"
  echo >> "$summary"
  echo "kmctl review due failed; run it locally to see why." >> "$summary"
  [ "$status" -eq 0 ] && status=1
else
  echo '```' >> "$summary"
fi

exit "$status"
