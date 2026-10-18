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
- Added `decisions/0013-kmctl-installs-through-apm-too` with `kmctl new decision`.
- Wrote `decisions/0013-kmctl-installs-through-apm-too`: APM is a second
  install route beside `kmctl plugin install`, through the `apm/apm.yml`
  package; it leaves out the CLI and skips ADR 0001's version check.
- Updated `manifesto` for ADR 0013: Parts says the plugin installs through
  `kmctl plugin install` or through APM.
- Updated `architecture/overview` for ADR 0013: the diagram, the plugin
  section and Depicts show `apm/apm.yml`, its `git: parent` dependency on
  `plugin/` and okf-skills, and `scripts/release.py set` writing its version.
- The briefing drops the knowledge rules `.claude/rules/` already carries and fits 500 tokens: `manifesto`, `decisions/0002-briefing-and-rules-injected-by-the-cli`, `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code`, `architecture/overview`.
- Corrected `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code`: init replaces the four knowledge rules when they differ, and `kmctl update` is an alias of init.
- Updated `architecture/overview`: `kmctl init` replaces the four knowledge rules when they differ, and `kmctl update` is its alias.
- Added `decisions/0014-apm-is-the-only-install-route` with `kmctl new decision`.
- Superseded `decisions/0013-kmctl-installs-through-apm-too` with `decisions/0014-apm-is-the-only-install-route`.
- Superseded `decisions/0003-claude-code-plugin-first-depends-on-okf` with `decisions/0014-apm-is-the-only-install-route`.
- Corrected `decisions/0001-standalone-cli-installs-its-plugin`, `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code` and `decisions/0012-releases-come-from-ci` for ADR 0014: the package in apm/ replaces the staged plugin, init stops writing the rules, and apm/apm.yml is the version source.
- Updated `manifesto` and `architecture/overview` for ADR 0014: the APM package in apm/ replaces the plugin, `kmctl plugin install --harness claude` installs it and writes the hook and okf's MCP server, and I1's test checks the hook kmctl writes.
- Added `decisions/0015-antigravity-gets-skills-and-rules-from-apm-and-a-kmctl-plugin-folder` with `kmctl new decision`.
- Updated `manifesto` and `architecture/overview`, and corrected `decisions/0003-claude-code-plugin-first-depends-on-okf`, for ADR 0015: Antigravity is a harness `kmctl plugin install` serves, through APM and the plugin folder `antigravity.py` writes.
- Updated `manifesto` and `architecture/overview`: `kmctl doctor` replaces `kmctl plugin status`, as ADR 0014's Consequences planned.

## 2026-10-17

- Added `decisions/0016-antigravity-rules-come-from-the-kmctl-plugin-folder` with `kmctl new decision`.
- Added `decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script` with `kmctl new decision`.
- Superseded `decisions/0010-the-ci-audit-runs-hermes-agent-against-any-openai-compatible-provider` with `decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script`.
- Corrected `decisions/0005-audits-report-only`: the audit mode now runs action/agent.py (ADR 0017), not Hermes.
- Updated `architecture/overview`: the audit mode runs action/agent.py, a standalone PydanticAI agent, instead of Hermes (ADR 0017).
- Corrected `decisions/0001-standalone-cli-installs-its-plugin` and `decisions/0015-antigravity-gets-skills-and-rules-from-apm-and-a-kmctl-plugin-folder`: `kmctl plugin status` became `kmctl doctor`. Found by the first live run of action/agent.py.
- Corrected `decisions/0002-briefing-and-rules-injected-by-the-cli`: `kmctl init` writes no rules since ADR 0014. Found by the same run.
- Added `decisions/0018-kmctl-runs-okf-s-stop-check-for-antigravity` with `kmctl new decision`.
- Corrected `decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script`: `action/agent.py publish` posts the report from its own job; updated `architecture/overview` to match.
- Corrected `decisions/0012-releases-come-from-ci`: six install lines, since the CI how-to's audit workflow has a publish job.
- Added `decisions/0019-kmctl-plugin-remove-uninstalls-the-package-and-reinstalls-the-harnesses-kept` with `kmctl new decision`.
- Added `decisions/0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest` with `kmctl new decision`.
- Superseded `decisions/0016-antigravity-rules-come-from-the-kmctl-plugin-folder` with `decisions/0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest`.
- Added `decisions/0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest` with `kmctl new decision`.
- Superseded `decisions/0019-kmctl-plugin-remove-uninstalls-the-package-and-reinstalls-the-harnesses-kept` with `decisions/0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest`.
- Corrected `decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script`: the report lists what was checked, findings are mismatches only, and the script sends back citations of lines the agent did not see; updated `architecture/overview` to match.
- Added `decisions/0022-docs-pages-carry-optional-okf-front-matter-and-generated-folder-indexes` with `kmctl new decision`.
- Corrected `decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script`: three shipped audits replace the audit skill as the default task; updated `architecture/overview` to show `action/prompts/`.
- Corrected `decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script`: optional OTLP traces to Langfuse or any OTLP backend; updated `architecture/overview` to show them.
- Updated `architecture/overview`: the briefing's setup line reads `kinds.ARCHITECTURE`.
- Corrected `decisions/0001-standalone-cli-installs-its-plugin`, `decisions/0002-briefing-and-rules-injected-by-the-cli`, `decisions/0015-antigravity-gets-skills-and-rules-from-apm-and-a-kmctl-plugin-folder`, `decisions/0018-kmctl-runs-okf-s-stop-check-for-antigravity` and `decisions/0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest`: `kmctl plugin install` is gone; APM installs the package and `kmctl plugin patch` adds the rest (ADR 0021). Found by the okf-vs-code audit.
- Corrected `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code`: init's current last line, and the kmctl block's five duties.
- Updated `decisions/index`: notes on the lines for ADRs 0001, 0002, 0011, 0012, 0014 and 0015 naming what amended them.
- Updated `manifesto`: APM installs kmctl's package and `kmctl plugin patch` adds the rest; the CLI no longer installs it.
- Updated `architecture/overview`: what `kmctl plugin patch` writes and runs, where the rules live, the audit's task and the four apm.yml files a release sets; updated `architecture/index` to match its description.
- Updated `index`: dropped the concept and record counts, which nothing keeps true.
- Added `decisions/0023-kmctl-verify-records-a-person-s-check` with `kmctl new decision`.
- Updated `manifesto` and `architecture/overview`: `kmctl verify` and `verify.py` record a person's check (ADR 0023).

## 2026-10-18

- Added `decisions/0024-opencode-gets-the-package-from-apm-and-its-agents-rules-and-briefing-from-kmctl-plugin-patch` with `kmctl new decision`.
