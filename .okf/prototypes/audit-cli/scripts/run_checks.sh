#!/usr/bin/env zsh
# Run an audit checks verb on kmctl with the shell's keys (~/.zshrc). LangSmith's endpoint, agent id and environment
# come from this folder's .env (git-ignored), which the CLI loads itself. Run from the audit-cli folder:
#   scripts/run_checks.sh diff|write|run|triage|list [flags]
source ~/.zshrc >/dev/null 2>&1
uv run audit checks "$@" ../../.. -c audit.toml 2> >(grep -v VIRTUAL_ENV >&2)
