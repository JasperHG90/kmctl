---
type: verdict
title: 'Verdict: ci-audit-hardening reviewer round 1'
description: 'reviewer verdict for round 1 of ci-audit-hardening: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T13:30:09+00:00'
slug: ci-audit-hardening
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The split works. The audit step's env holds only ANTHROPIC_API_KEY and KMCTL_PLUGIN_DIR. knowledge-audit.sh makes no gh call, refuses on GH_TOKEN, GITHUB_TOKEN or an extraheader (including one in an included file) before claude runs, and writes nothing about the header to the log. The issue script fails on a failed lookup without creating or editing an issue. One regression blocks: the new issue step dropped the working directory that gh needs to find the repository (f1). The fix is one line, either `working-directory: ${{ inputs.path }}` or `GH_REPO: ${{ github.repository }}`, and test_token_only_on_issue_step should assert it.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, and eval rows r1 to r7 pass. "stamp green: 319e73aa13182d23ec6a076c077e26cb6f64a9bb04f5d0b186a141a8f9732ba6".
- I read the staged diff and, in full, action.yml, action/knowledge-audit.sh, action/knowledge-audit-issue.sh, .github/workflows/knowledge-audit.yml and tests/test_ci_audit.py. The .loop changes in `git diff main` come from main moving on.
- Other ways a token could reach the audit step: the step's env names none. The runner gives `run:` steps no GITHUB_TOKEN or GH_TOKEN by default. ACTIONS_RUNTIME_TOKEN goes to JS and container actions only, and ACTIONS_ID_TOKEN_REQUEST_TOKEN appears only with id-token: write, which the shipped workflow does not grant. I agree with the plan review round 2 on all of this. A caller's job-level env is refused by the GH_TOKEN/GITHUB_TOKEN loop.
- Stale body: knowledge-audit.sh runs `rm -f` on the body before every check, including the event refusal. The issue step has no `always()`, so it is skipped after a failed audit step. The body is moved into place only after audit-report.py succeeds. The model has no Write or Bash tool, so it cannot plant a body. The nothing-due path removes the body and exits 0 without writing one, and the issue script then skips.
- Header leak: `git config --get-regexp ... > /dev/null 2>&1` prints nothing, the refusal message has no value in it, and r3's test asserts that "eHg=" is absent from stdout and stderr.
- Test helpers: `_env` drops GH_TOKEN and GITHUB_TOKEN from os.environ, and the fixture repos are fresh under tmp_path, so the host repo's checkout extraheader is not in their local config. Only a global or system extraheader on the host would reach them.
- Eval rows against fails_when: r1 finds the audit step by `knowledge-audit.sh` (the issue script's name does not match), checks its whole dumped YAML for the three names, and checks the issue env. r2 asserts the body and summary contents and that gh was never called. r3 covers all four cases with nonzero exit and no claude call. r4 asserts persist-credentials False, fetch-depth 0 and both words in the mode help. r5 covers create, edit 7 and skip (no gh calls, exit 0). r6's stub exits 4 on `issue list` and the test asserts nonzero exit with no create or edit. Each test fails when its behaviour breaks.
- Consistency: the script headers, the mode help and ADR 0005's audit line ("job summary and one Knowledge audit issue") still hold. There is no docs/ folder in this tree.

## Findings

- f1 (bug, blocking): the issue step runs gh in the workspace root instead of inputs.path, so audit mode breaks for a nested checkout. Add `working-directory: ${{ inputs.path }}` to the "Post the audit issue" step, or set `GH_REPO: ${{ github.repository }}`, and assert it in test_token_only_on_issue_step.

## Notes

- The extraheader check only reads the git config at inputs.path. Persisted credentials from a second checkout in the same job are still on disk where Read can reach them. The mode help's "Check out with persist-credentials: false" covers this for callers, and the plan scoped the check to the audited repository, so this is not a finding.
- knowledge-audit-issue.sh's header says it does nothing "or the audit failed". After a failed audit the step does not run at all, so no body is posted either way and the header is not wrong.
