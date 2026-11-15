---
type: plan
title: 'Plan: agent-audit-decide'
description: An optional kmctl audit judge failure|claim|link command asks a configured decision model (Jev or Clef) for one judgement about stored checks and claims and caches it in the store, off by default, behind the kmctl[audit] extra.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-11T08:07:21+00:00'
slug: agent-audit-decide
epic: agent-audit
depends_on:
- agent-audit-checks
priority: null
schema_version: '2.0'
---

# agent-audit-decide

Relayed from: none

## Intent

A ticket of the agent-audit epic, after agent-audit-checks, which stores each
check's claim id, its steps and its last run with each step's detail in the
git-ignored store at .kmctl/audit.sqlite (from agent-audit-claims), readable
by check id (agent-audit-checks O4). Everywhere else in the epic the CLI
makes no model call: the harness's own model extracts claims and writes
checks. This ticket adds the one optional model call, an add-on an agent or
skill runs when it wants a particular judgement from a decision model:
`kmctl audit judge failure|claim|link ID... --json`, under the `kmctl audit`
group that agent-audit-claims adds.

- **failure**: a check failed. Does what its steps saw show the claim is
  false (drift), or is the check wrong? Prints the chance the claim is false
  and the likeliest cause (`claim_false`, `check_wrong`, `unclear`).
- **claim**: do the lines given show a claim true, false, or neither? Prints
  the chance they show it true and the verdict (`true`, `false`,
  `not_shown`).
- **link**: does a check test what its claim says, or only a keyword or a
  nearby fact? Prints a score from 0 to 1 and the likeliest level
  (`unrelated`, `keyword`, `nearby`, `the claim`).

What lands:

- **The port.** The prototype's checks/decide.py becomes
  `new:src/kmctl/judge.py`: the three question sets (FAILURE, JUDGE, LINK)
  word for word, the `Answer` and `Reply` models, `DecisionError`, and the
  `asked_key` hash. Calls go through one `httpx.AsyncClient` (httpx is
  already a base dependency) with an explicit timeout as `POST base_url`
  with `{model, state, questions}` and a bearer key. Timeouts, dropped
  connections, 429 and 5xx are retried with `tenacity`'s
  `wait_exponential_jitter`, as the prototype did
  (`.claude/rules/httpx-for-http.md`). A 4xx, or an answer that leaves out a
  question, raises `DecisionError`. TypeSafe's systemone endpoint (Jev) and a
  gateway's decisions endpoint (Clef) both answer this shape.
- **The command.** `kmctl audit judge QUESTION ID... [--config FILE] --json`,
  in `src/kmctl/__init__.py`, following `.claude/rules/cli-interface.md` and
  `.claude/rules/interface-audience.md`. Its audiences are an agent or skill
  first (ids in, a short answer out, `--json` for parsing), and a person
  checking one result second. `failure` and `link` take check ids, and
  `claim` takes a claim id with the lines on stdin. kmctl builds the state
  from the store through agent-audit-checks's read functions (the claim, the
  check's steps, what its last run saw), so the caller never copies a check
  into the call. Several ids fan out under one `asyncio.Semaphore` of
  `max_calls` (`.claude/rules/async-python.md`). Each answer is cached in a
  `decisions` table under its `asked_key`, which covers the question, the
  model and the state, so asking again reads the store and sends nothing
  until the check, its result or the model changes. The table arrives as one
  more ordered schema step in the store (agent-audit-claims's
  `PRAGMA user_version` steps). The command writes only to the store, never
  `.okf/` or `docs/`: it reports and changes nothing (I2, ADR 0005).
- **Settings: a per-user audit.toml, created here.** kmctl has no settings
  file today: its only switches are the variables `KMCTL_NO_UPDATE_CHECK`
  and `KMCTL_PINNED`. Decision endpoints are personal (a gateway URL, a key
  variable) and .kmctl/ is per checkout, so the file is
  $XDG_CONFIG_HOME/kmctl/audit.toml (~/.config/kmctl/audit.toml when the
  variable is unset, on every platform), and `--config FILE` or
  `KMCTL_AUDIT_CONFIG` names another, for CI. `new:src/kmctl/audit_settings.py`
  reads it with `tomllib` into Pydantic models that refuse an unknown key,
  as the prototype's config.py does: `[decisions.providers.NAME]`
  (`base_url`, `api_key_env`), `[decisions.failure]`, `[decisions.claim]`
  and `[decisions.link]` (`enabled` = false, `provider`, `model`), and
  `[decisions]` `timeout` = 60 and `max_calls` = 4. With no file every
  question is off. A question switched on must name a provider under
  `[decisions.providers]` and a model, or the file refuses to load, naming
  the key. Asking a question that is off refuses with one stderr line naming
  the table to switch on. Rejected: a committed file in the repository (it
  would carry each person's gateway URL) and a file under .kmctl/ (one per
  worktree).
- **Tracing, optional, created here.** `new:src/kmctl/tracing.py` holds the
  switch: off unless `LANGSMITH_TRACING=true` is set; then each call is a
  LangSmith `traceable(run_type="llm")` span, as the prototype's
  `@traceable` was, and the rest comes from LangSmith's own variables
  (`LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`). The prototype traced by
  default; here it is opt-in.
