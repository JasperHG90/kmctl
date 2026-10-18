---
type: eval
title: 'Eval: starter-reviewer-gitignore'
description: 'Definition of done for starter-reviewer-gitignore: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T18:30:23+00:00'
slug: starter-reviewer-gitignore
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 16379128eb72cb09e05f512e15f24dfcd835cfa9ce962e50b1963d6e32ca99c0
  at: '2026-10-18T18:30:23+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Rendering the template with --defaults writes AGENTS.md with an adversarial-review section holding the rule's constraint (run an adversarial review in a separate sub-agent before reporting a ticket or feature done, act on its verdict), and writes .copier-answers.yml with adversarial_review: true.
  Fails when: the section or its constraint text is missing from AGENTS.md, or the answer is not recorded as true
- r2: With the default answer, apm.yml lists jasperhg90/skills/agents/adversarial-reviewer.agent.md pinned to commit 41f495021f3b264992c8fa764d58565c1184ab91 when claude is one of the harnesses, and has no such entry for [antigravity], [opencode] or [antigravity, opencode].
  Fails when: the entry is missing, unpinned or pinned to another commit for a harness set with claude, or present for a set without claude
- r3: Rendering with adversarial_review=false writes neither the AGENTS.md section nor the apm.yml entry, for every harness set.
  Fails when: either appears with the answer false
- r4: The generated .gitignore ignores apm_modules/, .DS_Store, Thumbs.db, .venv/, __pycache__/, *.pyc, .pytest_cache/, .ruff_cache/, .mypy_cache/, node_modules/, .env, .idea/, .vscode/ and *.swp, and ignores none of the files a bootstrapped project commits (apm.yml, apm.lock.yaml, AGENTS.md, CLAUDE.md, .claude/, .agents/, .opencode/, opencode.json, .okf/, docs/).
  Fails when: git check-ignore in a rendered project does not ignore one of the listed paths, or ignores one of the committed ones
- r5: In a project rendered with the defaults for [claude, antigravity, opencode], just bootstrap exits 0, the hooks pass, kmctl check exits 0, kmctl doctor fails no check except dep.claude, dep.agy, dep.opencode and antigravity.trust, and .claude/agents/adversarial-reviewer.md exists.
  Fails when: bootstrap, the hooks or check fail, doctor fails another check, or .claude/agents/adversarial-reviewer.md is missing
- r6: The how-to's question table names adversarial_review and what it adds, and README.md's adversarial reviewer section says the copier template offers it.
  Fails when: either page does not mention it
- r7: The full suite and every tier pass.
  Fails when: any test fails
