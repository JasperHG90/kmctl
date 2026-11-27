---
type: prototype
title: "Mixed claims"
description: "A count of how many claims answered with a reason join a checkable fact to an opinion: 1 of 384 on a strict reading, 3 on a loose one, so a split rule for the extractor is not worth a ticket."
tags: [prototype, audit]
generated:
  by: claude-opus/5.5
  at: 2026-11-11T18:00:00Z
verified:
  - by: human:jasper
    at: 2026-11-27T20:41:27Z
---

# Mixed claims

## Question

The claim "kmctl is a standalone CLI with thin skills" got a reason and no
check, because "thin" is an opinion. Its other half, "standalone CLI", is a
fact one step could test. Would a rule telling the extractor to split a
fact from an opinion have turned many reasons into checks?

## Method

`dump.py` reads the audit store and writes `reasons.tsv`: every claim whose
stored answer is a reason, with its text and the reason.

```
uv run python .okf/prototypes/mixed-claims/dump.py
```

Claude (claude-opus/5.5) read all 384 claims once and wrote the candidates
to `labels.tsv`: `mixed` for a claim that joins a checkable fact to an
opinion, `loose` for one that joins facts to a statement of purpose or
cause, and `opinion` for one with no checkable half. A claim not listed
there is neither. One reader labelled them once; nobody checked the labels.

## Results

On 2026-11-11 the store held 384 claims answered with a reason.

| Label | Claims |
|---|---|
| mixed (strict) | 1 |
| loose | 2 |
| opinion only | 2 |
| none of these | 379 |

A split rule would have fired on 1 of 384 reasons, or 3 of 384 on the loose
reading. That is not worth a ticket.

The reading showed a different pattern that this prototype did not count:
reasons on claims that one step looks able to test, such as "kmctl_ref is a
question in copier.yml" (reason: "no step can test a future choice") and
"starter/.gitignore ignores apm_modules/" (reason: "the gitignore is a file
checks cannot read").
