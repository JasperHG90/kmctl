# Log

## 2026-10-15

- Seeded the bundle: the manifesto and six decisions from the design
  discussion in loop-harness, which this repository formalizes.
- Added `decisions/0007-skills-are-made-with-skill-creator` and
  `decisions/0008-handoffs-are-okf-concepts` at the operator's request, and
  named both in `manifesto`: the plugin gains /handoff and /continue, and
  every skill is made with skill-creator.
- Added `decisions/0009-handoff-key-extension-field` and reworded I4 in
  `manifesto` to allow extension fields an ADR names, after the
  handoff-and-continue-skills plan review found the key broke I4.
- Marked invariants I1 and I3 in `manifesto` enforced, naming the tests
  that pin them: the plugin's hook tests and the briefing word budget.
- Marked invariant I4 in `manifesto` enforced by tests/test_okf_fields.py.
- Removed `decision_status` and `decided_on` from
  `decisions/0001-standalone-cli-installs-its-plugin`, which no ADR allows
  (I4) and appended a Correction with the Consequences it lacked, after the
  first audit of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0002-briefing-and-rules-injected-by-the-cli`, which no ADR allows
  (I4) and appended a Correction with the Consequences it lacked, after the
  first audit of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0003-claude-code-plugin-first-depends-on-okf`, which no ADR
  allows (I4) and appended a Correction with the Consequences it lacked, after
  the first audit of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0004-sessionstart-is-the-only-hook`, which no ADR allows (I4) and
  appended a Correction with the Consequences it lacked, after the first audit
  of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0005-audits-report-only`, which no ADR allows (I4) and appended a
  Correction with the Consequences it lacked, after the first audit of this
  bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0006-staleness-from-okf-fields`, which no ADR allows (I4) and
  appended a Correction with the Consequences it lacked, after the first audit
  of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0007-skills-are-made-with-skill-creator`, which no ADR allows
  (I4), after the first audit of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0008-handoffs-are-okf-concepts`, which no ADR allows (I4) and
  appended a Correction with the Consequences it lacked, after the first audit
  of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0009-handoff-key-extension-field`, which no ADR allows (I4),
  after the first audit of this bundle.
- Added the architecture section with `architecture/overview`: the CLI
  modules, the plugin and the action, with a diagram whose Depicts section
  names I1 to I4. Linked it from the root index.
- Added `decisions/0010-the-ci-audit-runs-hermes-agent-against-any-openai-compatible-provider` with `kmctl new decision`.
- Wrote `decisions/0010-the-ci-audit-runs-hermes-agent-against-any-openai-compatible-provider`:
  the CI audit moves from Claude Code to Hermes Agent with kmctl's read-only
  plugin, so it takes any OpenAI-compatible provider.
- Appended a Correction to `decisions/0005-audits-report-only`: its last
  Consequence named the Claude Code runner, which ADR 0010 replaces.
- Updated `architecture/overview` for the Hermes audit: the diagram, the
  action's text and Depicts now show hermes, `action/hermes/kmctl-read/` and
  the shipped audit workflow.
- Added `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code` with `kmctl new decision`.
- Wrote `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code`:
  `kmctl init` now writes four knowledge rules to `.claude/rules/`, a kmctl
  block into `CLAUDE.md` and `AGENTS.md`, and a first decision.
- Appended a Correction to `decisions/0002-briefing-and-rules-injected-by-the-cli`:
  ADR 0011 reverses its rejected native rule files for Claude Code only.
- Updated `manifesto`: the CLI's bookkeeping now includes seeding the
  knowledge rules, a `CLAUDE.md` block and a first decision (ADR 0011).
- Updated `architecture/overview` for ADR 0011: the diagram and the CLI table
  show init writing `.claude/rules/` from `repo_rules/`, the agent-file block,
  and the first decision through `concepts.py`; Depicts names `repo_rules/`.
- Appended a Correction to `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code`:
  beside an `AGENTS.md`, init writes a `CLAUDE.md` holding only `@AGENTS.md`,
  and it leaves a dangling or outside-the-repository `CLAUDE.md` or
  `AGENTS.md` symlink alone with a warning.
- Updated `architecture/overview`: the CLI table shows `kmctl new` writing
  `stale_after` from `--stale-after` and `sources` from `--source`, each source
  found through `okf.py` the way `review_due.py` finds it.
- Corrected `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code`: the kmctl block now has four duties, adding `--source` and `--stale-after`.

## 2026-10-16

- Added `decisions/0012-releases-come-from-ci` with `kmctl new decision`.
- Corrected `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code`: init replaces the four knowledge rules when they differ, and `kmctl update` is an alias of init.
- Updated `architecture/overview`: `kmctl init` replaces the four knowledge rules when they differ, and `kmctl update` is its alias.
