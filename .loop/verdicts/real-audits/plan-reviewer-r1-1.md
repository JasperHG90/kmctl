---
type: verdict
title: 'Verdict: real-audits plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of real-audits: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T16:27:19+00:00'
slug: real-audits
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan holds. Its one listed risk, that the citation validator traps the agent in retries until it runs out of requests, is settled by spike:real-audits/2: a live Gemini Flash run with the validator finished in 85 of 200 requests, with 0 of 62 citations rejected and no retries. I found no unlisted risk that would break the approach, the scope or the contract.

## Checked

- Spike real-audits/2: README outcome, run.json (exit 0, 566 s, not timed out), the tail of stdout (20 checked entries, 0 findings, "validator call 1: 0/62 rejected") and the prototype `files/agent.py`. The prototype is the plan's design: `Checked` model, findings with claim, contradicted_by and fix, read ranges and search hits recorded on the Workspace, an `output_validator` raising `ModelRetry` that names each bad citation, a past-end check, and `retries={"output": 5}`. The evidence answers the risk for this repo and model. The plan carries the spike's open point (recovery after a rejection was never exercised live) into the offline tests, which is the right place for it.
- `action/agent.py` on main: `Report`, `Finding`, `read_file` (which reports the exact line range), `search_files` (which returns `path:line` hits), `render` and `publish`. The tools emit what the validator needs to record. `publish` filters on `SEVERITIES` and `--min-severity`, so it keeps working whether or not `info` stays a finding severity.
- Other consumers of the report shape: `action.yml` passes `report.json` only to `publish`. `tests/test_audit.py` checks the audit skill's sample findings, not the agent's `Report`, so changing `Report` does not touch it. `tests/test_agent.py` exists for the offline tests.
- The follow-up stub `.loop/plans/audit-prompts.md`, to check that this plan's contract serves it.

## Findings

None.

## Notes

- Lines the agent sees only through `run_shell` (`grep -n`, `cat`, kmctl output) are not recorded, so citations taken from them are rejected and the agent has to re-read them. The spike's 4 shell calls caused no rejections, and the retry message says what to do, so this is not a risk here. It does matter for the follow-up's docs-vs-code audit, which checks flags against the CLI's real `--help`: that evidence is command output, not a `path:line`, so a contradiction has to cite the source line that defines the flag. The audit-prompts spike with planted claims will show whether the agent does this. Its plan should name it as a risk, not this one.
- The plan does not say whether `info` stays in the `Finding` severity literal. Either choice works with `publish`. Settle it while building.
