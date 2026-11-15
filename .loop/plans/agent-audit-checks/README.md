---
type: plan
title: 'Plan: agent-audit-checks'
description: The check step DSL, a model-free runner with change detection, mutation testing as the bar a check must clear, and kmctl audit checks todo/try/submit/run/list for agents, in base kmctl with code and query steps behind kmctl[audit]; the CLI writes no check with a model.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-11T08:07:51+00:00'
slug: agent-audit-checks
epic: agent-audit
depends_on:
- agent-audit-claims
schema_version: '2.0'
---

# agent-audit-checks

Relayed from: none

## Intent

Ticket 3 of the agent-audit epic, after agent-audit-claims (the claim models,
the new `kmctl audit` group with its `claims` verbs, and the git-ignored
store at .kmctl/audit.sqlite). It turns stored claims into checks: data a
coding agent writes once and kmctl reruns with no model. The skill and the
Haiku subagent that drive these verbs are the next ticket,
agent-audit-checks-skill. Settling claims from anchors alone (the
prototype's settle step) and decision-model judgements such as the link
score (agent-audit-decide's optional `kmctl audit judge`) are not here.

**The CLI makes no model call.** The harness's own model writes the checks:
the Haiku subagent that agent-audit-checks-skill adds reads the claims and
lines `todo` hands out, tests drafts with `try` and stores them with
`submit`. What kmctl provides is the step DSL, the answer schema and its
validation, the mutation bar, the store, retrieval from it and the model-free
runner. The prototype's langchain writer loop is not ported; only its
answer models, prompt and hints are.

The source is the prototype under the bundle's prototypes folder (audit-cli;
untracked until the operator commits it to main, so its files are named in
prose): checks/steps.py, checks/mutate.py, checks/anchors.py, checks/lines.py,
the change detection in checks/pipeline.py (`reads`, `reads_key`, the
mutation key, `plan`, `run`), the check answer models in checks/writer.py
(`ClaimCheck`, `NoCheck`) and its writer prompt and hints, and the README
sections "Claims turned into checks", "A code step", "One command, trust
scores" and "Resolving weak checks".

What lands:

- **The step DSL and runner**, `new:src/kmctl/claims/steps.py`: the seven
  step models (file, grep, code, query, definition, imports, help) as one
  Pydantic discriminated union, the `Repository` view (git-tracked files
  only, never `.okf/`, `docs/`, READMEs or agent notes, as the prototype's
  `[files]` defaults say; those defaults become constants, with no config
  file), `run_step`, `run_check`, `reads` and `reads_key`. The new modules sit
  in the claims package because `src/kmctl/checks.py` already holds
  `kmctl check`.
- **The dependency split (settled here).** The prototype needs three heavy
  libraries; this is where each goes:

  | Step or use | Library | Where |
  |---|---|---|
  | file, grep | `re`, `fnmatch`, git | base |
  | definition, imports | stdlib `ast` (the prototype already uses it, not tree-sitter) | base |
  | help | `subprocess` | base |
  | code | ast-grep-py (5.7 MB wheel) | `kmctl[audit]` |
  | query | jmespath (20 KB, pure Python) | `kmctl[audit]` |
  | `todo` context: definitions outside Python | tree-sitter-language-pack in the prototype | dropped: ast-grep's kind search (the prototype's `outline` already does it) with the extra, Python `ast` in base |

  Base kmctl keeps its four dependencies. This ticket adds
  `[project.optional-dependencies] audit` to `pyproject.toml` with
  ast-grep-py and jmespath, and the same two to the dev group so the tests
  run them. agent-audit-decide later adds tenacity and langsmith (optional
  tracing) to the same extra for its optional `kmctl audit judge`; whichever
  of the two lands first creates the extra. Both import lazily.
  Without the extra, a code or query step reports "skipped: needs
  kmctl[audit]" rather than failing, `run` counts the check as skipped, and
  `try` and `submit` refuse it with the install line, since its mutants
  cannot be measured.
