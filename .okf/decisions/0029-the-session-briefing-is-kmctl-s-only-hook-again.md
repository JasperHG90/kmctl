---
type: decision
title: "ADR 0029: The session briefing is kmctl's only hook again"
description: "kmctl drops the PostToolUse summary nudge for every harness; the briefing, the AGENTS.md duty and kmctl review due say when the summary is behind."
tags: [adr, decision, okf]
generated:
  by: process:kmctl/0.9.1
  at: 2026-10-19T05:20:55Z
status: stable
---

# ADR 0029: The session briefing is kmctl's only hook again

## Context

[ADR 0028](0028-two-hooks-the-session-briefing-and-the-summary-nudge.md)
added a second hook: after a tool call, `kmctl summary nudge` told the agent
when a concept in `.okf/` had changed after `.okf/summary.md`. It ran in
Claude Code, Antigravity and OpenCode.

Asked "Do we need the nudge at all?", the operator (2026-10-19) answered
"Ok, drop it". The reasons:

- The summary distils what is on disk in `.okf/`
  ([ADR 0027](0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md)),
  so a later agent can bring it up to date as well as the one that changed a
  concept. Catching the change in the same turn buys little.
- Three things already say when the summary is behind: the briefing's
  `summary behind: N concepts changed` line, the AGENTS.md duty to update it
  or run `kmctl summary ack`, and `kmctl review due` with the CI action.
- The nudge cost a kmctl start, about 0.25 s, after every matching tool
  call, and in Antigravity and OpenCode after every tool call, reads
  included. It needed three harness hooks and three `kmctl doctor` checks,
  and Antigravity's version relied on `injectSteps` after PostToolUse,
  which agy does not document.

## Decision

kmctl ships one hook of its own, the SessionStart briefing, as
[ADR 0004](0004-sessionstart-is-the-only-hook.md) set it, for Claude Code,
Antigravity and OpenCode's plugin. It never blocks (I1). In Antigravity kmctl
still relays okf's Stop check
([ADR 0018](0018-kmctl-runs-okf-s-stop-check-for-antigravity.md)).

Gone: the PostToolUse entries in both packages' `hooks.json`, the OpenCode
plugin's `execute.after` hook, the `kmctl summary nudge` verb and the
`claude.nudge-hook`, `antigravity.nudge-hook` and `opencode.nudge-hook`
checks. ADR 0027's freshness rule, `kmctl summary ack`, the briefing line and
`kmctl review due` stay.

Still rejected, as in ADR 0004: a nudge after code edits, a reminder at Stop
and a commit gate.

## Consequences

- A summary that falls behind mid-session stays behind until an agent acts
  on the next briefing, `kmctl review due`, or the CI report.
- No tool call waits on kmctl.
- No migration: kmctl has no outside users yet. An old settings file that
  still holds the nudge entry is harmless, because its guard prints `{}`
  when the verb is missing.

Supersedes [ADR 0028](0028-two-hooks-the-session-briefing-and-the-summary-nudge.md).
