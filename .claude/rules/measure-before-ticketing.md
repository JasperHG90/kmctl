---
paths: [".loop/plans/**", ".okf/proposals/**", ".okf/decisions/**"]
---

<constraint name="measure-the-effect-before-cutting-the-ticket">
Before a ticket is authored, MEASURE the effect the change would have had
over real history, and put the number in the ticket. A hypothesis without a
measured effect is not a ticket, it is a hunch.

Verifying a premise ("is this claim about the code true?") is not the same
check. This one asks "would this change have DONE anything?" A ticket can be
built on true premises and still fire zero times.
</constraint>

## What counts as a measurement

A count over real history, not a plausible story:

- **The denominator is the real population.** How many times did the
  situation this change addresses arise? Reconstruct it from `.loop/`, `git`,
  or a real bundle this tool runs on, and say which.
- **The numerator is how often the change would have FIRED**, with its own
  preconditions applied.
- **Apply the SAFE variant.** If the design has a strict and a loose setting,
  measure the strict one.
- **State the ceiling separately.** "Fires 3 of 51 today, ceiling 22 of 51
  once X lands" is a case for building. "Fires 3 of 51" alone is not.

Where a change cannot be measured before it exists, a time-boxed spike is the
measurement. A spike that settles one plan risk runs through
`loopctl plan spike`, which keeps its run and scripts with the ticket in
`.loop/`. Analysis behind a number that a decision or a manifesto cites is a
prototype in `.okf/prototypes/<name>/` (`.claude/rules/docs-layout.md`).
Arguing a number on paper across review rounds is not a measurement.

<constraint name="quality-is-not-the-thing-being-traded">
A saving is never worth a weaker check. Where a saving and a check conflict,
measure what the check actually caught before proposing to narrow it, and
tell "the check never fires" apart from "the check cannot fire".
</constraint>

## When the measurement is zero

Say so and drop it, recording the number and the method in the drop reason.
If the zero is a coverage problem (the mechanism is sound but its inputs are
missing), that is a dependency, not a drop. Name the dependency and measure
the ceiling that lands with it.
