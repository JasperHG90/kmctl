---
type: plan
title: 'Plan: agent-audit-claims-skill'
description: An extract-claims skill and a Haiku kmctl-claims-extractor subagent in kmctl's APM package that drive kmctl audit claims todo and submit and hand the main session only a short summary.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-11T07:36:03+00:00'
slug: agent-audit-claims-skill
epic: agent-audit
depends_on:
- agent-audit-claims
priority: 2
schema_version: '2.0'
---

# agent-audit-claims-skill

Relayed from: none

## Intent

Ticket 2 of the agent-audit epic, after agent-audit-claims, which lands the
new `kmctl audit` group with its `claims todo`, `submit` and `list` verbs,
the claim models and the git-ignored store. The CLI makes no model call:
the extraction is done by the harness's own model, the Haiku agent this
ticket adds, and kmctl only hands out sections, validates and stores. This ticket adds what drives those verbs from a coding
agent's session, in Claude Code and Antigravity, shipped through kmctl's APM
package (ADR 0014, ADR 0020, ADR 0021):

- **The skill**, `new:apm/.apm/skills/extract-claims/SKILL.md`, made with
  skill-creator (ADR 0007) and thin (`.claude/rules/skills-are-thin.md`). It
  runs `kmctl audit claims todo` for the counts, stops when nothing is left, splits
  the remaining concepts into batches, dispatches the extractor agent per
  batch (in parallel when there are several), then reports the agents'
  summaries and the counts from `kmctl audit claims list`. It never reads a claim,
  validates a schema or restates the instructions: `kmctl audit claims todo
  --json` hands the instructions to the agent, and `kmctl audit claims
  submit` enforces the schema.
- **The agent**, `new:apm/.apm/agents/kmctl-claims-extractor.md`, with
  `model: haiku`. It runs `kmctl audit claims todo --json` for its batch,
  writes verdicts per the instructions it was handed, pipes them to `kmctl
  audit claims submit -`, retries a refused section once with the refusal's fix, and
  returns only a short summary: sections done, claims stored, sections still
  refused and why. The main session never sees a claim, which is what the
  operator asked for. Haiku is the default because, in the prototype's
  "Claude as the checker" pilot (its README, 2026-11-10), Haiku subagents
  agreed with Opus on 46 of 60 claims at about the same token cost; that
  pilot measured checking, not extraction.
- **Its tools: Read and a plain shell (the operator's decision).** The
  agent's `tools` are `Read, Bash`, and its instructions say it writes only
  through `kmctl audit claims ...` and never edits `.okf/`, `docs/` or a
  `verified` stamp. A shell limited to `kmctl audit claims` commands cannot be
  held in every harness: spike:agent-audit-claims/1 found that Antigravity
  (agy 1.5.5) has no per-agent command allowlist (`commandExecutionPolicy`
  is only `off`, `auto` or `eager`; hooks are global and their payload names
  no agent), that kmctl's `translate_agent` refuses a command pattern (the spike tried `Bash(kmctl claims:*)`, the verbs' name before they moved under `kmctl audit`),
  and left Claude Code unconfirmed (the agent `tools` resolver maps that
  entry to the whole Bash tool; whether the pattern becomes a permission
  rule was not seen).
- **Its translations.** `kmctl plugin patch` already ships every agent in
  the package to Antigravity (`src/kmctl/antigravity.py`, ADR 0015) and
  OpenCode (`src/kmctl/opencode.py`, ADR 0024). `Read` and `Bash` are in the
  Antigravity tool table already (`view_file`, `run_command`), so the
  translation needs no code change, only tests. Antigravity's translation
  sets `model: inherit`, so the Haiku default holds in Claude Code only.
- **I2 is relaxed in the same change.** I2 says audits never write
  knowledge, and the extractor's plain shell can hold that only by its
  instructions. Following `.claude/rules/manifesto-invariants.md` (a rule
  with no test is a Value), `.okf/manifesto.md` narrows I2 to what holds by
  construction: the `kmctl-auditor` agent has no shell and no write tool,
  and the CI action's audit never commits or pushes and holds no GitHub
  token, so neither writes `.okf/`, `docs/` or a `verified` stamp. Its
  status stays `planned`, as no test pins it. A new Value says the claims
  and checks agents have a shell and write only through `kmctl audit claims`
  and `kmctl audit checks`, held by their instructions. The CI action's agent
  does have `run_shell` (ADR 0017), so I2 must not claim it has no shell;
  what holds is that nothing it changes is committed.
  `.okf/architecture/overview.md` describes the extractor beside the
  auditor, and its Depicts entry for I2 is reworded to the narrowed text.
