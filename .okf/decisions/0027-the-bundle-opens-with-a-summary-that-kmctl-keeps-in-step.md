---
type: decision
title: "ADR 0027: The bundle opens with a summary that kmctl keeps in step"
description: "kmctl init writes .okf/summary.md, a page of at most 500 words that the briefing points to first; kmctl review due lists it when a concept changed in a commit after it, and kmctl summary ack, which writes the checked extension field, clears that."
tags: [adr, decision, okf, briefing]
generated:
  by: process:kmctl/0.7.0
  at: 2026-10-18T20:10:32Z
status: stable
sources:
  - resource: "src/kmctl/summary.py"
  - resource: "src/kmctl/review_due.py"
  - resource: "src/kmctl/checks.py"
  - resource: "src/kmctl/briefing.py"
  - resource: "src/kmctl/kinds.py"
---

# ADR 0027: The bundle opens with a summary that kmctl keeps in step

## Context

The briefing sent an agent to `.okf/index.md`, which lists sections, not
what they hold. To learn the state of the project an agent had to open the
manifesto, then the decision index, then the decisions, one at a time. The
operator asked (2026-10-18) for a project summary of at most 500 words that
captures the current state of the bundle: one more layer of progressive
disclosure, where each layer is short and points to the next (briefing,
summary, section indexes, concepts). A summary is only worth reading while it
is true, so something has to say when it falls behind.

Measured in this repository: of 200 commits not made by the loop, 40 changed
a concept, 28 concepts in all, about 10 a day. The briefing's worst case
(`tests/test_briefing.py`) was 494 of its 500 tokens, so the new pointer had
to come out of words already there (spike:okf-summary/2).

## Decision

- **One summary, at `.okf/summary.md`.** `kmctl init` writes it with five
  sections, Decisions, Architecture, Open work, Practices and Known gaps,
  each a theme that links down to its concepts, and links it from
  `.okf/index.md`. It is the `summary` kind in `kinds.py`; `kmctl schema
  summary` prints it, and `kmctl new` does not offer it, since there is one.
  It holds no counts or due lists, which kmctl computes.
- **At most 500 words.** `kmctl check` fails a body (outside the front
  matter) over 500 words, counted as words between spaces, and names the
  count. The operator moved from 250 to 750 to 500: enough for a theme per
  section, short enough to read at every session start.
- **Freshness by commit order.** The summary is behind when a concept (the
  manifesto, a decision, practice, proposal, prototype `README.md` or
  architecture page) changed in a commit after the last commit that changed
  the summary, or is changed or new in the working tree while the summary is
  not. Indexes, `log.md`, handoffs and the summary itself never count.
  `kmctl review due` lists it with the reason `concepts changed: ID, ...`,
  `kmctl check` and the CI action report it as a warning and never fail on
  it, and the briefing's state line ends with `summary current` or `summary
  behind: N concepts changed`. Without full git history the rule is skipped,
  as `review_due` skips its source reason. The summary is never listed as
  `unverified` or for `stale_after`, so an edit clears it fully.
- **`kmctl summary ack` beside `kmctl verify`.** When an agent reads the
  changed concepts and the summary still holds, it runs `kmctl summary ack`,
  which writes `checked: {at: TIME, against: [IDS]}` into the summary's front
  matter and nothing else, with `at` a UTC timestamp to the second. That is
  an edit to the summary, so the same rule clears it with no special case; a
  date alone would not be, since a second ack on the same day against the
  same ids would rewrite the same bytes. It claims no person's review, which stays
  `kmctl verify`'s (ADR 0023).
- **`checked` is the second extension field.** Invariant I4 and ADR 0009
  allow only extension fields an ADR names. This ADR names `checked`, with
  `checked.at` and `checked.against`, beside `handoff_key`.
- The briefing says "Start at .okf/summary.md", and the kmctl block in
  `CLAUDE.md` and `AGENTS.md` says the same and adds a duty: after adding or
  changing a concept, update the summary or run `kmctl summary ack`.

Rejected:

- **Freshness by date.** A change still in the working tree has no commit
  date to compare, and commit dates stop following commit order after a
  rebase or cherry-pick. Commit order handles both, and covers a concept
  committed together with the summary (spike:okf-summary/1: 10 cases, 24 to
  54 ms here).
- **A `stale_after` on the summary.** A date says nothing about whether a
  concept changed, so it would nag on a quiet project and stay silent on a
  busy one.
- **The agent clears it with `kmctl verify`.** `verify` records that a
  person checked a page (ADR 0023); an agent writing it would claim a review
  nobody did.

## Consequences

- The summary goes stale about as often as concepts change, about 10 times a
  day here, and each time the agent either edits it or runs `ack`. A
  `kmctl verify` stamp on a concept also counts as a change, an expected
  nudge that `ack` clears.
- To drop the briefing into 500 tokens, its docs line no longer lists the
  four Diataxis types; the Verbs line still names them. The worst case is
  494 tokens.
- `kmctl update` in a bundle made before this writes `summary.md`, adds its
  one entry to the kept `.okf/index.md` (first, as in a fresh index) and a
  line to `.okf/log.md`, and changes nothing else in either file, so
  `kmctl check` passes after it. It does the same for a manifesto it writes
  into a kept bundle, which used to get only a warning. A second run changes
  nothing.
- Adding any other extension field still needs its own ADR.

## Correction, 2026-10-18

The summary's sections are now The project, How it works, What it has
settled and Where it stands, not Decisions, Architecture, Open work,
Practices and Known gaps. The operator: "Summary should not list decisions
verbatim, that's what index is for. Summary should **summarize the
knowledge in them** and **keep a holistic view of the repo**". Sections
named after the concept folders steered each summary into one bullet per
group of records, as the decision index already lists them: this
repository's had 17 of its 20 links in Decisions. The new sections follow
what a reader needs: what the project is for, how its parts fit, the
principles and constraints the records settle, with their reasons and the
records cited as evidence, and what works or is open. The prompts `kmctl
init` writes under each say so, and the indexes still list every concept.
The rest of this decision holds: one summary, at most 500 words, kept in
step by commit order and `kmctl summary ack`.
