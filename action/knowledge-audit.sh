#!/usr/bin/env bash
# The kmctl GitHub Action's audit mode, in one script the tests run locally
# (ADR 0005, ADR 0010, I2). Runs Hermes Agent, against any OpenAI-compatible
# model endpoint, on the concepts kmctl review due lists, with only the
# kmctl-read plugin's three read tools. Writes the findings to
# $GITHUB_STEP_SUMMARY and the issue body to $RUNNER_TEMP/kmctl-audit-body.md.
# It reports; it never edits or pushes. knowledge-audit-issue.sh, a later step,
# posts the body.
#
# Needs: kmctl, hermes and timeout on PATH; KMCTL_PLUGIN_DIR, the plugin folder
# from the action's checkout; and these settings:
#   KMCTL_AUDIT_MODEL        the model name (required)
#   KMCTL_AUDIT_PROVIDER     a Hermes provider name; default custom
#   KMCTL_AUDIT_BASE_URL     the endpoint's base URL; required for custom
#   KMCTL_AUDIT_API_KEY_ENV  the name of the variable that holds the key;
#                            empty for an endpoint that takes no key
#   KMCTL_AUDIT_TIMEOUT      how long hermes may run, as timeout takes it;
#                            default 30m
# No GitHub token may be reachable: the model runs in this process tree.
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

provider="${KMCTL_AUDIT_PROVIDER:-custom}"
model="${KMCTL_AUDIT_MODEL:-}"
base_url="${KMCTL_AUDIT_BASE_URL:-}"
key_env="${KMCTL_AUDIT_API_KEY_ENV:-}"
limit="${KMCTL_AUDIT_TIMEOUT:-30m}"
if [ -z "$model" ]; then
  echo "kmctl audit: KMCTL_AUDIT_MODEL is empty; set the model to audit with (the action's model input)." >&2
  exit 1
fi
if [ "$provider" = custom ] && [ -z "$base_url" ]; then
  echo "kmctl audit: KMCTL_AUDIT_BASE_URL is empty; provider custom needs the endpoint's base URL (the action's base_url input)." >&2
  exit 1
fi
if [ -n "$key_env" ]; then
  if ! [[ "$key_env" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "kmctl audit: KMCTL_AUDIT_API_KEY_ENV must be a variable name, such as AUDIT_API_KEY." >&2
    exit 1
  fi
  if [ -z "${!key_env:-}" ]; then
    echo "kmctl audit: $key_env is empty; set it from the secret that holds the key, or set KMCTL_AUDIT_API_KEY_ENV empty for an endpoint that takes none." >&2
    exit 1
  fi
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

# Hermes reads its config, plugins and sessions from a HOME of its own, so the
# runner's own config never applies, and the folder goes when the run ends.
repo="$(pwd -P)"
home="$work/home"
mkdir -p "$home/.hermes/plugins" "$work/no-writes"
cp -R "$here/hermes/kmctl-read" "$home/.hermes/plugins/kmctl-read"
# JSON is YAML, so json.dump writes a config any value is safe in. The key
# stays in the environment: the file names the variable, never the key.
if ! python3 - "$home/.hermes/config.yaml" "$provider" "$base_url" "$model" "$key_env" <<'PY'
import json, sys
out, provider, base_url, model, key_env = sys.argv[1:6]
entry = {"provider": provider, "default": model}
if base_url:
    entry["base_url"] = base_url
if key_env:
    entry["api_key"] = "${" + key_env + "}"
with open(out, "w") as f:
    json.dump({"model": entry, "plugins": {"enabled": ["kmctl-read"]}}, f, indent=2)
PY
then
  echo "kmctl audit: could not write the Hermes config." >&2
  exit 1
fi

# The audit skill names the review skills; send only those the due list needs.
skills="${KMCTL_PLUGIN_DIR}/skills"
reviews=""
grep -q '"id": "architecture/' "$work/due.json" && reviews="$reviews architecture-review"
grep -q '"id": "decisions/' "$work/due.json" && reviews="$reviews decision-log-review"
grep -q '"id": "practices/' "$work/due.json" && reviews="$reviews practices-review"
{
  cat <<EOF
Audit the repository at $repo by following the audit skill below, and report
only: you cannot change any file.

You are the kmctl-auditor yourself: there are no agents to dispatch. Audit
the batches one after another in this session, following the auditor
instructions and the review skill for each batch. Your tools take the
place of the ones the skill and the auditor name: kmctl_read_file for
Read, kmctl_search_files for Grep (plain text, not a regex) and
kmctl_list_files for Glob (files under a folder, optionally those whose path
holds some text). They take paths relative to $repo, or absolute ones inside
it, and refuse anything outside it.

For the skill's step 1, use this due list, already filtered to architecture,
decisions and practices, instead of running kmctl:

$(cat "$work/due.json")

End your reply with the combined findings as one fenced json block in the
auditor's shape, and nothing after it.

=== The audit skill ===

$(cat "$skills/audit/SKILL.md")

=== The kmctl-auditor instructions ===

$(cat "${KMCTL_PLUGIN_DIR}/agents/kmctl-auditor.md")
EOF
  for review in $reviews; do
    printf '\n=== The %s skill ===\n\n' "$review"
    cat "$skills/$review/SKILL.md"
  done
} > "$work/prompt"

# These would point Hermes at a config other than the one written above, or
# load plugins from the audited repository's own .hermes/ folder.
unset HERMES_PROFILE HERMES_CONFIG HERMES_ENV HERMES_ENABLE_PROJECT_PLUGINS
# -t kmctl_read offers the model only the plugin's three read tools; when the
# plugin is not loaded, hermes stops before calling the model (spike:
# audit-any-provider/1). HERMES_WRITE_SAFE_ROOT, an empty folder, is a second
# fence for any write tool. timeout stops a run that stalls.
HOME="$home" \
  HERMES_HOME="$home/.hermes" \
  HERMES_WRITE_SAFE_ROOT="$work/no-writes" \
  KMCTL_READ_ROOT="$repo" \
  timeout --kill-after=30s "$limit" hermes \
  --provider "$provider" -m "$model" -t kmctl_read -z "$(cat "$work/prompt")" \
  < /dev/null > "$work/hermes.out"
hermes_status=$?
if [ "$hermes_status" -eq 124 ] || [ "$hermes_status" -eq 137 ]; then
  echo "kmctl audit: hermes ran past the time limit ($limit) and was stopped." >&2
  exit 1
fi
if [ "$hermes_status" -ne 0 ]; then
  echo "kmctl audit: hermes exited $hermes_status." >&2
  exit 1
fi

if ! python3 "$here/audit-report.py" "$work/hermes.out" "$summary" "$work/body.md"; then
  echo "kmctl audit: the run gave no findings; no issue was written." >> "$summary"
  exit 1
fi
mv "$work/body.md" "$body"
