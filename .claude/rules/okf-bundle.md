---
paths: [".okf/**"]
---

# Using the OKF bundle

`.okf/` at the repository root holds durable knowledge as markdown with YAML
front matter (OKF v0.2). What belongs in it, and what belongs in `docs/`
instead, is `.claude/rules/docs-layout.md`.

`.loop/` is a second OKF bundle that holds this repository's ticket state. It
is written by `loopctl`, the tool this repository's tickets run on, and is
never edited by hand. This rule governs `.okf/`.

## Sections

Each section is created with its first concept.

- `summary.md`: the first page to read, at most 500 words, which
  `kmctl init` writes.
- `manifesto.md`: the root concept, the current kmctl design. Invariants in
  it follow `.claude/rules/manifesto-invariants.md`.
- `.okf/decisions/`: one record per decision where a real alternative was
  rejected, numbered `NNNN-kebab-summary.md`.
- `.okf/practices/`: lessons learned the hard way, each backed by a count or a
  code site.
- `.okf/proposals/`: designs not yet built.
- `.okf/handoffs/`: notes for an agent picking up the work, each with a
  `stale_after` date, written by `/handoff` (ADR 0008).
- `.okf/architecture/`: the design as diagrams and implementation design, kept
  current by `.claude/rules/diagrams-stay-current.md`.
- `.okf/prototypes/`: throwaway spikes that measure an idea before it becomes a
  ticket, each a folder with a `README.md` concept, its scripts and its raw
  results.

## Start at the summary

`.okf/summary.md` is the entry point: in at most 500 words it distils what
the knowledge says as a whole, citing concepts inline as evidence, rather
than giving one bullet per decision; the indexes list the concepts.
`.okf/index.md` carries
`okf_version` and links the summary, the manifesto and each section. Each
section has its own `index.md` listing its concepts with the description
from each concept's front matter. Follow links from the summary and the
indexes rather than grepping the bundle. A bundle with no summary yet
starts at `.okf/index.md`; `kmctl update` writes one. kmctl neither writes
nor checks concept counts.

`index.md` and `log.md` are reserved names. Never use either for a concept.

## One concept is one file

A concept's path minus `.md` is its id. Filenames are kebab-case and name an
entity, never a change. Prefer updating a concept to creating a neighbor.

Every non-reserved `.md` file needs parseable front matter with a non-empty
`type`. Hand-written concepts also carry `title`, `description`, `tags` and
`generated`. Quote a `description` that holds a colon. kmctl writes only the
fields the spec defines plus the extension fields an ADR names (ADR 0009).

## Trust

An agent records itself in `generated.by` as `<producer>/<version>` (for
example `claude-opus/5.5`) and leaves the concept unverified. Only a person
who checked the content adds a `verified` entry with `by: human:<id>`.

## Writing back

Touching a concept means updating its body. `log.md` records lifecycle
events only, and it is append-only.

When you add or change a concept, update `.okf/summary.md` in the same
change, or run `kmctl summary ack` when it still holds. `kmctl review due`
lists the summary until you do, and kmctl's CI action fails the pull request.
A `kmctl verify` alone does not put the summary behind.

<constraint name="the-log-records-lifecycle-events-only">
WHY: every line appended to the end of `log.md` lands in the same place, so
two open pull requests that both append one conflict there on GitHub. In a
repository that used kmctl, 52 of 81 merged pull requests wrote to the log,
and 18 of those wrote only lines about edits. Git history already records an
edit, and a page's `verified` front matter records a check.

A change appends a line to `log.md` only for a lifecycle event: a concept
created, renamed, superseded, deprecated, removed, or regenerated after its
source changed, a decision accepted (`draft` to `stable`), or a concept
verified. The line names each concept by
its id, in backticks. An edit to a concept gets no line. A change never
removes or rewrites an earlier line. kmctl's own verbs write their line; a
hand change that is a lifecycle event writes its own.
</constraint>

## Decisions

A decision gets a record at the moment it is made, in the same change that
acts on it. The record carries Context, Decision (with the rejected
alternative) and Consequences. `status` is `draft`, `stable` or
`deprecated`. A `draft` record holds a choice written down but not yet
accepted; a proposal in `proposals/` weighs options before there is a
choice. `kmctl decision accept` makes a draft `stable` and logs who accepted
it. Beyond that, a record is never rewritten: a correction is an appended
`## Correction, YYYY-MM-DD` section, and a reversal is written in both
records (`kmctl decision supersede` does this).

<constraint name="drafts-are-settled-before-review">
WHY: in a repository that used kmctl, 29 of the 44 decision records that
merged pull requests added were still drafts when they merged, so nobody had
said yes to them.

Write a decision you record for a person as a draft
(`kmctl new decision --draft`). Before the pull request is marked ready for
review, list its open drafts with `kmctl check --no-drafts` and explain each
one to its author in a sentence or two. The author says accept, change or
drop. On an explicit yes, run
`kmctl decision accept <number> --by human:<their id>`; to drop one, delete
its file and its line in `.okf/decisions/index.md`. Never accept a draft the
author did not say yes to. kmctl's CI action fails a pull request that is
ready for review while a draft is left.
</constraint>

<constraint name="okf-changes-are-validated">
WHY: a malformed concept still renders and still reads as knowledge.

A change to `.okf/` is not done until `Skill(okf:validate)` passes against it
with `--strict`.
</constraint>

<constraint name="okf-indexes-track-their-directory">
WHY: a reader who trusts an index stops looking when it is wrong.

Adding, renaming or removing a concept updates that section's `index.md`, and
a new section adds its link to the root index, in the same change. Rename a
concept with `kmctl mv OLD NEW`, which also rewrites the links to it.
</constraint>
