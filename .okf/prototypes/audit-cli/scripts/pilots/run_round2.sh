#!/usr/bin/env zsh
# Second measuring round, after the last-call fix: the two-call writer on the 52 agent claims, then each agent
# variant on all 15 left-over claims, one after another (they share the spending ledger). Run from the audit-cli
# folder; output goes to results/pilots/round2.log.
source ~/.zshrc >/dev/null 2>&1
{
  echo "== two-call"
  uv run python scripts/pilots/oneshot.py grouped --sample agent --fix 2>&1 | grep -v VIRTUAL_ENV
  for v in before after hints bare-tools; do
    echo "== $v"
    uv run python scripts/pilots/agent_spend.py $v --all --tag r2 2>&1 | grep -v VIRTUAL_ENV | grep -v batch_stopped
  done
} > results/pilots/round2.log 2>&1
