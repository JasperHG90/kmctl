---
type: plan
title: 'Plan: repo-uses-apm'
description: "This repository installs its agent rules, skills and AGENTS.md guidelines with APM (an apm.yml and its lock file) instead of aim, with the same files landing in the same places."
slug: repo-uses-apm
epic: repo
depends_on: []
priority: 6
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T17:37:09+00:00'
---

# repo-uses-apm

Relayed from: operator, 2026-10-15: "Instead of aim, this repository should use APM".

## Intent

aim manages, from `aim.toml` and `aim.lock.toml`: 13 rules from `https://github.com/jasperhg90/skills` (written to `.claude/rules/`), 3 skills from the same repository (agent-creator, rule-creator, generate-art, written to `.claude/skills/`), and two marker regions in `AGENTS.md` (the `aim:` header and the guidelines block; `CLAUDE.md` is a link to `AGENTS.md`). APM (Microsoft's Agent Package Manager, https://microsoft.github.io/apm, `apm-cli` 0.33.0) replaces it:

- An `new:apm.yml` with `targets: [claude]` lists the 13 rules as `jasperhg90/skills/rules/<name>.instructions.md#<ref>` and the 3 skills as `jasperhg90/skills/skills/tools/<name>#<ref>` under `dependencies.apm`, pinned to the commit that merges https://github.com/JasperHG90/skills/pull/139, which is after `f0813cd` (the commit that moved the rules to APM's `.instructions.md` form; earlier ones have none, and APM refuses a plain `.md` rule). That PR carries this repository's local additions to `python-testing` (the Test tiers section and the measure-before-marking, run-your-own-test and every-tier-runs-somewhere constraints, about 50 lines in no upstream commit), so the switch loses nothing; the operator chose to push them upstream (spike:repo-uses-apm/3 found them). The build waits for that merge: an eval row fails unless the installed `python-testing` holds the Test tiers section and the three constraints, which no commit has until PR 139 merges, so a build pinned earlier cannot pass. If the PR is changed in review, the row follows the merged text; if it is closed unmerged, the ticket blocks and the operator decides (round 2 plan review). `apm install` writes them and `new:apm.lock.yaml` pins the full commit and each file's sha256 (spike:repo-uses-apm/2). APM adds `apm_modules/` to `.gitignore`.
- APM writes each rule into `.claude/rules/`, named after the rule, with its front matter in Claude Code's form: `applyTo` becomes a `paths:` list, so path scoping holds; `name` and `description`, which Claude Code does not read in a rule, are dropped; a rule with no `applyTo` gets no front matter and so loads always, as it does today. Skills land in `.claude/skills/`, one folder each, byte for byte. Rule bodies come from the pinned commit. Against today's files, spike 3 found 11 of 13 bodies unchanged, `pre-existing-issues` losing a stray `%   ` at its end, and `python-testing` differing only by the text PR 139 adds; the `rule-creator` skill picks up upstream README edits. The build lists each change.
- This repository's own rules (`okf-bundle.md`, `diagrams-stay-current.md`, `manifesto-invariants.md`, `docs-layout.md`, `measure-before-ticketing.md`, `adversarial-reviews.md`, `cli-interface.md`, `cli-version-floor.md`, `skills-are-thin.md`, `skills-via-skill-creator.md`) are left as they are.
- The `AGENTS.md` guidelines block becomes plain text owned by this repository: APM does not write `AGENTS.md` on install, and `apm compile` never overwrites a hand-written one. The `aim:` markers and the header line naming aim go; the text in between stays.
- `tests/test_rules.py` tells upstream rules from this repository's own by reading `aim.toml` (`_aim_managed`); it reads the managed set from `apm.yml` instead, mapping each `<name>.instructions.md` entry to the installed `<name>.md`, and its docstring and the ruff comment in `pyproject.toml` stop naming aim (round 2 plan review).
- `aim.toml` and `aim.lock.toml` are removed, and `CLAUDE.md`/`AGENTS.md`'s routing text says rules come from `apm.yml` (changed in `jasperhg90/skills`, not here). `.loop/config.toml` and the loop's own plugin are untouched.

Measured: aim manages 16 items here (13 rules, 3 skills) and 2 marker regions; 0 are managed by APM. Spike 2 installed 2 of the rules and 1 skill with APM 0.33.0 to the right paths.

Done when `apm install` in a clean clone writes the 13 rules and 3 skills to the same paths as today; each rule's `paths:` scoping matches what it has now (or, for a rule with none, it has none); each rule body equals the pinned upstream file's body; each skill equals the pinned upstream folder; the installed `python-testing` holds the Test tiers section and the measure-before-marking, run-your-own-test and every-tier-runs-somewhere constraints; `tests/test_rules.py` reads the managed set from `apm.yml` and passes; `aim.toml` and `aim.lock.toml` are gone and no file names aim; the `AGENTS.md` guidelines text is unchanged apart from the markers and the aim header; and the gates pass.

## Could invalidate this plan

- Settled by spike:repo-uses-apm/3 (all 13 rules and 3 skills at `f0813cd`: placement, `paths:` scoping, bodies and skills match upstream). Spike 2 first showed APM 0.33.0 installs a `jasperhg90/skills` rule to `.claude/rules/` with Claude Code's `paths:` scoping and a skill to `.claude/skills/`; the rule's `name`/`description` front matter is dropped, which Claude Code does not read.
