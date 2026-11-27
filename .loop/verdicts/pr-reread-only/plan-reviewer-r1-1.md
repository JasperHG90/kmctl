---
type: verdict
title: 'Verdict: pr-reread-only plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of pr-reread-only: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-27T10:34:54+00:00'
slug: pr-reread-only
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works and the scope is right. The one listed risk is settled by spike 1. Removing the base-branch checkout is safe once the only prompt ships inside the action. Three things need fixing before building. The outcome facts would let plan.split ship O3 on its own, which breaks the action, this repository's workflow and tests/test_audit.py (p1). No check would catch action.yml passing a removed flag (p2). And the plan leaves it open whether refuse_tokens survives, though read_file can still read checkout's token from .git/config (p3).

## Checked

- Spike pr-reread-only/1: README outcome, stdout (64 against 72 over 15 merges, 8 docs pages), run.json exit 0, scope.py. It answers the listed risk.
- action/agent.py in full: the tools, Workspace.resolve and SKIP_DIRS, refuse_tokens, instruction_path, changed_decisions and source_matches, the parser.
- action.yml in full: the event check, the agent step's pull-request branch (worktree, --instructions-root, --no-shell), the publish step.
- .github/workflows/knowledge-audit.yml: today only schedule and dispatch, `--audit` matrix, Langfuse secrets, issue publish, `uv tool install .`.
- ADR 0057 and its Correction. The base checkout only made a prompt edit visible to review. With the prompt inside the action, pinned by commit, a consumer's pull request cannot edit it. In this repository the workflow runs action/agent.py from the pull request's checkout, so a prompt edit sits in the diff itself. The key is kept safe by having no shell, not by the checkout. So removing the checkout is safe.
- Grep for the removed names, leaving out prototypes, release notes, .loop and the hermes use in release.yml (its `system_prompt_file` belongs to the hermes action). Every hit is in a file O3 to O6 touch, apart from mentions in passing in ADR 0036, decisions/index.md, kmaudit's anchors.py and write-checks evals, and .okf/log.md. None of those break. copier.yml and the starter's CODEOWNERS are not the agent's.
- packages/kmctl/tests/test_action.py: the step tests stub uv and git (lines 515-560).
- tests/test_audit.py lines 13-25 and 73-85: they pin PROMPTS and DEFAULT_SKILLS in agent.py.
- The 2.0 facts against the prose, outcome by outcome.

## Findings

- p1: O3 cannot ship without O4, O5 and the tests/test_audit.py change, and its check takes over O7's. O2's `fixes: P1` is not something it fixes. plan.split acts on these facts.
- p2: The action and workflow step tests never parse the arguments with agent.py's own parser, so a removed flag left in action.yml passes the gates.
- p3: Whether refuse_tokens stays is not stated. The read-only tools can still read .git/config, so its extraheader check is still needed.

## Notes

- The plan does not say whether the agent still lists kmctl's shipped skills (DEFAULT_SKILLS from the action's own checkout, not the repository), or whether audit mode still needs the "Install kmctl" step once there is no shell. Both are build choices, but tests/test_audit.py pins the skills path, so whoever fixes p1 should settle it.
- The Intent says `kmctl review due --base` "already lists the pages a branch made due". ADR 0057's Correction says it matches sources only for pages with a `verified` entry. O1 does its own source matching in agent.py, so this does not break the plan. Just do not build O1 on top of `review due --base`.
- The eval rows file is empty. O6's grep check names an eval row that does not exist yet.
