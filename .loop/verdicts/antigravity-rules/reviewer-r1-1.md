---
type: verdict
title: 'Verdict: antigravity-rules reviewer round 1'
description: 'reviewer verdict for round 1 of antigravity-rules: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T06:51:46+00:00'
slug: antigravity-rules
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. kmctl translates the four instructions into
`.agents/plugins/kmctl/rules/` as `trigger: glob` with one comma-separated string
of `**/` globs, and the wheel ships `_instructions`. After APM's install it deletes
only the files the lock lists for kmctl's package under `.agents/rules/`, and
doctor stops expecting them there. I can re-check both open findings once they
are fixed, and neither blocks: the manifesto and architecture overview still
describe the old route (f1), and r4's command does not run doctor (f2).

## Checked

- I ran `loopctl gate stamp` from the worktree myself, with a scratch HOME.
  Result: `stamp green: fe5c53a914450a754d0243ab7e543c7684e9e7695e3aadc7cf7f276442318959`.
  Lint, format, tests and integration all passed, and r1 to r6 all passed. The
  r4 log shows 2 passed with no skip, so agy validate --strict really ran and
  counted the rules. The state commit was deferred only because the scratch
  HOME has no git identity.
- I read the full diff of antigravity.py, plugin.py, doctor.py, __init__.py,
  pyproject.toml, ADR 0016, the ADR 0015 pointer, the index, the log, commands.md,
  the how-to and the tests.
- I ran translate_rule on the four shipped instructions. The output is
  `"**/.okf/**, **/src/**, ..."` and similar, single strings with no doubled
  prefix and the order kept.
- Correctness: drop_apm_rules only removes lock-listed paths that start with
  `.agents/rules/` and are files, so other packages' rules stay. Antigravity
  refuses `--scope user` (plugin.py:1014), so `cwd / rel` is the right root.
  Reading the lock before the antigravity block is safe because APM has already
  written it. When write_plugin raises, nothing is deleted.
- Doctor: the `moved` filter applies only to antigravity and to kmctl's package.
  In the r3 fixture the lock lists `.agents/rules/okf-bundle.md` and the install
  deletes it, so the "absent passes" test really exercises the filter. The
  missing, edited and extra cases each assert the detail and AG_FIX.
- Eval rows. r1's tests cover a list, a doubled prefix, the order, the body and
  always_on. r2's tests cover the translations, the moved test (another file is
  kept and the skills stay), the wheel and the second install of the plugin
  folder. r3 is as above. r4: see f2. r5 checks all three pages plus the 0016
  pointer in 0015.
- Consistency: ADR 0016's rejected options and consequences agree with the code.
  The help epilog and the commands.md steps match the code. See f1 for the
  design docs.

## Findings

- f1 (docs, non-blocking): .okf/manifesto.md and .okf/architecture/overview.md
  still say APM supplies Antigravity's rules and that the plugin folder holds
  only agents, hook and MCP. They should name rules/ in the plugin folder, the
  deletion from .agents/rules/, the `_instructions` wheel data and ADR 0016.
- f2 (test-strength, non-blocking): r4's command does not run kmctl doctor, so
  the row's doctor clause is checked only through r6 and the integration gate.

## Notes

- test_adr_audit_fixes now checks `>= 15` instead of `== 15`. It still catches
  an empty record list, so this is acceptable.
- test_plugin_folder_second_install_changes_nothing compares only the plugin
  folder, not `.agents/rules/`. Because the deletion is deterministic, I did
  not raise this as a finding.
- A bare `apm install` puts APM's broken copies back, and doctor's `moved`
  filter will not flag them. ADR 0016 records this as a consequence.
- A non-mapping front matter, such as a YAML list, gives the "applyTo kmctl
  cannot read" message. The wording is slightly off, but no shipped file hits
  it.
