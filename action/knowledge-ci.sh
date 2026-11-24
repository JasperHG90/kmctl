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

# KMCTL_DRAFTS (the drafts input): fail-when-ready fails on a draft decision
# only on a pull request that is ready for review, read from the event GitHub
# wrote to $GITHUB_EVENT_PATH; fail always fails on one; pass never does (ADR 0050).
drafts="${KMCTL_DRAFTS:-fail-when-ready}"
check_args=()
case "$drafts" in
  fail) check_args=(--no-drafts) ;;
  pass) ;;
  fail-when-ready)
    case "${GITHUB_EVENT_NAME:-}" in
      pull_request | pull_request_target)
        ready=$(python3 -c 'import json, sys; print(str(not json.load(open(sys.argv[1]))["pull_request"].get("draft", False)).lower())' "${GITHUB_EVENT_PATH:-}" 2>/dev/null)
        [ "$ready" = "true" ] && check_args=(--no-drafts)
        ;;
    esac
    ;;
  *)
    echo "kmctl action: drafts must be fail-when-ready, fail or pass, not '$drafts'." >&2
    exit 1
    ;;
esac

{
  echo "## kmctl check"
  echo
  if [ "${#check_args[@]}" -eq 0 ]; then
    echo "Draft decisions pass here (drafts: $drafts)."
  else
    echo "Draft decisions fail (drafts: $drafts)."
  fi
  echo
  echo '```'
} >> "$summary"
kmctl check ${check_args[@]+"${check_args[@]}"} >> "$summary" 2>&1
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
