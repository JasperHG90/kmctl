---
paths: [".loop/plans/**", ".okf/proposals/**", ".okf/decisions/**"]
---

<constraint name="measure-the-effect-before-cutting-the-ticket">
Before a ticket is authored, MEASURE the effect the change would have had over
the real corpus, and put the number in the ticket. A hypothesis without a
measured interception rate is not a ticket, it is a hunch.

Verifying a premise ("is this claim about the code true?") is not the same
check. This one asks "would this change have DONE anything?" A ticket can be
built on true premises and still fire zero times.
</constraint>

## What counts as a measurement

A count over real history, not a plausible story:

- **The denominator is the real population.** How many times did the
  situation this change addresses arise? Reconstruct it from `.loop/` (the
  ledger, verdicts, the cost ledger), `git`, or the v1 corpus in
  `loop-harness-plugin/.loop/`, and say which.
- **The numerator is how often the change would have FIRED**, with its own
  preconditions applied.
- **Apply the SAFE variant.** If the design has a strict and a loose setting,
  measure the strict one.
- **State the ceiling separately.** "Fires 3 of 51 today, ceiling 22 of 51
  once X lands" is a case for building. "Fires 3 of 51" alone is not.

Where a change cannot be measured before it exists, a time-boxed spike is the
measurement (`.okf/decisions/0003-plan-review-is-capped-and-spike-backed.md`).
Arguing a number on paper across review rounds is the failure mode
`.okf/practices/plan-review-as-paper-proof.md` records.

## Why this rule exists

`.okf/practices/measure-before-building.md` holds the three v1 measurements
that produced it, including `verdict-rebind`: planned, reviewed twice, then
measured at 0 of 51 and dropped.

## The focus areas

State which one a ticket serves, and measure THAT:

- **A faster loop**: fewer wall-clock minutes from pickup to commit.
- **Fewer turns**: fewer review rounds, re-dispatches and operator round
  trips.
- **Less token waste**: fewer reviewer agents, less re-reading.

From M3 on, the cost ledger records all three per ticket
(`.okf/manifesto.md`, V18).

<constraint name="quality-is-not-the-thing-being-traded">
None of the three is worth a weaker gate. Where a saving and a gate conflict,
measure what the gate actually caught over the same corpus before proposing
to narrow it, and distinguish "the check never fires" from "the check cannot
fire" (`.okf/practices/validate-a-gate-against-the-corpus.md`).
</constraint>

## When the measurement is zero

Say so and drop it, recording the number and the method in the drop reason.
If the zero is a coverage problem (the mechanism is sound but its inputs are
missing), that is a dependency, not a drop. Name the dependency and measure
the ceiling that lands with it.
