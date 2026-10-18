---
type: verdict
title: 'Verdict: opencode-harness plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of opencode-harness: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T04:18:55+00:00'
slug: opencode-harness
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

All four listed risks are settled by spikes whose evidence answers them, and I found no unlisted risk that would break the plan.

## Checked

- Briefing (spike 2): a source read of 9d97a5b shows the V2 loader takes `.opencode/plugins/*.js` with a default `{id, setup}` and a `context` session hook that can change `event.system`. V2 is the released line (CHANGELOG v2.0.32, 2026-10-16), so the plugin targets the OpenCode users actually run. The first live run is r5/r9, as the plan says.
- Agents (spike 1): I re-read the path myself. V2's native agent key is `permissions` (plural), so the plan's `permission` sends the file through the V1 legacy decode. That decode accepts it, keeps key order (v1/config/permission.ts `Entries`, so `"*": deny` first then allows survives last-match-wins), and migrates it to V2 `permissions` with bash->shell (v1/config/migrate.ts). The plan works as written.
- In-place rewrite (spikes 4 and 7): the risk is real, and the changed flow (re-patch after every install, delete the agents in `--undo` before `apm uninstall`) is shown to hold.
- MCP (spike 6): the server entry is valid, starts, and survives a reinstall along with `instructions`.

Unlisted things I checked:

- The `./claude` and `./antigravity` sub-packages declare `targets: [claude]` / `[antigravity]`. Under `--target opencode`, APM 0.33.0 skips them with a warning (install/target_filter.py `resolve_effective_package_targets`); it does not fail. So the full package installs.
- `instructions` globs resolve upward to the project root (config/plugin/instruction.ts `match`), and OpenCode reads `.agents/skills/` through its compatibility plugin. Both support the plan.

## Findings

None.

## Notes

Notes for the build, none of which breaks the plan:

- `.okf/decisions/0023-*` is taken (`0023-kmctl-verify-records-a-person-s-check.md`). The new ADR needs the next free number.
- `doctor.harnesses_found` reads `kmctl_package`, not `kmctl_files`, so it never sees the Antigravity sub-package's rules or hooks. The plan's new rule ("Antigravity = `.agents/` paths outside `.agents/skills/`") needs `kmctl_files` there, or doctor will miss an unpatched Antigravity install. r4 covers this.
- The V2 CLI has `opencode debug agents`; I found no `opencode agent list`. The plan already allows "an equivalent".
- Run `kmctl briefing` in the plugin without blocking (async with a timeout), so it does not hold up OpenCode's start for up to 10 s.
