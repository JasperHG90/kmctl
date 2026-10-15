---
type: verdict
title: 'Verdict: plugin-install-known-marketplace reviewer round 1'
description: 'reviewer verdict for round 1 of plugin-install-known-marketplace: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T14:50:39+00:00'
slug: plugin-install-known-marketplace
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The main path works: the six add arguments, the merge order, the stop before claude for an entry no argument can carry, and the clear error when claude still refuses are all in place and tested, and the two real-claude tests stay inside an isolated CLAUDE_CONFIG_DIR, HOME and XDG_DATA_HOME. One blocking bug: kmctl treats a malformed `scaccogatto` entry as live when claude ignores it, so kmctl now refuses installs that claude would allow (f1). The dot-file check in the r2 test cannot fail (f2).

## Checked

- Read the staged diff and the changed parts of src/kmctl/plugin.py and tests/test_plugin_install.py in full.
- `loopctl gate stamp` from the worktree: all green (lint, format, tests, rows r1-r6 pass), `stamp green: a37e3f6c63663dc7bf9c30dd48c3ee6ea5190d5fa01847f832fc09f07268f0fe`.
- Probed claude 2.1.300 with isolated CLAUDE_CONFIG_DIR/HOME/XDG_DATA_HOME, running `claude plugin marketplace add scaccogatto/okf-skills --scope project` against each user settings file. Refused with "source doesn't match" for: a git entry with another URL (control), an npm entry, and a github entry with `path`. That matches the plan and kmctl. Accepted, meaning claude ignored the entry, for: `"scaccogatto": {}`, `"source": "github"` (a string), `"source": {"source": "github"}` with no repo, invalid JSON (trailing comma), and a valid git entry in a file that also has `"permissions": "oops"`.
- Ran okf_source() against those same files: `{}` raises PluginError; the no-repo entry returns `('None', file)`; the file with the bad `permissions` field returns the git URL.
- Rows: r1 runs -k okf_source and covers every kind with and without ref, plus the default. r2 is covered except the dot-file clause (f2). r3 asserts the file is named in the message and that _claude is never called; okf_source runs before stage(). r4 asserts exit 0, that okf is listed, and that the settings file is unchanged. r6 asserts a nonzero exit and that the output names the settings path and URL. claude's bare _require message never names the settings path, so that assertion does tell the two messages apart. r5 is covered by the gate.
- Invalid JSON: kmctl skips the file (OSError/ValueError), and claude does the same.
- Messages: plain, and both name the file. The first quotes the entry's source as JSON. The second names the URL kmctl tried.
- /etc/claude-code does not exist on this machine. The real-claude tests monkeypatch _managed_dir to a missing folder, so kmctl reads no real managed settings. With HOME and CLAUDE_CONFIG_DIR both under tmp_path, nothing reaches the real ~/.claude.

## Findings

- f1 (bug, blocking): at plugin.py:146-160, a non-dict or missing `source` becomes `{}` and raises "declares the scaccogatto marketplace as {}". claude 2.1.300 ignores that entry and accepts the default add, so this is a regression: kmctl used to succeed here. A `{"source": "github"}` with no repo passes the subset check, and kmctl runs `claude plugin marketplace add None`. claude seems to drop entries (likely whole files) that fail its settings schema. The fix: treat an entry without a dict `source` holding a string for its kind's required field (repo, url or path) as no entry, the way invalid JSON is handled, and add tests for `{}`, a string `source` and a missing repo. Whether claude then falls back to an earlier file's entry is worth one probe, because that decides between "skip this entry" and "keep the earlier found". The broader case, where an unrelated invalid field (`"permissions": "oops"`) makes claude drop the whole file, is outside what kmctl should copy. A Notes line is enough for it.
- f2 (test-mismatch, non-blocking): pathlib's glob does match dot-files, so the filter at plugin.py:116 matters, but `.99-hidden.json` sorts first ('.' < '1') and is overridden anyway. Any dot-file sorts before a digit-named file, so the check needs another shape: a case where the dot-file is the only file in managed-settings.d (the managed-settings.json entry must still win), or an assertion that _settings_files() does not list it. A plain fix is fine.
- f3 (nit): use `import os` (or `isolated.parent / "claude-config"`) in _isolated_home.

## Notes

kmctl reads a settings file that claude rejects for an unrelated schema error and builds the add argument from it. claude then compares against nothing, so the add still succeeds, just from the declared source. That is harmless enough to leave alone.
