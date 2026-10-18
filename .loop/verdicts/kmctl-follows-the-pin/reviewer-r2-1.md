---
type: verdict
title: 'Verdict: kmctl-follows-the-pin reviewer round 2'
description: 'reviewer verdict for round 2 of kmctl-follows-the-pin: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T19:43:06+00:00'
slug: kmctl-follows-the-pin
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

The one finding sent back, f1, is fixed. The ADR's Consequences bullet now names only `just install`, and the starter justfile confirms that recipe runs `kmctl plugin patch` through `uvx --from git+...@kmctl_ref`. Nothing else in the tree moved, and the stamp I re-ran is green.

## Checked

- Read the Consequences section of ADR 0026 in the worktree. The bullet now reads "`just install`, which runs `kmctl plugin patch` by tag through `uvx`, fills the same cache." A grep for `apm install` in the ADR finds nothing.
- Checked the claim against `starter/justfile.jinja`: the `install` and `install-frozen` recipes call `{{kmctl}} plugin patch`, where `kmctl := "uvx --from " + kmctl_src + " kmctl"` and `kmctl_src` is the git URL at `kmctl_ref`.
- Re-ran `loopctl gate stamp` from the worktree. It printed: "stamp green: 96647e295268a6a8d0b9d72c801c1ba9b1c9a75c2a3cc892fbe561ed3d543d81", which matches the stamp the briefing named.

## Findings

- f1 (resolved): the ADR sentence no longer credits `apm install` with running kmctl. It names `just install`, which the starter justfile shows is correct.
