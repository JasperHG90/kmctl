---
type: eval
title: 'Eval: opencode-starter'
description: 'Definition of done for opencode-starter: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T07:07:38+00:00'
slug: opencode-starter
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 55bab5580720818feda1e2289aab47066f1da236b5bddf4cfb72d7cea3ae0081
  at: '2026-10-18T07:07:38+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl's README.md says kmctl-starter sets up a repository for Claude Code, Antigravity or OpenCode.
  Fails when: the README's kmctl-starter paragraph does not name OpenCode
- r2: Rendering /home/vscode/kmctl-starter at its HEAD with --defaults and harnesses [opencode] writes an apm.yml whose targets are [opencode] and whose kmctl ref is v0.5.1, and a justfile and CI workflow pinned to v0.5.1.
  Fails when: copier fails, or apm.yml's targets or ref, the justfile's kmctl_ref or the CI workflow's pin differ
- r3: copier refuses harnesses including opencode with kmctl_ref v0.5.0, naming v0.5.1, and still accepts [claude] with v0.5.0.
  Fails when: copier renders opencode at v0.5.0, its refusal does not name v0.5.1, or it refuses [claude] at v0.5.0
- r4 (judgment): kmctl-starter's test workflow on GitHub, for the pushed commit, passes for every matrix entry, including [opencode] and [claude, antigravity, opencode]: render, YAML parse and the pre-commit hooks of the generated project. Its bootstrap steps are off while JasperHG90/kmctl is private, with a comment saying so, and the same bootstrap passes locally for both OpenCode entries with doctor failing only on dep.claude, dep.agy, dep.opencode and antigravity.trust.
  Fails when: any matrix entry fails, the opencode entries are missing, the bootstrap steps are off without saying why, or the local bootstrap of an OpenCode entry fails or doctor fails another check
- r5 (judgment): kmctl-starter's README.md and template/README.md.jinja tell an OpenCode user what they need: OpenCode 2.x only, start a new session after just bootstrap, every rule loads in every session, run just install again after any apm install; the README's harnesses row names OpenCode.
  Fails when: any of those is missing or contradicts kmctl's docs
- r6 (judgment): kmctl-starter has a v0.3.0 tag (plain, as v0.1.0 to v0.2.1) and a GitHub release on the commit that holds this change, pushed after kmctl v0.5.1 became Latest, and uvx copier copy --defaults gh:JasperHG90/kmctl-starter with harnesses [opencode] renders from it.
  Fails when: the tag or release is missing, sits on another commit, or copier from GitHub refuses or does not offer opencode
