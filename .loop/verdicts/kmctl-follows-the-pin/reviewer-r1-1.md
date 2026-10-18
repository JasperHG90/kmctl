---
type: verdict
title: 'Verdict: kmctl-follows-the-pin reviewer round 1'
description: 'reviewer verdict for round 1 of kmctl-follows-the-pin: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T19:31:57+00:00'
slug: kmctl-follows-the-pin
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. The kmctl on PATH finds the project from --path or the current folder, walks up to apm.lock.yaml and stops at a .git folder or file. It runs the pinned commit through uvx as a child with KMCTL_PINNED=1, with streams and exit code intact. For briefing, it probes offline first and otherwise briefs itself with the not-installed notice. The copy on PATH adds the newer-release line in each output form. `just kmctl` no longer installs over a same or newer kmctl. I re-ran the gates and they are green. The one finding is a wrong sentence in the ADR, which a plain fix can correct.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and rows r1 to r10 all pass, "stamp green: 397c5e0b9f1fbf0a940fc4497383045de72da8df5d1e004e67c9d79c43331720".
- Read src/kmctl/pin.py, the main/briefing changes in src/kmctl/__init__.py, LockDependency.resolved_commit, action.yml, starter/justfile.jinja, tests/conftest.py, tests/test_pin.py, and the new tests in tests/test_briefing.py and tests/test_starter.py, plus the docs and ADR 0026.
- Plan-review build notes: find_lock uses `.exists()`, so a .git file in a worktree or submodule stops the walk (tested with a `gitdir:` file). The briefing runs a captured child, not exec, so the outer copy can add the line.
- No duplicate notices: briefing_notices returns nothing when KMCTL_PINNED is set, so a handed-off child never adds its own; the outer adds only update_notices over the child's output.
- Stdin: the probe uses DEVNULL, so Antigravity's hook JSON reaches the briefing child unread (asserted byte for byte in test_hands_off_from_agents_with_the_hook_json).
- The hooks (apm/claude, apm/antigravity, the OpenCode plugin) run only `kmctl briefing`, so no hook goes down the building path.
- Rows: r1 asserts args, commit, cwd, KMCTL_PINNED, stdin, stdout and exit code 3. r2 covers each runs-itself case, including a parent lock above .git and a .git file. r3 is not a constant: if the hand-off fails, the second (briefing) run adds the not-installed notice, which the test checks is absent. r4 covers missing, older, a pre-release of the pin, same and newer, and the final `--version`. r5 covers the three forms, the self and handed-off paths, count == 1, and every case with no line. r6 mocks Popen and checks start_new_session and DEVNULL stdio; a fake git covers exit 128 and a timeout. r7, r8 and r10 assert what their fails_when names.
- The justfile recipe: `have` is empty when kmctl is missing (pipefail plus `|| have=""`); packaging's Version accepts the leading v of kmctl_ref.

## Findings

- f1 (docs, non-blocking): ADR 0026's Consequences bullet says `apm install` runs kmctl by tag. It does not; `just install` does, through `{{kmctl}} plugin patch`. Drop `apm install` from that sentence or say what really fills the cache.

## Notes

- The version is still 0.6.0, and the README and how-tos tell users to install @v0.6.0, a tag that has no hand-off. The release bump has to change those before "one install serves every repository" is true for a fresh install. That is release work, not this ticket's.
- `kmctl briefing --help` from a pinned project gets the newer-release line added to the help text. Harmless.
