---
type: plan
title: 'Plan: antigravity-okf-stop-hook-reviewer-f4'
description: Deferred hardening from antigravity-okf-stop-hook, reviewer finding f4 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T07:43:06+00:00'
slug: antigravity-okf-stop-hook-reviewer-f4
status: draft
epic: null
depends_on: []
priority: null
---

# antigravity-okf-stop-hook-reviewer-f4

Relayed from: antigravity-okf-stop-hook, reviewer finding f4 in review round 1

## Intent

apm_okf_stop_present matches the raw text of .agents/hooks.json, but drop_apm_okf_stop skips a file that is not valid JSON. So when that file is unparsable but mentions okf-stop-check.sh, antigravity.apm-hooks fails and names `kmctl plugin install` as the fix, and install leaves the file alone. Either have doctor parse the file the same way install does, or have the fix name the file to repair by hand. at src/kmctl/antigravity.py:244.

The fix: doctor reads .agents/hooks.json the way install does. When the
file is not a JSON object, `antigravity.apm-hooks` fails saying so, with the
fix to repair the file by hand and run `kmctl plugin install --harness
antigravity` again (agy cannot load a broken hooks.json either). When it
parses, the check fails only for a handler whose command runs
`okf-stop-check.sh`, so a mention elsewhere in the file does not count.
`docs/reference/commands.md` and the install how-to's sample doctor output
show the check, and the how-to's copy of the install note names okf's Stop
check as the CLI prints it.

It worked when doctor's test for an unparsable file names the file and the
repair, and a parsed file with no okf handler passes.

## Could invalidate this plan

- none
