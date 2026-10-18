---
type: decision
title: "ADR 0028: Two hooks: the session briefing and the summary nudge"
description: "kmctl ships a SessionStart hook that prints the briefing and a Claude Code PostToolUse hook that runs kmctl summary nudge after Write, Edit, MultiEdit and Bash calls; neither blocks."
tags: [adr, decision, okf]
generated:
  by: process:kmctl/0.8.0
  at: 2026-10-18T23:11:18Z
status: stable
sources:
  - resource: "src/kmctl/summary.py"
  - resource: "apm/claude/.apm/hooks/hooks.json"
  - resource: "src/kmctl/plugin.py"
  - resource: "src/kmctl/doctor.py"
---

# ADR 0028: Two hooks: the session briefing and the summary nudge

## Context

[ADR 0004](0004-sessionstart-is-the-only-hook.md) made SessionStart kmctl's
only hook and rejected a PostToolUse nudge by name. Since then
[ADR 0027](0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md)
added `.okf/summary.md`, which is only worth reading while it is true, and a
rule that says when it falls behind: a concept changed after the summary. The
briefing reports that rule once, at session start; an agent that changes a
decision mid-session hears nothing until the next one.

The operator (2026-10-18) asked for a hook "so that any time something is
changed in the okf bundle, the summary should plausibly be updated", then:
"Not at the end of a turn. Just when anything in .okf changes", and
"But not .log". On ADR 0004 and invariant I1: "3. Fine. Supersede."

Measured: 17% of this repository's 9,103 Write, Edit, MultiEdit and Bash
calls name `.okf/`. Claude Code hands a PostToolUse hook's
`hookSpecificOutput.additionalContext` to the model after Write and Bash, with
`cwd`, `tool_name` and `tool_input` on stdin, and ignores empty output or
`{}` (spike:okf-summary-nudge/2). APM 0.33.0 writes a PostToolUse entry with
a matcher into `.claude/settings.json` once across reinstalls and records it
in `.claude/apm-hooks.json` (spike:okf-summary-nudge/3).

## Decision

kmctl ships two hooks of its own, and neither blocks:

- **SessionStart: the briefing**, as ADR 0004 and
  [ADR 0002](0002-briefing-and-rules-injected-by-the-cli.md) set it, for
  Claude Code and Antigravity.
- **PostToolUse: the summary nudge**, for Claude Code only. Its matcher is
  `Write|Edit|MultiEdit|Bash` and it runs `kmctl summary nudge --format
  claude` with the hook's stdin. When the summary is behind by ADR 0027's
  rule (never for `log.md`, indexes, handoffs or the summary itself), it
  prints one `additionalContext` naming the changed concepts and the two ways
  out: update `.okf/summary.md`, or `kmctl summary ack`. Otherwise it prints
  `{}`. It uses git only, about 2 ms a query, where `review_due` takes
  300 ms. It remembers the set it last named as a hash in
  `kmctl/summary-nudge` under the git directory, so later calls on the same
  set stay quiet and a grown set nudges again. It never writes `.okf/`.
- **The nudge runs on the copy on PATH.** The hook command sets
  `KMCTL_PINNED=1`, the escape [ADR
  0026](0026-the-kmctl-on-path-runs-the-release-a-project-s-lock-pins.md)
  records for the CI action, because ADR 0026's hand-off would start uvx
  after every matching tool call and could build an uncached pin past the
  hook's 10 s timeout. `hand_off` does not change.
- **The guard.** Like the SessionStart hook, the command checks that `kmctl`
  is on PATH and prints `{}` and exits 0 when it is missing or the verb fails,
  as it does on a copy older than this one, which exits 2 with a usage error.
  The verb itself exits 0 and prints `{}` on any failure.
- `kmctl doctor` checks the entry in `.claude/settings.json`
  (`claude.nudge-hook`).

Still rejected, as in ADR 0004: a reminder at Stop (the operator: "Not at
the end of a turn") and a commit gate.

## Consequences

- Invariant I1 names both hooks: each exits 0 and never blocks a session or
  a tool call.
- After an agent changes a concept, it hears about the summary once per
  changed set, in the same turn. It answers by editing the summary or running
  `kmctl summary ack`, the same two ways out the briefing gives.
- Antigravity and OpenCode get no nudge yet; `--format` leaves room for
  theirs.
- A copy of kmctl on PATH older than this release runs no nudge: the hook
  prints `{}` until it is upgraded.

Supersedes [ADR 0004](0004-sessionstart-is-the-only-hook.md).
