---
type: decision
title: "ADR 0011: kmctl init writes knowledge rules and a CLAUDE.md block for Claude Code"
description: "kmctl init writes four knowledge rules to .claude/rules/, a kmctl block into CLAUDE.md and AGENTS.md, and a first decision; the briefing stays the cross-harness path."
tags: [adr, decision, init, rules]
generated:
  by: claude-opus/5.5
  at: 2026-10-15T16:13:16Z
status: stable
---

# ADR 0011: kmctl init writes knowledge rules and a CLAUDE.md block for Claude Code

- Status: Accepted
- Date: 2026-10-15

## Context

An agent in a repository set up with `kmctl init` wrote code and left the
bundle nearly empty: it made 6 design choices and recorded 1, wrote no
architecture page, and left the manifesto's values empty. A fresh
`kmctl init` wrote four files and nothing else, so the agent got a briefing
and empty templates. In this repository knowledge stays current because of
things kmctl did not ship: rule files loaded by path, a `CLAUDE.md` that
routes to `.okf/`, and a seeded bundle.

[ADR 0002](0002-briefing-and-rules-injected-by-the-cli.md) rejected native
rule files per harness, because only some harnesses have them. The briefing
it chose is at 526 of its 600 words (I3), so the two rules it lacks
(`diagrams-stay-current`, `manifesto-invariants`) do not fit in it.

A spike (loop spike `init-seeds-the-habit/1`, one FastAPI task, three runs
per arm) compared init plus the briefing with the same plus the seeding
below: architecture pages went from 0 of 3 runs to 3 of 3, and decisions
recorded from a mean of 3.0 to 4.3.

## Decision

`kmctl init` also seeds the habit, for Claude Code first
([ADR 0003](0003-claude-code-plugin-first-depends-on-okf.md)):

- It writes the knowledge rules `okf-bundle`, `docs-layout`,
  `diagrams-stay-current` and `manifesto-invariants` to `.claude/rules/`, in
  full with their WHY paragraphs and `paths:` front matter, from package data
  in `src/kmctl/repo_rules/`. These copies are written for any repository. An
  existing file of the same name is kept.
- It adds a block between `<!-- kmctl:start -->` and `<!-- kmctl:end -->` to
  each `CLAUDE.md` and `AGENTS.md` that exists, once per real file, so a
  `CLAUDE.md` symlinked to `AGENTS.md` gets one block; with neither, it
  writes `CLAUDE.md`. The block holds the routing table and three duties:
  record each choice as a decision, keep `.okf/architecture/` matching the
  code, run `kmctl check` before finishing. A re-run replaces only the block.
- It records the decision "Keep project knowledge in an OKF bundle" through
  `kmctl new decision`'s writer when no record has that title.
- Its last line names the next steps: the manifesto's purpose and
  invariants, an architecture page once there is code, and a decision for
  each choice.

This reverses, for Claude Code only, the alternative ADR 0002 rejected
(native rule files per harness). The briefing stays the cross-harness path
and keeps its two one-line rules from `src/kmctl/rules/`, unchanged. The
CLAUDE.md block carries the gist of the other two rules for any harness that
reads `CLAUDE.md` or `AGENTS.md`.

Rejected:

- Add the two rules to the briefing. They take it past its 600-word budget
  (I3).
- Leave init as it was and rely on the briefing. The spike's unseeded arm
  wrote no architecture page in any run.
- Write rule files for every harness. Each has its own format, which is
  ADR 0002's reason, and the plugin is Claude Code first.

## Consequences

- `kmctl init` no longer leaves every kept file alone. The exceptions are the
  kmctl block in `CLAUDE.md` and `AGENTS.md` and the first decision's index
  entry and log line; `ScaffoldResult` and `kmctl init --help` name them.
- Two copies of the knowledge rules ship in the package: the briefing's
  one-line forms in `src/kmctl/rules/` and the full files in
  `src/kmctl/repo_rules/`. A change to a rule changes both.
