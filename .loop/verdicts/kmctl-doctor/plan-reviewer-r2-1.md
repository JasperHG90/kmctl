---
type: verdict
title: 'Verdict: kmctl-doctor plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of kmctl-doctor: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-16T20:26:58+00:00'
slug: kmctl-doctor
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

All five round-1 risks are settled, either by a spike or by a revision that matches the dependency plans as they stand now. I found no new risk that could break the plan. Pass.

## Checked

- p1: apm-only-install's plan now has kmctl merge an `okf-bundle` server into `.mcp.json`, or `claude mcp add-json --scope user` at user scope. It uses the walk-up launcher that antigravity-harness reuses, so doctor has a writer function to compare against. The lock records MCP only as a `kind: uri` deployment with no file (spike:kmctl-doctor/3), so the entry is not double-checked by hash.
- p2: spike:kmctl-doctor/3 README, run.json (exit 0) and stdout. The lock lists 40 paths and 32 hashes. The only hook paths it lists are the two stop-check scripts. There were 0 mismatches after the SessionStart merge.
- p3: spike:kmctl-doctor/4 README and stdout. `uv tool run --offline` made 0 inet connects and changed nothing under HOME. `claude plugin list` made 4 connects and wrote `.claude.json`. The plan now reads enabledPlugins instead. That spike pointed UV_CACHE_DIR at the real cache, outside the scratch HOME, so it never watched the uv cache. I checked that gap by hand: a warm `uv tool run --offline --from apm-cli==0.33.0 apm --version` left nothing newer than a marker file in `~/.cache/uv`, `~/.local/share/uv` or `~/.local/bin`.
- Old-plugin check: `src/kmctl/plugin.py` installs `kmctl@kmctl` with `claude plugin install --scope project|user`. Those scopes record it in `.claude/settings.json` or the user settings file, which are the two files the plan reads.
- p4: apm-only-install keeps `--scope user` (spike:apm-only-install/2). The plan and row r3b cover both directions.
- p5: antigravity-harness's plan defines the per-file comparison (missing, extra, different) and the 6-file folder. Doctor reuses it, and row r2 lists a missing apm_modules/.

## Findings

p1, p2, p3, p4 and p5 are resolved, as listed in the front matter. None are new.

## Notes

These are things the builder will hit. None of them breaks the plan.

- `agy` is on PATH in this dev container. The r7 integration run will therefore get an `antigravity.trust` check, and the scratch repository is not in `trustedWorkspaces`. Done-when (exit 0) needs the test to give doctor a scratch Antigravity settings file that trusts the scratch repository. It must never write to the real `~/.gemini`.
- In spike:kmctl-doctor/3 the lock tags `.agents/hooks/...` deployments with `target: legacy`, not `antigravity`. Group the lock's files by harness on the path prefix (`.claude/` or `.agents/`), not on `deployments[].target`.
- With CLAUDE_CONFIG_DIR set, the user-scope MCP entry lives in `$CLAUDE_CONFIG_DIR/.claude.json`, as spike:kmctl-doctor/4 saw. Without it, the entry is in `~/.claude.json`, not under `~/.claude/`.
- On a fresh clone, `antigravity.plugin` fails until someone runs install, because apm_modules/ is git-ignored. That is the chosen behaviour. Anyone who later runs doctor in CI on a checkout should know about it.
