---
type: plan
title: 'Plan: antigravity-okf-stop-hook'
description: okf's Stop hook works in Antigravity through kmctl's plugin folder, and APM's broken copy stops erroring.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:28:19+00:00'
slug: antigravity-okf-stop-hook
epic: null
depends_on:
- antigravity-rules
priority: null
---

# antigravity-okf-stop-hook

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none

## Intent

okf-skills ships a Stop hook, dormant unless a bundle sets `upkeep: enforced`
in `.okf/index.md`, that keeps an agent from stopping when tracked files
changed and nothing under `.okf/` did. APM 0.33.0 puts it in Antigravity's
.agents/hooks.json as `bash ".agents/hooks/okf-skills/hooks/okf-stop-check.sh"`,
and that never works there:

- agy runs a hook in the folder that holds its hooks.json (`.agents/`), so
  the path is not found and agy logs a failed hook (exit 127) at the end of
  every turn, in every repository.
- The script also reads `.okf/` and runs git from its working folder, which
  must be the repository root.
- It prints Claude's `{"decision":"block"}`; agy blocks a stop only on
  `"continue"` and lets any other value stop.

So kmctl owns the hook for Antigravity. After APM's install, kmctl takes the
okf handler (the one whose command names `okf-stop-check.sh`) out of
.agents/hooks.json, dropping a named hook left empty and keeping every
other hook. `hooks()` in `src/kmctl/antigravity.py` adds a second named
hook, `kmctl-okf-stop`, with one Stop handler that: continues only on the
first stop of a turn (`executionNum` 0; agy counts from 0); runs okf's script
from the repository root (`../../..` from the plugin folder) with `{}` on
stdin; prints its reason with `"decision": "continue"` when okf blocks; and
otherwise, or when the script is missing or fails, prints `{}` and exits 0,
so it never breaks a turn (I1). doctor's `antigravity.hook` and
`antigravity.plugin` checks cover both handlers, and a new check fails when
.agents/hooks.json still runs `okf-stop-check.sh`. ADR 0015 and the
install how-to say what the hook does in Antigravity.

It worked when, after a scratch install for antigravity, .agents/hooks.json
holds no okf handler, the plugin folder's hooks.json holds both hooks, and
the handler run by hand from the plugin folder prints the continue JSON once
for an enforced bundle with a stray change, `{}` on `executionNum` 1, and
`{}` with exit 0 when the script is missing.

## Could invalidate this plan

- agy may not re-enter the loop on a plugin Stop hook's `"continue"`, or
  may give no way to tell a forced stop from the first, so the hook would
  either do nothing or loop. It does neither (spike:antigravity-okf-stop-hook/2):
  the first stop came back with okf's reason, and the second carried
  `executionNum` 1 and ended.
