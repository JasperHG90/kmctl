---
type: verdict
title: 'Verdict: plugin-remove plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of plugin-remove: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T06:59:44+00:00'
slug: plugin-remove
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

p4 is resolved. The plan now builds the uninstall name from the apm.yml entry's own `git:` URL, case kept, and both forms that yields were run: spike 5's script writes `git: https://github.com/JasperHG90/Knowledge-management.git` and uninstalls `github.com/JasperHG90/Knowledge-management/apm` (exit 0, apm.yml emptied, apm_modules cleared), and spike 3's script writes `http://127.0.0.1:18765/o/kmctl.git` and uninstalls `127.0.0.1:18765/o/kmctl/apm` (exit 0). The two build notes from round 2 are folded in. No open risk could break the plan.

## Checked

- Read the plan, the empty eval rows, my round 2 verdict, and spikes 3, 4 and 5 (README and the script copies). The names the scripts pass are exactly what the plan's rule builds from the URLs the scripts write.
- Re-read kmctl_entry, write_manifest, _is_kmctl_entry, _locked_kmctl_urls and _bare_url in src/kmctl/plugin.py. Remove takes no --source, so it must find kmctl's entry without one; _is_kmctl_entry already matches on the kmctl repo name or the lock's URLs, so this is a build detail, not a risk.
- Depends-on tickets antigravity-rules (verifying) and antigravity-okf-stop-hook (ready) are not done yet; the loop orders that. Spike 2 already saw okf's Antigravity hook script, so the stop-hook ticket does not change the remove route.

## Findings

- p1 resolved (round 1): source and ref come from the removed entry, with a failure path.
- p2 resolved (round 1): targets dropped only when no other dependency is left; doctor ignores kept targets once kmctl is locked.
- p3 resolved (round 1): spike 5 proves the github.com form.
- p4 resolved: the name is built from the entry's git: URL with case kept, which is what spikes 5 and 3 ran.

## Notes

Not findings. An old hand-written string entry (ADR 0013, `JasperHG90/Knowledge-management/apm`) has no `git:` URL; the string itself is the uninstall name. An SSH-form `git:` URL would need its host and path parsed differently. Tests will catch both. One ticket is still the right size.