- **The extra.** The command needs `tenacity` and, for tracing, `langsmith`.
  This ticket adds both to the `kmctl[audit]` extra with
  `uv add --optional audit`, beside the ast-grep-py and jmespath that
  agent-audit-checks puts there for code and query steps, and `uv.lock`
  follows. It imports them only inside the command, so `--help` and base
  kmctl run without them. Without the extra it refuses with one stderr line
  naming `uv tool install --force 'kmctl[audit] @
  git+https://github.com/JasperHG90/kmctl@vX.Y.Z'`. No langchain is needed:
  the prototype's decide.py already used plain httpx.
- **Credentials.** A key is read only from the variable a provider's
  `api_key_env` names, only for providers that a question in use names, and
  never printed, logged, traced, stored or put in an error. A 401 or 403
  names `decisions.providers.NAME.api_key_env`.
- **The record and docs.** A decision record, written with `kmctl new
  decision`: decision models are an optional CLI add-on, the one model call
  kmctl makes, asked by id, off by default, a provider and model per
  question, settings in a per-user file. `docs/reference/commands.md`
  documents the command, its settings, tracing and the extra;
  `.okf/manifesto.md` Parts and `.okf/architecture/overview.md` name it.

**Measured effect.** In the prototype's full run on kmctl's 255 claims (its
README, 2026-11-10), 22 checks failed, 52 claims ended with only a reason
and 181 checks held. So on this repository `failure` has 22 checks to rank,
`claim` up to 52 claims, and `link` up to 181 holding checks, 25 of the 161
measurable ones being hollow by mutation testing. Jev answered 486 routing
calls for 187 claims in 15 s for about $0.05. Today no kmctl command can ask
any of the three: 0 of its verbs call a decision model.

**The outcome that shows it worked:** on a fixture store with a failed check,
against a fake decision endpoint, `kmctl audit judge failure CHECK_ID --json`
prints the chance and cause; asking again sends no request; with
`[decisions.failure]` off it refuses naming the table; and the key appears in
no output.

The operator commits the prototype folder to main before building; until
then it is untracked, so its files are named here in prose, not as paths.

## Problems

- P1: No kmctl command can ask a decision model whether a failed check shows drift, whether lines show a claim true, or whether a check tests its claim, so an agent has no second opinion it can call
- P2: kmctl has no settings file, no tracing switch and no `tenacity` or `langsmith` in any extra, so an optional model call has nowhere to read its endpoint and nothing to retry or trace with

## Goals

- G1: An agent or skill asks an optional decision model for a judgement about a stored check or claim with one `kmctl audit judge` command, and nothing is asked unless the operator switched the question on

## Outcomes

### O1: A per-user audit.toml loads decision settings per question, off by default, with a provider and model each and keys read only from named variables
- kind: support
- goal: G1
- fixes: P2
- needs: none
- touches: `new:src/kmctl/audit_settings.py`, `new:tests/test_audit_settings.py`
- checked by: `new:tests/test_audit_settings.py` (XDG path and `~/.config` fallback, `--config` and `KMCTL_AUDIT_CONFIG` win, all questions off with no file, a misspelt key refuses naming it, a question switched on without a known provider or a model refuses naming the key, a missing key variable refuses naming the variable and not a value)
- seen by: calling code

### O2: The `kmctl[audit]` extra gains tenacity and langsmith, and LangSmith tracing turns on only when `LANGSMITH_TRACING=true`
- kind: support
- goal: G1
- fixes: P2
- needs: none
- touches: `pyproject.toml`, `uv.lock`, `new:src/kmctl/tracing.py`
- checked by: a test in `new:tests/test_judge.py` that tracing is off with the variable unset and wraps calls with it set, and `tests/test_help.py` (help loads without the extra)
- seen by: calling code

### O3: `kmctl audit judge failure|claim|link` asks the configured model about stored checks and claims and caches each answer under its asked key
- kind: behaviour
- goal: G1
- fixes: P1
- needs: O1, O2
- touches: `kmctl audit judge`, `new:src/kmctl/judge.py`, `src/kmctl/__init__.py`
- checked by: `new:tests/test_judge.py` on respx (each question's state and answer shape, the link score from level probabilities, a repeat sends no request, a changed check result asks again, several ids under `max_calls`, 503 then 200 retries, a 401 and an answer missing a question raise `DecisionError` as one stderr line, a question that is off refuses naming its table, without the extra it refuses naming the install command, the key appears in no output, no tracked or unignored file changes) and `tests/test_help.py`
- seen by: operator

### O4: A decision record, the manifesto, the architecture overview and the command reference describe `kmctl audit judge`
- kind: support
- goal: G1
- fixes: P1
- needs: O3
- touches: `.okf/manifesto.md`, `.okf/architecture/overview.md`, `.okf/decisions/index.md`, `.okf/summary.md`, `.okf/log.md`, `docs/reference/commands.md`
- checked by: `kmctl check`, strict OKF validation in the pre-commit hooks, and the docs tests
- seen by: operator

## Could invalidate this plan

- none
