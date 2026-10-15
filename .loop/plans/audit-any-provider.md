---
type: plan
title: 'Plan: audit-any-provider'
description: "The CI audit runs Hermes Agent against any OpenAI-compatible provider (OpenAI, Ollama, Bifrost, OpenRouter and others) instead of Claude Code with an Anthropic key, and the shipped workflow spells out every command it runs."
slug: audit-any-provider
epic: ci
depends_on: [ci-audit-hardening]
priority: 10
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T14:24:02+00:00'
---

# audit-any-provider

Relayed from: operator, 2026-10-15: "Use hermes instead, and let it take any provider e.g. OLLAMA, OPENAI, brifrost etc." and, for the workflow, explicit steps over a hidden `uses:`.

## Intent

The audit mode added by ci-audit runs `claude -p` and needs an Anthropic API key. The operator does not want either. It changes to [Hermes Agent](https://hermes-agent.nousresearch.com) (PyPI `hermes-agent`, pinned to 0.19.0), which talks to any OpenAI-compatible endpoint:

- `action/knowledge-audit.sh` writes a Hermes config into a fresh `HOME` for the run (`model: {provider, base_url, default, api_key: ${KEY_ENV}}`, with the key read from the secret the caller names) and runs `hermes -z PROMPT --provider P -m MODEL -t kmctl_read` (spike:audit-any-provider/2: unattended, no wizard, no prompt, stdout is the final answer). `provider` defaults to `custom` with a `base_url`, which covers Ollama, OpenAI, Bifrost, OpenRouter and any other OpenAI-compatible server; Hermes' own provider names also pass through. Nothing in the script names a vendor.
- Read only (I2): Hermes has no read-only toolset; its `file` toolset includes `write_file` and `patch`, and with no `-t` it offers a terminal and code execution, all auto-approved under `-z` (spike:audit-any-provider/1). So kmctl ships a small Hermes plugin, `new:action/hermes/kmctl-read/__init__.py` and `new:action/hermes/kmctl-read/plugin.yaml`, that registers a toolset `kmctl_read` holding only `kmctl_read_file` and `kmctl_search_files`, wrapping Hermes' own read and search handlers. The script installs it into the run's `HOME`, enables it in the config and always passes `-t kmctl_read`; if the plugin is not loaded, Hermes exits before calling the model (fails closed). Both tools resolve every path, following symlinks, and refuse anything outside the audited repository's root, which the script passes in; so `/proc`, the run's `HOME` and the rest of the runner are out of reach. Without that guard Hermes' handlers read any file and a count search on `/proc/PID/environ` rebuilds the API key one character at a time (round 1 plan review); Hermes' own denylist says it is not a security boundary. `HERMES_WRITE_SAFE_ROOT` points at an empty folder as a further guard. The plugin imports Hermes inside `register()`, so its tests run without Hermes installed. The plugin uses Hermes internals, which is why the version is pinned and a spike reruns on each bump.
- The prompt carries the audit skill, the review skill for each batch and the `kmctl-auditor` instructions as text, with absolute paths, since `-z` does not take `--skills` and the grep fallback misses relative paths (spike:audit-any-provider/2). The runner installs ripgrep. Hermes injects the audited repository's own AGENTS.md (or CLAUDE.md) and a default persona; neither can give it a write tool.
- The token rules from ci-audit-hardening stay: no GitHub token reachable from the model's step, checkout without persisted credentials, and a separate issue step. `action/audit-report.py` reads Hermes' plain stdout instead of Claude Code's JSON `result` field, and keeps taking the last fenced json block, since Hermes may add a footer after it. One Hermes session audits every batch in turn, as Hermes has no subagent for the auditor.
- `.github/workflows/knowledge-audit.yml` spells out each step (install kmctl, install ripgrep and Hermes, run the audit script, post the issue) instead of `uses: ./`, so a reader sees every command. `action.yml` keeps the same steps for callers who prefer `uses:`, with `provider`, `model`, `base_url` and `api_key_env` inputs in place of `anthropic_api_key`.
- A new decision record says why: the audit must not tie a repository to one model vendor. It names what it replaces (the Claude Code runner from ci-audit) and links ADR 0005. The how-to, the architecture overview and ADR 0005's Consequences follow; the how-to tells Ollama users to set the model's context size (`num_ctx`, 64K or more), since Ollama serves a smaller default than the model reports.

Measured on main: audit mode accepts 1 provider (Anthropic, through `ANTHROPIC_API_KEY`), and the shipped workflow shows 0 of the commands it runs.

Done when the tests run the audit script with a stub `hermes` and show the provider, model, base URL and key reach its config from the environment, `-t kmctl_read` is always passed and the plugin is installed and enabled, the prompt holds the skill and auditor text, and the findings still reach the summary and the issue body; tests of the plugin itself show its toolset holds only the two read tools and both refuse a path outside the repository root, through a symlink, and on `/proc/self/environ` including a count search; the shipped workflow's steps name every command; and a spike runs the real script with real Hermes 0.19.0 against a fake OpenAI-compatible endpoint, shows only the two read tools offered and a requested write refused, and the findings reach the summary.

## Could invalidate this plan

- Settled: Hermes can offer only file read and search, through a kmctl Hermes plugin, and refuses every other tool (spike:audit-any-provider/1).
- Settled: `hermes -z` runs unattended with a fresh `HOME` and a script-written config, and prints a parseable findings block (spike:audit-any-provider/2).
