---
type: manifesto
title: "Manifesto: kmctl"
description: What kmctl is for, where each kind of knowledge lives, the parts (CLI, plugin, CI action), the invariants, values, and what is out of scope for now.
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [manifesto, design, invariants]
status: stable
---

# Manifesto: kmctl

A repository's knowledge is only useful while it is true, and nothing can
force it to stay true. An agent can forget to update a decision, and no
deterministic hook can tell whether an architecture page still matches the
code. kmctl does not pretend otherwise. It does two things instead:

1. **It puts the right knowledge in front of the agent** at the start of
   every session: where knowledge lives, the rules for writing it, and what
   is due for review. Injecting into context works in every harness; a page
   the agent has to find does not (ADR 0002).
2. **It audits.** A separate agent checks, on request or in CI, that
   decisions still hold, the architecture still matches the code and the
   practices still have their evidence. It reports; a person decides
   (ADR 0005).

kmctl came out of the setup in `loop-harness` v2, which worked and which
this formalizes so every repository can have it.

## Where knowledge lives

| Kind | Where | Reader |
|---|---|---|
| Docs for people who use the project | `docs/`, sorted by Diataxis: `tutorials/`, `how-to/`, `reference/`, `explanation/` | users |
| Durable project knowledge | `.okf/`, an OKF v0.2 bundle | agents and people working on the project |
| Repeatable tasks | skills | agents |
| General maxims and strategies | rules | agents |

`.okf/` has these sections, each created with its first page: `manifesto.md`
(the root concept), `decisions/`, `architecture/`, `practices/`,
`proposals/`, `prototypes/` and `handoffs/`. A repository may add its own.

## Parts

- **`kmctl`, a standalone CLI** (ADR 0001). It serves the briefing and the
  rules that are injected into context, installs the plugin, and does the
  bookkeeping a script can do: scaffold `docs/` and `.okf/`, create a new
  decision or practice with the next number and its index entry, supersede a
  decision, list what is due for review, check indexes and links, and list
  live and expired handoffs.
- **A plugin**, for Claude Code first (ADR 0003). It depends on the `okf`
  plugin for OKF authoring and validation and adds: one SessionStart hook
  that relays `kmctl`'s briefing (ADR 0004), an audit agent with three review
  skills (architecture, decision log, practices), and a skill for writing
  Diataxis docs. Skills route; `kmctl` decides and writes.
- **A reusable GitHub Action** (ADR 0005). On every pull request it runs the
  deterministic checks for free. The LLM audit is opt-in and reports only.

## Invariants

Each is `planned` until the test named for it passes, then `enforced`.

- **I1. One hook, and it never blocks.** The plugin's only hook is
  SessionStart, and it exits 0 even when `kmctl` is missing or fails.
  Status: planned.
- **I2. Audits never write knowledge.** The audit agent, its skills and the
  CI action report findings; they never edit `.okf/` or `docs/` and never
  write a `verified` stamp. Status: planned.
- **I3. The briefing comes from the CLI and fits a budget.** The hook prints
  what `kmctl` prints, so upgrading the CLI updates the briefing, and its
  word count stays under a fixed budget. Status: planned.
- **I4. kmctl reads OKF as it is.** It uses only fields the OKF v0.2 spec
  defines (`stale_after`, `verified`, `sources`, `status`). Extension fields
  are allowed by the spec but none are added yet (ADR 0006).
  Status: planned.

## Values

- **Context beats documentation** for agents: what must be known is
  injected, not linked.
- **Prompts may, code must.** What a script can check, a script checks; the
  agent does only the judging.
- **Measure before gating.** No new hook or gate without a count showing it
  catches something.
- **Plain language** in everything kmctl prints and every page it writes.

## Out of scope for now

- A `covers` field mapping concepts to code paths (ADR 0006).
- Hooks beyond SessionStart: a nudge after code edits, a reminder at Stop,
  a commit gate (ADR 0004).
- Harnesses other than Claude Code: opencode, Antigravity, Hermes and others
  come after the Claude Code plugin works (ADR 0003).
- Writing `verified` stamps from an audit (ADR 0005).
