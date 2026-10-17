---
type: decision
title: "ADR 0016: Antigravity rules come from the kmctl plugin folder"
description: "kmctl writes its four knowledge rules for Antigravity into .agents/plugins/kmctl/rules/ in the form agy reads, and deletes the copies APM writes to .agents/rules/."
tags: [adr, decision, install, antigravity]
generated:
  by: process:kmctl/0.3.0
  at: 2026-10-17T06:40:44Z
status: stable
sources:
  - resource: "src/kmctl/antigravity.py"
  - resource: "src/kmctl/plugin.py"
  - resource: "src/kmctl/doctor.py"
---

# ADR 0016: Antigravity rules come from the kmctl plugin folder

## Context

[ADR 0015](0015-antigravity-gets-skills-and-rules-from-apm-and-a-kmctl-plugin-folder.md)
left the rules for Antigravity to APM, which writes them to `.agents/rules/`.
The first live agy session (agy 1.4.0, `gemini-3.8-flash-high`, 2026-10-17)
showed that none of the four rules reached it:

- APM 0.33.0, the newest release, writes Antigravity rules in Windsurf's
  form. A rule with several globs gets `globs:` as a YAML list, and agy
  refuses the file ("cannot unmarshal !!seq into string"). Three of the four
  rules have several globs.
- agy matches a glob that holds a `/` against the file's absolute path, so a
  glob relative to the repository, such as `.okf/**` or `docs/**`, never
  matches. `**/.okf/**` matches inside the hidden `.okf/` folder, and a glob
  without a `/` matches the file name (spike:antigravity-rules/3).
- agy reads several globs from one comma-separated string; a `{a,b}` brace
  pattern never matches. It loads glob rules from a plugin's `rules/` folder.

## Decision

kmctl writes the rules for Antigravity itself, as it writes the agents:
`.agents/plugins/kmctl/rules/NAME.md` for each
`apm/.apm/instructions/NAME.instructions.md`, which the wheel now carries
beside the agents. `applyTo` becomes `trigger: glob` and `globs:` as one
comma-separated string, each glob given a leading `**/`; an instruction
without `applyTo` becomes `trigger: always_on`. The body is copied
unchanged.

After APM's install, kmctl deletes the rule files the lock lists for kmctl's
package under `.agents/rules/`, so agy loads each rule once and logs no
parse error. APM writes them back on the next install and removes nothing
else because of it, and `apm uninstall` still cleans up
(spike:antigravity-rules/2). Other packages' rules stay. `kmctl doctor`
checks the rules with the rest of the plugin folder (`antigravity.plugin`)
and no longer expects kmctl's rules in `.agents/rules/`
(`antigravity.files`).

Rejected:

- Rewriting APM's files in `.agents/rules/` in place. Their hashes would no
  longer match the lock, so doctor would fail and a later APM install could
  treat them as local edits.
- Waiting for APM to fix its Antigravity writer. The newest APM has the same
  writer, and the rules would stay dead until then.

## Consequences

- Antigravity sessions get the four rules; the Claude Code rules are
  unchanged.
- The `**/` prefix also matches folders of the same name deeper in the
  repository, such as a nested `docs/`; the rules are guidance, so that is
  harmless.
- A bare `apm install` puts APM's broken copies back until the next
  `kmctl plugin install`.
