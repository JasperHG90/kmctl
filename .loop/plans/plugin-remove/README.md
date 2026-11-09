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
  `apm.yml` entry, named as APM names it: `HOST[:PORT]/OWNER/REPO/apm`,
  built from that entry's own `git:` URL (its host, port and path without
  `.git`), keeping its case. The lock is not used for the name: APM
  lowercases a GitHub `repo_url` there. Both forms this builds were tested,
  `github.com/JasperHG90/Knowledge-management/apm` (spike:plugin-remove/5)
  and `127.0.0.1:PORT/o/kmctl/apm` (spike:plugin-remove/3). That takes kmctl's and okf's skills, agent,
  rules, hooks and lock entries with it (spike:plugin-remove/3).
- The harnesses kept. When some stay installed, it reinstalls them alone
  with the normal install, from the `git:` source and at the `ref` the
  removed entry named, so a partial remove never changes their version.
  Dropping one target and reinstalling instead leaves okf's Antigravity hook
  script behind, listed in the lock (spike:plugin-remove/2). If that
  reinstall fails (offline, say), remove refuses with exit 1, names APM's
  cause, says the kept harnesses were uninstalled, and names the exact
  `kmctl plugin install --harness KEPT --source SOURCE` that puts them back,
  saying it installs them at this kmctl's version.
- `targets:` in `apm.yml`. Install only adds targets, so remove cannot tell
  whether a target was there before kmctl. It takes a removed harness out of
  `targets:` only when no other `dependencies.apm` entry is left after the
  uninstall, and otherwise keeps it and says so in a note, so the
  repository's own APM packages keep their target. That note also says a
  bare `apm install` (without `--target`) would deploy kmctl to that
  harness again. doctor's
  `harnesses_found` counts `apm.yml` targets only when the lock lists no
  kmctl package, so a kept target no longer marks a removed harness as
  installed.
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
- The uninstall name might differ for the real GitHub source, whose lock
  has no port and a lowercased repo_url. Built from the entry's `git:` URL
  instead, it does not (spike:plugin-remove/5; spike:plugin-remove/4
  ran the same check but counted settings.json): `apm uninstall
  github.com/JasperHG90/Knowledge-management/apm` removed a GitHub-sourced
  entry and its files, and the dry run took the short form too.
