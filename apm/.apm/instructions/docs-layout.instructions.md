---
applyTo: "docs/**, .okf/**, README.md"
---

# `docs/` and `.okf/`

Two places hold prose, and they have different readers.

- `docs/` is for people who USE the project: someone installing it, calling
  it, or reading why it failed. Its index page, README.md at the top of
  `docs/`, lists every page.
- `.okf/` is for agents and people working ON this repository: decisions and
  the alternative each rejected, lessons learned the hard way, and proposals
  not yet built. How to read and extend it is `.claude/rules/okf-bundle.md`.
  The current design (vision, invariants, values) is the bundle's root
  concept, `.okf/manifesto.md`. It links to the decisions for the why and
  never repeats a decision record.

<constraint name="docs-sorted-by-reader-intent">
WHY: a page filed under the wrong heading is read by the wrong person.

`docs/` has one subdirectory per Diataxis type, created with its first page:
`docs/how-to/` (one task, one way), `docs/reference/` (commands, config keys,
API entries, without instructing), `docs/explanation/` (why the project is
shaped this way), and `docs/tutorials/` (a lesson sure to succeed in one
sitting). Mixing two intents in one page is a reason to split it.
</constraint>

<constraint name="audience-gates-the-folder">
WHY: a spike, a build plan or a handoff reads as current instructions to a
user who finds it in `docs/`.

A prototype, a proposal, a build plan, an audit, a handoff note, or the
record of a choice goes to `.okf/`, even when it is shaped like a guide.
</constraint>

<constraint name="prototypes-hold-their-scripts">
WHY: a spike's numbers are only evidence if someone can re-run them, and a
script run from a heredoc or a scratch folder is gone when the session ends.

A prototype is one folder, `.okf/prototypes/<name>/`, with its `README.md`
concept, every script that produces a number in that README, and the raw
results those scripts read. That covers one-off analysis too: a count, a
control run, a benchmark. Write it as a script or a command in the folder and
run that, never inline or from a scratch folder. Data that must stay private
is git-ignored inside the folder, not kept elsewhere.
</constraint>

<constraint name="docs-describe-what-exists">
WHY: a user page about a feature that does not exist yet is a hallucination
with a table of contents.

A `docs/` page lands in the same change as the behavior it describes. Until
then the design lives in `.okf/manifesto.md` and `.okf/proposals/`.
</constraint>

<constraint name="index-tracks-the-folder">
WHY: an index is believed, so an index that disagrees with its folder is
worse than none.

Adding, renaming or removing a page under `docs/` updates the docs index in
the same change, and updates every link to the old path. `kmctl check`
fails when they disagree.
</constraint>
