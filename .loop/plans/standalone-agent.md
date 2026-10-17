---
type: plan
title: 'Plan: standalone-agent'
description: Replace the Hermes CI audit with one standalone PydanticAI script that takes a user prompt, an optional system prompt, any provider, context folders and skill folders, and writes a typed report kept as an artifact.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:59:07+00:00'
slug: standalone-agent
epic: null
depends_on: []
priority: null
---

# standalone-agent

Relayed from: none

## Intent

Replace the CI audit's bash, Hermes and helper scripts with one standalone
Python script, `new:action/agent.py`. Its dependencies are declared inline
(PEP 723) and `uv run action/agent.py` runs it. It does not import kmctl and
kmctl does not depend on it. It is built on PydanticAI.

The operator chose these on 2026-10-17:

- `run` takes the user message (`--prompt` or `--prompt-file`) and an
  optional system prompt override (`--system-prompt-file`). The script ships
  defaults for both, and the default user message is kmctl's knowledge
  audit.
- Any provider: `--model provider:name` as PydanticAI names models, plus
  `--base-url` and `--api-key-env` for any OpenAI-compatible endpoint.
- `--context DIR` (repeatable) gives the agent extra folders, such as
  enterprise architecture docs a workflow fetched.
- `--skills DIR` (repeatable) adds skill folders (default: kmctl's
  `apm/.apm/skills`). The system prompt lists each skill's name and
  description from its SKILL.md front matter, and the agent reads the rest
  when it needs it.
- Tools: read, search and list files in the repository, the context folders
  and the skill folders, and a shell tool so the agent can run the scripts
  skills ship. Shell commands run with a clean environment that has no API
  key or GitHub token in it. Reading the parent process's environment from
  `/proc` stays possible; the new ADR records that risk.
- Output: the agent returns a typed report (summary plus findings, each with
  title, severity, path and evidence). `run` writes `report.json`,
  `report.md` and the transcript to `--out DIR`, and the summary to
  `$GITHUB_STEP_SUMMARY`.

Posting to GitHub stays as it is for now: `action/knowledge-audit-issue.sh`
posts `report.md` in its own step, the only one with the token. The
`agent-publish` ticket replaces it with a `publish` command that opens an
issue only above a severity and tags CODEOWNERS.

`.github/workflows/knowledge-audit.yml` runs `run`, uploads `--out` with
`actions/upload-artifact`, then runs the issue step, each as its own step.
`action.yml`'s `mode: audit` does the same. This deletes
`action/knowledge-audit.sh`, `action/audit-batches.py`,
`action/audit-report.py`, `action/hermes/kmctl-read/__init__.py` and their tests
(`tests/test_ci_audit.py`, `tests/test_hermes_plugin.py`, and the audit
parts of `tests/test_action.py`). Tests for the script, in
`new:tests/test_agent.py`, run offline with PydanticAI's test models.

A new ADR supersedes ADR 0010
(`.okf/decisions/0010-the-ci-audit-runs-hermes-agent-against-any-openai-compatible-provider.md`)
and records the shell tool and its risk. I2 in `.okf/manifesto.md` still
holds: in CI the agent works on a throwaway checkout with no credentials, and
nothing it changes is committed or pushed. `.okf/architecture/overview.md`
and `docs/how-to/install-the-plugin-and-the-ci-action.md` change to match.

The outcome: on `workflow_dispatch`, the workflow runs the default audit
against an OpenAI-compatible endpoint, uploads `report.json` and `report.md`
as an artifact, and posts `report.md` to the "Knowledge audit" issue.
`uv run action/agent.py run --prompt-file
P --context DIR` with a custom prompt also works. Offline tests in
`tests/test_agent.py` cover both.

## Could invalidate this plan

- PydanticAI may not run tool calls and a typed final report through a
  plain OpenAI-compatible endpoint (`--base-url`) on the models the audit
  will use. If it can't, the design behind "any provider" and the typed
  report is wrong. Settled by spike:standalone-agent/2: pydantic-ai-slim
  2.57.0 with `OpenAIProvider(base_url=...)` on Gemini's OpenAI-compatible
  endpoint ran a read tool and a shell tool and returned a validated nested
  `Report` on gemini-3.8-flash and gemini-2.5-flash, with no retries and the
  default output mode. Set `PYDANTIC_AI_NO_BANNER=1` so stderr stays clean.
