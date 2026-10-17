---
type: decision
title: "ADR 0017: The CI audit is a standalone PydanticAI agent script"
description: "action/agent.py, one PydanticAI script run with uv run, replaces the Hermes audit: it takes a task, a system prompt, any provider, context and skill folders, can run shell commands, and writes a typed report kept as an artifact."
tags: [adr, decision, ci, audit]
generated:
  by: claude-opus/5.5
  at: 2026-10-17T07:11:45Z
status: stable
---

# ADR 0017: The CI audit is a standalone PydanticAI agent script

- Status: Accepted
- Date: 2026-10-17

## Context

[ADR 0010](0010-the-ci-audit-runs-hermes-agent-against-any-openai-compatible-provider.md)
ran the CI audit through Hermes Agent: a bash script built one prompt per
batch of due concepts, pasted the audit skill, a review skill and the
auditor's instructions into it, and parsed a JSON block out of Hermes' free
text. It could do only the knowledge audit. Much of the script fenced Hermes
in (its own HOME, unset `HERMES_*` variables, a write-safe root), and the
batching existed because a prompt went to Hermes as one command-line
argument.

On 2026-10-17 the operator asked for a simple, adjustable agent instead: a
user message and an optional system prompt, both with defaults; any provider;
extra folders a workflow fetches, such as enterprise architecture docs; skills
the agent finds and uses as it needs them, scripts included; a report kept as
an artifact and posted to GitHub. They asked for Python only, separate from
kmctl, as one standalone script.

## Decision

- `action/agent.py` is one Python script. Its dependencies are declared
  inline (PEP 723) and `uv run --script` runs it. It does not import kmctl,
  and kmctl does not depend on it; PydanticAI is only a dev dependency, so
  the tests can import the script.
- It runs one PydanticAI agent. `--prompt` or `--prompt-file` is the task and
  `--system-prompt-file` replaces the system prompt. The defaults are the
  kmctl knowledge audit (the audit skill, with the kmctl-auditor's
  instructions) and a system prompt that lists the folders the agent can read
  and its skills.
- `--model` takes PydanticAI's `provider:model` name, and `--base-url` with
  `--api-key-env` reaches any OpenAI-compatible endpoint, so no vendor is
  required (spike:standalone-agent/2 ran tools and a typed report through
  Gemini's OpenAI-compatible URL).
- The agent reads, searches and lists files in the repository, every
  `--context` folder and every `--skills` folder, and nowhere else. The
  system prompt lists each skill's name and description from its SKILL.md,
  and the agent reads the rest when a skill fits.
- It also has `run_shell`, so it can run the scripts skills ship and
  commands such as `kmctl review due`. Commands get a clean environment:
  PATH, HOME and the locale, with no API key and no GitHub token.
- It returns a typed `Report` (summary and findings, each with a title,
  severity, path, summary and evidence). `run` writes `report.json`,
  `report.md` and `transcript.json` to `--out`, and the workflow uploads that
  folder as an artifact.
- It refuses to start when `GH_TOKEN` or `GITHUB_TOKEN` is set or git config
  holds checkout's token. Posting stays in a separate step, the only one
  given the token.

Rejected:

- Keep Hermes. It needs a fence of environment tricks, takes the prompt as
  one argument, returns free text, and cannot take a user's own task.
- Google ADK. It has a skill toolset, but it is built Gemini-first, reaches
  other providers only through LiteLLM and pulls in a large dependency tree.
- DSPy. It optimises prompts through typed signatures; a user cannot simply
  hand it a system prompt.
- A `kmctl agent` command. The operator wanted the agent separate from
  kmctl, so kmctl's users do not install an agent framework.
- Read-only tools only. The operator wants skills' scripts to run.

## Consequences

- This replaces ADR 0010. ADR 0005's report-only rule stands: the system
  prompt says never to change, commit or push a file, the checkout keeps no
  credentials, and nothing the agent changes is committed or pushed.
- Shell commands run as the same user as the script, so a command can still
  read the API key from the script's own `/proc/PID/environ`. Use a key
  scoped to the audit, with a spending limit. The GitHub token is never in
  the agent's step, so no command can reach it.
- `action/knowledge-audit.sh`, `action/audit-batches.py`,
  `action/audit-report.py` and the `kmctl-read` Hermes plugin are gone, with
  their tests. `action/knowledge-audit-issue.sh` now posts the report the
  agent wrote.
- The action's audit inputs are `model`, `base_url`, `api_key_env`,
  `prompt`, `prompt_file`, `system_prompt_file`, `context`, `skills` and
  `timeout`; `provider` is gone, folded into `model`.
- The agent works through the due list in one run; there is no batching.
  A long audit is bounded by `--timeout` and `--max-requests`.
- Posting only above a severity and mentioning the CODEOWNERS owners is the
  `agent-publish` ticket.

Supersedes [ADR 0010](0010-the-ci-audit-runs-hermes-agent-against-any-openai-compatible-provider.md).
