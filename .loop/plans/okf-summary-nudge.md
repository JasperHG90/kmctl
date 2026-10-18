---
type: plan
title: 'Plan: okf-summary-nudge'
description: Right after the agent changes a concept in .okf/, a Claude Code PostToolUse hook asks it to update .okf/summary.md or ack it as still right.
tags:
- plan
slug: okf-summary-nudge
status: draft
epic: null
depends_on: [okf-summary, okf-summary-holistic]
priority: 2
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T19:40:54+00:00'
---

# okf-summary-nudge

Relayed from: okf-summary, split at the operator's word (2026-10-18, "1. Split.")

## Intent

The operator (2026-10-18, ask j-20261018T192834+0000-db7087e2): "you can add
a hook or something so that any time something is changed in the okf bundle,
the summary should plausibly be updated (unless it's not so relevant or
something)", then "Not at the end of a turn. Just when anything in .okf
changes", and "But not .log".

A new verb, `kmctl summary nudge`, reads the hook JSON on stdin and, when
okf-summary's freshness rule says the summary is behind a changed concept
(never for `log.md`, indexes, handoffs or the summary itself), prints one
nudge naming the concepts and the two ways out: update `.okf/summary.md`, or
`kmctl summary ack`. It remembers the changed set it last nudged about as a
hash under the git directory, so later tool calls on the same set stay
quiet; it uses git only (2 ms a query; `review_due` takes 300 ms), never
writes `.okf/`, and exits 0 with `{}` on any failure. Claude Code runs it
from a PostToolUse hook on `Write|Edit|MultiEdit|Bash` in
`apm/claude/.apm/hooks/hooks.json`, returning the nudge as
`hookSpecificOutput.additionalContext`; `kmctl doctor` checks the entry.
Measured: 17% of this repo's 9,103 Write, Edit, MultiEdit and Bash calls
name `.okf/`.

The nudge never goes through the hand-off to a project's pin (ADR 0026,
`hand_off` in `src/kmctl/pin.py`): the hook runs after every Write, Edit,
MultiEdit and Bash call, and a hand-off would start uvx each time, building
an uncached pin past the hook's 10 s timeout (plan review round 1, p1). The
hook command sets `KMCTL_PINNED=1` for the call, the escape ADR 0026 already
records for the CI action, so every copy on PATH runs the verb itself,
including v0.7.0 and v0.8.0, whose hand-off would otherwise send it to uvx
(plan review round 2, p2): one that has the verb nudges, needing only git
and the summary; an older one prints a usage error, which the hook's guard
turns into `{}`. `hand_off` itself does not change. The new decision says
in one line that the nudge runs on the copy on PATH, and why.

Done when: in a repository made with `kmctl init`, a PostToolUse payload for
a Bash call that ran `kmctl new decision` makes `kmctl summary nudge --format
claude` print one `additionalContext` naming the decision and the two ways
out; the same payload again prints `{}`; after the summary is edited or
acked it prints `{}`; the package's `hooks.json` carries the PostToolUse
entry; and `kmctl doctor` reports it.

ADR 0004 rejected a PostToolUse nudge by name, and invariant I1 says kmctl's
own hook is SessionStart. The operator said to supersede it ("3. Fine.
Supersede."): a new decision supersedes ADR 0004 with `kmctl decision
supersede`, I1 widens, and `docs/explanation/why-one-hook-and-report-only-audits.md`
follows.

## Could invalidate this plan

- Claude Code's PostToolUse hook may not deliver
  `hookSpecificOutput.additionalContext` to the model right after a Bash,
  Write or Edit call, or may not give the hook the repository's `cwd`.
  spike:okf-summary-nudge/2 (it does, after Write and Bash, with `cwd`,
  `tool_name` and `tool_input` on stdin; empty output or `{}` is harmless)
- APM 0.33.0 may not deploy a PostToolUse entry with a matcher from the
  package's `hooks.json` into `.claude/settings.json` (proven only for
  SessionStart and okf's Stop). spike:okf-summary-nudge/3 (it does, byte for
  byte, once across reinstalls; APM tracks hooks in .claude/apm-hooks.json,
  not `apm.lock.yaml`, so `kmctl doctor` reads `.claude/settings.json`)
