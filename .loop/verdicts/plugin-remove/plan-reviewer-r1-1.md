---
type: verdict
title: 'Verdict: plugin-remove plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of plugin-remove: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T06:51:05+00:00'
slug: plugin-remove
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach holds: spikes 1 and 3 show apm uninstall of kmctl's entry plus a reinstall for the kept harnesses leaves no APM file, lock entry or okf leftover, and spike 2 rightly rules out the drop-a-target route. Three gaps could still break it as written: the reinstall's ref and its failure leave the kept harness at risk (p1), dropping targets can wipe the user's own packages (p2), and the uninstall name for the real GitHub source is untested (p3). None needs a rethink; all need a revised plan.

## Checked

- Read the plan, the empty eval rows, and spikes plugin-remove/1, 2, 3 (README, stdout, stderr, run.json). Spike 1 exit 1 is from kmctl-owned leftovers the plan already deletes; spike 3 exit 0 covers the uninstall-plus-reinstall route at project scope.
- Read install, _preflight, write_manifest, kmctl_entry, apm_install_args, read_lock, kmctl_package, _locked_kmctl_urls and LockDependency in src/kmctl/plugin.py, and harnesses_found in src/kmctl/doctor.py. install passes --target explicitly, so the reinstall deploys only the kept harnesses whatever targets says (matches spike 3). Antigravity is refused at user scope, so user-scope remove is claude only.
- Read the antigravity-rules and antigravity-okf-stop-hook plans and their spikes. antigravity-rules/2 shows apm uninstall still works after kmctl deletes APM's rule copies. The stop-hook ticket strips okf's handler from .agents/hooks.json after install; no spike runs apm uninstall after that edit, but the plan already deletes an emptied hooks.json, and the build will show it. Because the partial remove reruns the normal install, both tickets' post-install fix-ups run for the kept harness, which is right.

## Findings

- p1: the reinstall uses the CLI's ref, not the installed one, and a failed reinstall leaves the kept harness half removed.
- p2: dropping targets that predate kmctl removes the user's own packages from that harness on their next apm install.
- p3: the github.com uninstall identifier is unproved; a spike should settle it.

## Notes

One ticket is the right size; the risks are tied to one flow.
