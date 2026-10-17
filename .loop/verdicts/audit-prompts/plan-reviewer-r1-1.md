---
type: verdict
title: 'Verdict: audit-prompts plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of audit-prompts: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T17:38:35+00:00'
slug: audit-prompts
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The two listed risks are settled by evidence that answers them. Spikes 1 and 2
ran the draft prompts live through a copy of action/agent.py that differs from
the repo's only in its PACKAGE path, and caught 9 of 9 plants once okf-vs-code
used the revised wording, with no false positives. Spike 3 shows the flag
rename was cited against source, so the evidence check does not block the docs
audit. One risk the plan does not list would break its contract: action.yml's
fixed artifact name means the composite action, which the how-to teaches,
cannot run the three audits the way the workflow does.

## Checked

- Spike folders 1, 2 and 3: README outcomes, run.json, stdout tails; the
  spike's agent.py against action/agent.py (diff is one line, the PACKAGE path).
- action/agent.py: DEFAULT_PROMPT, default_prompt(), run()'s prompt choice and
  the --prompt/--prompt-file exclusivity, the 200-request default, and publish
  finding its issue by exact title (so three titles keep three issues apart).
- action.yml: the `agent-report` upload and download names, the inputs.
- .github/workflows/knowledge-audit.yml and tests/test_action.py, which pin
  `agent-report` for both the workflow and the action.
- scripts/release.py DOC_LINES = 6 against the install lines in README.md, the
  tutorial and the how-to (1 + 1 + 4). The plan's how-to edit leaves the two
  `uses:` lines in section 5 alone unless it rewrites the example.
- tests/test_audit.py: it pins the audit skill, not the default prompt, so it
  survives the old prompt going.

## Findings

- p1: action.yml's artifact name is fixed at `agent-report`, so the three
  audits cannot run as a matrix through the composite action, while the plan
  changes only the workflow's artifact names. See the claim for what the plan
  needs to decide.

## Notes

- The spikes ran Gemini 3.8 Flash; the workflow names qwen/qwen3-coder. The plan
  does not say whether the workflow's model changes. Not a break, but the
  spike evidence is for Flash.
- Spike 2 used 135 of the 200 default requests on this repo's bundle; a larger
  bundle may hit the cap. The spike README says so; the plan could carry it into
  the how-to.
- The publish legs of a matrix all wait on every audit leg; if one audit fails,
  the default `needs:` skips every publish. A build detail, not a plan risk.
- The eval has no rows yet, though the plan states its done-when.
