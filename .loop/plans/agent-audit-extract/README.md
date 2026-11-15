---
type: plan
title: 'Plan: agent-audit-extract'
description: kmctl claims extract calls an OpenAI-compatible model itself and stores claims through the same models, submit path and store as the agent path, with settings in a user audit.toml and optional LangSmith tracing, behind a kmctl[audit] extra.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-11T08:07:17+00:00'
slug: agent-audit-extract
epic: agent-audit
depends_on:
- agent-audit-claims
priority: null
schema_version: '2.0'
---

# agent-audit-extract

Relayed from: none

## Intent

A ticket of the agent-audit epic, after agent-audit-claims, which lands the
claim models (src/kmctl/claims/models.py there), the section cutter and keys,
the extraction instructions, the git-ignored store at .kmctl/audit.sqlite
and the `kmctl claims todo`, `submit` and `list` verbs. The operator still
wants extraction to run with no agent. This ticket adds `kmctl claims
extract [PATH]`, which calls a model itself and stores what it gets back
through the agent path's own code.

What lands:

- **One path to the store.** `extract` takes its sections from the same
  function `kmctl claims todo` uses, so it skips exactly the sections `todo`
  would not hand out. For each section it builds the answer an agent would
  pipe to `kmctl claims submit` (section id, the key `todo` gave, the
  verdicts) and stores it through the same function `submit` calls. So the
  Pydantic validation, the stale-key and missing-verdict refusals, the claim
  ids and the rows are one code path. Both paths make identical rows, and a
  section stored by either is skipped by both. The stored extraction records
  `kmctl claims extract` and the model as its submitter. The system prompt is
  the instructions module agent-audit-claims ships, unchanged, so the
  instructions hash in the section key is the same for both paths.
