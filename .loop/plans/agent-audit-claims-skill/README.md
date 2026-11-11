---
type: plan
title: 'Plan: agent-audit-claims-skill'
description: An extract-claims skill and a Haiku kmctl-claims-extractor subagent in kmctl's APM package that drive kmctl claims todo and submit and hand the main session only a short summary.
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
`kmctl claims todo`, `submit` and `list` verbs, the claim models and the
git-ignored store. This ticket adds what drives those verbs from a coding
agent's session, in Claude Code and Antigravity, shipped through kmctl's APM
package (ADR 0014, ADR 0020, ADR 0021):

- **The skill**, `new:apm/.apm/skills/extract-claims/SKILL.md`, made with
  skill-creator (ADR 0007) and thin (`.claude/rules/skills-are-thin.md`). It
  runs `kmctl claims todo` for the counts, stops when nothing is left, splits
  the remaining concepts into batches, dispatches the extractor agent per
  batch (in parallel when there are several), then reports the agents'
  summaries and the counts from `kmctl claims list`. It never reads a claim,
  validates a schema or restates the instructions: `kmctl claims todo --json`
  hands the instructions to the agent, and `kmctl claims submit` enforces the
  schema.
- **The agent**, `new:apm/.apm/agents/kmctl-claims-extractor.md`, with
  `model: haiku`. It runs `kmctl claims todo --json` for its batch, writes
  verdicts per the instructions it was handed, pipes them to `kmctl claims
  submit -`, retries a refused section once with the refusal's fix, and
  returns only a short summary: sections done, claims stored, sections still
  refused and why. The main session never sees a claim, which is what the
  operator asked for. Haiku is the default because, in the prototype's
  "Claude as the checker" pilot (its README, 2026-11-10), Haiku subagents
  agreed with Opus on 46 of 60 claims at about the same token cost; that
  pilot measured checking, not extraction.
- **Its translations.** `kmctl plugin patch` already ships every agent in
  the package to Antigravity (`src/kmctl/antigravity.py`, ADR 0015) and
  OpenCode (`src/kmctl/opencode.py`, ADR 0024). Antigravity's translation
  sets `model: inherit`, so the Haiku default holds in Claude Code only, and
  it maps tool names through a fixed table that refuses anything else. How
  the agent's shell is limited (risk 1) decides whether that table changes.
- **I2.** The agent writes no file itself; its only writes are through
  `kmctl claims submit`, which writes only to the git-ignored store
  (agent-audit-claims). The agent's tools must not let it write `.okf/` or
  `docs/`; risk 1 asks whether the harnesses can enforce that.
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
repository, `/extract-claims` leaves `kmctl claims todo` with nothing to
hand out, `kmctl claims list` shows the claims, and the main session's
transcript holds the agents' summaries but no claim text.

## Problems

- P1: No skill or agent drives the `kmctl claims` verbs, so a session that wants a bundle's claims must do the extraction itself and hold every claim in its own context

## Goals

- G1: A main session in Claude Code or Antigravity gets a bundle's claims extracted by a subagent and sees only a short summary

## Outcomes

### O1: The extract-claims skill dispatches a Haiku extractor agent that runs `kmctl claims todo` and `kmctl claims submit` and returns a summary
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:apm/.apm/skills/extract-claims/SKILL.md`, `new:apm/.apm/skills/extract-claims/evals/evals.json`, `new:apm/.apm/skills/extract-claims/evals/results.md`, `new:apm/.apm/agents/kmctl-claims-extractor.md`, `tests/test_apm_package.py`, `tests/test_skills.py`
- checked by: `tests/test_apm_package.py` (package and wheel carry the skill and the agent), a test in `tests/test_skills.py` that every `kmctl` command the skill and agent name exists, and the skill's skill-creator evals
- seen by: operator

### O2: `kmctl plugin patch` translates the extractor agent for Antigravity and OpenCode with its shell limit intact
- kind: support
- goal: G1
- fixes: P1
- needs: O1
- touches: `src/kmctl/antigravity.py`, `src/kmctl/opencode.py`, `tests/test_antigravity.py`, `tests/test_opencode.py`
- checked by: `tests/test_antigravity.py` and `tests/test_opencode.py` (the extractor translates, keeps only the shell the risk-1 spike shows each harness can limit, and the auditor's translation is unchanged)
- seen by: nobody

### O3: The briefing stays in budget and the manifesto names the skill and agent
- kind: support
- goal: G1
- fixes: P1
- needs: O1
- touches: `.okf/manifesto.md`, `.okf/summary.md`, `.okf/log.md`, `tests/test_briefing.py`
- checked by: `tests/test_briefing.py::test_briefing_token_budget`, `kmctl check` and strict OKF validation in the pre-commit hooks
- seen by: operator

## Could invalidate this plan

- The extractor must run `kmctl claims todo` and `kmctl claims submit` itself so the main session never holds claims, so it needs a shell. The audit-agent-and-skills plan kept I2 by the tool list alone (no Bash), because `kmctl new` and `kmctl init` write knowledge. If neither Claude Code nor Antigravity can limit a subagent's shell to `kmctl claims` commands, and `src/kmctl/antigravity.py` refuses any tool name outside its table, I2 rests on the agent's instructions alone and the design must change: the subagent returns claims to the skill, or submits through something other than a shell. Spike pending: a spike-runner is settling this against agent-audit-claims; the coordinator will cite its spike:agent-audit-claims/N here.
