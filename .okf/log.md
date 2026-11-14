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
- Added `decisions/0025-the-starter-template-lives-in-kmctl-and-shares-its-release-tags` with `kmctl new decision`.
- Added `decisions/0026-the-kmctl-on-path-runs-the-release-a-project-s-lock-pins` with `kmctl new decision`.
- Added `decisions/0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step` with `kmctl new decision`.
- Added `summary`, the bundle's first page (ADR 0027), and updated `manifesto` (I4 names `checked`; the sections and Parts name the summary), `architecture/overview` (`summary.py`, `kmctl summary ack`) and `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code` (a correction: the block starts at the summary and holds six duties).
- Rewrote `summary` in its new sections (The project, How it works, What it has settled, Where it stands), distilling the bundle rather than listing the decisions; corrected `decisions/0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step` (a correction naming the sections and why) and updated `decisions/index` and `index` to match.
- Added `decisions/0028-two-hooks-the-session-briefing-and-the-summary-nudge` with `kmctl new decision`.
- Superseded `decisions/0004-sessionstart-is-the-only-hook` with `decisions/0028-two-hooks-the-session-briefing-and-the-summary-nudge`.
- Updated `manifesto` (I1 names both hooks, SessionStart and PostToolUse, and that neither blocks; the package ships the nudge hook), `architecture/overview` (`kmctl summary nudge`, the PostToolUse hook and its edge to `summary.py`) and `summary` (two hooks; the nudge keeps the summary in step) for ADR 0028.
- Corrected `decisions/0028-two-hooks-the-session-briefing-and-the-summary-nudge` (Antigravity's PostToolUse nudge and OpenCode's execute.after nudge, and the caveat that agy documents PostToolUse as expecting `{}`), and updated `manifesto` (I1 and Parts name the nudge in all three harnesses), `architecture/overview` (the two new nudge edges, the Antigravity hooks file, the OpenCode plugin) and `summary` (an after-tool hook, not only PostToolUse).

## 2026-10-19