- **The extractor**, ported from the prototype's claims/extractor.py and
  claims/runner.py into src/kmctl/claims/extract.py (the package agent-audit-claims creates, so named here in prose), with the model client in `new:src/kmctl/llm.py`:
  - one call per section with the instructions, the context (concept, type,
    status, title, section, earlier sections, corrections) and the numbered
    sentences, forcing one function call whose parameters are the `Verdicts`
    JSON schema (the prototype used `method="function_calling"`);
  - a lenient reader: when the answer as a whole fails validation, it keeps
    each sentence verdict that validates. A `sentences` list sent as JSON
    text, sometimes with a stray `]}` after it (DeepSeek, per the
    prototype's jsontext.py), is read as a list;
  - one more ask for the sentences the answer skipped or dropped (the
    prototype's FILL_NOTE). A sentence still without a verdict leaves the
    section unstored and reported, so the next pass asks again;
  - two runs per section by default, merged as the prototype's `merge_runs`
    merges them: the first run's verdicts stand, and the second adds claims
    only for sentences the first gave none. The merged answer is what gets
    submitted. A failed first run is tried once more; a failed second run
    leaves the first run's answer;
  - one `asyncio.Semaphore` of `max_calls` around each section's whole run,
    so its second ask never waits behind other sections
    (`.claude/rules/async-python.md`).
- **httpx and Pydantic, not langchain and langgraph.** The prototype's graph
  has two fixed nodes (ask, then turn verdicts into claims) and no branching,
  and `ChatOpenAI` is used only to send one forced function call and read
  the raw reply. kmctl sends the same request with one `httpx.AsyncClient`
  to `{base_url}/chat/completions`, reads `tool_calls` and `usage` into
  Pydantic models (`.claude/rules/pydantic-boundaries.md`), and retries
  timeouts, dropped connections, 429 and 5xx with `tenacity`'s
  `wait_exponential_jitter` (`.claude/rules/httpx-for-http.md`). Measured
  with `uv pip compile` for Python 3.12: base kmctl resolves to 19 packages;
  adding the prototype's model stack (langchain-openai, langchain-core,
  langgraph, langsmith, tenacity) makes 50; adding only langsmith and
  tenacity makes 36. Risk 1 asks whether the port reads answers as well.
- **The extra.** `pyproject.toml` gains `[project.optional-dependencies]
  audit = ["tenacity", "langsmith"]`, added with `uv add --optional audit`,
  and `uv.lock` follows. Base kmctl keeps its four dependencies. `extract`
  imports the extra only inside the command, so `--help` and every other
  verb run without it; without it, `extract` refuses with one stderr line
  naming `uv tool install --force 'kmctl[audit] @
  git+https://github.com/JasperHG90/kmctl@vX.Y.Z'`.
- **Tracing, optional.** The prototype traced every call to LangSmith and
  turned it on by default. Here it is off unless `LANGSMITH_TRACING=true`
  is set; then each section run and each model call is a LangSmith
  `traceable` span with its tokens, and the rest comes from LangSmith's own
  variables (`LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`). The switch lives in
  `new:src/kmctl/tracing.py`, so agent-audit-decide can trace the same way.
- **Settings: a user file, audit.toml.** kmctl has no settings file today:
  its only switches are the variables `KMCTL_NO_UPDATE_CHECK` and
  `KMCTL_PINNED`. The prototype's audit.toml holds personal endpoints and is
  "kept out of the repository", and .kmctl/ is per checkout, so each loop
  worktree would need its own copy. So the file is
  $XDG_CONFIG_HOME/kmctl/audit.toml (~/.config/kmctl/audit.toml when the
  variable is unset, on every platform), and `--config FILE` or
  `KMCTL_AUDIT_CONFIG` names another, for CI. It is read by
  `new:src/kmctl/audit_settings.py` with `tomllib` into Pydantic models that
  refuse an unknown key, as the prototype's config.py does:
  `[providers.NAME]` (`base_url`, `api_key_env`) and `[extract]` (`provider`,
  `model`, `runs` = 2, `max_calls` = 4, `timeout` = 120, `temperature` = 0,
  `max_retries` = 3, optional `reasoning_effort`). agent-audit-decide adds its
  `[decisions]` tables to the same file. With no file or no model set,
  `extract` refuses, naming the file and the key to set. Rejected: a
  committed file in the repository (it would carry each person's gateway
  URL) and a file under .kmctl/ (one per worktree).
- **Credentials.** A key is read only from the variable `api_key_env` names,
  at call time, and never printed, logged, traced or put in an error. A
  refusal names the variable, not its value; a 401 or 403 names
  `providers.NAME.api_key_env`.
- **What extract does not do.** The prototype's claims/corrections.py ties
  each correction to the claims it overturns with a second model call. The
  agent path has no such step, so running it here would leave rows the agent
  path cannot make. Both paths already show corrections as context and mark
  an overturned sentence none, so that step is left to its own ticket.
- **The verb.** `kmctl claims extract [PATH] [--limit N] [--config FILE]
  --json`, in `src/kmctl/__init__.py`, follows
  `.claude/rules/cli-interface.md` and `.claude/rules/interface-audience.md`.
  Its audiences are a person or CI job running a whole pass, and an agent
  that wants claims with no subagent. It prints counts (sections done, claims
  per kind, sections unstored and why, tokens in and out), or the same as
  `--json`, exits 1 when a section is left unstored, and ends with
  `Next: kmctl claims list`. It writes only to the git-ignored store (I2).
- **The record and docs.** A decision record, written with `kmctl new
  decision`: automatic extraction submits through the agent path, on httpx
  and Pydantic, behind the `kmctl[audit]` extra, with settings in a user
  audit.toml. `docs/reference/commands.md` documents the verb, the file and
  the extra; `.okf/manifesto.md` Parts and `.okf/architecture/overview.md`
  name the verb.

**Measured effect.** agent-audit-claims measured how much a pass skips: over
the 66 commits since 2026-10-15 that changed a concept in `.okf/`, the
median changed 2 of 38 concepts. The prototype took about three model calls
a section (`extract` on the manifesto: 18 calls for 77 claims; 450 calls
left for the rest of the bundle, its README, 2026-11-08). So a typical
`extract` pass calls the model for about 5% of the bundle instead of all of
it, and today no kmctl verb extracts claims without an agent: 0 of its
commands call a model.

**The outcome that shows it worked:** on a fixture repository with a fake
OpenAI-compatible endpoint, `kmctl claims extract` stores claims whose rows
equal those `kmctl claims submit` stores for the same verdicts; `kmctl
claims todo` then lists nothing; a second `extract` makes no request; and
the key never appears in any output.

The operator commits the prototype folder to main before building; until
then it is untracked, so its files are named here in prose, not as paths.

## Problems

- P1: kmctl cannot extract claims without a coding agent, while the prototype's automatic extraction lives outside kmctl on langchain and langgraph
- P2: kmctl has no place to keep model settings (provider, model, key variable, concurrency), and its only switches are environment variables

## Goals

- G1: A person or CI job extracts a bundle's claims with one kmctl command, and gets the same rows and the same skipped sections as the agent path
- G2: Model settings live in one user file shared by every audit verb that calls a model, with keys read only from the variable a setting names

## Outcomes

### O1: Settings for model calls load from a user audit.toml, refusing unknown keys, with keys read only from named variables
- kind: support
- goal: G2
- fixes: P2
- needs: none
- touches: `new:src/kmctl/audit_settings.py`, `new:tests/test_audit_settings.py`
- checked by: `new:tests/test_audit_settings.py` (XDG path and `~/.config` fallback, `--config` and `KMCTL_AUDIT_CONFIG` win, a misspelt key refuses naming it, a missing key variable refuses naming the variable and not a value, no file means extract has no model)
- seen by: calling code

### O2: The `kmctl[audit]` extra carries tenacity and langsmith, and LangSmith tracing turns on only when `LANGSMITH_TRACING=true`
- kind: support
- goal: G1
- fixes: P1
- needs: none
- touches: `pyproject.toml`, `uv.lock`, `new:src/kmctl/tracing.py`
- checked by: a test in `new:tests/test_claims_extract.py` that tracing is off with the variable unset and wraps calls with it set, and `tests/test_help.py` (help loads without the extra)
- seen by: calling code

### O3: `kmctl claims extract` asks a model for each pending section, re-asks skipped sentences, merges two runs, and stores the answer through the submit path
- kind: behaviour
- goal: G1
- fixes: P1
- needs: O1, O2
- touches: `kmctl claims extract`, `new:src/kmctl/llm.py`, `src/kmctl/__init__.py`
- checked by: `new:tests/test_claims_extract.py` on respx (rows equal those `kmctl claims submit` stores for the same verdicts; `todo` then lists nothing; a second pass sends no request; an edited section is the only one asked; skipped sentences asked once more; a list sent as JSON text with a trailing `]}` is read; an unreadable answer is not stored and exits 1; the second run adds claims only for sentences the first left without one; at most `max_calls` sections in flight; 429 then 200 retries; the key appears in no output; without the extra it refuses naming the install command) and `tests/test_help.py`
- seen by: operator

### O4: A decision record, the manifesto, the architecture overview and the command reference describe extract, its settings and the extra
- kind: support
- goal: G1
- fixes: P1
- needs: O3
- touches: `.okf/manifesto.md`, `.okf/architecture/overview.md`, `.okf/decisions/index.md`, `.okf/summary.md`, `.okf/log.md`, `docs/reference/commands.md`
- checked by: `kmctl check`, strict OKF validation in the pre-commit hooks, and the docs tests
- seen by: operator

## Could invalidate this plan

- Dropping langchain for a direct httpx call is right only if it reads the models' answers as well as `ChatOpenAI.with_structured_output(Verdicts, method="function_calling", include_raw=True)` plus the prototype's salvage did. The prototype needed lenient parsing for slips on DeepSeek and gemma (lists sent as JSON text, stray brackets), and its README notes DeepSeek through Bifrost ignores a forced tool choice in the checks agent. If langchain fixes answers the direct reader cannot, the port loses sections and the approach must change to carrying langchain-openai in the extra. Spike pending.
