---
type: eval
title: 'Eval: audit-any-provider'
description: 'Definition of done for audit-any-provider: 8 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T14:48:49+00:00'
slug: audit-any-provider
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 83bf002559d8b881e0dc052a67ffcd4b2d79c4af0ba833d9514b5bddfd1fae9b
  at: '2026-10-15T14:48:49+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The audit script runs hermes -z with the caller's provider, model and base URL, and the API key from the secret the caller names, through a config it writes into a fresh HOME; no vendor is named in the script.
  Fails when: with a stub hermes, the recorded call lacks --provider P and -m MODEL from the environment, the config it saw lacks base_url or an api_key taken from the named env var, HOME is the runner's own, or the script contains anthropic, claude or openai outside comments
- r2: Every audit run passes -t kmctl_read, installs the kmctl-read Hermes plugin into the run's HOME and enables it, sets HERMES_WRITE_SAFE_ROOT to an empty folder, and runs hermes under a time limit, with timeout-minutes on the audit step.
  Fails when: the stub hermes's arguments lack -t kmctl_read, the plugin files or plugins.enabled are missing from the run's HOME, HERMES_WRITE_SAFE_ROOT is unset or not an empty folder, hermes is not run under timeout, a stub hermes that sleeps past the limit is not stopped, or the audit step in action.yml and the shipped workflow has no timeout-minutes
- r3: The kmctl-read plugin registers one toolset, kmctl_read, holding only kmctl_read_file, kmctl_search_files and kmctl_list_files, written in plain Python with no shell; listing finds files by name inside the root; all three refuse any path that resolves outside the repository root, and a search pattern is only ever text to match.
  Fails when: loading action/hermes/kmctl-read with a recording ctx registers any other tool or toolset; kmctl_list_files does not return a file inside the root whose path holds the given text, or returns any file for a folder outside the root; any of the three tools returns content or a count for a path outside the root, a symlink in the repo pointing out of it, the run's HOME, or /proc/self/environ; a pattern such as --pre=rm changes or creates any file; or the plugin source imports subprocess, os.system, pty or shlex; a pattern such as (a+)+$ on a line of 40 a's and a b takes more than a second; or a file symlink inside the repo pointing out of it is read by search
- r4: The prompt carries the audit skill, the needed review skills and the kmctl-auditor instructions as text, the filtered due list, and the repository's absolute path; findings still reach the summary and the issue body.
  Fails when: the prompt hermes receives lacks any of those texts or the absolute path, or a findings block in the stub's plain stdout (with a footer after it) does not appear in the summary and the body under RUNNER_TEMP
- r5: The shipped audit workflow names every command as its own step, uses no uses: ./ for the audit, and takes provider, model, base URL and key secret as visible settings; action.yml has the same steps with provider, model, base_url and api_key_env inputs and no anthropic_api_key.
  Fails when: .github/workflows/knowledge-audit.yml has a uses: ./ step, lacks a run step for kmctl, hermes installation, knowledge-audit.sh or knowledge-audit-issue.sh, or action.yml still has anthropic_api_key or lacks one of the four inputs
- r6: The token and event rules from ci-audit and ci-audit-hardening still hold.
  Fails when: any other test in tests/test_ci_audit.py or tests/test_action.py fails
- r7: A new decision record says the audit does not tie a repository to one model vendor and replaces the Claude Code runner, and the bundle stays valid.
  Fails when: .okf/decisions/ has no record naming Hermes and provider choice that links ADR 0005, or okf_validate --strict fails
- r8 (judgment): A spike runs the real knowledge-audit.sh with real Hermes 0.19.0 against a fake OpenAI-compatible endpoint: only kmctl_read_file, kmctl_search_files and kmctl_list_files are offered, a requested write is refused, and the findings reach the summary.
  Fails when: no audit-any-provider spike after the build records those three facts
