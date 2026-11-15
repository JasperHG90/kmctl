---
type: decision
title: "ADR 0037: The claims and checks agents get a plain shell and I2 narrows"
description: "The kmctl-claims-extractor and the later check writer get Read and a plain shell and write only through kmctl audit, held by their instructions, since Antigravity cannot limit a subagent's shell; I2 narrows to the read-only auditor and the CI audit."
tags: [decision]
generated:
  by: process:kmctl/0.12.1
  at: 2026-11-11T09:22:28Z
status: stable
sources:
  - resource: "packages/kmctl/apm/.apm/agents/kmctl-claims-extractor.md"
  - resource: "packages/kmctl/apm/.apm/skills/extract-claims/SKILL.md"
---

# ADR 0037: The claims and checks agents get a plain shell and I2 narrows

## Context

[ADR 0036](0036-claims-are-extracted-by-the-agent-through-kmctl-audit-claims.md)
has a coding agent extract claims through `kmctl audit claims todo` and
`submit`. The operator wants that work in a subagent, so the main session
sees only a summary, and the subagent needs a shell to call `kmctl`. I2 said
audits never write knowledge, which held because the `kmctl-auditor` agent
has only Read, Grep and Glob.

Spike agent-audit-claims/1 (in `.loop/spikes/`) asked whether a subagent's
shell can be limited to `kmctl` claims commands. In Antigravity (agy 1.5.5)
it cannot: `commandExecutionPolicy` is only `off`, `auto` or `eager`, hooks
are global and their payload names no agent, and kmctl's `translate_agent`
refuses a command pattern in `tools`. In Claude Code the agent `tools`
resolver maps such an entry to the whole Bash tool; whether the pattern
also becomes a permission rule was not seen.

## Decision

- The `kmctl-claims-extractor` agent (and the check writer a later ticket
  adds) has `tools: Read, Bash`. Its instructions say it writes only through
  `kmctl audit claims ...` (or `kmctl audit checks ...`) and never edits
  `.okf/`, `docs/` or a `verified` stamp. That holds by instruction, not by
  construction, in every harness alike.
- `.okf/manifesto.md` narrows I2 to what holds by construction: the
  `kmctl-auditor` agent has no shell and no write tool, and nothing the CI
  action's audit changes is committed or pushed, as the step that runs the
  audit agent holds no GitHub token; only the later publish step does
  ([ADR 0017](0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md)).
  I2 stays `planned`. A new Value states the claims and checks agents'
  discipline.

Rejected:

- MCP-only tools: a kmctl MCP server for submitting would be a second
  interface to keep in step with the CLI the operator wants agents to call.
- Restricting the shell in Claude Code only: one harness held by
  construction and one by instruction is two rules for one agent, and
  Claude Code's restriction is unconfirmed.
- A file handoff, where the agent writes its answer to a file the skill
  submits: it still needs a write tool that can reach `.okf/`, and it moves
  the work back into the main session.

## Consequences

The extractor could edit a file if it ignored its instructions; nothing
stops it but the instructions and the harness's own permission prompts.
`kmctl plugin patch` translates it for Antigravity with `view_file` and
`run_command` and no `commandExecutionPolicy: off`, and for OpenCode with a
shell. Antigravity's translation sets `model: inherit`, so the Haiku default
holds in Claude Code only.

## Correction, 2026-11-11

[ADR 0040](0040-the-audit-pipeline-holds-its-agents-by-a-hook-and-keeps-answers-through-rewording.md):
in Claude Code the extractor and check writer are now held to
`kmctl audit` commands by a PreToolUse hook in their front matter
(`kmctl audit guard`), since the first full run showed most writer runs
broke the instruction. In Antigravity and OpenCode the instruction alone
still holds it.