- A repository that edits a seeded rule keeps its edit; init never
  overwrites it, so an upgrade does not reach it.
- Every new bundle starts with decision 0001, so a user's first
  `kmctl new decision` is numbered 0002.

## Correction, 2026-10-15

The Decision said that with neither `CLAUDE.md` nor `AGENTS.md` init writes
`CLAUDE.md`. That left a repository with only `AGENTS.md` without a
`CLAUDE.md`, and the operator asked for one whenever it is missing. Claude
Code 2.1.300 reads `AGENTS.md` only when there is no `CLAUDE.md`, or when
`CLAUDE.md` imports it with `@AGENTS.md`, which loads it once (loop spike
`init-claude-md-always/1`). So:

- With `AGENTS.md` and no `CLAUDE.md`, init adds the block to `AGENTS.md`
  and writes a `CLAUDE.md` holding only `@AGENTS.md`. With neither, it
  writes `CLAUDE.md` with the block, as before.
- A `CLAUDE.md` with an `@AGENTS.md` line, beside an `AGENTS.md`, never gets
  the block, since it already loads `AGENTS.md`'s; a second init changes
  nothing.
- A file counts as missing only when no directory entry exists. A
  `CLAUDE.md` or `AGENTS.md` symlink that is dangling or resolves outside the
  resolved repository root is left alone, with a warning naming the link and
  its target, so init never creates or edits a file through it. A symlink
  inside the repository is written through once, as before. When `AGENTS.md`
  is such a link and there is no `CLAUDE.md`, init writes no `CLAUDE.md` and
  the warning says to fix the link.

## Correction, 2026-10-15

The kmctl block now holds four duties, not three: a new one tells agents to
name the code a concept describes with `kmctl new --source` and to give
anything time-bound a `--stale-after`, so `kmctl review due` can flag the
concept when that code changes or the date passes (ticket new-concept-freshness).

## Correction, 2026-10-16

The briefing no longer carries the knowledge rules. `kmctl init` writes them
to `.claude/rules/`, and those files reach the agent's system prompt anyway,
so repeating them only spent the budget. `src/kmctl/rules/` is gone; the
briefing keeps one rule the rule files lack (`unverified-is-a-lead`, in
`src/kmctl/briefing.py`), and its budget is 500 tokens instead of 600 words
(I3). The operator asked for this on 2026-10-16.

## Correction, 2026-10-16

The Decision said an existing rule file of the same name is kept, and the
Consequences said an upgrade does not reach an edited rule. In practice an
upgrade reached no copy at all, edited or not, so every repository kept the
rules of the kmctl that first set it up. The operator asked for the rules to
be overwritten and for a `kmctl update` verb, and rejected tracking hashes to
spare edited copies. So:

- The four rule files belong to kmctl. Each run of `kmctl init` replaces one
  that differs from the packaged copy, edits included, and lists it under
  `updated`; one that matches is listed under `skipped` and not rewritten.
  Other files in `.claude/rules/` are never read or written. A rule that is a
  symlink dangling or pointing outside the repository is left alone with a
  warning, as `CLAUDE.md` and `AGENTS.md` are.
- `kmctl update` is the same command as `kmctl init`, for users who look for
  an update verb after upgrading.
- A repository that wants its own version of one of these rules puts it under
  another name (ticket update-refreshes-rules).

## Correction, 2026-10-16

`kmctl init` no longer writes the four knowledge rules, and `kmctl update`
no longer refreshes them. Since
[ADR 0014](0014-apm-is-the-only-install-route.md) they ship in kmctl's APM
package as `apm/.apm/instructions/NAME.instructions.md`, with the same
bodies and their `paths:` written as `applyTo:`, and `kmctl plugin install`
puts them in `.claude/rules/` through APM, which also replaces an older copy.
`src/kmctl/repo_rules/` is gone, and init's last line now starts with
`kmctl plugin install --harness claude`. The rest of this record stands: the
kmctl block in `CLAUDE.md` and `AGENTS.md`, and the first decision.