- **A decision record here**, written with `kmctl new decision`, after the
  store's record that agent-audit-claims lands: the claims and checks
  agents get a plain shell and I2 narrows, with spike:agent-audit-claims/1
  as the evidence. Rejected: MCP-only tools (a kmctl MCP server for
  submitting would be a second interface to keep in step with the CLI the
  operator wants agents to call); restricting the shell in Claude Code only
  (one harness held by construction and one by instructions is two rules
  for one agent, and Claude Code's restriction is unconfirmed); a file
  handoff (the agent writes its answer to a file the skill submits, which
  still needs a write tool that can reach `.okf/`, and moves the work back
  into the main session).
- **The briefing budget.** `kmctl briefing` lists every skill in the package
  (`src/kmctl/briefing.py`), and I3 caps the briefing at 500 tokens, about
  2,000 characters. It is 1,866 characters on this repository today, so the
  new skill's first sentence must stay short enough to keep
  `tests/test_briefing.py::test_briefing_token_budget` green.
- `.okf/manifesto.md` Parts names the new skill and agent beside the audit
  agent, with `.okf/summary.md` and `.okf/log.md` in step.

**Measured effect.** agent-audit-claims measured the work this hands out:
over the 66 commits since 2026-10-15 that changed a concept in `.okf/`, the
median changed 2 of 38 concepts, so a typical run dispatches one small
batch. Without this ticket a session that wants claims has no route at all:
0 of the package's 7 skills and 0 of its 1 agent touch claims.

**The outcome that shows it worked:** in Claude Code, on a fixture
repository, `/extract-claims` leaves `kmctl audit claims todo` with nothing
to hand out, `kmctl audit claims list` shows the claims, and the main session's
transcript holds the agents' summaries but no claim text.

## Problems

- P1: No skill or agent drives the `kmctl audit claims` verbs, so a session that wants a bundle's claims must do the extraction itself and hold every claim in its own context
- P2: I2 says audits never write knowledge, but a subagent's shell cannot be limited to `kmctl audit claims` commands in Antigravity (spike:agent-audit-claims/1), so the extractor can hold I2 only by its instructions

## Goals

- G1: A main session in Claude Code or Antigravity gets a bundle's claims extracted by a subagent and sees only a short summary
- G2: The manifesto's invariants claim only what holds by construction, and the agents' write discipline is stated as a Value

## Outcomes

### O1: The extract-claims skill dispatches a Haiku extractor agent that runs `kmctl audit claims todo` and `kmctl audit claims submit` and returns a summary
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:apm/.apm/skills/extract-claims/SKILL.md`, `new:apm/.apm/skills/extract-claims/evals/evals.json`, `new:apm/.apm/skills/extract-claims/evals/results.md`, `new:apm/.apm/agents/kmctl-claims-extractor.md`, `tests/test_apm_package.py`, `tests/test_skills.py`
- checked by: `tests/test_apm_package.py` (package and wheel carry the skill and the agent), a test in `tests/test_skills.py` that every `kmctl` command the skill and agent name exists, and the skill's skill-creator evals
- seen by: operator

### O2: `kmctl plugin patch` translates the extractor agent, with Read and a shell, for Antigravity and OpenCode
- kind: support
- goal: G1
- fixes: P1
- needs: O1
- touches: `tests/test_antigravity.py`, `tests/test_opencode.py`
- checked by: `tests/test_antigravity.py` and `tests/test_opencode.py` (the extractor translates with `view_file` and `run_command` in Antigravity and without `commandExecutionPolicy: "off"`, and the auditor's translation is unchanged)
- seen by: nobody

### O3: The briefing stays in budget and the manifesto names the skill and agent
- kind: support
- goal: G1
- fixes: P1
- needs: O1
- touches: `.okf/manifesto.md`, `.okf/summary.md`, `.okf/log.md`, `tests/test_briefing.py`
- checked by: `tests/test_briefing.py::test_briefing_token_budget`, `kmctl check` and strict OKF validation in the pre-commit hooks
- seen by: operator

### O4: The manifesto narrows I2 to what holds by construction, adds a Value for the agents' shell, and a decision record says why
- kind: support
- goal: G2
- fixes: P2
- needs: O1
- touches: `.okf/manifesto.md`, `.okf/architecture/overview.md`, `.okf/decisions/index.md`, `.okf/summary.md`, `.okf/log.md`
- checked by: `kmctl check`, strict OKF validation in the pre-commit hooks, and a hand check that the overview's Depicts entry for I2 matches the manifesto (`.claude/rules/diagrams-stay-current.md`)
- seen by: operator

## Could invalidate this plan

- none
