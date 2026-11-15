---
type: verdict
title: 'Verdict: kmaudit-cli-slim reviewer round 1'
description: 'reviewer verdict for round 1 of kmaudit-cli-slim: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T10:35:08+00:00'
slug: kmaudit-cli-slim
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `kmaudit --help` lists only mcp, ui,
namespaces, briefing, claims list and checks list. Each dropped verb is a
hidden stub that takes any arguments, `--help` included, and exits 2 with
one stderr line naming its MCP tool. guard.py is gone. POST /api/rerun calls
`check_verbs.run` on the server's root, which is the same namespace the
page's /api/data builds from. It sits behind the same Host, Origin,
Content-Type and Content-Length checks as the other writes. No string in
kmaudit's source or ui.html names a dropped verb as a command, and no doc,
skill, agent or kmctl file outside history does either. Two
non-blocking doc fixes remain.

## Checked

- Gates: `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1 to r4 all pass; "stamp green: 9eac5b5209ea2a3b3e053523f85701b4cf46dd2530a7c914d9a641decf5a9902".
- Read cli.py, ui.py, ui.html, mcp_server.py, check_verbs.py and judge.py in
  full where they changed, plus the diffs of verbs.py, sections.py,
  coverage.py, briefing.py, instructions.py, check_instructions.py,
  models.py, README, commands.md, manifesto, overview, ADR 0040 and ADR 0043.
- r1: test_cli_slim.py checks the visible command set at the click level and
  in `--help`, and runs each of the nine dropped verbs bare, with arguments
  and with `--help`. It asserts exit 2, empty stdout, one stderr line and
  the tool's name. A verb that still ran, or a missing kept command, fails it.
- r2: test_audit_ui.py makes the `exits` check stale, then POSTs /api/rerun.
  It asserts `rerun == 1`, the claim's row reran, and /api/data then shows
  it not stale and holding. It also checks the endpoint calls
  `check_verbs.run`, that a cross-site Origin gets 403 and leaves the check
  stale, and that the page has the button. The endpoint stays safe: a
  cross-site browser POST needs a preflight for application/json, which the
  server never answers, and any Origin it does send must match the Host.
- r3: the source scan works line by line, so I also joined wrapped lines and
  re-scanned all of kmaudit's .py files and ui.html for `kmaudit
  claims|checks|judge|coverage|guard` and bare `claims todo` / `checks run`
  forms. It found nothing. A repo-wide git grep outside .loop found only
  history: older ADRs, prototypes and skill eval results.md logs. The ADR
  0043 test anchors to the amendment's text.
- r4: compared the test names before and after. The only CLI-only tests
  deleted are the ones the briefing lists: submit from a file, the
  people-facing todo counts, the coverage text summary, test_audit_guard.py
  and the `checks run` exit code. That last one became a check of the
  function's `fails` status. The judge, namespaces, briefing and
  independent tests now drive `run_judge`, `verbs` and `check_verbs`
  directly, with the same assertions on content. They no longer assert exit
  codes. The MCP refusal prefix change is matched in test_mcp.py. No skill,
  agent or doc matched the old `kmaudit VERB: refused:` prefix.

## Findings

- f1: ADR 0043's line "the CLI holds nothing that changes a store" and ADR
  0040's correction "no longer carries any verb that writes to a store"
  overstate it, because `kmaudit ui` writes to the store and now reruns
  checks. Say instead that no command writes except through the page.
- f2: judge.py:234 and :244 send an MCP caller to shell commands. Name the
  claims_list and checks_list tools there, or both.

## Notes

- After one rerun, `lastRun` in ui.html stays on the bar through later
  Reloads. That is harmless, but it can show a stale "Reran 1 check."
- Two reruns at once from two tabs both run every stale check. The store's
  write lock or the sqlite error path covers that.
