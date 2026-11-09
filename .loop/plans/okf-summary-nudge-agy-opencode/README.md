---
type: plan
title: 'Plan: okf-summary-nudge-agy-opencode'
description: Antigravity and OpenCode get the summary nudge right after a tool call changes a concept, through agy's PostToolUse hook and OpenCode's execute.after plugin hook.
tags:
- plan
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:59:12+00:00'
slug: okf-summary-nudge-agy-opencode
epic: null
depends_on: [okf-summary-nudge]
priority: 3
---

# okf-summary-nudge-agy-opencode

Relayed from: okf-summary, split at the operator's word (2026-10-18, "1. Split.")

## Intent

okf-summary-nudge's `kmctl summary nudge` for the other two harnesses, at
the operator's word: "Just when anything in .okf changes", "Not at the end
of a turn", "But not .log". Measured: 17% of this repo's 9,103 Write, Edit,
MultiEdit and Bash calls name `.okf/` (okf-summary-nudge's plan); both
harnesses can feed text back right after a tool call (spikes 1 and 2).

What changes:

- **`--format antigravity`.** `kmctl summary nudge --format antigravity`
  reads agy's PostToolUse stdin, finds the repository from
  `workspacePaths[0]` (the hook runs in `.agents/`, as the SessionStart hook
  does; `hook_workspace` in `src/kmctl/briefing.py`), and prints
  `{"injectSteps":[{"systemMessage":{"systemMessage":TEXT}}]}` when the
  summary is behind, `{}` otherwise.
- **`--format opencode`.** Reads no stdin: it takes the repository from
  `--path`, as `kmctl briefing --path` does for the OpenCode plugin, and
  prints the nudge text alone (or nothing), for the plugin to add. Node's
  `execFile` leaves a child's stdin open, so a verb that read stdin would
  wait out the timeout on every tool call (plan review round 1, p1).
- **Antigravity's hook.** `apm/antigravity/.apm/hooks/hooks.json` gains a
  PostToolUse entry (matcher `*`) running `KMCTL_PINNED=1 kmctl summary
  nudge --format antigravity`, guarded like the SessionStart one so a
  missing kmctl or verb prints `{}`, with a timeout. `KMCTL_PINNED=1` for the
  reason okf-summary-nudge gives (no hand-off per tool call).
- **OpenCode's plugin.** The plugin `src/kmctl/opencode.py` writes to
  .opencode/plugins/kmctl.js registers `ctx.tool.hook("execute.after")`
  that runs `kmctl summary nudge --format opencode --path <project>` with
  `KMCTL_PINNED=1` and stdin closed (`stdio: ["ignore", "pipe", "ignore"]`),
  asynchronously with its timeout as the briefing does, and appends the text
  as `{type: "text", text}` to `event.result.content` when there is any; it
  never throws and never blocks. `kmctl plugin patch` writes it,
  `--undo` removes it with the rest, and `kmctl doctor` checks both hooks;
  APM writes Antigravity's PostToolUse entry in the nested `{matcher,
  hooks}` form, so doctor's reading of .agents/hooks.json looks inside the
  groups (`_flat_commands` and `hook_present` in `src/kmctl/antigravity.py`
  read flat lists today).
- **Docs.** The nudge's reference and ADR (from okf-summary-nudge) name the
  three harnesses; `docs/how-to/install-kmctl-with-apm.md`'s per-harness
  notes say what the nudge does.

Done when: an agy PostToolUse payload with `workspacePaths` for a repository
whose summary is behind makes `kmctl summary nudge --format antigravity`
print the injectSteps JSON naming the concepts, the package's Antigravity
hooks carry the PostToolUse entry, the OpenCode plugin's execute.after hook
appends the nudge text to a tool result in a test of the generated JS (run
with node), and `kmctl doctor` reports both.

## Could invalidate this plan

- agy 1.4.0 may have no post-tool hook, or none whose output reaches the
  agent at once. spike:okf-summary-nudge-agy-opencode/1 (PostToolUse fires
  after write_to_file in `.agents/` with workspacePaths on stdin, and
  injectSteps reached the model; undocumented for this event, so a later agy
  may drop it)
- OpenCode's V2 plugin API may have no after-tool hook that puts text in
  front of the agent before its next step.
  spike:okf-summary-nudge-agy-opencode/2 (`ctx.tool.hook("execute.after")`
  in 2.0.32; text appended to `event.result.content` reached the model once)
