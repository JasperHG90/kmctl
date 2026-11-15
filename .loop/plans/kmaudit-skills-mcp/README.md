---
type: plan
title: 'Plan: kmaudit-skills-mcp'
description: kmaudit's skills and agents move into kmaudit's own APM package and call its MCP tools instead of its CLI, and the package declares the kmaudit MCP server.
tags:
- plan
slug: kmaudit-skills-mcp
status: draft
epic: kmaudit
depends_on:
- kmaudit-mcp
- apm-per-package
priority: 2
schema_version: '2.0'
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T14:31:36+00:00'
---

# kmaudit-skills-mcp

Relayed from: none

## Intent

The operator: "The skills that we currently have stay, but they should
point at the MCP", and, on where they live, that kmaudit gets its own APM
package beside kmctl's (apm-per-package creates `packages/kmaudit/apm/`
with the version alone). Today the extract-claims and write-checks skills
and their agents, `kmctl-claims-extractor` and `kmctl-check-writer`, sit in
kmctl's package, so kmaudit's skills arrive only with kmctl's. The agents
drive kmaudit through a shell: heredoc answers to `kmaudit claims submit`
and `kmaudit checks submit`, held to those commands by a `kmaudit guard`
PreToolUse hook.

This ticket moves both skills and both agents into kmaudit's package
(`git mv` from `packages/kmctl/apm/.apm/` to `packages/kmaudit/apm/.apm/`),
renames the agents `kmaudit-claims-extractor` and `kmaudit-check-writer`,
and rewrites them to call the MCP tools kmaudit-mcp added (`claims_todo`,
`claims_submit`, `checks_todo`, `checks_try`, `checks_submit`) with
structured answers. The agents need no shell, so their `tools` become Read,
Grep, Glob and those MCP tools, named as Claude Code names them
(`mcp__kmaudit__claims_todo`), and the guard hook leaves their front matter.
The skills keep sequencing (see what is left, batch, hand each batch to the
agent, report) through `claims_todo` and `claims_list`; where a harness has
no such agent (Antigravity, which APM gives no agents), the skill does a
batch itself with the same tools. Both skills are changed through
skill-creator with their evals, as `.claude/rules/skills-via-skill-creator.md`
asks.

kmaudit's `apm.yml` declares the kmaudit MCP server, as kmctl's declares
okf's: `uvx --from git+https://github.com/JasperHG90/kmctl@kmaudit-vX.Y.Z#subdirectory=packages/kmaudit kmaudit mcp`,
so the server and the skills always come from one release and nothing has
to be installed first. `scripts/release.py set --package kmaudit` pins that
ref with the version. APM writes the server for Claude Code, Antigravity and
OpenCode (it already writes okf's for all three). kmctl's package loses the
two skills and agents, and kmctl's wheel with them; kmctl's own `audit`
skill and the `kmctl-auditor` agent stay.

`kmaudit guard` stays in the CLI for anyone who still drives kmaudit
through a shell; kmaudit-cli-slim decides its fate.

It worked when, in a project that installs kmaudit's package with APM,
Claude Code's subagent `kmaudit-claims-extractor` stores claims through the
kmaudit MCP tools with no shell, and kmctl's package no longer carries the
two skills or agents.

## Problems

- P1: kmaudit's skills and agents ship in kmctl's package and drive kmaudit through a shell, which needs a per-harness guard hook and heredoc quoting, and arrive only with kmctl.

## Goals

- G1: kmaudit's skills ship with kmaudit and drive it through its MCP tools in every harness APM installs them for.

## Outcomes

### O1: kmaudit's package carries the two skills, the two agents and the MCP server, and the agents call MCP tools with no shell
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:packages/kmaudit/apm`, `new:packages/kmctl/apm`, `scripts/release.py`, `.github/workflows/release.yml`, `packages/kmaudit/README.md`, `packages/kmaudit/docs/commands.md`, `new:packages/kmaudit/tests/test_apm_package.py`, `packages/kmctl/tests/test_apm_package.py`, `tests/test_skills.py`, `tests/scripts/test_release.py`, `.okf/decisions/0043-the-audit-is-its-own-library-kmaudit-served-over-mcp.md`, `.okf/architecture/audit-pipeline.md`
- checked by: tests that kmaudit's apm.yml declares the kmaudit server at its own tag and lists the skills and agents, that the agents' tools are Read, Grep, Glob and the five kmaudit MCP tools with no Bash and no hook, that kmctl's package and wheel no longer hold them, and that `set --package kmaudit` pins the server's ref; the skills' evals rerun through skill-creator; an integration test that installs kmaudit's package with APM into a project and finds the server in .mcp.json and the agents in .claude/agents/
- seen by: operator

## Could invalidate this plan

- none

## Evidence

The one risk this plan had, that a Claude Code subagent may not see a
project's MCP tools through its `tools` list, was measured before review,
so it is no longer listed above. It could not run through
`loopctl plan spike`: the loop's eval-sign guard refuses a spike command
that starts a nested `claude` session. It ran as a plain script (Claude
Code 2.1.325): a git project with a stdio MCP server, `probe`, whose one
tool `secret_word` returns a random word; an agent `prober` with
`tools: mcp__probe__secret_word` and `model: haiku`; and
`claude -p "Dispatch the prober subagent to get the secret word ..."`.

- First run, with `permissions.allow: ["mcp__probe__secret_word"]` in the
  project's `.claude/settings.json` only: the main session dispatched the
  agent, the agent called `mcp__probe__secret_word`, and the call was
  denied, so the reply had no word. The tool is visible to the subagent;
  the project allow rule did not reach it in `-p` mode.
- Second run, adding `--allowedTools mcp__probe__secret_word`: the agent
  called the tool and the reply was exactly the word
  (`kumquat-6453-17180`), which only the MCP server knew.

So the agents can reach kmaudit with no shell. A person running the skill
interactively answers a permission prompt for each kmaudit tool once, or
allows `mcp__kmaudit__*` up front; kmaudit's README says how, and the
build checks whether APM can write that allow rule.
