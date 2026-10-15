---
type: eval
title: 'Eval: kmctl-docs'
description: 'Definition of done for kmctl-docs: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T12:45:46+00:00'
slug: kmctl-docs
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 2d93890a1dac0500b9544e8d6c23724261b8845caa9dd89a76bde380aba51a4c
  at: '2026-10-15T12:45:46+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: README.md says what kmctl is, gives the install line and the plugin install step, and links every docs page.
  Fails when: README.md lacks `uv tool install git+https://github.com/JasperHG90/Knowledge-management` or `kmctl plugin install`, or a page under docs/ is not linked from it
- r2: docs/ holds at least one page in each Diataxis folder (tutorials, how-to, reference, explanation), and kmctl check passes on the repository.
  Fails when: any of the four folders has no page besides its index, or kmctl check run on the repository root exits nonzero
- r3: The reference page names every kmctl command and subcommand that --help lists.
  Fails when: a command or subcommand from kmctl's Typer app is missing from the reference page
- r4: .okf/architecture/overview.md has a Depicts section naming every invariant in the manifesto, and every id it names resolves.
  Fails when: an invariant id from .okf/manifesto.md is missing from the Depicts section, or the section names an I-id the manifesto lacks
- r5: The .okf bundle with the new architecture section passes the okf validator in strict mode, and the root index links the section.
  Fails when: okf_validate --strict reports a problem, or .okf/index.md does not link architecture/
- r6 (judgment): The pages were written with the write-docs skill, each command on them was run and its real output pasted, kmctl plugin install ran only with isolated CLAUDE_CONFIG_DIR, HOME and XDG_DATA_HOME, and GitHub-only steps say they come from action.yml and the shipped workflow.
  Fails when: a page shows output no run produced, guesses a command or URL, or the plugin install step touched the operator's config
