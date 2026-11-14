---
type: prototype
title: "Link question"
description: "How rewording the decision model's link question moved its answers on 679 checks: finding the exact text or value a claim describes now counts as testing the claim, so checks judged to test the claim itself rose from 198 to 328 and the median score from 0.70 to 0.76, most for checks that only grep, query or read files (0.75 to 0.84); nothing yet measures whether the model agrees with people."
tags: [prototype, audit, decision-model]
generated:
  by: claude-opus/5.5
  at: 2026-11-14T08:40:00Z
---

# Link question

## Question

`kmctl audit judge link` asks a decision model whether a check tests its
claim, on four levels: unrelated, a keyword only, a nearby fact, the claim
itself. A person reviewing checks found the model calling good checks
"nearby" or "keyword" when the check finds the exact text or value the claim
describes, such as a workflow's triggers, or a package name in
`pyproject.toml`. For a claim about what a file says, that is the best check
there is. Does rewording the question to say so change the answers?

## Method

The link question in `src/kmctl/judge.py` (`LINK`) was reworded on
2026-11-14: finding the exact text or value a claim describes counts as
testing the claim, a part of a claim no file could show (where a repository
lives) is not held against the check, and "a nearby fact" means the fact the
claim states could change while the steps still pass. Every check that has
run, 789, was judged again with `jev-latest`:

```
uv run kmctl audit judge link ID... --config audit.toml --json
```

`compare.py` takes each check's latest answer before the rewording and its
answer after, from `.kmctl/audit.sqlite`, and writes `results.csv` (ids and
numbers only):

```
uv run python .okf/prototypes/link-question/compare.py 2026-11-14T08:26:06+00:00
```

"Wording" checks are those whose every step is a grep, query, file or help
step; "code" checks have at least one code, definition or imports step.

## Results

679 checks had an answer from before; 9 of them were rewritten in between.

| Checks | Count | "The claim itself" | Median score | Below 0.5 | Up / down / same |
|---|---|---|---|---|---|
| All | 679 | 198 → 328 | 0.70 → 0.76 | 32 → 25 | 331 / 9 / 339 |
| Wording | 311 | 140 → 202 | 0.75 → 0.84 | 9 → 6 | 161 / 3 / 147 |
| Code | 368 | 58 → 126 | 0.66 → 0.71 | 23 → 19 | 170 / 6 / 192 |

"Up" and "down" mean the score moved by more than 0.05.

- Wording checks gained most, as intended. The two the reviewer flagged
  went different ways: the workflow-trigger check moved from 0.82 (split 50%
  nearby, 48% the claim) to 0.94 (82% the claim); the `pyproject.toml`
  check stayed at 0.67, nearby, the model still holding the claim's
  "repository" half against it.
- "A keyword only" went up, 17 → 29: the narrower wording sends checks that
  find a name but not the fact there, rather than to "nearby".

What this does not show: whether the model is right. Nothing compares its
levels with people's thumbs yet, so the page shows its answer as a guess and
no check is sent back on the model's word alone. One model, one repository,
one day.
