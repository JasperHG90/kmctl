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

`.okf/` has these sections, each created with its first page: `summary.md`
(the first page to read, at most 500 words, linking down to the rest;
ADR 0027), `manifesto.md` (the root concept), `decisions/`, `architecture/`, `practices/`,
`proposals/`, `prototypes/` and `handoffs/`. A repository may add its own.

## Parts

- **`kmctl`, a standalone CLI** (ADR 0001). It serves the briefing that is
  injected into context, adds what APM cannot install yet for its package
  (`kmctl plugin patch`, ADR 0021) and checks the install (`kmctl doctor`,
  which writes nothing), and does the bookkeeping a
  script can do: scaffold `docs/` and `.okf/` with a `CLAUDE.md` block and a
  first decision (ADR 0011), create a new decision or practice with the next
  number and its index entry, supersede a decision, list what is due for
  review in `.okf/` and `docs/`, record a person's check of one
  (`kmctl verify`, ADR 0023), say when the bundle summary is behind its
  concepts and record an agent's word that it still holds (`kmctl summary
  ack`, ADR 0027), check indexes, docs front matter and links
  (`kmctl check --fix` writes the generated `docs/` folder indexes, and the
  `kmctl-check` pre-commit hook runs the check, ADR 0022), and list live
  and expired handoffs. Its `kmctl audit` group holds the audit verbs:
  `kmctl audit claims todo`, `submit` and `list` hand a coding agent a
  bundle's sections, validate its verdicts against one schema and keep the
  claims in a git-ignored store, `.kmctl/audit.sqlite`; kmctl calls no
  model for them (ADR 0036). `kmctl audit checks todo`, `try`, `submit`,
  `run` and `list` turn those claims into checks, steps kmctl reruns with
  no model when the files they read change; `submit` refuses a weak check,
  one that notices no change to the code it matched, and code and query
  steps need the `kmctl[audit]` extra (ADR 0038). `kmctl audit judge`
  is the one model call kmctl makes: off by default, it asks a decision
  model set in a per-user `audit.toml` whether a failed check shows drift,
  whether lines show a claim true, or whether a check tests its claim, and
  caches each answer in the store (ADR 0039). `kmctl audit ui` serves a
  page on 127.0.0.1 where a person reviews claims and checks: a thumbs up
  or down and a note on either, their own verdict on whether a claim holds,
  and a second opinion from that model. A thumbs down, or a verdict the
  check disagrees with, goes back to the agent with the next `todo`
  (ADR 0041).
- **An APM package**, `apm/`, which APM installs from the user's `apm.yml`
  entry (ADR 0014, ADR 0021). It holds an
  audit agent with three review skills (architecture, decision log,
  practices), a skill for writing Diataxis docs, `/handoff` and `/continue`,
  which write and read back handoffs in `.okf/handoffs/` (ADR 0008), and the
  four knowledge rules, and it depends on the okf skills for OKF authoring and
  validation. `/extract-claims` hands the bundle's changed sections to the
  `kmctl-claims-extractor` agent (Haiku, Read and a shell), which stores
  claims through `kmctl audit claims` and returns only a summary;
  `/write-checks` hands the claims with no check to the
  `kmctl-check-writer` agent, built the same way, which tries and stores
  checks through `kmctl audit checks`. Skills route; `kmctl` decides and writes.
  The package also ships, per harness, the SessionStart hook that relays
  `kmctl`'s briefing (ADR 0029), okf's MCP server and, for Antigravity, okf's
  Stop check (ADR 0018), so APM (Agent Package Manager) installs all of it
  (ADR 0020). The user adds the package to `apm.yml` at the CLI's own
  version and runs `apm install --target claude` (or `--target
  antigravity`, or `--target opencode`); `kmctl plugin patch` then adds
  only what APM cannot install yet: the agents translated to Antigravity's
  format, in `.agents/plugins/kmctl/` (ADR 0015, ADR 0021), and for
  OpenCode the agents rewritten into its format, the rules and a plugin
  that relays the briefing (ADR 0024). The harnesses are Claude Code,
  Antigravity and OpenCode.
- **A reusable GitHub Action** (ADR 0005). On every pull request it runs the
  deterministic checks for free. The LLM audit is opt-in and reports only.
- **A copier template, kmctl-starter**, in `copier.yml` and `starter/`
  (ADR 0025). It sets up a new repository with `docs/`, `.okf/` and the
  package for the harnesses it names, pinned to the kmctl release whose tag
  it comes from.

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
  without a working script) and `tests/test_opencode.py` (OpenCode's
  briefing plugin adds nothing and throws nothing without a working
  `kmctl`).
- **I2. The audit agent and the CI audit never write knowledge.** The
  `kmctl-auditor` agent has no shell and no write tool, and nothing the CI
  action's audit changes is committed or pushed (the step that runs the
  audit agent holds no GitHub token; only the later publish step does),
  so neither writes `.okf/`, `docs/` or a `verified` stamp (ADR 0037).
  Status: planned.
- **I3. The briefing comes from the CLI and fits a budget.** The hook prints
  what `kmctl` prints, so upgrading the CLI updates the briefing, and it
  stays under 500 tokens (estimated at four characters a token). Status: enforced by `tests/test_briefing.py::test_briefing_token_budget`.
- **I4. kmctl reads OKF as it is.** It uses the fields the OKF v0.2 spec
  defines (`stale_after`, `verified`, `sources`, `status`) plus the extension
  fields an ADR names. There are two: `handoff_key` (ADR 0009) and
  `checked` on the summary (ADR 0027); a covers field is out of scope
  (ADR 0006). `docs/` pages may carry four of those
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
- **The claims and checks agents write only through `kmctl audit`.** They
  have a shell. In Claude Code a hook in their front matter (`kmctl audit
  guard`) blocks any command but `kmctl audit claims` or `kmctl audit
  checks`; Antigravity and OpenCode have no per-agent hook, so there their
  instructions hold the rule. They never write `.okf/`, `docs/` or a
  `verified` stamp (ADR 0037, ADR 0040).

## Out of scope for now

- A `covers` field mapping concepts to code paths (ADR 0006).
- Hooks of kmctl's own beyond SessionStart: a nudge after code edits, a
  reminder at Stop, a commit gate (ADR 0004, ADR 0029).
- More harnesses than the three in Parts: Hermes and others come later
  (ADR 0014, ADR 0015).
- Writing `verified` stamps from an audit (ADR 0005).
