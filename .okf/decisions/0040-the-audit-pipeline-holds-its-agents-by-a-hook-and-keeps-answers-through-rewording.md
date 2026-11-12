---
type: decision
title: "ADR 0040: The audit pipeline holds its agents by a hook and keeps answers through rewording"
description: "After the first full kmctl audit run: a kmctl audit guard PreToolUse hook holds the Claude Code agents to kmctl audit commands, answers follow a reworded claim of the same sentence, reasons go stale only on files their anchors name, checks read markdown outside the knowledge, a YAML key rename is a mutation, and a correction section sees the corrections after it."
tags: [decision]
generated:
  by: process:kmctl/0.12.1
  at: 2026-11-11T13:30:41Z
status: stable
sources:
  - resource: "src/kmctl/claims/guard.py"
  - resource: "src/kmctl/claims/sections.py"
  - resource: "src/kmctl/claims/check_store.py"
  - resource: "src/kmctl/claims/check_verbs.py"
  - resource: "src/kmctl/claims/steps.py"
  - resource: "src/kmctl/claims/mutate.py"
  - resource: "apm/.apm/agents/kmctl-claims-extractor.md"
  - resource: "apm/.apm/agents/kmctl-check-writer.md"
---

# ADR 0040: The audit pipeline holds its agents by a hook and keeps answers through rewording

## Context

On 2026-11-11 the pipeline ran over this repository's whole bundle: 180
sections, 1,094 claims, 947 of them checkable, through about 60 Haiku
agent runs (see [the audit pipeline](../architecture/audit-pipeline.md)).
Every claim but one got a check or a reason: 504 checks and 442 reasons.
The run showed seven faults in the design of
[ADR 0036](0036-claims-are-extracted-by-the-agent-through-kmctl-audit-claims.md),
[ADR 0037](0037-the-claims-and-checks-agents-get-a-plain-shell-and-i2-narrows.md)
and [ADR 0038](0038-checks-are-step-data-that-kmctl-reruns-and-only-checks-that-notice-a-change-are-stored.md):

- The agents' shell was held by instructions only, and most writer runs
  broke them: pipes into `python3`, `grep`, `head` or `jq`, and redirects
  that left files in the repository root, `.git/` and `/tmp`.
- A claim's id follows its text, so re-extracting an edited section
  reworded its claims and lost their checks.
- A reason went stale whenever any file its lines came from changed,
  keyword-search windows included, so ordinary code edits sent dozens of
  reasons back to `todo`.
- Checks never read markdown, so claims about skills, agent files and
  prompts got reasons, and the writers reported two false drifts for files
  they could not see.
- The mutations never renamed a YAML key, so a correct check on a
  workflow's input names was refused as weak.
- A markdown table is one sentence, so each claim from a table row carried
  the whole table and the spans of every row: a round of five claims from
  the architecture overview's command table was 135 KB, and a writer gave
  up after two rounds.
- A correction section was shown no corrections, so a later correction
  that overturned an earlier one was invisible to it: the earlier
  correction's claims were extracted again and drifted.

The Claude Code documentation says a subagent's front matter may carry
its own PreToolUse hooks, which run only while that subagent is active,
and that exit code 2 blocks the call. Antigravity and OpenCode have no
per-agent hook (spike:agent-audit-claims/1).

## Decision

- `kmctl audit guard --allow claims|checks` is a PreToolUse hook in the
  front matter of `kmctl-claims-extractor` and `kmctl-check-writer`. It
  lets a Bash call through only when it is one `kmctl audit GROUP`
  command, optionally after `cd DIR &&`, optionally fed by one quoted
  heredoc whose body is data. A pipe, redirect, second command or
  substitution exits 2. The rule lives in the CLI, so the agents ship no
  script. In Antigravity and OpenCode, whose translations drop the
  `hooks` key, the instructions still hold it.
- Each stored answer keeps its claim's concept, section and sentence. When
  its claim is gone and its section is extracted again, `prune` moves the
  answer to the one unanswered claim of that concept made from the same
  sentence and clears its last run, so `run` checks it against the new
  claim; with no such claim, or more than one, the answer is dropped.
- A reason goes stale only when a file its claim's anchors named changes.
  A reason whose lines came from keyword search stays until its claim
  changes.
- Checks read markdown outside the knowledge: skills, agent files and
  prompts are what the code runs. They still never read `.okf/`, `docs/`,
  READMEs, `CLAUDE.md`, `AGENTS.md` or `CHANGELOG.md`, and a step that
  matches only those names says why.
- Renaming a YAML key is a mutation (mutation version 4, so every holding
  check is measured again).
- A correction section is shown the corrections after it, so the
  extractor marks a sentence a later correction overturns as none, as it
  already does for the record's other sections.
- `kmctl audit checks todo` cuts a sentence over 800 characters to its
  first line and the lines sharing the most words with the claim, and a
  claim with no span of its own resolves only those lines' spans; the
  overview's round went from 135 KB to 24 KB.
- `kmctl audit checks todo --brief` leaves out the instructions and schema
  after an agent's first round, and the lines shown per claim are cut to
  1,500 characters; a round of five claims went from about 27 KB to 14 KB.

Rejected:

- An MCP server as the agents' only tool: still a second interface to keep
  in step with the CLI (ADR 0037).
- `Bash(kmctl audit:*)` in the agents' `tools`: the documentation does not
  say the field takes a pattern, and a pattern there gives the whole Bash
  tool.
- A claim id from the sentence alone: two claims of one sentence would
  share it.
- Keeping a reason forever: a code change can make a claim checkable.

## Consequences

In Claude Code the extractor and check writer can no longer leave
`kmctl audit`; the rule holds by construction there and by instruction in
the other harnesses, so it stays a Value in the manifesto. A carried answer
can sit on a claim that means something slightly different: `run` reruns
it and drift shows up as a failure. The hook needs `kmctl` on PATH and, for
a project agent, the trusted workspace Claude Code asks for; without them
it does not run.
