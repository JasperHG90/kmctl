---
type: verdict
title: 'Verdict: audit-any-provider plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of audit-any-provider: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T14:41:27+00:00'
slug: audit-any-provider
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The repo-root guard settles round 1's p1 for paths. It does not cover the search tool's other arguments. The `pattern` goes to ripgrep as a bare positional argument, so the model can pass `--pre=PROGRAM` and make ripgrep run a program on every file. I confirmed this deletes files and runs scripts. A fix in the plugin's wrapper is small and fits this ticket, so the plan needs a revision, not a rethink.

## Checked

- Plan revision against round 1: the guard resolves symlinks and refuses anything outside the root, the plugin imports Hermes inside register(), audit-report.py reads plain stdout, one session audits all batches, and the how-to covers Ollama num_ctx. Rows r1 to r8 re-read, and r3 now covers the refusals round 1 asked for.
- Read Hermes 0.19.0 `_handle_search_files`, `search_tool`, `_search_with_rg` and `_search_with_grep`. `file_glob` goes in after `--glob`, so it is a value and safe. `pattern` and `path` are shell-quoted but have no `-e`/`--` in front, so a leading dash becomes a flag.
- Ran the real handler from the spike install with a fresh HOME under the review scratch folder, with rg on PATH (Hermes' login shell resets PATH, so the probe added rg's folder to the front of each command and left the command itself unchanged). Pattern `--pre=rm`: every file in the working folder was deleted. Pattern `--pre=/bin/sh`: a script in the repo ran and wrote a file outside it. `-L` and `--follow` also parse as flags.
- Symlinks: rg does not follow a symlinked folder inside the repo by default (a plain search with the repo as root did not reach a file behind `repo/linkdir -> outside`), and the `find` fallback has no `-L`. So once the dash-flag problem is closed, the root guard plus rg's defaults is enough.
- Read paths go to `cat`, `sed` and `head` as quoted arguments with no `--` either. Passing the resolved absolute path (which starts with '/') closes that too.

## Findings

- p1 (resolved): the path guard and r3's refusal cases answer round 1's finding.
- p2 (open): pattern flag injection into ripgrep gives command execution. It breaks I2 and the key's confinement, and the plan's path-only guard does not cover it. Details are in the front matter.

## Notes

- Secrets already in the audited repository are out of scope. The repo is the caller's own, the model can only see what is checked in, and the issue goes to the same repository with the same visibility. This is worth one line in the how-to (the audit quotes repo content into an issue), not a finding.
- When the guard resolves a relative path, it should use the same base as Hermes' `_resolve_path_for_task` (TERMINAL_CWD, else the process cwd). Otherwise the check and the actual read can land on different files. Passing the resolved absolute path to the handler fixes this as well.
