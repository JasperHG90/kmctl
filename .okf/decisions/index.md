# Decisions

- [ADR 0001](0001-standalone-cli-installs-its-plugin.md): kmctl is a
  standalone Typer CLI that installs its own plugin, with thin skills.
  (amended: APM installs the package and kmctl plugin patch adds the rest,
  ADR 0021)
- [ADR 0002](0002-briefing-and-rules-injected-by-the-cli.md): The CLI serves
  one briefing with state, routing and rules; the hook injects it.
  (amended: the rules moved to .claude/rules/, ADR 0011)
- [ADR 0003](0003-claude-code-plugin-first-depends-on-okf.md): The Claude Code
  plugin comes first and depends on okf@scaccogatto. (superseded by ADR 0014)
- [ADR 0004](0004-sessionstart-is-the-only-hook.md): SessionStart is the only
  hook. (superseded by ADR 0028)
- [ADR 0005](0005-audits-report-only.md): Audits report only; CI runs free
  checks on every PR and an opt-in LLM audit.
- [ADR 0006](0006-staleness-from-okf-fields.md): Staleness comes from OKF's
  own fields; a covers field is out of scope.
- [ADR 0007](0007-skills-are-made-with-skill-creator.md): Every skill is made
  with the skill-creator skill.
- [ADR 0008](0008-handoffs-are-okf-concepts.md): /handoff and /continue write
  and read handoff concepts in .okf/handoffs/.
- [ADR 0009](0009-handoff-key-extension-field.md): handoff_key is kmctl's
  one OKF extension field; I4 allows fields an ADR names.
- [ADR 0010](0010-the-ci-audit-runs-hermes-agent-against-any-openai-compatible-provider.md):
  The CI audit runs Hermes Agent with read-only kmctl tools against any
  OpenAI-compatible provider, replacing Claude Code. (superseded by ADR 0017)
