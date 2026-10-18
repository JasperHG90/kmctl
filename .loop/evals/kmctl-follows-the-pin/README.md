---
type: eval
title: 'Eval: kmctl-follows-the-pin'
description: 'Definition of done for kmctl-follows-the-pin: 10 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T19:05:46+00:00'
slug: kmctl-follows-the-pin
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 37a63aebf2f442930015473ac7c884dca258686d0e287dc83262a7040dbb121f
  at: '2026-10-18T19:05:46+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: In a project whose apm.lock.yaml names kmctl's package at a resolved_ref other than this CLI's package_ref(), `kmctl ARGS` runs `uvx --from git+https://github.com/JasperHG90/kmctl@<resolved_commit> kmctl ARGS` as a child in the same directory, with ARGS unchanged, KMCTL_PINNED=1 in its environment, stdin and stdout inherited, and exits with the child's code. The project is found from --path (both `--path X` and `--path=X`) or else the current directory, walking up to the first folder with apm.lock.yaml and stopping at a folder with .git; run from the project's .agents/ with hook JSON on stdin, the child gets that JSON unread.
  Fails when: the fake uvx is not called, gets other arguments, another commit or another directory, sees no KMCTL_PINNED=1, does not get the caller's stdin byte for byte or write to its stdout, kmctl exits with another code, --path does not choose the pin, or the walk up from .agents/ finds no lock
- r2: kmctl runs as itself, never calling uvx, when no folder up to the .git boundary has apm.lock.yaml, the lock does not parse, it has no kmctl package, its resolved_ref is this CLI's, it has no resolved_commit, KMCTL_PINNED is set, or uvx is not on PATH; the walk does not cross a .git folder into a parent project.
  Fails when: the fake uvx is called in any of these cases, a lock above the .git boundary is used, or the command's own output is missing
- r3: With a real uvx and git rewriting GitHub's kmctl URL to a file:// bare clone of this tree, a project whose lock pins this tree's commit at another resolved_ref runs that commit's kmctl: `kmctl --version` prints the version, and the uv cache, not GitHub, answers a second run with --offline semantics.
  Fails when: the version printed is not this tree's, the run fails, or the second run fails offline
- r4: The template's `just kmctl` installs the pinned kmctl when no kmctl is on PATH or the one there is older than the pin (v0.6.0rc1 older than v0.6.0, the `kmctl X.Y.Z` output and the vX.Y.Z pin compared as versions), leaves a same or newer kmctl alone, then runs `kmctl --version` in the project.
  Fails when: the recipe installs over a same or newer kmctl, does not install when kmctl is missing or older (including a pre-release of the pin), or does not run kmctl --version afterwards
- r5: kmctl briefing, run with KMCTL_PINNED unset in a project pinning vA.B.C, adds the newer-release line naming vX.Y.Z and `just upgrade vX.Y.Z` when the cached newest tag is newer than the pin, in the output's own form (text: a last line; --json: a newer_release key with latest and pinned; --format antigravity: appended to the systemMessage text), both when it runs as itself and over a handed-off child's output as an old release prints it; it adds none when the cached tag is the same or older, when only pre-releases are newer, when KMCTL_NO_UPDATE_CHECK=1, when KMCTL_PINNED is set, or when there is no lock.
  Fails when: the line is missing when a release is newer, appears twice or in any other case, names the wrong versions, or breaks the json or antigravity output's JSON
- r6: When the cache of the newest tag is missing or older than a day, kmctl briefing starts a detached refresh (stdio closed, its own session) and returns without waiting for it; the refresh writes the newest release tag from `git ls-remote --tags` to the cache; a failing or slow git leaves the cache as it was and the briefing unchanged; a fresh cache starts no refresh.
  Fails when: the briefing waits for the refresh, starts one when the cache is fresh, the refresh writes a pre-release or a wrong tag, or a git failure raises or writes the cache
- r7: No test reaches GitHub through the hand-off: the default suite runs with KMCTL_PINNED=1 except in the tests that unset it on purpose.
  Fails when: the conftest does not set KMCTL_PINNED for the suite
- r8: The install how-to and README say the kmctl on PATH runs each project's pinned kmctl and what the briefing's newer-release line means; a decision records the hand-off and the alternatives it rejected.
  Fails when: a page does not say so, or no decision names the hand-off
- r10: action.yml sets KMCTL_PINNED=1 for the steps that run kmctl, so the action runs the kmctl of its own tag whatever the repository's lock pins.
  Fails when: a step that runs kmctl has no KMCTL_PINNED=1 in its environment
- r9: The full suite and every tier pass.
  Fails when: any test fails
