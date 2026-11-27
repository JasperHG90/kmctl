---
type: decision
title: "ADR 0039: kmctl audit judge asks an optional decision model, off by default"
description: "kmctl audit judge failure|claim|link asks a configured decision model (Jev or Clef) one question about stored checks or a claim by id, caches the answer in the store, and is the one model call kmctl makes: off by default, a provider and model per question, settings in a per-user audit.toml."
tags: [decision]
generated:
  by: process:kmctl/0.12.1
  at: 2026-11-11T09:43:40Z
status: stable
sources:
  - resource: "packages/kmaudit/src/kmaudit/judge.py"
  - resource: "packages/kmaudit/src/kmaudit/settings.py"
  - resource: "packages/kmaudit/src/kmaudit/tracing.py"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0039: kmctl audit judge asks an optional decision model, off by default

## Context

Everywhere else in the agent-audit work the CLI makes no model call: the
harness's own model extracts claims
([ADR 0036](0036-claims-are-extracted-by-the-agent-through-kmctl-audit-claims.md))
and writes checks
([ADR 0038](0038-checks-are-step-data-that-kmctl-reruns-and-only-checks-that-notice-a-change-are-stored.md)).
Some judgements are cheap for a small decision model and costly for an
agent: whether a failed check shows drift, whether lines show a claim true,
whether a check tests its claim. The prototype's `checks/decide.py` asked
them of TypeSafe's systemone endpoint (Jev); on kmctl's 255 claims Jev
answered 486 routing calls in 15 s for about $0.05 (its README,
2026-11-10). kmctl had no settings file: its only switches were
`KMCTL_NO_UPDATE_CHECK` and `KMCTL_PINNED`.

## Decision

- `kmctl audit judge failure|claim|link ID... --json` asks one question set,
  word for word from the prototype, about stored checks (failure, link) or a
  claim with lines on stdin (claim). kmctl builds the state from the store
  through the check store's read functions, so the caller never copies a
  check into the call.
- It posts `{model, state, questions}` with one `httpx.AsyncClient` and an
  explicit timeout, retries timeouts, dropped connections, 429 and 5xx with
  tenacity's `wait_exponential_jitter`, and keeps at most `max_calls`
  requests in flight under one `asyncio.Semaphore`. A 4xx or an answer
  missing a question is one stderr line.
- Each answer is cached in a `decisions` table, the store's next schema
  step, under a hash of the question, the model and the state, so asking
  again sends nothing until the check, its result or the model changes. It
  writes nothing but the store.
- Settings live in a per-user file, `$XDG_CONFIG_HOME/kmctl/audit.toml`
  (`~/.config/kmctl/audit.toml` when unset), or the file `--config` or
  `KMCTL_AUDIT_CONFIG` names. Each question is off until its table switches
  it on with a provider and a model. A key is read only from the variable a
  provider's `api_key_env` names, and never printed, stored or put in an
  error.
- Tracing is opt-in: with `LANGSMITH_TRACING=true` each call is a LangSmith
  `llm` span. tenacity and langsmith join the `kmctl[audit]` extra and are
  imported only when a question is asked.

Rejected:

- A committed settings file in the repository: it would carry each person's
  gateway URL.
- A settings file under `.kmctl/`: one per checkout and worktree.
- langchain for the call: the prototype's decide.py already used plain
  httpx.
- Tracing on by default, as the prototype did: a call should not leave the
  machine for a trace no one asked for.

## Consequences

`kmctl audit judge` is the one model call kmctl makes, and it never runs
unless a person switched a question on. Audits still report only
([ADR 0005](0005-audits-report-only.md)).