- [ADR 0011: kmctl init writes knowledge rules and a CLAUDE.md block for Claude Code](0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code.md): kmctl init writes four knowledge rules to .claude/rules/, a kmctl block into CLAUDE.md and AGENTS.md, and a first decision; the briefing stays the cross-harness path. (amended: APM installs the rules since ADR 0014, and the block holds six duties and starts at summary.md, and init links a page it adds to a kept index, ADR 0027)
- [ADR 0012: Releases come from CI](0012-releases-come-from-ci.md): A hand-run release workflow opens a version pull request and a tag workflow publishes the GitHub Release; the plugin manifest is the one version source, with no PyPI and no hatch-vcs. (amended: apm/apm.yml is the one version source)
- [ADR 0013: kmctl installs through APM too](0013-kmctl-installs-through-apm-too.md): APM installs kmctl's skills, agent and hook from the apm subfolder package as a second route beside kmctl plugin install; the CLI is still installed with uv tool install. (superseded by ADR 0014)
- [ADR 0014: APM is the only install route](0014-apm-is-the-only-install-route.md): kmctl's skills, audit agent and knowledge rules ship only as the APM package in apm/, which kmctl plugin install --harness writes into apm.yml and installs with APM; kmctl writes the SessionStart hook and okf's MCP server itself. (amended by ADR 0020 and ADR 0021: APM installs the hooks and MCP server too, from the user's apm.yml entry, and kmctl plugin patch adds the rest)
- [ADR 0015: Antigravity gets skills and rules from APM and a kmctl plugin folder](0015-antigravity-gets-skills-and-rules-from-apm-and-a-kmctl-plugin-folder.md): kmctl plugin install --harness antigravity installs the skills and rules with APM and writes .agents/plugins/kmctl/ itself, holding the translated agents, the SessionStart hook and okf's MCP server. (amended by ADR 0020 and ADR 0021: apm install, then kmctl plugin patch for the agents)
- [ADR 0016: Antigravity rules come from the kmctl plugin folder](0016-antigravity-rules-come-from-the-kmctl-plugin-folder.md): kmctl writes its four knowledge rules for Antigravity into .agents/plugins/kmctl/rules/ in the form agy reads, and deletes the copies APM writes to .agents/rules/. (superseded by ADR 0020)
- [ADR 0017: The CI audit is a standalone PydanticAI agent script](0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md): action/agent.py, one PydanticAI script run with uv run, replaces the Hermes audit: it takes a task, a system prompt, any provider, context and skill folders, can run shell commands, and writes a typed report kept as an artifact.
- [ADR 0018: kmctl runs okf's Stop check for Antigravity](0018-kmctl-runs-okf-s-stop-check-for-antigravity.md): kmctl's plugin folder runs okf's Stop check from the repository root and in Antigravity's format, and takes APM's broken copy out of .agents/hooks.json.
- [ADR 0019: kmctl plugin remove uninstalls the package and reinstalls the harnesses kept](0019-kmctl-plugin-remove-uninstalls-the-package-and-reinstalls-the-harnesses-kept.md): kmctl plugin remove runs apm uninstall on kmctl's entry, removes the hook, MCP entry and plugin folder kmctl wrote, and installs the kept harnesses again at their ref. (superseded by ADR 0021)
- [ADR 0020: APM installs the hooks, MCP server and rules; kmctl patches the rest](0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest.md): kmctl's APM package ships its SessionStart hooks, okf's MCP server and per-harness rules in sub-packages; kmctl writes only what APM cannot install yet: Antigravity agents and the fix for okf's Antigravity Stop hook.
- [ADR 0021: APM installs kmctl's package; kmctl plugin patch adds the rest](0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest.md): kmctl plugin install, update and remove give way to apm install, apm uninstall and kmctl plugin patch, which writes only what APM cannot install yet.
- [ADR 0022: Docs pages carry optional OKF front matter and generated folder indexes](0022-docs-pages-carry-optional-okf-front-matter-and-generated-folder-indexes.md): docs/ pages may carry the OKF fields description, stale_after, verified and sources, and each Diataxis folder gets a README.md index that kmctl check --fix generates, without docs/ becoming an OKF bundle.
- [ADR 0023: kmctl verify records a person's check](0023-kmctl-verify-records-a-person-s-check.md): kmctl verify writes the verified entry a person's check earns, so a concept or docs page leaves kmctl review due; an agent runs it only on that person's confirmation, never on an audit verdict.
- [ADR 0024: OpenCode gets the package from APM and its agents, rules and briefing from kmctl plugin patch](0024-opencode-gets-the-package-from-apm-and-its-agents-rules-and-briefing-from-kmctl-plugin-patch.md): apm install --target opencode brings the skills and okf's MCP server; kmctl plugin patch rewrites the agents into OpenCode's format and writes the rules, their instructions entry and a briefing plugin.
- [ADR 0025: The starter template lives in kmctl and shares its release tags](0025-the-starter-template-lives-in-kmctl-and-shares-its-release-tags.md): copier.yml sits at kmctl's root with the template in starter/, so each kmctl release tag is a template release, and scripts/release.py set moves kmctl_ref's default to it.
- [ADR 0026: The kmctl on PATH runs the release a project's lock pins](0026-the-kmctl-on-path-runs-the-release-a-project-s-lock-pins.md): Before any command, kmctl reads apm.lock.yaml and, when it pins another release, runs that release through uvx at the lock's commit with KMCTL_PINNED=1; the copy on PATH adds the briefing's newer-release line.
- [ADR 0027: The bundle opens with a summary that kmctl keeps in step](0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md): kmctl init writes .okf/summary.md, a page of at most 500 words that the briefing points to first; kmctl review due lists it when a concept changed in a commit after it, and kmctl summary ack, which writes the checked extension field, clears that. (amended: the summary's sections are The project, How it works, What it has settled and Where it stands, and it distils the knowledge rather than listing the decisions)
- [ADR 0028: Two hooks: the session briefing and the summary nudge](0028-two-hooks-the-session-briefing-and-the-summary-nudge.md): kmctl ships a SessionStart hook that prints the briefing and a Claude Code PostToolUse hook that runs kmctl summary nudge after Write, Edit, MultiEdit and Bash calls; neither blocks. (superseded by ADR 0029)
- [ADR 0029: The session briefing is kmctl's only hook again](0029-the-session-briefing-is-kmctl-s-only-hook-again.md): kmctl drops the PostToolUse summary nudge for every harness; the briefing, the AGENTS.md duty and kmctl review due say when the summary is behind.
- [ADR 0030: Projects commit what APM deploys](0030-projects-commit-what-apm-deploys.md): A project commits the files apm install and kmctl plugin patch deploy for its harnesses and gitignores only apm_modules/, as APM's guide says.
- [ADR 0032: kmctl review due decides by commit order](0032-kmctl-review-due-decides-by-commit-order.md): kmctl review due finds the commit that holds a file's newest verified entry and compares sources and the file itself with HEAD from there, so a squash or rebase merge keeps a verification and an edit after it makes the file due.
