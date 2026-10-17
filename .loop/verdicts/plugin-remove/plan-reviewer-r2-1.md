---
type: verdict
title: 'Verdict: plugin-remove plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of plugin-remove: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T06:58:15+00:00'
slug: plugin-remove
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Round 1's three findings are resolved: the reinstall keeps the removed entry's source and ref and has a failure story (p1), targets are dropped only when no other APM dependency is left and doctor ignores kept targets once kmctl is locked (p2), and spike 5 shows the github.com form works (p3). One new gap is left. The plan builds the uninstall name from the lock's repo_url, which APM lowercases for GitHub, and the spike only tried the mixed-case name typed by hand (p4). One spike settles it, and the fix is small either way.

## Checked

- Read the revised plan, the empty eval rows, my round 1 verdict (plan-reviewer-r1-1), and spikes plugin-remove/4 and /5 (README, stdout, stderr, run.json, and the script copies). 4 and 5 differ only in that 5 does not count .claude/settings.json. Spike 5 exits 0: the dry run accepts both github.com/OWNER/REPO/apm and OWNER/REPO/apm, and the real uninstall clears apm.yml and apm_modules/.
- Spike 5's stdout shows the lock entry: `repo_url: jasperhg90/knowledge-management`, `materialization_repo_url: JasperHG90/Knowledge-management`, `host: github.com`. Spike 3's local server path (127.0.0.1:18765/o/kmctl) is all lowercase, so it says nothing about case. This is where p4 comes from.
- Read install, _preflight, write_manifest, kmctl_entry, package_ref, apm_install_args, read_lock, kmctl_package, _locked_kmctl_urls and _bare_url in src/kmctl/plugin.py. install always writes kmctl_entry(source) at package_ref(), so reinstalling at the removed entry's ref needs a ref passed through install, write_manifest and kmctl_entry. That is a plain change, not a risk. After the uninstall, write_manifest only appends targets and the kmctl entry, so the kept harness's reinstall cannot touch the user's entries.
- Read harnesses_found and _manifest_targets in src/kmctl/doctor.py. _manifest_targets already counts targets only while apm.yml names a `path: apm` entry, so after a full remove the leftover targets already do not count. After a partial remove the entry is back and the lock lists kmctl, so the plan's new lock condition is what stops a kept antigravity target from counting. That matches the plan. Callers: plugin update's default harness set and doctor; both want this behaviour.

## Findings

- p1 resolved: source and ref come from the removed entry, and the failure path refuses with the cause and the fix.
- p2 resolved: targets are dropped only when no other dependency is left, and doctor's harnesses_found ignores targets once kmctl is locked.
- p3 resolved: spike:plugin-remove/5 proves the github.com form for a real GitHub install.
- p4 open: the name the plan builds from the lowercased repo_url is untested against APM's apm.yml match. Spike question: does `apm uninstall --dry-run github.com/jasperhg90/knowledge-management/apm` succeed after a GitHub install of the mixed-case URL?

## Notes

Not findings, but the build should get them right. (1) The failure message's fix, `kmctl plugin install --harness KEPT --source SOURCE`, reinstalls at the running CLI's version, not the removed ref, so on that one path the kept harness's version can change. Say so in the message, or accept it. (2) A partial remove keeps kmctl's apm.yml entry, and may keep the removed harness in targets (when other dependencies exist). A plain `apm install` by the user without --target would then deploy kmctl to the removed harness again. The plan's note on the kept target should say this. One ticket is still the right size.
