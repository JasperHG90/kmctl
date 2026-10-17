---
type: manifesto
title: "Manifesto: kmctl"
description: What kmctl is for, where each kind of knowledge lives, the parts (CLI, APM package installed by APM, CI action), the invariants, values, and what is out of scope for now.
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
| Docs for people who use the project | `docs/`, sorted by Diataxis: `tutorials/`, `how-to/`, `reference/`, `explanation/`, each with a generated `README.md` index, and pages with optional OKF staleness fields (ADR 0022) | users |
| Durable project knowledge | `.okf/`, an OKF v0.2 bundle | agents and people working on the project |
| Repeatable tasks | skills | agents |
| General maxims and strategies | rules | agents |

`.okf/` has these sections, each created with its first page: `manifesto.md`
(the root concept), `decisions/`, `architecture/`, `practices/`,
`proposals/`, `prototypes/` and `handoffs/`. A repository may add its own.

## Parts

- **`kmctl`, a standalone CLI** (ADR 0001). It serves the briefing that is
  injected into context, adds what APM cannot install yet for its package
  (`kmctl plugin patch`, ADR 0021) and checks the install (`kmctl doctor`,
  which writes nothing), and does the bookkeeping a
  script can do: scaffold `docs/` and `.okf/` with a `CLAUDE.md` block and a
  first decision (ADR 0011), create a new decision or practice with the next
  number and its index entry, supersede a decision, list what is due for
  review in `.okf/` and `docs/`, check indexes, docs front matter and links
  (`kmctl check --fix` writes the generated `docs/` folder indexes, and the
  `kmctl-check` pre-commit hook runs the check, ADR 0022), and list live
  and expired handoffs.
- **An APM package**, `apm/`, which APM installs from the user's `apm.yml`
  entry (ADR 0014, ADR 0021). It holds an
  audit agent with three review skills (architecture, decision log,
  practices), a skill for writing Diataxis docs, `/handoff` and `/continue`,
  which write and read back handoffs in `.okf/handoffs/` (ADR 0008), and the
  four knowledge rules, and it depends on the okf skills for OKF authoring and
  validation. Skills route; `kmctl` decides and writes.
  The package also ships, per harness, the SessionStart hook that relays
  `kmctl`'s briefing (ADR 0004), okf's MCP server and, for Antigravity, okf's
  Stop check (ADR 0018), so APM (Agent Package Manager) installs all of it
  (ADR 0020). The user adds the package to `apm.yml` at the CLI's own
  version and runs `apm install --target claude` (or `--target
  antigravity`); `kmctl plugin patch` then adds only what APM cannot
  install yet: the agents translated to Antigravity's format, in
  `.agents/plugins/kmctl/` (ADR 0015, ADR 0021). The harnesses are Claude
  Code and Antigravity.
- **A reusable GitHub Action** (ADR 0005). On every pull request it runs the
  deterministic checks for free. The LLM audit is opt-in and reports only.

## Invariants

Each is `planned` until the test named for it passes, then `enforced`.

- **I1. One hook of its own, and it never breaks a session.** kmctl's own
  hook is SessionStart, and it exits 0 even when `kmctl` is missing or
  fails. In Antigravity kmctl also relays okf's opt-in Stop check, which
  APM's copy cannot run there (ADR 0018); it exits 0 and prints `{}` when
  okf's script is missing or fails. Status: enforced by
  `tests/test_plugin.py` (the package ships one SessionStart hook; it exits
  0 without `kmctl` and when it fails) and
  `tests/test_antigravity.py` (Antigravity's SessionStart hook prints `{}`
  and exits 0 in both cases; the okf Stop relay prints `{}` and exits 0
  without a working script).
- **I2. Audits never write knowledge.** The audit agent, its skills and the
  CI action report findings; they never edit `.okf/` or `docs/` and never
  write a `verified` stamp. Status: planned.
- **I3. The briefing comes from the CLI and fits a budget.** The hook prints
  what `kmctl` prints, so upgrading the CLI updates the briefing, and it
  stays under 500 tokens (estimated at four characters a token). Status: enforced by `tests/test_briefing.py::test_briefing_token_budget`.
- **I4. kmctl reads OKF as it is.** It uses the fields the OKF v0.2 spec
  defines (`stale_after`, `verified`, `sources`, `status`) plus the extension
  fields an ADR names. The only one is `handoff_key` (ADR 0009); a covers
  field is out of scope (ADR 0006). `docs/` pages may carry four of those
  fields (`description`, `stale_after`, `verified`, `sources`) with their OKF
  meaning, and nothing else of OKF: `docs/` is not a bundle (ADR 0022).
  Status: enforced by `tests/test_okf_fields.py` (written keys, and reads through
  `okf.field`).

## Values

- **Context beats documentation** for agents: what must be known is
  injected, not linked.
- **Prompts may, code must.** What a script can check, a script checks; the
  agent does only the judging.
- **Measure before gating.** No new hook or gate without a count showing it
  catches something.
- **Plain language** in everything kmctl prints and every page it writes.
- **Every skill is made with the skill-creator skill** (ADR 0007).

## Out of scope for now

- A `covers` field mapping concepts to code paths (ADR 0006).
- Hooks beyond SessionStart: a nudge after code edits, a reminder at Stop,
  a commit gate (ADR 0004).
- More harnesses than the two in Parts: opencode, Hermes and others come
  later (ADR 0014, ADR 0015).
- Writing `verified` stamps from an audit (ADR 0005).
