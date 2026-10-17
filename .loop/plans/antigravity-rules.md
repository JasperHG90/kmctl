---
type: plan
title: 'Plan: antigravity-rules'
description: Antigravity gets kmctl's four knowledge rules from kmctl's plugin folder, in a form agy parses and matches, instead of APM's broken copies.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:28:18+00:00'
slug: antigravity-rules
epic: null
depends_on: []
priority: null
---

# antigravity-rules

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none

## Intent

A live run of agy 1.4.0 (with `gemini-3.8-flash-high`, in a scratch project
installed by `kmctl plugin install --harness claude,antigravity`) showed that
none of kmctl's four rules reaches an Antigravity session:

- APM 0.33.0 writes `.agents/rules/` in Windsurf's format. A rule with
  several globs gets `globs:` as a YAML list, and agy refuses the file
  ("cannot unmarshal !!seq into string"). That is three of the four.
- agy matches a glob that holds a `/` against the file's absolute path, so a
  repository-relative glob such as `.okf/**` never matches. Tested: `docs/**`
  and docs/guide/intro.md never fired for docs/guide/intro.md, while
  `**/docs/**`, `*.md` and `intro.md` did. That is the fourth.
- agy takes several globs as one comma-separated string (`"**/README.md,
  **/docs/**"` fired for both files; a `{a,b}` brace pattern did not), and it
  loads glob rules from a plugin's `rules/` folder.
- APM 0.33.0 is the newest release, and its Antigravity writer is the same.

So kmctl writes the rules itself, as it does the agents: `plugin_files` in
`src/kmctl/antigravity.py` adds rules/NAME.md for each
apm/.apm/instructions/NAME.instructions.md (shipped in the wheel beside the
agents), with front matter `trigger: glob` and `globs:` one comma-separated
string of the `applyTo` globs, each given a leading `**/` unless it has one;
the body is unchanged. A rule without `applyTo` gets `trigger: always_on`.
After APM's install, kmctl deletes the copies APM wrote of kmctl's own rules
under `.agents/rules/` (the paths the lock lists for kmctl's package there),
so agy loads each rule once and logs no parse error. Other packages' rules
are left alone.

`kmctl doctor` follows: `antigravity.plugin` compares the rules as it does
the other files, and `antigravity.files` no longer expects kmctl's rules in
`.agents/rules/`. ADR 0015 records the change, and the install how-to and
`docs/reference/commands.md` say where the rules are.

It worked when a scratch install for antigravity leaves the four rules in
`.agents/plugins/kmctl/rules/` with single-string `**/` globs, none of
kmctl's rules in `.agents/rules/`, `agy plugin validate --strict` reports no
finding for the folder, and doctor passes.

## Could invalidate this plan

- Deleting the rule files APM deployed for kmctl's package may make a later
  `apm install` (a second `kmctl plugin install`) or `apm uninstall` fail,
  refuse, or skip files, so kmctl could not remove them. It does not
  (spike:antigravity-rules/1): APM writes the deleted files back without a
  skip, and `apm uninstall` still exits 0 and leaves nothing.
