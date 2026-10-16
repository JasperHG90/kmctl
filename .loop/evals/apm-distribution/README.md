---
type: eval
title: 'Eval: apm-distribution'
description: 'Definition of done for apm-distribution: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T10:41:39+00:00'
slug: apm-distribution
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 818221e7db4bf8ab81a2ddcce3b036f729d16a97965f66ebc3fefda7a17eaf5c
  at: '2026-10-16T10:41:39+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: apm/apm.yml is kmctl's APM package: it has a name and version, and depends on exactly this repository's plugin folder ({git: parent, path: plugin}) and scaccogatto/okf-skills pinned to a full commit; plugin/ holds no apm.yml.
  Fails when: apm/apm.yml is missing, lacks name or version, depends on anything else (such as a jasperhg90/skills item) or on okf-skills unpinned or pinned to a branch or tag, or plugin/apm.yml exists
- r2: scripts/release.py set VERSION writes the version to the plugin manifest, the root apm.yml and apm/apm.yml, and current refuses when they differ.
  Fails when: after set 0.2.0 any of the three files is not at 0.2.0, or current exits 0 when an apm.yml version differs from the manifest's
- r3: In a scratch consumer, installing the apm subfolder package of this repository (served from a local git server at this tree's commit) with APM 0.33.0 writes kmctl's 7 skills and agent byte for byte, its SessionStart hook in .claude/settings.json and okf's skills, and none of the 16 dev items; its apm.lock.yaml lists no jasperhg90/skills entry.
  Fails when: any of the 7 skills or the agent is missing or differs from plugin/, the hook is not in .claude/settings.json, no okf skill is installed, any dev rule or dev skill is installed, or the lock names jasperhg90/skills
- r4: A new decision records APM as a second install route beside kmctl plugin install, what it leaves out and why the CLI route stays; the manifesto's Parts names it; docs/how-to/install-kmctl-with-apm.md gives the project-scope apm install line for JasperHG90/Knowledge-management/apm, says to install the CLI first and that a private repository needs GitHub auth, and the install how-to links to it; release.py set also rewrites that page's #vX.Y.Z pin.
  Fails when: the decision is missing, does not match kmctl schema decision or does not name kmctl plugin install, ADR 0001 and the version check; the manifesto does not mention APM; the how-to page is missing any of those points or uses apm install -g; the install how-to has no link to it; or set leaves the page's pin unchanged
- r5: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
