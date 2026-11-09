---
type: plan
title: 'Plan: kmctl-docs'
description: "kmctl gets the docs its own rules ask for: a README with the real install line, user pages in docs/ by Diataxis type written with the write-docs skill, and an architecture page in .okf/."
slug: kmctl-docs
epic: docs
depends_on: [audit-agent-and-skills, ci-audit]
priority: 13
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev77+gbd4712cf8.d20261015
  at: '2026-10-15T12:25:15+00:00'
---

# kmctl-docs

Relayed from: none

## Intent

kmctl's commands exist, so `.claude/rules/docs-layout.md` (docs describe what exists) now asks for user docs, and the write-docs test runs showed agents guess the install line because nothing states it.

- `README.md`: what kmctl is in three sentences, the install line (`uv tool install git+https://github.com/JasperHG90/Knowledge-management`, then `kmctl plugin install` in a repository), and links to the docs pages.
- docs/, set up with `kmctl init` and written with the write-docs skill, one page per type: a tutorial (get started: init, a first decision, check), a how-to (install the plugin and the CI action in a repository), a reference (every command and option, from `--help`), and an explanation (why the briefing is the only hook and audits only report). Every command on a page is run and its real output pasted, with two named exceptions: `kmctl plugin install` is run in a scratch repository with an isolated `CLAUDE_CONFIG_DIR`, `HOME` and `XDG_DATA_HOME`, as tests/test_plugin_install.py does, so the operator's config is never touched; and the workflow steps that only run on GitHub are taken from action.yml and the shipped workflow and say so on the page. This ticket waits for the two audit tickets, so the explanation page describes audits that exist.
- An architecture page, overview.md in a new .okf/architecture/ section: the parts (CLI modules, plugin, action) and how they connect, with a `## Depicts` section naming invariants I1 to I4 and the verbs in its flows (`.claude/rules/diagrams-stay-current.md`). The section index, the root index link and a log line come with it.

Done when `kmctl check` passes with docs/ present (no index or link findings), the okf validator passes in strict mode, every invariant appears in the architecture page's Depicts section, and a test checks the README names the install line.

## Could invalidate this plan

- none
