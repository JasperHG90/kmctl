---
type: plan
title: 'Plan: plugin-remove'
description: kmctl plugin remove takes out what kmctl plugin install put in, per harness, and leaves everything else.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:04:05+00:00'
slug: plugin-remove
epic: null
depends_on:
- harness-prompt
- antigravity-rules
- antigravity-okf-stop-hook
priority: null
---

# plugin-remove

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none

## Intent

Add `kmctl plugin remove`, the undo of `kmctl plugin install`, to
`src/kmctl/plugin.py` (the logic, no prompts) and `src/kmctl/__init__.py`
(the command). It takes `--harness`, `--scope` and `--json` like install. It
asks the same harness question when `--harness` is left out at a terminal,
with the installed harnesses (`harnesses_found` in `src/kmctl/doctor.py`) as
the default, and refuses without a terminal or with `--json`.

For the harnesses named, it removes:

- APM's files. It runs `apm uninstall` (`-g` at user scope) on kmctl's
  `apm.yml` entry, named as APM names it: `HOST/OWNER/REPO/apm` built from
  the lock's host, port and repo_url, which takes kmctl's and okf's skills,
  agent, rules, hooks and lock entries with it (spike:plugin-remove/1). When
  harnesses stay installed, it then runs the normal install for them alone,
  from the `git:` source the removed entry named, because dropping one
  target from `targets:` leaves okf's Antigravity hook script behind, listed
  in the lock (spike:plugin-remove/2). Either way it takes the removed
  harnesses out of `targets:` in `apm.yml`, which install only adds to
  (spike:plugin-remove/3).
- For claude, kmctl's SessionStart hook in `.claude/settings.json` (found by
  its command, every other key and hook kept) and kmctl's `okf-bundle` MCP
  entry in `.mcp.json` (at user scope, `claude mcp remove --scope user`).
  An okf server kmctl did not write stays.
- For antigravity, the folder `.agents/plugins/kmctl/`, and
  .agents/hooks.json when APM's uninstall left it empty (`{}`).

When nothing is installed it says so and exits 0. A second run changes
nothing. It ends with a `Next: kmctl doctor` line. The help,
`docs/reference/commands.md` and the install how-to document it.

It worked when, in a scratch consumer installed for claude and antigravity
from a local git server, `kmctl plugin remove --harness antigravity` leaves
claude's install whole (doctor passes for claude) and nothing of kmctl under
`.agents/`; and `kmctl plugin remove --harness claude,antigravity` then
leaves no kmctl file, hook, MCP entry or lock entry, with the repository's
other files, `apm.yml` entries, hooks and MCP servers untouched.

## Could invalidate this plan

- Uninstalling kmctl's entry and reinstalling the harnesses kept may leave
  APM files of the removed harness, okf's transitive skills or lock entries
  behind, so remove would have to delete APM's files itself. It leaves none
  (spike:plugin-remove/3): after a claude and antigravity install, `apm
  uninstall` left no APM file and no lock (only `{}` in
  .agents/hooks.json, which remove deletes), and reinstalling claude alone
  left nothing under .agents/ and claude whole. Dropping a target and
  reinstalling instead leaves okf's Antigravity hook script behind
  (spike:plugin-remove/2), which is why remove does not do that.
