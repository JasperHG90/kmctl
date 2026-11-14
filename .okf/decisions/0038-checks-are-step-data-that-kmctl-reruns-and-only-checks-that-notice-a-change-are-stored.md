---
type: decision
title: "ADR 0038: Checks are step data that kmctl reruns and only checks that notice a change are stored"
description: "An agent writes each claim's check as steps from a fixed DSL through kmctl audit checks; kmctl reruns them with no model when the files they read change, and submit refuses a weak check that notices none of the in-memory changes to the code it matched; code and query steps need kmctl[audit]."
tags: [decision]
generated:
  by: process:kmctl/0.12.1
  at: 2026-11-11T09:33:47Z
status: stable
sources:
  - resource: "packages/kmaudit/src/kmaudit/steps.py"
  - resource: "packages/kmaudit/src/kmaudit/mutate.py"
  - resource: "packages/kmaudit/src/kmaudit/check_verbs.py"
---

# ADR 0038: Checks are step data that kmctl reruns and only checks that notice a change are stored

## Context

[ADR 0036](0036-claims-are-extracted-by-the-agent-through-kmctl-audit-claims.md)
puts a bundle's claims in `.kmctl/audit.sqlite`. The prototype in
`.okf/prototypes/audit-cli/` turned claims into checks with a langchain model
loop, and its pilots found two problems. A check can hold without testing
its claim: 25 of 161 measurable holding checks noticed no change to the
code they matched, 21 of them greps for a name. And the writer mostly failed
by guessing code it was never shown. Measuring all 171 checks took 23.3 s,
0.14 s a check, so measuring each one as it is stored is cheap.

## Decision

- A check is data: steps from a fixed DSL (file, grep, code, query,
  definition, imports, help) in `src/kmctl/claims/steps.py`, read only from
  git-tracked files outside `.okf/` and `docs/`, and never from markdown,
  which restates the knowledge (the prototype read markdown prompts; the
  plan's eval rows rule markdown out). A
  coding agent writes them with its own model through `kmctl audit checks
  todo`, `try` and `submit`; kmctl calls no model.
- `todo` hands each claim out with its anchors (each backticked span
  resolved to a path, command, flag or name) and the lines around them, or
  keyword windows from its concept's `sources`, so the agent sees the code.
  `try` runs a draft and writes nothing.
- `submit` runs each check and changes the lines it matched in memory
  (`src/kmctl/claims/mutate.py`). It refuses a weak check: one that holds
  but notices none of those changes, or matched only comments or
  docstrings. It also refuses a failing check not marked `drift`, and
  `drift` on a step that could not run. A check with no change to try is
  stored and reported as not measured.
- A `help` step never runs `uv run` on the project, which would create
  `.venv` or rewrite `uv.lock`: it runs a pyproject script from `.venv` or
  `PATH`, and a tracked script with `uv run --no-project --offline`.
- An answer whose claim is gone is dropped only once no section waits for
  extraction, so a claim that comes back with the same text keeps its
  check.
- `kmctl audit checks run` reruns a stored check only when the set or
  content of the files it reads changes, and measures it again only when
  its steps or reads move. It exits 0 whatever the checks find.
- Code steps need ast-grep-py and query steps jmespath, both in a new
  `kmctl[audit]` extra and imported only when such a step runs. Without
  them those steps report skipped, and `submit` refuses them, since their
  changes cannot be measured. Python definitions come from the standard
  library's `ast`, and YAML, TOML and JSON keys from their parsers.

Rejected:

- Checks as code: a script per claim cannot be validated, measured or kept
  from writing.
- A model writer inside the CLI (the prototype's way): the agent already
  has a model.
- tree-sitter-language-pack for definitions: a large wheel for what `ast`
  and the config parsers do for this repository's files.
- jmespath in base kmctl: base keeps its four dependencies.
- Storing weak checks with a trust label (the prototype's way): a stored
  check is believed, so one that tests nothing is worse than none.

## Consequences

The store is git-ignored, so a fresh checkout, CI among them, has no
checks; bringing checks to CI is a later ticket. In the prototype 93 of 171
checks used a code or query step, so a run without the extra checks less
than half of them. Audits still report only
([ADR 0005](0005-audits-report-only.md)).

## Correction, 2026-11-11

[ADR 0040](0040-the-audit-pipeline-holds-its-agents-by-a-hook-and-keeps-answers-through-rewording.md):
checks now read markdown outside the knowledge (skills, agent files,
prompts), and still never `.okf/`, `docs/`, READMEs, `CLAUDE.md`,
`AGENTS.md` or `CHANGELOG.md`. An answer whose claim is reworded follows it
to the claim of the same sentence, a reason goes stale only on files its
anchors name, and renaming a YAML key is a mutation.
