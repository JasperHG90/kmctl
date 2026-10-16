---
type: verdict
title: 'Verdict: apm-only-install-reviewer-f2 plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of apm-only-install-reviewer-f2: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-16T22:19:53+00:00'
slug: apm-only-install-reviewer-f2
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works once one premise is fixed. The lock does record `name: kmctl` and `virtual_path: apm` for a git-URL dependency with `path: apm`, so a lock match is possible. But it does not record a URL that can be compared with the git: URL as the plan describes. The plan also does not say how the reverse direction, default source first and then another source, gets past remove_old_apm_entry.

## Checked

- The real lock files in the spikes. spike:apm-only-install/4 and /5 (stdout.txt lines 34-60) show a git-URL dependency recorded as `repo_url: o/pkg`, `host: 127.0.0.1`, `port: 46239`. spike:apm-only-install/6 (stdout.txt line 40) shows the `{git: http://127.0.0.1:PORT/o/kmctl.git, path: apm}` entry locked as `('o/kmctl', 'apm', '127.0.0.1')` for repo_url, virtual_path and host, and okf-skills as host github.com.
- That `name: kmctl` is recorded: apm/apm.yml names the package kmctl, and the integration test in tests/test_apm_package.py passes doctor's lock check against a real install, and that check relies on kmctl_package (name == kmctl and virtual_path == apm).
- src/kmctl/plugin.py: LockDependency (no host or port), _names_old_package, _is_kmctl_entry, remove_old_apm_entry, write_manifest and install's order (remove_old_apm_entry runs before write_manifest).
- Existing lock fixtures in tests/test_plugin.py and tests/test_doctor.py use owner/repo in repo_url, as the real lock does.
- spike:apm-only-install/6 outcome: swapping a `{git, path: apm}` entry and running apm install re-owns the files and leaves no orphans. So replacing the entry in place, with no uninstall, is sound for the new package, which carries no APM hook.

## Findings

- p1: the lock gives repo_url as owner/repo, with host and port in their own fields. So the URL comparison as written never matches a local or fork source, and the fix does nothing in the case it targets.
- p2: in the reverse direction, remove_old_apm_entry runs apm uninstall on the default-source entry first. Whether that removes a git-URL mapping is untested. If it does not, install fails before the new code runs. Either change _names_old_package or run the named spike.

## Notes

The plan lists no risks. The two above are the ones that could break it. Neither calls for a split.
