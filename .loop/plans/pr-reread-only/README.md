---
type: plan
title: 'Plan: pr-reread-only'
description: The CI agent's one job becomes rereading, on a pull request, every .okf/ and docs/ page whose sources the pull request changed; everything that does not serve that is removed.
slug: pr-reread-only
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-27T10:32:22+00:00'
tags:
- plan
epic: null
depends_on: []
priority: null
schema_version: '2.0'
---

# pr-reread-only

Relayed from: none

## Intent

Operator's decision, 2026-11-27: the CI agent (`action/agent.py`) needs to do
one thing. On a same-repository pull request it lists every page under
`.okf/` and `docs/` whose `sources` name a file the pull request changed,
rereads each against the changed code, and the publish job posts one comment
saying which pages still hold and which the change may have outdated.
Everything from ADR 0005, ADR 0017 and ADR 0057 that does not serve that is
removed.

`kmctl review due --base` lists the pages a branch made due, but only those
with a `verified` entry (ADR 0057's Correction); the agent matches `sources`
itself, and judges whether each page still holds. Over the last 15
merged pull requests, the decisions-only scope `okf-vs-change` uses found 64
pages and the wide scope 72: the 8 more are docs pages
(`docs/how-to/...`, `docs/reference/...`) that `okf-vs-change` never checks
(spike:pr-reread-only/1). Architecture and practices pages name no sources
today, so they add none, but the wide scope takes them when they do.

It worked when a same-repository pull request that changes a file a docs page
names in `sources` gets that page in the agent's scope, a run with nothing in
scope writes an empty report without calling the model, and nothing removed
is still referenced by code, docs or tests.

This breaks repositories that use the action's scheduled audit, issue
publishing or the removed inputs. kmctl is pre-1.0 and its install lines pin a
release; the operator made that call ("drop the rest"), and the release notes,
the how-to and the draft ADR say what was removed.

All outcomes ship together in this one ticket: removing the agent's flags
(O3) breaks `action.yml` (O4) and `knowledge-audit.yml` (O5) unless they
change in the same commit.

The agent keeps `refuse_tokens`: without a shell it cannot read `/proc`, but
`read_file` reaches any file in the repository, `.git/config` included, so a
checkout that kept its token header must still be refused. The environment
check stays too; it costs nothing.

## Problems

- P1: The pull request audit, `okf-vs-change`, checks stable decisions only, so a docs page, a non-decision concept or a draft decision the pull request adds is never reread, though `kmctl review due --base` lists pages of every kind (8 docs pages over 15 pull requests, spike:pr-reread-only/1).
- P2: The agent carries a whole second product the pull request check does not use: three whole-repository audits with their prompts (`docs-vs-code`, `okf-vs-code`, `okf-vs-docs`), scheduled and manual runs, publishing to an issue with CODEOWNERS mentions, `run_shell` with its environment scrubbing and timeout, task and system prompts and context and skills from the repository (and the base-branch checkout that guards them), and Langfuse tracing; each is code, inputs, tests and docs to keep true.
- P3: The agent's prompt predates three rules it cannot get from the kmctl briefing or the Claude rules, which it never loads: a new decision is a draft the author accepts (ADR 0050), a page that holds is confirmed with `kmctl verify ID ... --by human:<id>` (ADR 0055), and a Correction is followed by `kmctl summary ack` when the summary still holds (ADR 0056).
- P5: Every push runs the model, even when no page names a changed file.
- P4: This repository's `.github/workflows/knowledge-audit.yml` runs only by hand and weekly, so the pull request check never runs here.

## Goals

- G1: On every same-repository pull request, each page whose sources it changed is reread and the author sees one comment on which still hold.
- G2: The agent, the action and their docs hold only what that check needs.

## Outcomes

### O1: The scope is every page under .okf/ and docs/ whose sources the pull request changed
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `action/agent.py`, `tests/test_agent.py`
- checked by: tests on a real git repository under tmp_path: a pull request that changes a file a docs page, an architecture page, a stable decision and a draft decision name puts all four in scope with their status and changed files; a deprecated or superseded decision, a handoff, the log and a URL source stay out; a folder source matches as a prefix
- seen by: operator

### O2: Nothing in scope means no model call
- kind: behaviour
- goal: G1
- fixes: P5
- needs: O1
- touches: `action/agent.py`, `tests/test_agent.py`
- checked by: a test that runs `run` with a model that fails when called, on a change no page covers, and gets exit 0 and a report whose summary says no page names a changed file
- seen by: operator

### O3: The agent has one task and one prompt, read-only tools, and a pull request comment as its only output
- kind: behaviour
- goal: G2
- fixes: P2
- needs: O1
- touches: `action/agent.py`, `new:action/prompt.md`, `action/prompts/`, `tests/test_agent.py`
- checked by: `agent.py run --help` lists only `--model`, `--base-url`, `--api-key-env`, `--base` (required), `--repo`, `--out`, `--timeout`, `--max-requests`; `publish --help` lists `--pr` (required), `--min-severity`, `--title`; tests that the tools are read_file, search_files and list_files only, that `run` still refuses a checkout whose git config holds a token header, and that no OpenTelemetry dependency is left in the script header
- seen by: operator

### O7: The prompt carries the draft, verify and summary rules
- kind: behaviour
- goal: G1
- fixes: P3
- needs: O3
- touches: `new:action/prompt.md`, `tests/test_agent.py`
- checked by: a test that the shipped prompt names `kmctl new decision --draft`, `kmctl verify` with `--by human:` and `kmctl summary ack`
- seen by: operator

### O4: The action runs the reread on a same-repository pull request and nothing else in audit mode
- kind: behaviour
- goal: G2
- fixes: P2
- needs: O3
- touches: `action.yml`, `packages/kmctl/tests/test_action.py`
- checked by: tests that audit mode runs on a same-repository `pull_request`, skips a fork or Dependabot pull request with exit 0, and refuses `schedule` and `workflow_dispatch`; that the inputs `audit`, `prompt`, `prompt_file`, `system_prompt_file`, `context`, `skills` and `mention` are gone; that the agent step passes `--base origin/$GITHUB_BASE_REF` and no base-branch worktree; that publish passes `--pr`; and that the arguments the run and publish steps build, captured from a stub `uv`, parse with `agent.parser()` from the real script, so a flag the agent no longer takes fails the gate
- seen by: operator

### O5: This repository runs the reread on its pull requests
- kind: behaviour
- goal: G1
- fixes: P4
- needs: O4
- touches: `.github/workflows/knowledge-audit.yml`, `tests/scripts/test_workflows.py`, `tests/test_audit.py`
- checked by: workflow tests that it triggers on `pull_request` only, both jobs carry the same-repository condition, only publish has `pull-requests: write`, the audit job checks out with `persist-credentials: false`, no Langfuse secret is passed, and the agent and publish commands it runs parse with `agent.parser()`
- seen by: operator

### O6: The records and docs describe only the pull request check
- kind: support
- goal: G2
- fixes: P2
- needs: O3, O4, O5
- touches: `new:.okf/decisions/0060-the-ci-agent-only-rereads-the-pages-a-pull-request-changed.md`, `.okf/decisions/0005-audits-report-only.md`, `.okf/decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md`, `.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`, `.okf/architecture/overview.md`, `docs/how-to/install-the-plugin-and-the-ci-action.md`, `docs/tutorials/audit-your-repository-with-the-agent.md`, `docs/explanation/why-one-hook-and-report-only-audits.md`, `packages/kmctl/README.md`, `new:.okf/prototypes/pr-reread-scope/`
- checked by: an eval row that greps the docs, records and tests for each removed name (`docs-vs-code`, `okf-vs-code`, `okf-vs-docs`, `okf-vs-change`, `prompt_file`, `system_prompt_file`, `--skills`, `--context`, `run_shell`, `LANGFUSE`, `issue_title`, `instructions-root`) outside Corrections, superseded text, release notes and prototypes; `prek run --all-files` green
- seen by: operator

## Could invalidate this plan

- 1. Scope: the wide scope may add nothing over decisions only, which would make widening pointless. spike:pr-reread-only/1 settled it: over the last 15 merged pull requests it adds 8 docs pages to 64 decisions.
