---
type: plan
title: 'Plan: agent-audit-checks-skill'
description: A write-checks skill and a Haiku kmctl-check-writer subagent in kmctl's APM package that drive kmctl audit checks todo, try and submit and hand the main session only a short summary.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-11T08:10:29+00:00'
slug: agent-audit-checks-skill
epic: agent-audit
depends_on:
- agent-audit-checks
- agent-audit-claims-skill
schema_version: '2.0'
---

# agent-audit-checks-skill

Relayed from: none

## Intent

Ticket 4 of the agent-audit epic. agent-audit-checks lands `kmctl audit
checks todo`, `try`, `submit`, `run` and `list`, the step DSL and the weak
bar. The CLI makes no model call: the checks are written by the harness's
own model, the Haiku agent this ticket adds, and kmctl validates, measures,
stores and reruns them.
agent-audit-claims-skill lands the extract-claims skill and its Haiku agent,
the agents' plain shell, and the narrowed I2 with its new Value. This ticket
adds what drives the checks verbs from a coding agent's session, in Claude
Code and Antigravity, shipped through kmctl's APM package (ADR 0014,
ADR 0020, ADR 0021), built the same way as the claims skill:

- **The skill**, `new:apm/.apm/skills/write-checks/SKILL.md`, made with
  skill-creator (ADR 0007) and thin (`.claude/rules/skills-are-thin.md`). It
  runs `kmctl audit checks todo` for the counts and stops when nothing is left. It
  splits the claims into batches by concept, dispatches the check-writer
  agent per batch (in parallel when there are several), then reports the
  agents' summaries and the counts from `kmctl audit checks list`. It never reads a
  check, restates the step DSL or judges strength: `kmctl audit checks todo
  --json` hands the agent the instructions and answer schema, and `kmctl
  audit checks submit` enforces the schema and the weak bar.
- **The agent**, `new:apm/.apm/agents/kmctl-check-writer.md`, with
  `model: haiku`, Read and a plain shell, as agent-audit-claims-skill decided
  for the extractor (the shell question is settled there, with
  spike:agent-audit-claims/1; this ticket adds nothing to it). Its
  instructions say it writes only through `kmctl audit checks ...` and never
  edits `.okf/`, `docs/` or a `verified` stamp. The agent runs
  `kmctl audit checks todo --json` for its batch and reads the lines it is handed,
  plus more of the repository when they fall short. It tests each draft with
  `kmctl audit checks try -` until it holds and misses no mutant, or gives a reason
  no check fits. It stores answers with `kmctl audit checks submit -`, retries a
  refused claim once with the refusal's fix, and returns only a short
  summary: checks stored, reasons, drift found, claims still refused and
  why. The main session never sees a check or a step. Haiku is the default
  because, in the prototype's "Claude as the checker" pilot (60 claims),
  Haiku agreed with Opus on 46 of 60 at 5.4k tokens a claim against Opus's
  5.1k, and caught both of the pipeline's false failures. Read access fixes
  the prototype writer's main failure, guessing code from too few lines,
  because the agent can open the file before `try`.
- **Its translations.** `kmctl plugin patch` already ships every agent to
  Antigravity (`src/kmctl/antigravity.py`) and OpenCode
  (`src/kmctl/opencode.py`), and Read and Bash are in the Antigravity tool
  table, so only tests change. Antigravity sets `model: inherit`, so the Haiku
  default holds in Claude Code only.
- **The briefing budget.** `kmctl briefing` lists every shipped skill, one
  line each, cut to 12 words (`src/kmctl/briefing.py`), and I3 caps it below
  500 tokens (2,000 characters). It is 1,866 characters on this repository
  today. A full 12-word line is about 85 characters, so two of them (this
  skill and extract-claims) would take it to about 2,036, over the cap. The
  skill's description must open with a short first sentence (about 45
  characters, such as "Write checks for a bundle's stored claims."), so
  both new lines fit with about 25 characters to spare.
- `.okf/manifesto.md` Parts names the skill and agent beside the extractor,
  with `.okf/summary.md` and `.okf/log.md` in step.

**Measured effect.** Without this ticket, no session has a route to checks
that keeps them out of the main context: 0 of the package's 7 skills and
0 of its 1 agent touch checks. Per the prototype's pilots, a writer that
reads first costs about 5k tokens a claim. The weak bar refused 25 of 161
holding checks there, and each refusal reaches the agent, not the main
session.

**The outcome that shows it worked:** in Claude Code, on a fixture
repository with stored claims, `/write-checks` leaves `kmctl audit checks
todo` with nothing to hand out, and `kmctl audit checks list` shows a check or a reason
for every claim. The main session's transcript holds the agents' summaries
but no step.

## Problems

- P1: No skill or agent drives the `kmctl audit checks` verbs, so a session that wants checks must write them itself and hold every claim, line and draft in its own context

## Goals

- G1: A main session in Claude Code or Antigravity gets a bundle's claims checked by a subagent and sees only a short summary

## Outcomes

### O1: The write-checks skill dispatches a Haiku check-writer agent that runs `kmctl audit checks todo`, `try` and `submit` and returns a summary
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:apm/.apm/skills/write-checks/SKILL.md`, `new:apm/.apm/skills/write-checks/evals/evals.json`, `new:apm/.apm/skills/write-checks/evals/results.md`, `new:apm/.apm/agents/kmctl-check-writer.md`, `tests/test_apm_package.py`, `tests/test_skills.py`
- checked by: `tests/test_apm_package.py` (package and wheel carry the skill and the agent), a test in `tests/test_skills.py` that every `kmctl` command the skill and agent name exists, and the skill's skill-creator evals
- seen by: operator

### O2: `kmctl plugin patch` translates the check-writer agent, with Read and a shell, for Antigravity and OpenCode
- kind: support
- goal: G1
- fixes: P1
- needs: O1
- touches: `tests/test_antigravity.py`, `tests/test_opencode.py`
- checked by: `tests/test_antigravity.py` and `tests/test_opencode.py` (the check writer translates with `view_file` and `run_command` in Antigravity, and the auditor's and extractor's translations are unchanged)
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

- none
