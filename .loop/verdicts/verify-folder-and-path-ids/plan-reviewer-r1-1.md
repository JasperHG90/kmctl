---
type: verdict
title: 'Verdict: verify-folder-and-path-ids plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of verify-folder-and-path-ids: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-27T09:52:45+00:00'
slug: verify-folder-and-path-ids
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No risk found that would break the plan. The approach builds on code that exists and works the way the plan says. The Problems, Goals and Outcomes match the prose.

## Checked

- `_target` in packages/kmctl/src/kmctl/verify.py: `.okf/decisions/0001-x.md` becomes `.okf/.okf/decisions/0001-x.md`, which is refused. A docs path with .md already works because of `removesuffix(".md")`. `decisions/index` resolves to a real file and gets past every check, so P3 is real.
- `_concepts` and `_docs_pages` in review_due.py: `_concepts` drops index.md and log.md and keeps only `prototypes/*/README.md`. `_docs_pages` drops README.md. `review_due` builds ids as `path.relative_to(okf).with_suffix("")`, so a folder filter over these lists gives the same ids review due prints (prototypes as `prototypes/X/README`).
- Batch refusal: `verify_all` prepares every id before it writes. So `.okf/decisions/*`, which always expands to include index.md, is refused as a whole, which is what the plan wants. No decision record or prototype README has a `stale_after` in its front matter (the two grep hits are body text), so `kmctl verify decisions` will not trip the passed-stale_after refusal today.
- ADR 0055 rejected `--base` because it "would record checks for pages nobody named" (ADR 0023). The plan sends this tension to a draft ADR 0059 for the operator to accept, with a correction on 0055. That is the right venue, so it is not a risk.
- Outcomes against the prose: O1 covers the folder id, docs folders and the untouched index. O2 covers the path form. O3 covers decisions/index, log and the handoffs folder, and needs O1's shared page set. O4 covers refusal text and help. O5 covers the ADR. Every bullet in the intent maps to an outcome, and no outcome goes beyond the prose.

## Findings

None.

## Notes

These are build details, not plan risks:
- review_due.py imports `outside_verify` from verify.py at module level. If verify.py imports `_concepts`/`_docs_pages` at module level, the two modules import each other in a loop. Move the helpers or import them inside the function.
- O4 edits okf-bundle.instructions.md. Its body hash is pinned in `OLD_RULES` in packages/kmctl/tests/test_apm_package.py (ADR 0055's consequences say the same), so that hash moves too.
- `summary` is in `_concepts`, and review due says it is never verified. O3's rule ("refuse what review due never lists") leaves it verifiable, as it is today.
