---
type: verdict
title: 'Verdict: okf-vs-change-audit plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of okf-vs-change-audit: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-26T16:48:38+00:00'
slug: okf-vs-change-audit
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

Pass, round 3. The revised plan matches ADR 0057 as merged to main,
including its no-shell rule, and the code it touches. I found no new risk
that could break it.

## Checked

- No-shell rule against `action/agent.py`. `make_tools` returns
  `[read_file, search_files, list_files, run_shell]` (line 411), and
  `run_agent` passes `make_tools(ws)` to `Agent` (line 662). So a flag that
  drops `run_shell` from that list is a small change. The shipped
  `SYSTEM_PROMPT` names `run_shell` in one sentence (lines 94-96), and
  `system_prompt()` fills it in, so r27's "the system prompt does not offer
  it" is easy to check. The read, search and list tools already refuse any
  path outside the workspace roots, following symlinks (`Workspace.resolve`),
  so they cannot reach `/proc/*/environ`. Without the shell, the ADR's
  reason (the key read from the agent's own process) holds.
- The ADR's Consequence that a skill's scripts cannot run on a PR. The
  plan's `okf-vs-change` prompt uses only read, search and list (r21 judges
  this). Only `docs-vs-code.md` mentions `run_shell`, and only as optional
  ("you may also"), so a repository that runs another audit on a PR loses
  a little, but nothing breaks.
- The accepted ADR says a fork is "refused". The plan skips it with exit 0
  and keeps untracked context folders in the working tree. Both rest on
  the Correction in `adr-0057-correction`, which the plan lists in
  `depends_on`. That ticket's O2 and O3 carry exactly these two points, and
  this plan no longer touches ADR 0057, so the two tickets do not edit the
  same file.
- 2.0 facts. P7/O7 match the new prose. O7's touches (agent.py, action.yml,
  both test files) cover what changes. Its `needs: O3` holds, because the
  action passes `--no-shell` on a pull request only once O3 lets a pull
  request run. O5 now also needs O7, which fits the docs describing the
  missing shell. The ADR 0057 path left O5's touches, which matches the
  prose.
- Risks 1 and 2: the spikes `okf-vs-change-audit/1` and `/2` are the same
  ones round 2 accepted, and they still answer both risks. The old PR 71
  delivery risk is gone, because the plan now lands on main.

## Findings

- p1: resolved. P4/O4 and P6/O6 are still separate.
- p2: resolved. O6 still gives the workflow's download step continue-on-error (r25).

## Notes

These go to the build. They are not findings.

- With `--no-shell`, the shipped system prompt still lists the default
  skills. If a listed skill tells the agent to run its scripts, the prompt
  should say those scripts cannot run on this run, so the agent does not
  try a tool it lacks.
- A repository's own `--system-prompt-file` may still mention `run_shell`.
  The tool is gone anyway, so this is only a docs note.
- The round 2 notes still apply: an `inputs.path` subfolder inside the base
  checkout, the matcher running from the bundle root, and the first PR that
  adds a custom prompt exiting 2.
