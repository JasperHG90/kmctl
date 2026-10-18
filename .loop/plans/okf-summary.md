---
type: plan
title: 'Plan: okf-summary'
description: The .okf/ bundle gets a summary of at most 500 words that the briefing points to first, and kmctl review due lists it when a concept changed after it.
tags:
- plan
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T19:32:34+00:00'
slug: okf-summary
epic: null
depends_on: []
priority: 2
---

# okf-summary

Relayed from: none

## Intent

The operator (2026-10-18, ask j-20261018T192834+0000-db7087e2): "I want that
the okf bundle contains a project summary of max some length (suggest
something) that captures the current state of the repository", "Or well:
current state of the okf docs", "Bit like a progressive disclosure mechanism
on the project level", "What's also nice about that is that you can add a
hook or something so that any time something is changed in the okf bundle,
the summary should plausibly be updated (unless it's not so relevant or
something)", "250 word limit? How about making that 750 words", then "Not at
the end of a turn. Just when anything in .okf changes", and "make it 500
words max".

Measured on this repository:

- **How often a concept changes.** Of the 200 commits whose subject does not
  start with `loop:` (2,477 in all, 2026-10-15 to 2026-10-18), 45 touched
  `.okf/` and 40 changed a concept (manifesto, a decision, practice,
  proposal, prototype README or architecture page; not an index, `log.md`
  or a handoff): 28 distinct concepts, a median of 3 per commit. So the
  summary would have gone stale in 40 of 200 commits, about 10 a day.
- **How often the hook runs.** The Claude Code transcripts for this repo
  and its worktrees (441 sessions, main and subagent) hold 9,103 Write,
  Edit, MultiEdit and Bash calls, so a PostToolUse hook on those tools runs
  about 9,100 times; 1,511 (17%) of them name `.okf/` in their input.
  Starting `kmctl --version` takes 86 to 145 ms, `kmctl review due --json`
  300 ms, and `git status --porcelain -- .okf` and `git log -1 -- .okf`
  2 ms each. So the hook's check must not run `review_due`: it uses git
  only and stays under 150 ms a call.
- **The briefing budget.** `kmctl briefing` is 1,893 characters here (474
  of 500 tokens), and the test worst case
  (`tests/test_briefing.py::test_briefing_long_handoff_title_keeps_the_budget`)
  is 494, matching ADR 0023. The new line has 5 tokens (about 20
  characters) to work with unless it cuts words elsewhere.

Split (operator, 2026-10-18: "1. Split."): this ticket is the summary
itself. The hook that nudges the agent right after it changes a concept is
okf-summary-nudge (Claude Code), and okf-summary-nudge-agy-opencode
(Antigravity and OpenCode); both depend on this one.

What changes:

- **The `summary` kind.** `src/kmctl/kinds.py` gets `summary` at
  `.okf/summary.md`: front matter `type: summary`, title, description, tags,
  generated, `verified` (a person), `checked` (an agent's ack), and sections Decisions, Architecture, Open work
  (proposals and prototypes), Practices, Known gaps. Each section describes
  a theme of what the bundle knows and links down to its concepts; no
  counts or due lists, which kmctl computes. `kmctl schema summary`
  prints it. `kmctl init` (`src/kmctl/scaffold.py`) writes the skeleton and
  links it from `.okf/index.md`. Progressive disclosure, which means each
  layer is short and points to the next: briefing, then summary, then the
  section indexes, then the concepts.
- **The check.** `kmctl check` (`src/kmctl/checks.py`) fails a summary
  body over 500 words (counted as `len(text.split())` outside front matter)
  and names the count; links in it are checked like other `.okf/` pages
  (the okf validator for links inside the bundle, kmctl's `link` check for
  links out of it).
- **Freshness.** One function in `new:src/kmctl/summary.py` decides
  whether the summary is stale: a concept was changed in a commit after the
  last commit that changed `.okf/summary.md`, or is changed in the working
  tree while the summary is not, and it returns those concepts. The
  summary itself, indexes, `log.md` and handoffs never count. Commit order
  rather than dates, so a concept committed together with the summary
  edit, or after a `kmctl verify` stamp written earlier the same session,
  is covered. A shallow clone or no git skips the check, as `review_due`
  does. `kmctl review due` (`src/kmctl/review_due.py`) lists the summary
  with reason `concepts changed: ID, ...`; an edit to the summary clears
  it, and so does `kmctl summary ack`. ADR 0023 keeps `kmctl verify` for a
  person who checked a page; the operator agreed (2026-10-18, "2. Fine.")
  that when an agent judges the summary still right after a change, it
  says so with `ack`, which writes `checked: DATE` and the concepts it was
  checked against into the summary's front matter. That is an edit to the
  summary, so the commit-order rule clears it with no special case, and it
  claims no human review. `kmctl check` and the CI action report a stale
  summary and never fail on it.
- **The briefing and the AGENTS.md block.** `ROUTING` in
  `src/kmctl/briefing.py` says "Start at .okf/summary.md" in place of
  `.okf/index.md`, and the state line says whether it is current, inside
  `TOKEN_BUDGET` in the worst-case test. The `BLOCK` in
  `src/kmctl/scaffold.py` says the same and adds a duty: when you add or
  change a concept, update `.okf/summary.md`, or run `kmctl summary ack`
  when it is still right.
- **The record.** A decision records the summary, its limit, the
  commit-order freshness rule and `ack` beside ADR 0023's `verify`;
  `.okf/manifesto.md`'s Parts list, `.okf/architecture/overview.md`,
  `docs/reference/commands.md` and the AGENTS.md block follow. This
  repository gets its own `new:.okf/summary.md`.

The outcome that shows it worked: in a test repository made with `kmctl
init`, `kmctl new decision` makes `kmctl review due` list the summary with
that decision's id; an edit to `.okf/summary.md`, or `kmctl summary ack`,
clears it; `kmctl check` fails a summary over 500 words; and the briefing
says "Start at .okf/summary.md" within 500 tokens in the worst-case test.
Tests in `new:tests/test_summary.py` drive this from the CLI.

## Could invalidate this plan

- The commit-order freshness rule may misfire over real history: flag a
  summary that was updated in the same session, or miss concept changes
  made through `kmctl verify`, which rewrites a concept's front matter and
  `log.md`. Then freshness needs another baseline.
  spike:okf-summary/1 (10 cases pass; a verify stamp nudges, which ack
  clears; 24 to 54 ms on this repository; new untracked concepts need
  `git status --untracked-files=all`)
- The briefing may not fit the new line: the worst case is 494 of 500
  tokens, and "Start at .okf/summary.md" plus whether it is current must
  come out of words already there.
  spike:okf-summary/2 (fits: dropping the Diataxis list from ROUTING's
  docs/ line, which the Verbs line repeats, gives 488 tokens with "summary
  current" and 493 with "summary behind: N concepts changed")
