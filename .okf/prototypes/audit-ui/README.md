---
type: prototype
title: "Audit UI"
description: "A starter page for browsing kmctl audit results: documents that need a new audit, each sentence coloured by whether its claims are checked, and the selected text's claims, checks and confidence."
tags: [prototype, audit]
generated:
  by: claude-opus/5.5
  at: 2026-11-11T16:15:00Z
---

# Audit UI

## Question

Can one page show a person what `kmctl audit` knows about the bundle: which
documents need auditing again, which sentences no check covers, and for a
selected passage its claims, the checks behind them and how far to trust
those checks? `mock.excalidraw.png` is the sketch it starts from.

## Method

`export.py` reads the audit store (`.kmctl/audit.sqlite`) through kmctl's
own `Store`, `check` and `list_checks`, after refreshing the stored sections
as `kmctl audit claims todo` does. It writes `data.js` next to itself, which
`index.html` loads, so the page opens from disk with no server:

```
uv run python .okf/prototypes/audit-ui/export.py
open .okf/prototypes/audit-ui/index.html
```

`data.js` is generated from a local store, so it is git-ignored here.

The page has three columns, as in the sketch:

- **Documents.** Every concept, by folder, with a thin bar showing its
  sentences' split by coverage and a count of its drifts (or sentences with
  no check, or "outdated" when a section's key moved). A search box and
  chips narrow the list to drift, not checked or needs extraction.
- **Document.** The text set as a page to read, with one mark per kind of
  coverage: a wavy red underline for drift, dashed for not checked, dotted
  for reason only, solid green for checked, grey for needs extraction, and
  plain grey text for no claim or not checkable. Tables and code blocks
  render as such. A strip above the text has one tick per sentence in
  document order; click a tick, a sentence or a heading to select it, click
  a count in the key to go to the next sentence of that kind, and press
  `j` or `k` for the next or previous sentence with a claim.
- **Claims, checks, confidence.** One card per claim, with an arrow tip
  pointing at the text. The card stacks the claim, then its check (steps,
  last results, any drift, or the writer's reason), then its confidence
  (how many test changes the check noticed), each on its own colour from
  the sketch. A section with more than three claims shows them closed;
  click one to open its check.

  Confidence is written out: how many of kmctl's trial edits to the code
  the check caught, what an exact or an indirect (`proxy`) check means, and
  the missed edits grouped by file. The words Low, Medium and High are this
  page's own, cut at a third and two thirds of the edits caught; kmctl
  stores only the counts.

The page opens on the first document with drift, and the address holds the
selection, so a link points at one sentence.

## Results

On 2026-11-11 the export read 37 concepts from this repository's store
(1.4 MB of `data.js`); the page renders them all. It is a starter: it has
no judge decisions, no history and no way to act on a finding.

On 2026-11-12 the page moved into the package as `kmctl audit ui`, which
serves it on 127.0.0.1 with live data and adds feedback, verdicts and
second opinions
([ADR 0041](../../decisions/0041-people-review-claims-and-checks-on-a-local-page-and-their-feedback-goes-back-to-the-agents.md)).
This folder keeps the starter and its export script as they were.
