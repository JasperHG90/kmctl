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

# KMCTL_SUMMARY (the summary input): fail fails when .okf/summary.md is behind
# the concepts that changed after it; pass only warns (ADR 0056).
summary_mode="${KMCTL_SUMMARY:-fail}"
case "$summary_mode" in
  fail) check_args+=(--summary-current) ;;
  pass) ;;
  *)
    echo "kmctl action: summary must be fail or pass, not '$summary_mode'." >&2
    exit 1
    ;;
esac

{
  echo "## kmctl check"
  echo
  case " ${check_args[*]-} " in
    *" --no-drafts "*) echo "Draft decisions fail (drafts: $drafts)." ;;
    *) echo "Draft decisions pass here (drafts: $drafts)." ;;
  esac
  if [ "$summary_mode" = "fail" ]; then
    echo "A summary behind its concepts fails (summary: fail); run kmctl summary ack when it is still right."
  else
    echo "A summary behind its concepts only warns (summary: pass)."
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

# On a pull request, first the pages this pull request made due: the ones to
# read before review (ADR 0055). GITHUB_BASE_REF names the base branch. A
# checkout with fetch-depth: 0 already has origin/BASE; fetch it only when it
# is missing, since a fetch fails in a private repository checked out with
# persist-credentials: false.
base_ref="origin/${GITHUB_BASE_REF:-}"
if [ -n "${GITHUB_BASE_REF:-}" ] && {
  git rev-parse --verify --quiet "$base_ref^{commit}" >/dev/null ||
    git fetch --quiet origin "+refs/heads/$GITHUB_BASE_REF:refs/remotes/$base_ref" 2>/dev/null
}; then
  {
    echo
    echo "## Pages this pull request made due"
    echo
    echo "Read each one; a person who checked them runs kmctl verify ID ID ... --by human:<id>."
    echo
    echo '```'
  } >> "$summary"
  if ! kmctl review due --base "$base_ref" >> "$summary" 2>&1; then
    echo "kmctl review due --base $base_ref failed; run it locally to see why." >> "$summary"
  fi
  echo '```' >> "$summary"
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