- Corrected `decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script` (the release workflows run without the uv cache).
- Corrected `decisions/0014-apm-is-the-only-install-route` (the package layout and its sub-packages, what the wheel carries, `kmctl plugin status` folded into `kmctl doctor`, which tests cover the install), `decisions/0012-releases-come-from-ci` (its 2026-10-16 correction: `release.py set` writes four apm.yml files and moves copier.yml's `kmctl_ref` default), `decisions/0001-standalone-cli-installs-its-plugin` (its 2026-10-16 correction: the wheel carries the skills, agents and rules) and `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code` (its 2026-10-16 correction: the rules moved to `apm/claude/.apm/instructions/`), and updated `architecture/overview` (`action/agent.py` is an audit agent of its own, every module that reads front matter through `okf.py`, and `release.py`'s four apm.yml writes), from the audit rerun after fix-audit-drift.
- Added `decisions/0029-the-session-briefing-is-kmctl-s-only-hook-again` with `kmctl new decision`.
- Superseded `decisions/0028-two-hooks-the-session-briefing-and-the-summary-nudge` with `decisions/0029-the-session-briefing-is-kmctl-s-only-hook-again`.
- Added `decisions/0030-projects-commit-what-apm-deploys` with `kmctl new decision`.
- Added `decisions/0031-a-decision-record-may-be-draft-until-it-is-accepted` with `kmctl new decision`.
- Corrected `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code` (init writes the first decision only when `.okf/decisions/` holds no record, not when no record has its title, issue #26) and updated `decisions/index` to match.
- Corrected `decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code` (the kmctl block names the rules folder of each installed harness, the briefing names none, and the package's rules name each other by name, not by a `.claude/` path) and `decisions/0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest` (the Antigravity rule copies no longer open with a generated-file comment), from consumer-surfaces.
- Added `decisions/0032-kmctl-review-due-decides-by-commit-order` with `kmctl new decision`.
- Corrected `decisions/0006-staleness-from-okf-fields` and `decisions/0023-kmctl-verify-records-a-person-s-check`: `kmctl review due` decides by commit order and lists `edited after verification` (ADR 0032).
- Corrected `decisions/0014-apm-is-the-only-install-route` and
  `decisions/0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest`
  (okf's MCP server is `bundle` now, so `apm audit --ci` passes
  `config-consistency`, and `kmctl plugin patch` no longer removes a
  server), renamed the server in
  `decisions/0019-kmctl-plugin-remove-uninstalls-the-package-and-reinstalls-the-harnesses-kept`
  and `architecture/overview`, and gave
  `decisions/0018-kmctl-runs-okf-s-stop-check-for-antigravity` a consequence:
  `apm audit --ci` reports `.agents/hooks.json` as drift, and a frozen
  install on a clean checkout is the drift check (issue #28).
- Corrected `decisions/0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step`: `kmctl check` warns on an id in `checked.against` that is not a concept in the bundle, and `kmctl summary ack` leaves out deleted concepts (issue #34).
- Added `decisions/0033-kmctl-check-fails-on-a-missing-link-target-inside-the-bundle` with `kmctl new decision`.
- Corrected `decisions/0026-the-kmctl-on-path-runs-the-release-a-project-s-lock-pins`: a handed-off `kmctl --version` names the pin, and `KMCTL_PINNED=1` keeps the bare line (issue #37).
- Added `decisions/0034-kmctl-mv-renames-a-concept-and-rewrites-the-links-to-it` with `kmctl new decision`.
- Wrote `decisions/0034-kmctl-mv-renames-a-concept-and-rewrites-the-links-to-it` and updated `architecture/overview` (`mv.py`, `kmctl mv`) for it (issue #36); `summary` still holds (kmctl summary ack).

## 2026-10-20

- Added `decisions/0035-kmctl-s-repository-answers-and-triages-with-hermes` with `kmctl new decision`.
- Wrote `decisions/0035-kmctl-s-repository-answers-and-triages-with-hermes` and added the Hermes workflows to `architecture/overview`.

## 2026-11-05

- Added `prototypes/audit-agent` with `kmctl new prototype`.
- Measured claim extraction in `prototypes/audit-agent`: a gold set, three prompt variants and their scores.
- Reran v0 and v1 in `prototypes/audit-agent` with the prompt-hashed cache; recorded the run-to-run spread.
- Recorded the 2026-11-07/08 optimisation round in `prototypes/audit-agent`: Clef checkability, confirmations, second opinions, 120 random labelled claims, and what was tried and dropped.
- Moved the audit-agent label files and scoring scripts into `prototypes/audit-agent` (`labels/`, `scripts/`), and listed partly claims whose code changed under "Look at first".
- Traced purpose claims first in `prototypes/audit-agent` and refreshed its stale labels.
- Added a switch in `prototypes/audit-agent` that reports text a later correction replaces as a warning.

## 2026-11-08

- Added `prototypes/audit-cli`: the audit agent's steps up to claims as a Typer CLI with an audit.toml and a per-project SQLite database.
- Cut `prototypes/audit-cli` down to `audit claims extract|diff PATH` (a bundle or one concept file), with a progress bar and structlog JSON logs per project.
- Dropped the third (Flash) run from `prototypes/audit-cli`'s defaults, and made `audit init` write a generic OpenAI-compatible setup with no model.
- Gave `prototypes/audit-cli`'s extractor a reason per verdict and examples with near misses per kind, stored the reasons, and scored five prompt variants on the gold set (`scripts/gold_compare.py`): the old prompt still has the best recall.
- Moved `prototypes/audit-cli`'s schema changes to Alembic revisions, added `audit claims list`, made config errors name the setting, and switched its own runs to DeepSeek.
- Added a corrections pass to `prototypes/audit-cli` (links each correction to the sentences and claims it overturns), reduced telemetry to an on/off switch over LangSmith's own variables, and scored the prompts on DeepSeek: the CLI's prompt reached 99.3 recall merged.
- Made `prototypes/audit-cli` count an answer that leaves a sentence without a verdict as failed, not as a section with no claims: 20 of 260 saved gold answers were empty, which explains the low single-run recall.
- Piloted settling `prototypes/audit-cli` claims without a model (`scripts/settle_claims.py`): 8 of 187 settled, all correct; every anchor located for 125 of 135.
- Piloted turning `prototypes/audit-cli` claims into checks a model writes once and runs free after (`src/audit_cli/checks/`, `scripts/compile_checks.py`): 19 claims, about 23k tokens in per claim, 10 of 16 checks good.
- Measured each cost idea for `prototypes/audit-cli` (`scripts/pilots/`): one model call per shared file costs 2.5k tokens a claim against 23k for the agent, caught real drift in decision 0017, and a decision model's "enough information" answer predicts which claims it can check.
- 2026-11-10: `prototypes/audit-cli`: both check prompts guard JMESPath functions against a missing key; Jev now called at api.typesafe.ai/v1/systemone and its dedup and router pilots measured ("enough" sorts as well as Clef's, 4x faster).
- 2026-11-10: `prototypes/audit-cli`: decision-model questions before extraction and routing scored against the gold sentences (questions.py): Clef's "when = current" and "could the files confirm it" drop 23% of sentences for 3% of checkable claims; restates and stakes sort nothing; routing labels too thin to settle.
- 2026-11-10: `prototypes/audit-cli`: funnel.py counts how far steps 4 to 7 get on all 187 claims; 52 still need the searching agent.
- 2026-11-10: `prototypes/audit-cli`: a code step (ast-grep) added to the checks and both prompts; 38 of 44 grep steps search code, but the model run stopped at the 500k cap after 10 of 30 claims.
- 2026-11-10: `prototypes/audit-cli`: code step measured on the 30 claims: same 17 hold, fewer fail, grep over code 38 to 16 steps; cap raised to 1.1M tokens by the user.
- 2026-11-10: `prototypes/audit-cli`: code step is presence-only after review (Go out, shell and Ruby variables literal); dossier.py gives lines to the 52 agent claims, and the grouped one call settles about 19 of them at 5.4k tokens a claim.
- 2026-11-10: `prototypes/audit-cli`: agent with dossier lines and no trimming finished 7 of 7 left-over claims (9.1k uncached tokens a claim, 75-79% cached) where the old agent finished 0 of 4 in 80k; writer counts cached tokens and makes its last submit call when tokens run out; cap at 1.34M of 1.35M.
- 2026-11-10: `prototypes/audit-cli`: writer's last call fires on the last call's size plus growth, after review; traced rebuild of the agent run made strict.
- 2026-11-10: `prototypes/audit-cli`: agent code tools (CodeSearch, Outline) and hints measured on 15 claims: hardly used, no effect; the last call now reads a Submit among other calls and retries; the two-call writer settles 36 of 52 at 5.2k tokens a claim, and its fix call can bend drift into a pass.
- 2026-11-10: `prototypes/audit-cli`: two-call writer rerun with the no-bending rule: 35 of 52 hold at 5.5k tokens a claim; on the drift claim it now gives a proxy with its doubt instead of a plain pass.
- 2026-11-10: `prototypes/audit-cli`: decision models after the check: Jev ranks the 3 drift checks among 69 failures at 1, 2 and 8 (AUC 0.98); judging claims from their lines, Jev gets prose 8 of 9, point 26 of 30, structural 12 of 15; absence over unseen files is the gap.
- 2026-11-10: `prototypes/audit-cli`: `audit checks` diff/write/run/triage built into the CLI (migration 0004, change detection by claim text and file hashes, traced, passes measured), three review rounds; on kmctl 183 claims: 5.0k tokens a claim to write, rerun reuses 136 of 144 checks in 0.6 s, Jev ranks the known drift in its top four.
- 2026-11-10: `prototypes/audit-cli`: strategies from Koenigstein's *AI Agents* recorded: 14 the checks stage already follows, 10 it could add, mutation-testing checks first.
- 2026-11-10: `prototypes/audit-cli`: checks commands take any folder of the repository (claims, not a bundle, are what they work on); `audit checks list` added.
- 2026-11-10: `prototypes/audit-cli`: LangSmith's EU endpoint, agent id and environment in the folder's git-ignored .env, so audit run from here traces without a wrapper.
- 2026-11-10: `prototypes/audit-cli`: checks run takes every claim to a verdict; mutation and link trust scores; per-question decision settings; background runs with status, stop and a one-run lock; three review rounds.
- 2026-11-10: `prototypes/audit-cli`: weak checks resolved by a rewrite kept only when it notices more and stays on the claim, else accepted automatically until the code changes; `checks accept`, `write --claim`, the unsure level, and mutation version 3; two review rounds.
- 2026-11-10: `prototypes/audit-cli`: checks run builds a fresh model client for strengthening, since a client reused from the write stage crashed on its closed event loop.
- 2026-11-10: `prototypes/audit-cli`: the extractor and the checks writer read a list sent as JSON text with a stray closing bracket, and sentence labels sent as numbers; both seen from DeepSeek on decision 0020 (`scripts/probe/stringed_lists.py` reads them from LangSmith).
- 2026-11-10: `prototypes/audit-cli`: an extractor answer that does not read as a whole keeps each sentence verdict that does and asks again for the rest, so one wrong field (a kind given as a quantifier, on decision 0005) costs a sentence its second ask, not the section.
- 2026-11-10: `prototypes/audit-cli`: an extraction waits for its slot before its graph starts and holds it through the re-ask, so LangSmith shows at most concurrency.max_model_calls graph runs going, not one per section.
- 2026-11-10: `prototypes/audit-cli`: checks run runs write, triage and strengthen in one event loop, since langchain_openai shares one connection pool between all its clients; a fresh client alone did not stop "Event loop is closed".
- 2026-11-10: `prototypes/audit-cli`: Claude Opus as the checker on 60 claims: 5.1k tokens a claim; right where it differed from the pipeline on 9 of 28 (2 false failures, 2 missed drifts, 4 reasons it settled); 3 drifts among 32 unchecked claims.
- 2026-11-10: `prototypes/audit-cli`: Claude Haiku as the checker on the same 60 claims: 5.4k tokens a claim, agrees with Opus on 46; stricter on two-file claims, shallower on the rest, and accepts docs as proof of outside tools.

## 2026-11-11

- Added `decisions/0036-claims-are-extracted-by-the-agent-through-kmctl-audit-claims` with `kmctl new decision`.
- Documented the `kmctl audit` group and its claims verbs and store (agent-audit-claims): wrote `decisions/0036-claims-are-extracted-by-the-agent-through-kmctl-audit-claims`, and updated `manifesto` (Parts) and `architecture/overview` (the CLI table, the claims flow, Depicts).
- Updated `summary` (Where it stands) for the claims verbs, and dropped its line that no prototypes are recorded, which no longer held.
- Added `decisions/0037-the-claims-and-checks-agents-get-a-plain-shell-and-i2-narrows` with `kmctl new decision`.
- Added the extract-claims skill and the kmctl-claims-extractor agent (agent-audit-claims-skill): wrote `decisions/0037-the-claims-and-checks-agents-get-a-plain-shell-and-i2-narrows`; narrowed I2 to the read-only auditor and the CI audit and added a Value for the claims and checks agents in `manifesto`, which also names the skill and agent in Parts; `architecture/overview` gains them in its diagram, a bullet and Depicts, with the I2 entry reworded to match.
- Updated `summary` (Where it stands) for the narrowed I2 and the claims subagent.
- Added `decisions/0038-checks-are-step-data-that-kmctl-reruns-and-only-checks-that-notice-a-change-are-stored` with `kmctl new decision`.
- Documented `kmctl audit checks` (agent-audit-checks): wrote `decisions/0038-checks-are-step-data-that-kmctl-reruns-and-only-checks-that-notice-a-change-are-stored`; `manifesto` (Parts) and `architecture/overview` (the CLI table, the claims flow, the diagram node, Depicts) name the checks verbs, the weak bar and the `kmctl[audit]` extra. Also amended `decisions/0036-claims-are-extracted-by-the-agent-through-kmctl-audit-claims` (earlier sections are in a section's key) and the `manifesto` Value (Claude Code's shell limit is unconfirmed), both new in this change.
- Updated `summary` (Where it stands) for the checks verbs.
- Added the write-checks skill and the kmctl-check-writer agent (agent-audit-checks-skill): `manifesto` (Parts) and `architecture/overview` (diagram, bullet, Depicts) name them.
- Amended `decisions/0038-checks-are-step-data-that-kmctl-reruns-and-only-checks-that-notice-a-change-are-stored` (new in this change) after review: markdown is never read, help steps never run uv run on the project, drift needs steps that ran, pruning waits for extraction.
- Added `decisions/0039-kmctl-audit-judge-asks-an-optional-decision-model-off-by-default` with `kmctl new decision`.
- Documented `kmctl audit judge` (agent-audit-decide): wrote `decisions/0039-kmctl-audit-judge-asks-an-optional-decision-model-off-by-default`; `manifesto` (Parts) and `architecture/overview` (the CLI table, the claims flow, Depicts) name it, its per-user settings and the extra.
- Updated `summary` (Where it stands) for `kmctl audit judge`.
- Drew `kmctl audit judge`, its decision endpoint and optional LangSmith in `architecture/overview` after review.
- Corrected I2 in `manifesto`: the step that runs the audit agent holds no GitHub token, the publish step does. Found by a `kmctl audit checks` run on the bundle.
- Corrected `decisions/0037-the-claims-and-checks-agents-get-a-plain-shell-and-i2-narrows` (new in this change) the same way: only the publish step holds a GitHub token.
- Appended a 2026-11-11 correction, from the first `kmctl audit checks` run over the bundle, to `decisions/0001-standalone-cli-installs-its-plugin`, `decisions/0009-handoff-key-extension-field`, `decisions/0012-releases-come-from-ci`, `decisions/0014-apm-is-the-only-install-route`, `decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script`, `decisions/0018-kmctl-runs-okf-s-stop-check-for-antigravity`, `decisions/0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest`, `decisions/0022-docs-pages-carry-optional-okf-front-matter-and-generated-folder-indexes`, `decisions/0034-kmctl-mv-renames-a-concept-and-rewrites-the-links-to-it`.
- Added `decisions/0040-the-audit-pipeline-holds-its-agents-by-a-hook-and-keeps-answers-through-rewording` with `kmctl new decision`.
- Fixed the audit pipeline's design after its first full run (ADR 0040): wrote `decisions/0040-the-audit-pipeline-holds-its-agents-by-a-hook-and-keeps-answers-through-rewording` and `architecture/audit-pipeline` (the pipeline as a diagram, with the run's numbers and open limits); appended 2026-11-11 corrections to `decisions/0036-claims-are-extracted-by-the-agent-through-kmctl-audit-claims`, `decisions/0037-the-claims-and-checks-agents-get-a-plain-shell-and-i2-narrows` and `decisions/0038-checks-are-step-data-that-kmctl-reruns-and-only-checks-that-notice-a-change-are-stored`; updated the `manifesto` Value for the guard hook and `architecture/overview` (link, Depicts).
- Updated `summary` (Where it stands) to link `architecture/audit-pipeline`.
- Updated `decisions/0040-the-audit-pipeline-holds-its-agents-by-a-hook-and-keeps-answers-through-rewording` (new in this change): a correction section now sees the corrections after it, after four drifts came from 2026-10-17 corrections that later ones overturn. Narrowed the `manifesto`'s out-of-scope hooks line to kmctl's own hooks, which an extractor had read as "kmctl ships no other hook".
- Added `prototypes/audit-ui`: a starter page and its export script for browsing `kmctl audit` results, from the sketch in `mock.excalidraw.png`.
- Updated `decisions/0040-the-audit-pipeline-holds-its-agents-by-a-hook-and-keeps-answers-through-rewording` (new in this change): `kmctl audit checks todo` cuts a long sentence, usually a table, to the lines its claim is about.
- Second `kmctl audit checks` pass over the bundle: corrected `decisions/0015-antigravity-gets-skills-and-rules-from-apm-and-a-kmctl-plugin-folder` (OpenCode agents), and extended the 2026-11-11 corrections in `decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script` (action inputs), `decisions/0018-kmctl-runs-okf-s-stop-check-for-antigravity` (OpenCode files) and `decisions/0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest` (repository URL); dropped `scaffold.py` from the modules `architecture/overview` says read front matter through `okf.py`.
- After review: added `src/kmctl/claims/check_verbs.py` to the sources of `decisions/0040-the-audit-pipeline-holds-its-agents-by-a-hook-and-keeps-answers-through-rewording`; `prototypes/audit-ui` now marks sentences with only subjective or external claims as not checkable, keeps sections in document order, and gives top-level concepts their own header.
- Redesigned the page of `prototypes/audit-ui` for reading: underline marks per coverage kind, a per-sentence strip, numbered claims linked across the three tags, search, state chips and keyboard moves.
- `prototypes/audit-ui` now shows one card per claim holding its check and its confidence, so what belongs together sits together.
- `prototypes/audit-ui` explains a check's confidence in a sentence, names exact and indirect checks, and groups the missed edits by file.
- Added `prototypes/mixed-claims`: counted the reasons that sit on a claim joining a fact to an opinion (1 of 384), to decide whether a split rule for the extractor is worth a ticket. It is not.

## 2026-11-12

- Added `decisions/0041-people-review-claims-and-checks-on-a-local-page-and-their-feedback-goes-back-to-the-agents` (draft): `kmctl audit ui` serves a local page for thumbs, notes, verdicts and second opinions, and open feedback goes back to the agents with the next `todo`; listed it in `decisions/index`.
- Updated `manifesto`, `architecture/audit-pipeline` and `architecture/overview` for `kmctl audit ui` and the `feedback` table (verb, modules, flow step 7), and `summary` for the review page.
- Updated `prototypes/audit-ui`: the page moved into the package as `kmctl audit ui`.
- Corrected `architecture/audit-pipeline`'s open issues: dropped the uncounted claim that writers gave reasons when short on context, and said what the 4 false drifts do and do not show.
- Added `decisions/0042-code-coverage-counts-the-lines-a-check-matched` (draft): steps record the lines they matched, and `kmctl audit coverage` and the page's code view count a line as covered when a check matched it; listed it in `decisions/index`.
- Updated `manifesto`, `architecture/audit-pipeline` (flow step 8, the coverage verb and module) and `architecture/overview` for `kmctl audit coverage` and the code view.
- Fixed three drifts the audit found: `architecture/overview` now says `scripts/release.py set` copies the version from `apm/apm.yml` into the other apm.yml files, and `architecture/audit-pipeline` says claims todo also hands out sections a person sent back, and that only grep, code, definition and import steps record matched lines.
- Added `prototypes/token-costs`: measured what kmctl's audit agents cost from 141 real runs (extraction $0.0068 per section, check writing $0.0081 per claim on Haiku 5.5) and the per-session context the briefing and knowledge rules add.
- Fixed three more drifts in `architecture/overview`'s table of what each verb writes: the checks verbs also write `.kmctl/.gitignore` when missing, `kmctl audit coverage` creates an empty store when there is none, and `kmctl audit ui` refreshes the sections and claims tables on each page load.
- Fixed a drift in `architecture/overview`: `kmctl audit checks run` also reruns a check whose last run was skipped, and every check with `--all`.
- Fixed two drifts in `architecture/overview` (in commit a29ddf1e, which left out this line): `kmctl audit ui` also writes the `cache` table and deletes a removed section's claims, extractions and verdicts, and `kinds.py` names each kind's fields itself, with `tests/test_schema.py` checking they are allowed.
- Added `prototypes/link-question`: rewording the decision model's link question so finding the exact text or value a claim describes counts as testing it moved 679 checks' median score from 0.70 to 0.76, wording checks from 0.75 to 0.84.