## Correction, 2026-10-17

The 2026-10-16 correction says init's last line starts with `kmctl plugin
install --harness claude`. That verb is gone ([ADR 0021](0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest.md)). Init's last line now
starts: "Next: install kmctl's package with APM for the skills and the
knowledge rules (the kmctl README's install section: an apm.yml entry, apm
install, kmctl plugin patch)" (`src/kmctl/__init__.py`), and `apm install`
puts the rules in `.claude/rules/`.

The kmctl block now holds five duties, not four: the fourth says a `docs/`
page may carry `description`, `stale_after` and `sources` front matter and
that a folder's `README.md` index is written by `kmctl check --fix`, never
by hand ([ADR 0022](0022-docs-pages-carry-optional-okf-front-matter-and-generated-folder-indexes.md),
`src/kmctl/scaffold.py`).

## Correction, 2026-10-18

The kmctl block now says to start at `.okf/summary.md`, not
`.okf/index.md`, and holds six duties, not five: the fifth says to update
`.okf/summary.md` after adding or changing a concept, or run `kmctl summary
ack` when it still holds ([ADR 0027](0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md),
`src/kmctl/scaffold.py`).

It also has a third kept-file exception. When init or update writes
`.okf/summary.md` or `.okf/manifesto.md` into a bundle whose kept
`.okf/index.md` does not link it, kmctl inserts that one index entry and
appends one line to the kept `.okf/log.md`, and changes nothing else in
either file, so `kmctl check` passes after an update (ADR 0027).

## Correction, 2026-10-19

The second 2026-10-16 correction, the one that says `kmctl init` no longer
writes the four rules, puts them in kmctl's package as
`apm/.apm/instructions/NAME.instructions.md`. Since
[ADR 0020](0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest.md)
they sit in the Claude Code sub-package,
`apm/claude/.apm/instructions/NAME.instructions.md`, with a copy for
Antigravity in `apm/antigravity/.apm/instructions/`. The rest of that
correction stands as the 2026-10-17 correction amends it.

## Correction, 2026-10-19

The Decision says init records the first decision when no record has that
title. A repository that records the same choice under another title, or
moves its decision log into `.okf/decisions/`, got a new copy on every run,
numbered after its own records (issue #26). Init and update now write the
first decision only when `.okf/decisions/` is missing or holds no decision
record: no `.md` file other than `index.md`, in it or in a folder inside it.
They no longer read titles, and a record whose front matter does not parse
still counts (`_write_first_decision` in `src/kmctl/scaffold.py`). A fresh
bundle still starts with `0001`.

Rejected: a tag that marks the record kmctl wrote. A migrated log or a
record written by hand does not carry it, so it fixes only the case kmctl
wrote itself, and it adds a field to keep.

## Correction, 2026-10-19

The kmctl block no longer says the rules for writing knowledge are in
`.claude/rules/` for every repository. `kmctl init` and `kmctl update` name
the rules folder of each harness `harnesses_found` in `src/kmctl/doctor.py`
reports: `.claude/rules/` for Claude Code, `.agents/rules/` for Antigravity,
`.opencode/rules/` for OpenCode. When it finds none, as on a first `kmctl
init` before `apm install`, the block names all three, each with its tool
(`src/kmctl/scaffold.py`). The briefing's line, which reaches every
harness, now says "the rules your tool loads cover writing knowledge" and
names no folder (`src/kmctl/briefing.py`).

The four rules the package installs had the same fault. `okf-bundle` and
`docs-layout` pointed to each other and to their siblings as
`.claude/rules/NAME.md`, a path an Antigravity-only install lacks; they now
name the rule, as "the `docs-layout` rule". `diagrams-stay-current` no
longer asks the user to edit its globs: a repository whose code lives
elsewhere adds a rule of its own under another name, since `apm install`
overwrites the package's file and doctor counts an edit as drift
(`apm/claude/.apm/instructions/`).