- **What that means for CI.** `kmctl audit checks run` never calls a model, so it
  costs nothing with or without the extra (ADR 0005's free tier). But 93 of
  the prototype's 171 measured checks (54%, its mutation pilot results) use a
  code or query step, so a run without the extra checks less than half of
  them. CI is out of scope (operator, 2026-11-11): the store is git-ignored,
  so a fresh CI checkout has no checks, and this ticket does not change
  `action.yml`. `run` stays usable by a CI job for a later ticket that
  brings checks to CI.
- **Mutation testing**, `new:src/kmctl/claims/mutate.py`, ported as is
  (stdlib and pyyaml): in-memory changes to the lines a holding check matched
  and the lines around them (flip a boolean, change a number or string, swap
  `==`, negate a condition, delete a statement, rename a definition, change
  or delete a YAML value, delete a found file). Comments and docstrings are
  never changed, and a change that no longer parses is dropped. A check is
  **weak** when it holds but noticed none of its mutants, or when every line
  it matched is a comment or docstring (the prototype's "hollow" rule). A
  check with no mutants to try is stored and reported as "not measured". In
  the prototype's pilot, 25 of 161 measurable holding checks were weak, 21 of
  them proxy greps for a name, and measuring all 171 took 23.3 s (0.14 s a
  check), so `try` and `submit` can measure each check in-line.
- **The lines a writer sees**, `new:src/kmctl/claims/anchors.py` and
  `new:src/kmctl/claims/lines.py`: each backticked span in a claim resolves
  to a path, command, flag or name, and the writer gets the lines around it,
  or else BM25 windows from the concept's `sources` and named files. The
  Claude review pilot found the writer mostly failed by guessing code it was
  never shown, so `todo` hands these lines out and `try` lets the agent test
  a draft before submitting it. The CLI `--help` walk is cached in the store.
- **The instructions**, `new:src/kmctl/claims/check_instructions.py`: the
  prototype writer's prompt and hints, reworded for an agent that runs
  `kmctl audit checks try` in place of a tool call. `todo --json` hands them out
  once with the JSON Schema of the answer, so the skill stays thin
  (`.claude/rules/skills-are-thin.md`).
- **The answer and the store**, `new:src/kmctl/claims/check_store.py`: the
  answer models (a check: claim id, steps, strength exact or proxy, why, and
  `drift` with a reason when the check fails because the claim is wrong; or a
  reason no check fits), and tables added to the agent-audit-claims store as
  its next `PRAGMA user_version` steps: checks (each with its claim id, its
  steps and who submitted it), the files each check read with content
  hashes, the last run's result with each step's detail (what it matched or
  printed), and mutation quality keyed on steps, read hashes and the mutation
  version. Functions in the module read a check's claim, steps and last run
  by check id, so later tickets (agent-audit-decide's `kmctl audit judge`)
  call them rather than parse command output.
- **Change detection.** A claim's id follows its text, so a changed claim
  loses its check and goes back to `todo`. A stored check reruns only when the
  set or content of the files it reads changes (globs are matched again each
  run), and is measured again only when that key changes. A reason goes back
  to `todo` when its claim or the files its lines came from change.
- **The verbs**, `kmctl audit checks` under the `kmctl audit` group that
  agent-audit-claims adds in `src/kmctl/__init__.py`, following
  `.claude/rules/cli-interface.md` and `.claude/rules/interface-audience.md`.
  Audiences: a check-writing subagent first, a person reading results
  second, and a script or later CI job running stored checks third:
  - `kmctl audit checks todo [PATH] [--limit N] --json`: claims with no current
    check or reason, each with its sentence, concept, anchors and lines, plus
    the instructions and answer schema once. Without `--json`, counts.
  - `kmctl audit checks try [FILE|-] --json`: validates a draft against the answer
    models, runs it, and returns holds or fails, each step's detail, and the
    mutants it missed. It writes nothing, not even the store.
  - `kmctl audit checks submit [FILE|-] --json`: validates, runs and measures. It
    refuses a weak check, naming the mutants it missed or "matched only
    comments or docstrings" (the operator's decision). It also refuses a
    failing check not marked `drift`, an unknown or stale claim id (pointing
    to `kmctl audit checks todo`), and a code or query step without the extra. It
    stores everything else, reasons included. A refusal is one stderr line
    with the fix and a nonzero exit; good answers in the same file are kept.
  - `kmctl audit checks run [PATH] [--all] --json`: reruns the stored checks whose
    reads changed (`--all` reruns every one) and re-measures where the key
    moved. It reports holds, fails, drift, weak, reason, no check and skipped.
    It exits 0 whatever the checks find (ADR 0005: audits report only), and
    nonzero only when it cannot run.
  - `kmctl audit checks list [PATH] [--status S] --json`: each claim's check
    status, strength and why.
  - I2: every verb writes only under .kmctl/, never `.okf/` or `docs/`.
- **The record and docs.** A decision record made with `kmctl new decision`:
  checks are step data from a fixed DSL, written by the harness's model
  through `kmctl audit checks`, rerun with no model on change, and `submit`
  stores only checks that notice a mutant. Code and query steps
  need `kmctl[audit]`. Rejected: checks as code, a model writer inside the CLI,
  tree-sitter-language-pack,
  jmespath in base, storing weak checks with a trust label (the prototype's
  way). It relates to ADR 0005. `.okf/manifesto.md` Parts,
  `.okf/architecture/overview.md` and `docs/reference/commands.md` gain the
  verbs, the extra and the weak bar, with `.okf/summary.md` and `.okf/log.md`
  in step.

**The outcome that shows it worked:** in a fixture repository with stored
claims, a scripted agent takes a claim from `kmctl audit checks todo --json`;
a draft that greps a comment is refused by `kmctl audit checks submit -`,
naming what it missed; a code check on the real line is stored. A second
`kmctl audit checks run` reruns nothing. Editing the matched file reruns only that
check, and no tracked or unignored file changes.

## Problems

- P1: Checks exist only in the untracked prototype, written by a langchain model loop, so no coding agent can write, test or store one through kmctl
- P2: Nothing reruns a stored check only when its claim or the files it reads change, so every pass would run every check
- P3: A check can hold without testing its claim (25 of 161 in the prototype's pilot noticed no change), and nothing keeps such a check out of the store
- P4: A check writer shown too few lines guesses code it never saw, the prototype writer's main failure, and cannot run a draft before storing it

## Goals

- G1: A coding agent, using its harness's own model, writes, tries and stores a claim's check through `kmctl audit checks`, with no model call in kmctl and base kmctl's four dependencies unchanged
- G2: Stored checks rerun with no model, only when their claim or the files they read changed
- G3: Only checks that notice a change to the code they read are stored

## Outcomes

### O1: Base kmctl holds the step DSL and a model-free runner, with code and query steps behind `kmctl[audit]`
- kind: support
- goal: G1
- fixes: P1
- needs: none
- touches: `new:src/kmctl/claims/steps.py`, `pyproject.toml`, `uv.lock`
- checked by: `new:tests/test_claims_steps.py` (each step holds and fails on a fixture git repository; markdown, `.okf/` and untracked files are never read; a code step tests presence only; with ast-grep-py and jmespath hidden, code and query steps report skipped and the other five run)
- seen by: calling code

### O2: Each claim comes with the lines around its anchors and the check instructions
- kind: support
- goal: G1
- fixes: P4
- needs: O1
- touches: `new:src/kmctl/claims/anchors.py`, `new:src/kmctl/claims/lines.py`, `new:src/kmctl/claims/check_instructions.py`
- checked by: `new:tests/test_claims_lines.py` (a claim naming a path, a flag and a Python name gets lines around each; a claim naming nothing gets keyword windows from its concept's sources; Python definitions resolve without the extra)
- seen by: calling code

### O3: Mutation testing marks a holding check weak when it notices no change or matched only comments
- kind: support
- goal: G3
- fixes: P3
- needs: O1
- touches: `new:src/kmctl/claims/mutate.py`
- checked by: `new:tests/test_claims_mutate.py` (a grep on a comment is weak, a code step on the condition kills its mutants, unparsable mutants are dropped, nothing is written to disk)
- seen by: calling code

### O4: The store keeps each check's claim, steps, reads and last run with step detail, and reruns a check only when its claim or reads change
- kind: support
- goal: G2
- fixes: P2
- needs: O1, O3
- touches: `new:src/kmctl/claims/check_store.py`
- checked by: `new:tests/test_claims_check_store.py` (the new user_version steps open a fresh database and a claims-only one; an unchanged repository reruns nothing; an edited read file, a newly matching glob file and a changed claim each rerun only their check; a mutation score is reused until its key moves; a check's claim, steps and last step detail read back by check id)
- seen by: calling code

### O5: `kmctl audit checks` lets an agent take claims with `todo`, test drafts with `try`, store checks with `submit` and rerun them with `run`
- kind: behaviour
- goal: G1
- fixes: P1
- needs: O1, O2, O3, O4
- touches: `kmctl audit checks todo`, `kmctl audit checks try`, `kmctl audit checks submit`, `kmctl audit checks run`, `kmctl audit checks list`, `src/kmctl/__init__.py`
- checked by: `new:tests/test_checks_cli.py` (the fixture-repository flow in the intent; submit refuses a weak check naming its survivors, a failing check without drift, a stale claim id, a malformed answer and a code step without the extra, each with one stderr line and the fix, keeping good answers in the same file; try writes nothing; run exits 0 when a check fails; no tracked or unignored file changes; no verb opens a network connection) and `tests/test_help.py`
- seen by: operator

### O6: A decision record, the manifesto, the architecture overview and the command reference describe checks, the extra and the weak bar
- kind: support
- goal: G1
- fixes: P1
- needs: O5
- touches: `.okf/manifesto.md`, `.okf/architecture/overview.md`, `.okf/decisions/index.md`, `.okf/summary.md`, `.okf/log.md`, `docs/reference/commands.md`
- checked by: `kmctl check`, strict OKF validation in the pre-commit hooks, and the docs tests
- seen by: operator

## Could invalidate this plan

- none
