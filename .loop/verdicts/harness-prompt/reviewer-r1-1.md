---
type: verdict
title: 'Verdict: harness-prompt reviewer round 1'
description: 'reviewer verdict for round 1 of harness-prompt: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T06:07:42+00:00'
slug: harness-prompt
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. Without --harness, install and update ask on stderr at a terminal. Install suggests claude and update suggests the harnesses that doctor's harnesses_found reports. Both refuse with exit 1, naming --harness and every harness, when stdin is not a terminal or --json is given. With --harness nothing changes. The help, the reference page and both how-tos say this. All gates and eval rows pass on my own stamp. One small hardening finding remains, and it does not block.

## Checked

- `loopctl gate stamp` run from the worktree: lint, format, tests, integration and eval rows r1 to r5 all pass. Result: "stamp green: 71ac86a244d49aa29aed350f258e73a3f2d14a3d61bf96289491fefca3aa68f7".
- Read the full diff of src/kmctl/__init__.py, tests/test_plugin.py, docs/reference/commands.md and both install how-tos. The change is uncommitted in the worktree, and the stamp hashes that tree.
- Correctness. A PluginError raised by _harnesses is mapped to the existing refusal path, before install_plugin runs. `names` is now computed once and reused for the Next: line. harnesses_found cannot raise here: _manifest_targets catches PluginError, and read_lock returns None on bad YAML. At user scope it never returns antigravity. An empty answer takes typer.prompt's default, and a whitespace-only answer fails parse_harnesses and is asked again. EOF at the prompt raises click's Abort, which exits 1.
- r1: the tests assert the question and the numbered list are on stderr and not on stdout. They assert the real APM --target for answer "1", parsing of numbers, names, mixed and empty answers (through a fake install_plugin), and that "3" and "opencode" are each asked again with the accepted values.
- r2: the test writes an apm.yml that names kmctl's package with targets [], [antigravity] or [claude, antigravity]. It asserts the bracketed default shown on stderr and the set an empty answer updates.
- r3: the no-terminal test does not patch _at_terminal, so it exercises the real sys.stdin.isatty() check under CliRunner. It asserts exit 1, no question, --harness and "claude, antigravity" in stderr, and no tool calls. The --json test runs with a simulated terminal, and the --harness test asserts that no question is asked.
- r4: the help and the three pages are checked for the question wording, for "refuses" or "already installed", and for no "Default: claude". By reading them, I judged that the how-tos also tell scripts and agents to pass --harness.
- Callers: grepped tests, the justfile, action.yml, .github and docs for bare `plugin install`/`update` calls. The only one was test_install_update_runs_the_same_steps, which now passes --harness claude. That matches the plan's spike.

## Findings

- f1 (hardening, non-blocking): `str.isdigit()` accepts superscript and other digit characters that `int()` rejects, so `_read_answer('²')` raises ValueError, which I confirmed by running it. The fix is `word.isdecimal()`, or catching ValueError and treating the word as a name so it is asked again. A person is unlikely to type this, so a plain fix is enough.
