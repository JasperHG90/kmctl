---
type: eval
title: 'Eval: standalone-agent'
description: 'Definition of done for standalone-agent: 12 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T07:05:20+00:00'
slug: standalone-agent
signoff:
  signer: delegated:jasperginn@gmail.com/claude
  hash: 232147a3d95cf49a3ad332ada29a23ad019bfd3ef632ba8f610ab5bae2ffb75f
  at: '2026-10-17T07:05:20+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: action/agent.py run, with PydanticAI's offline test model, writes report.json (a valid Report: summary plus findings with title, severity, path and evidence), report.md and the transcript to --out, and appends report.md to $GITHUB_STEP_SUMMARY when that is set.
  Fails when: a file is missing from --out, report.json does not validate as a Report, report.md lacks a finding that report.json holds, or the step summary is not written
- r2: --prompt or --prompt-file becomes the user message, and with neither the shipped default (the kmctl knowledge audit) is sent; --system-prompt-file replaces the shipped system prompt; passing both --prompt and --prompt-file exits 2 naming both.
  Fails when: the model receives a different user message or system prompt than the options say, the default is empty, or both prompt options are accepted
- r3: Every --skills folder (repeatable; kmctl's apm/.apm/skills when none is given) is scanned for */SKILL.md, and the system prompt lists each skill's name, description and SKILL.md path; a SKILL.md with no name or description front matter stops the run with a message naming the file.
  Fails when: a skill in a given folder is missing from the system prompt, the default folder is not used, or a bad SKILL.md is skipped silently
- r4: The read, search and list tools reach the repository, every --context folder and every --skills folder, and return an error to the model for any path that resolves outside them, symlinks included; search matches plain text, not a regex.
  Fails when: a file in a context or skill folder cannot be read, or a path outside every root (or a symlink pointing out) is read or listed
- r5: The shell tool runs a command in the repository root with an environment that holds PATH and HOME but not the API key variable, GH_TOKEN or GITHUB_TOKEN, returns its exit code, stdout and stderr (cut to a cap), and stops it at a time limit.
  Fails when: the command can see the API key or a GitHub token in its environment, output is not returned, or a command that runs past the limit is not stopped
- r6: --model provider:name selects the provider as PydanticAI names it; with --base-url it builds an OpenAI-compatible model on that URL with the key from the variable --api-key-env names; a named variable that is empty stops the run with a message naming it, before any model call.
  Fails when: the base URL or key is not used, or a missing key is only found by a failed model call
- r7: run refuses to start when GH_TOKEN or GITHUB_TOKEN is set or git config holds an http extraheader, with a message saying which and how to fix it.
  Fails when: run starts with a GitHub token reachable, or the message does not name the cause
- r8: knowledge-audit.sh, audit-batches.py, audit-report.py and the hermes plugin are gone; .github/workflows/knowledge-audit.yml and action.yml's audit mode run uv run action/agent.py run as one step with no GitHub token, upload --out with actions/upload-artifact, then post report.md in a separate step that alone gets the token.
  Fails when: an old file remains, Hermes is still installed, the run step can see a token, the artifact is not uploaded, or the issue step does not post report.md
- r9: A new ADR supersedes ADR 0010 and records PydanticAI, the shell tool and its /proc risk; ADR 0005's consequences, the architecture overview diagram and docs/how-to/install-the-plugin-and-the-ci-action.md describe the new runner; the bundle and docs check clean.
  Fails when: ADR 0010 is not marked superseded, any of those pages still describes Hermes as the runner, or kmctl check fails
- r10: All of the repository's gates pass.
  Fails when: just lint or just test fails
- r11 (judgment): A live run against Gemini Flash through its OpenAI-compatible URL, with the default prompt and kmctl's skills on this repository, finishes with a valid report.json that cites real repository paths.
  Fails when: the run errors, times out, or returns findings citing paths that do not exist
- r12 (judgment): action/agent.py --help, run --help and every option's help say what it takes, its default and where it can come from, so an agent or a person can use the script from the help alone.
  Fails when: an option lacks a description or its default
