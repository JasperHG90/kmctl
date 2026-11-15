---
applyTo: '**/.okf/**'
---

# Using the OKF bundle

`.okf/` at the repository root holds durable knowledge as markdown with YAML
front matter (OKF v0.2). What belongs in it, and what belongs in `docs/`
instead, is the `docs-layout` rule.

## Sections

Each section is created with its first concept, by `kmctl new`.

- `summary.md`: the first page to read, at most 500 words, which
  `kmctl init` writes.
- `manifesto.md`: the root concept, the project's current design. Invariants
  in it follow the `manifesto-invariants` rule.
- `.okf/decisions/`: one record per decision where a real alternative was
  rejected, numbered `NNNN-kebab-summary.md`.
- `.okf/practices/`: lessons learned the hard way, each backed by a count or a
  code site.
- `.okf/proposals/`: designs not yet built.
- `.okf/handoffs/`: notes for an agent picking up the work, each with a
  `stale_after` date, written by `kmctl new handoff`.
- `.okf/architecture/`: the design as diagrams and implementation design, kept
  current by the `diagrams-stay-current` rule.
- `.okf/prototypes/`: throwaway spikes that measure an idea before it is
  built, each a folder with a `README.md` concept, its scripts and its raw
  results.

## Start at the summary

`.okf/summary.md` is the entry point: in at most 500 words it distils what
the knowledge says as a whole, citing concepts inline as evidence, rather
than giving one bullet per decision; the indexes list the concepts.
`.okf/index.md` carries
`okf_version` and links the summary, the manifesto and each section. Each
section has its own `index.md` listing its concepts with the description
from each concept's front matter. Follow links from the summary and the
indexes rather than grepping the bundle.
A bundle with no summary yet starts at `.okf/index.md`; `kmctl update`
writes one.

`index.md` and `log.md` are reserved names. Never use either for a concept.

## One concept is one file

A concept's path minus `.md` is its id. Filenames are kebab-case and name an
entity, never a change. Prefer updating a concept to creating a neighbor.

Every non-reserved `.md` file needs parseable front matter with a non-empty
`type`. Hand-written concepts also carry `title`, `description`, `tags` and
`generated`. Quote a `description` that holds a colon. Write only the fields
the OKF spec defines; `kmctl new` writes them for you.

## Trust

An agent records itself in `generated.by` as `<producer>/<version>` (for
example `claude-opus/5.5`) and leaves the concept unverified. Only a person
who checked the content adds a `verified` entry with `by: human:<id>`.

A concept with no `verified` entry stays in `kmctl review due`, however often
an audit finds it holds. To clear one, the person reads it and confirms it is
still right. When they ask you to record that, run
`kmctl verify <id> --by human:<their id>` (ask for their id if you do not know
it); add `--stale-after 6m` when it is listed as `stale_after passed`. Never
run it on an audit verdict alone, or for a concept they did not confirm.

## Writing back

Touching a concept means updating its body, then appending a dated bullet to
`log.md` that says why. `log.md` is append-only.

When you add or change a concept, update `.okf/summary.md` in the same
change, or run `kmctl summary ack` when it still holds. `kmctl review due`
lists the summary until you do.

<constraint name="every-touched-concept-is-logged">
WHY: in the repository these rules came from, 43 of 53 commits that changed a
concept left at least one changed concept out of the log, so the log read as
complete and was not.

Each concept a change touches is named by its id, in backticks, in a line
that change appends to `log.md` (a file inside a prototype folder may be
named by the folder). A change never removes or rewrites an earlier line.
kmctl's own verbs write their log line; a hand edit writes its own.
</constraint>

## Decisions

A decision gets a record at the moment it is made, in the same change that
acts on it. The record carries Context, Decision (with the rejected
alternative) and Consequences. `status` is `draft`, `stable` or
`deprecated`. A `draft` record holds a choice written down but not yet
accepted; a proposal in `proposals/` weighs options before there is a
choice. Once the choice is accepted, the record's `status` becomes `stable`
and a line in `log.md` says so. Beyond that, a record is never rewritten: a
correction is an appended `## Correction, YYYY-MM-DD` section, and a
reversal is written in both records (`kmctl decision supersede` does this).

<constraint name="okf-changes-are-validated">
WHY: a malformed concept still renders and still reads as knowledge.

A change to `.okf/` is not done until `kmctl check` passes, and, where the
okf plugin is installed, `Skill(okf:validate)` passes against it with
`--strict`.
</constraint>

<constraint name="okf-indexes-track-their-directory">
WHY: a reader who trusts an index stops looking when it is wrong.

Adding, renaming or removing a concept updates that section's `index.md`, and
a new section adds its link to the root index, in the same change. Rename a
concept with `kmctl mv OLD NEW`, which also rewrites the links to it.
</constraint>
