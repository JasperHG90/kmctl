---
type: plan
title: 'Plan: consumer-surfaces'
description: 'Fix four things kmctl ships into consumer repositories (issues 20 to 23), the hook''s install hint, the diagrams rule, the Antigravity rule comment and the block''s rules folder.'
tags:
- plan
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:31:13+00:00'
slug: consumer-surfaces
epic: null
depends_on: []
priority: null
---

# consumer-surfaces

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none
<!-- When this ticket carries a finding raised while building another ticket,
replace "none" with that ticket's slug and the finding, in one line (ADR 0001). -->

## Intent

Four things kmctl ships into a consumer repository say something wrong for
that repository (issues #20 to #23). Each gets fixed where it is written.

1. **#20, the install hint names the pinned release.** The Claude Code
   SessionStart hook in `apm/claude/.apm/hooks/hooks.json` and its twin
   `HOOK_COMMAND` in `src/kmctl/plugin.py` suggest `uv tool install
   git+https://github.com/JasperHG90/kmctl` with no ref, so both install the
   default branch. Both hints (missing kmctl, failed briefing) gain
   `@vVERSION`. `HOOK_COMMAND` builds it from the CLI's own version, so
   `hook_entry()` and doctor's `claude.hook` check keep matching the
   package of the same release. `scripts/release.py` `set` also rewrites the
   ref in `hooks.json`, beside the docs' install lines, so each release tag
   carries a hook naming itself. The hook still checks for kmctl and exits 0
   (`.claude/rules/cli-version-floor.md`, the-hook-survives-a-missing-cli).
   The Antigravity hook prints no install hint, so it does not change.
   ADR 0026 already sends a kmctl of any release to the pinned one; this
   fix only stops the hint from installing an unreleased HEAD.
2. **#21, `diagrams-stay-current` stops asking users to edit it.** The
   sentence "change them to where this repository's code lives" in
   `apm/claude/.apm/instructions/diagrams-stay-current.instructions.md`
   goes. In its place: the globs name common source folders, and a
   repository whose code lives elsewhere adds a rule of its own under
   another name that names its folders, because `apm install` overwrites
   this file and doctor counts an edit as drift (ADR 0011's 2026-10-16
   correction). The Antigravity copy and the OpenCode copy come from this
   file, so they follow.
3. **#22, installed Antigravity rules drop the maintainer comment.**
   `notice()` in `scripts/sync_antigravity_rules.py` goes, so the copies in
   `apm/antigravity/.apm/instructions/` open with their front matter and the
   Claude body only. What marks them as generated for maintainers is what
   already guards them: the pre-commit hook that regenerates them on any
   edit and the stale-copy test in `tests/test_apm_package.py`, plus the
   script's docstring. A 2026-10-19 correction to ADR 0020
   (`.okf/decisions/0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest.md`)
   records that the comment is gone and why.
4. **#23, the kmctl block names the rules folder of each installed
   harness.** `BLOCK` in `src/kmctl/scaffold.py` says the rules are in
   `.claude/rules/` for every repository. `kmctl init` and `kmctl update`
   write the line from the harnesses `harnesses_found` in
   `src/kmctl/doctor.py` reports: `.claude/rules/` for Claude Code,
   `.agents/rules/` for Antigravity, `.opencode/rules/` for OpenCode. When
   none is found, as on a first `kmctl init` before `apm install`, the line
   names all three, each with its tool. The same block goes to CLAUDE.md
   and AGENTS.md. The briefing's line in `src/kmctl/briefing.py`
   (".claude/rules/ holds the rules for writing knowledge") has the same
   fault and reaches Antigravity and OpenCode too; it stops naming one
   folder. The worst-case briefing measures 494 of its 500-token budget
   (invariant I3; `tests/test_briefing.py`, a summary 100 concepts behind
   with a long handoff title, measured 2026-10-19), so the new line must
   not be longer than the old one: it says "the rules files your tool
   loads" or similar, not a list of folders. ADR 0011
   (`.okf/decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code.md`) gets a
   correction for the block line.

Tests and docs that pin the old text change with it: `tests/test_plugin.py`,
`tests/test_repo_name.py`, `tests/test_apm_package.py`,
`tests/scripts/test_release.py`, `tests/test_init.py`, and
`docs/reference/commands.md` where it describes the block or the briefing.

Outcome: in a fresh consumer installed for Antigravity at a release tag, the
Claude hook hint ends `kmctl@vX.Y.Z`, no installed rule contains
`sync_antigravity_rules` or asks to be edited, and `kmctl update` writes an
AGENTS.md block that names `.agents/rules/`. The gates pass.

## Could invalidate this plan

- none
