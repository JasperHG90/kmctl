---
type: verdict
title: 'Verdict: action-pin-shas plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of action-pin-shas: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-19T14:31:25+00:00'
slug: action-pin-shas
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan holds up. All four SHAs match their release tags upstream. The plan calls this a pin, but it also jumps several major versions (setup-uv v6 to v10.2.0, upload-artifact v4 to v7.0.2, download-artifact v4 to v8.0.2, checkout v4 to v7.0.1). I read the breaking changes for each jump, and none of them touches how `action.yml` or `knowledge-audit.yml` uses these actions. The pin test can take both files as they are.

## Checked

- Ran `gh api repos/<owner>/<repo>/commits/<tag>` for each tag. download-artifact v8.0.2 = 9000827c..., upload-artifact v7.0.2 = cf430e03..., setup-uv v10.2.0 = c18668ad..., checkout v7.0.1 = 3d3c42e5.... All four match the plan.
- `grep -n uses:`: action.yml has exactly the three lines the plan names (136, 192, 200). knowledge-audit.yml has the seven tag refs the plan describes. Neither file has a `uses:` in a comment that the line-based test in `tests/scripts/test_workflows.py:262` would catch by mistake.
- setup-uv v7 to v10 breaking changes: node24, `server-url` removed, no floating major/minor tags from v8, `prune-cache` now off by default, `enable-cache: auto` turned off for some events. Both files set `enable-cache: false`, the same as ci.yml already does on v10.2.0. ci.yml runs the composite action (`uses: ./`) in checks mode, so the setup-uv change gets tested in CI.
- upload-artifact v5 to v7: node24, ESM, an opt-in `archive: false`. The defaults are unchanged for name+path uploads.
- download-artifact v5 to v8: the path change applies only to downloads by artifact ID (we download by name). The digest-mismatch default is now `error`, which is a stricter check, not a break. v8 still unzips zipped artifacts, and our uploads are zipped (the default). Upload v7 and download v8 work together, the same pairing release.yml relies on.

## Findings

None.

## Notes

- Consumers on self-hosted runners will need Actions Runner 2.327.1 or later, because every pinned version runs on Node 24. The project has no outside users yet and GitHub-hosted runners already qualify, so this does not block. A line in the changelog or the how-to would help a future self-hosted user.
- CI never runs the artifact steps in `action.yml` (audit and publish modes). They will first run in a consumer repo. The release notes above are the evidence they still work; a manual knowledge-audit run after landing would test the same pair end to end.
