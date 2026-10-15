---
type: verdict
title: 'Verdict: audit-any-provider plan-reviewer round 4'
description: 'plan-reviewer verdict for round 4 of audit-any-provider: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T14:46:21+00:00'
slug: audit-any-provider
pass: plan-reviewer
round: 4
body_schema: verdict/1
---

## Summary

p1, p2 and p3 are resolved. Plain-text search is enough for content search: no review skill or the auditor needs a regex, they search for names taken from pages. One gap is left (p4). The new search only looks inside files, and the auditor also needs Glob, to find files by name and list folders. Without that, the architecture review cannot check lists of files. The fix is small: a name mode on the search, or folder listing on read, plus one r3 condition. It needs a revision, not a rethink.

## Checked

- Read the round 4 plan, the re-signed rows r1 to r8, the round 3 verdict and spike 1's README and plugin.
- p3: substring matching runs in linear time, so (a+)+$ is just seven characters to look for. `timeout MINUTES` plus step timeout-minutes covers any other stall. r2 checks both, with a sleeping stub; r3 checks the (a+)+$ case and a file symlink.
- Regex need: grepped plugin/skills/*-review/SKILL.md, plugin/skills/audit/SKILL.md and plugin/agents/kmctl-auditor.md. The auditor will "search the code for the names it uses" (kmctl-auditor.md:19). The review skills ask it to find files, functions and calls and to compare lists. Nothing needs a pattern, but finding files and comparing lists need file lookup by name (the Glob tool, kmctl-auditor.md:4; architecture-review SKILL.md:16-23).
- Done-when to rows: the config to r1; -t, plugin install and enable, and time limits to r2; the toolset holding only two tools, root, symlink and /proc refusals, literal --pre=rm and (a+)+$, and no shell imports to r3; prompt text and findings reaching the summary and issue to r4; workflow commands to r5; the real-Hermes spike to r8. r6 and r7 cover regressions and the ADR. Every done-when item has a row.

## Findings

- p1 (resolved): each file the search opens is checked against the root, and r3 now also covers a file symlink.
- p2 (resolved): no program is started, so a pattern cannot become a flag.
- p3 (resolved): plain-text matching cannot backtrack, and two outer time limits stop any other stall, with r2 and r3 checking both.
- p4 (open): the tools cannot find or list files by name, which the architecture review's list checks need. Details in the front matter.

## Notes

- For the build, not findings: walk the tree in a stable order and cap the number of matches returned, so a short pattern such as "e" stops early instead of sending the whole repository through Hermes' result cap.
