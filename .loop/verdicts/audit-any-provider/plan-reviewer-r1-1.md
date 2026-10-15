---
type: verdict
title: 'Verdict: audit-any-provider plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of audit-any-provider: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T14:38:22+00:00'
slug: audit-any-provider
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan stands on its two spikes, and both answer their risks: a plugin toolset limits Hermes to read and search and fails closed, and `hermes -z` runs unattended from a script-written config. One gap is left. The plugin's read tools are not confined to the repository, and Hermes' search handler leaks a count oracle on `/proc/*/environ`, the environment file the provider key sits in. A path guard in the plugin fixes it, so this is a revision, not a rethink.

## Checked

- Spike 1 (README, stdout, run.json): `-t kmctl_read` offers only the two tools, write/patch/terminal/execute_code calls get "does not exist", and the run exits 2 with no model call when the plugin is off. This settles risk 1.
- Spike 2: a fresh HOME, no TTY and a config with `api_key: ${ENV}` sends the key as Bearer, stdout is the answer, and a footer may follow the json block. This settles risk 2.
- I called the spike install's `tools.file_tools._handle_read_file` and `_handle_search_files` (the handlers the plugin wraps) directly, with a fresh HOME under the review scratch folder, the plan's config shape, and a key with no known prefix in the environment, with ripgrep and without. Config read: shows `${KMKEY}`, no key. `/proc/self/environ`, `/proc/PID/environ`, `/proc/self/task/TID/environ`, `/proc/self/root/proc/self/environ` and a symlink in the repo pointing at environ: all refused. Files outside the repo, such as /etc/hostname, ~/.bashrc and /proc/self/status: read. Search in count mode on environ: returns match counts, confirmed as a prefix oracle.
- I checked that Hermes wrote no copy of the key under the spike runs' HOME folders.
- Code on main: knowledge-audit.sh, audit-report.py, action.yml, the workflow, and the test names in tests/test_ci_audit.py.

## Findings

- p1: the plugin is not confined to the repository, and a count search leaks the provider key from /proc/*/environ. Details are in the front matter. It blocks because the plan's own security claim (only the repo is readable, nothing secret reaches the public issue) depends on it, and the fix belongs to this ticket's plugin.

## Notes

- Row r1's "no anthropic, claude or openai outside comments" makes sense as a guard against a hard-coded vendor default, since `custom` plus `base_url` covers them all and the auditor lives at plugin/agents/kmctl-auditor.md (no vendor in the path). One trap: a user-facing error string such as "an OpenAI-compatible server" would trip it, so write such messages without the word or in a comment.
- audit-report.py now parses Claude's JSON envelope (`json.loads(output)["result"]`). It will need to read Hermes' raw stdout. The plan implies this and the build will catch it.
- r3 loads the plugin in kmctl's test environment, but the plugin imports `tools.file_tools` at the top. Either the import moves inside register(), or hermes-agent becomes a dev dependency. The build will find this on the first run.
- Not worth a finding: Ollama's /api/show reports the model's maximum context, but Ollama serves its default num_ctx unless one is set. Small local setups may truncate the prompt silently. The how-to should say so.
- Subagent dispatch goes away. One Hermes agent does every batch with the auditor text inlined. The prompt is small (about 9 KB of skill and auditor text), so this fits.
