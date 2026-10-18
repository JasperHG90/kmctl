---
type: verdict
title: 'Verdict: kmctl-follows-the-pin plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of kmctl-follows-the-pin: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T19:02:49+00:00'
slug: kmctl-follows-the-pin
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Both listed risks are settled by spikes. Spike 4 shows a cache miss with `--offline` fails in about 60 ms with no connects. Spike 3 shows exit codes pass through, which is why the plan probes with `--version` first. Spike 2 shows a detached refresh does not hold up Claude Code's hook and outlives it. Two gaps not on the list would break the plan's contract. Antigravity's hook does not run in the repository, so the cwd-based hand-off never fires there (p1). And the newer-release line is printed by the pinned copy, so older pins, which are the ones that need it, never print it (p2). Both can be fixed by revising the plan; neither means it has to be rethought.

## Checked

- Spikes 1 to 4: README outcomes, stdout, run.json. Spike 4's per-case fresh cache answers spike 3's leftover question. The file:// git fetch while offline only matters when insteadOf points at a local path, which affects the r3 integration test only and is a build detail.
- src/kmctl/plugin.py: `package_ref()` is `v{version}`, and the version is static from apm/apm.yml (pyproject `[tool.hatch.version]`). `kmctl_package` matches name kmctl with virtual_path apm. `LockDependency` has no `resolved_commit` yet. This repo's apm.lock.yaml (APM 0.33.0) writes `resolved_commit` for every entry, so the field is there to read.
- src/kmctl/__init__.py: `main()` only calls `app()`, so the hand-off has a clean place to go. `briefing --format antigravity` reads the workspace from stdin (`hook_workspace`).
- apm/antigravity/.apm/hooks/hooks.json, src/kmctl/antigravity.py (`APM_HOOKS = .agents/hooks.json`), the operator's agy notes ("hooks run in the folder holding hooks.json"), and the Stop hook's `cd ..`: Antigravity's hook cwd is `.agents/`.
- src/kmctl/opencode.py: the plugin spawns `kmctl briefing --path <project dir>` with cwd set to the same folder, so cwd works there.
- This repo's apm.yml does not list kmctl's package, so kmctl runs as itself here. action.yml installs kmctl from the action's checkout and runs `kmctl check` and `kmctl review due` in the user's repo, so a project whose lock pins another tag will now run its pin through uvx in CI (see Notes).
- starter/justfile.jinja: the `install`, `init` and `check` recipes already call kmctl through tag-pinned uvx, and copier's validator allows only release tags for kmctl_ref.
- tests: the suite calls the typer app in process, and test_starter.py runs a real `kmctl` in a consumer, so a suite-wide KMCTL_PINNED=1 covers both.

## Findings

- p1: the hand-off finds the project from cwd, which is wrong for Antigravity's hook (cwd `.agents/`, repo on stdin) and for `--path`. Without a fix, Antigravity sessions keep running the PATH kmctl.
- p2: older pins run their own briefing, which has no update check, so the line the operator asked for does not show where it is needed. The plan has to say which copy prints it.

## Notes

- Windows: `os.execvp` on Windows starts a new process and the parent exits at once, so the caller gets neither the child's exit code nor its output in order. The hooks are bash, so this is minor, but if Windows matters, run the child and exit with its code there.
- CI action: in a repo where the action's tag and the lock's pin differ, the action will now run the pinned kmctl and fetch it from GitHub. Template projects keep the two equal. Either set KMCTL_PINNED=1 in action.yml or say in the docs that the pin wins.
- `just kmctl`: `kmctl --version` prints `kmctl 0.6.0` while the pin is `v0.6.0`, and `sort -V` puts `0.6.0rc1` after `0.6.0`. Strip both before comparing; a test will catch this. During `just upgrade`, the `kmctl --version` warm-up runs before `apm install` rewrites the lock, so it warms the old commit. The tag-pinned `plugin patch` in `install` warms the new one (spike 1), so nothing breaks.
- One ticket is fine; two real gaps do not call for a split.
