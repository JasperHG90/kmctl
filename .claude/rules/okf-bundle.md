---
paths: [".okf/**"]
---

# Using the OKF bundle

`.okf/` at the repository root holds durable knowledge as markdown with YAML
front matter (OKF v0.2). What belongs in it, and what belongs in `docs/`
instead, is `.claude/rules/docs-layout.md`.

`.loop/` is a second OKF bundle that holds loop state
(`.okf/architecture/loop-state.md`). This rule governs `.okf/`. Most of
`.loop/` is written by the harness and is never edited by hand.

## Sections

- `manifesto.md`: the root concept, the current v2 design. Invariants in it
  follow `.claude/rules/manifesto-invariants.md`.
- `decisions/`: one record per decision where a real alternative was
  rejected, numbered `NNNN-kebab-summary.md`.
- `practices/`: lessons learned the hard way, each backed by a count or a
  code site, mostly carried over from v1.
- `proposals/`: designs not yet built, including the v2 build plan.
- `handoffs/`: notes for an agent picking up the work, each with a
  `stale_after` date.
- `architecture/`: the design as diagrams and implementation design, kept
  current by `.claude/rules/diagrams-stay-current.md`.
- `prototypes/`: throwaway spikes that measure an idea before it becomes a
  ticket, each a folder with a `README.md` concept, its scripts and its raw
  results.

`components/` is created when v2 has code to describe.

## Start at the root index

`.okf/index.md` is the entry point. It carries `okf_version`, one link per
section, and a count. Each section has its own `index.md` listing its
concepts with the description from each concept's front matter. Follow links
from the index rather than grepping the bundle.

`index.md` and `log.md` are reserved names. Never use either for a concept.

## One concept is one file

A concept's path minus `.md` is its id. Filenames are kebab-case and name an
entity, never a change. Prefer updating a concept to creating a neighbor.

Every non-reserved `.md` file needs parseable front matter with a non-empty
`type`. Hand-written concepts also carry `title`, `description`, `tags` and
`generated`. Quote a `description` that holds a colon.

## Trust

An agent records itself in `generated.by` as `<producer>/<version>` (for
example `claude-opus/5.5`) and leaves the concept unverified. Only a person
who checked the content adds a `verified` entry with `by: human:<id>`.

## Writing back

Touching a concept means updating its body, then appending a dated bullet to
`log.md` that says why. `log.md` is append-only.

<constraint name="every-touched-concept-is-logged">
WHY: before this was checked, 43 of 53 commits that changed a concept left
at least one changed concept out of the log (169 of 237 concept edits), so
the log read as complete and was not.

Each concept a change touches is named by its id, in backticks, in a line
that change appends to `log.md` (a file inside a prototype folder may be
named by the folder). A change never removes or rewrites an earlier line.
`scripts/check_okf.py` checks this against where the branch left `main`
(in CI, against the pushed range or the pull request's base), and also
checks that every section index links its concepts and the root index's
counts match. It runs in the `okf` gate, prek and CI.
</constraint>

## Decisions

A decision gets a record at the moment it is made, in the same change that
acts on it. The record carries Context, Decision (with the rejected
alternative) and Consequences. `status` is `stable` or `deprecated`.
`decision_status` carries the record's own words (`Accepted`,
`Superseded by ADR NNNN`). A record is never rewritten: a correction is an
appended `## Correction, YYYY-MM-DD` section, and a reversal is written in
both records.

<constraint name="okf-changes-are-validated">
WHY: a malformed concept still renders and still reads as knowledge.

A change to `.okf/` is not done until `Skill(okf:validate)` passes against it
with `--strict`.
</constraint>

<constraint name="okf-indexes-track-their-directory">
WHY: a reader who trusts an index stops looking when it is wrong.

Adding, renaming or removing a concept updates that section's `index.md` and
the root index count in the same change.
</constraint>
