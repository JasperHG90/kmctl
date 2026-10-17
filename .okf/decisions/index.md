# Decisions

- [ADR 0001](0001-standalone-cli-installs-its-plugin.md): kmctl is a
  standalone Typer CLI that installs its own plugin, with thin skills.
- [ADR 0002](0002-briefing-and-rules-injected-by-the-cli.md): The CLI serves
  one briefing with state, routing and rules; the hook injects it.
- [ADR 0003](0003-claude-code-plugin-first-depends-on-okf.md): The Claude Code
  plugin comes first and depends on okf@scaccogatto. (superseded by ADR 0014)
- [ADR 0004](0004-sessionstart-is-the-only-hook.md): SessionStart is the only
  hook.
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
  OpenAI-compatible provider, replacing Claude Code.
- [ADR 0011: kmctl init writes knowledge rules and a CLAUDE.md block for Claude Code](0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code.md): kmctl init writes four knowledge rules to .claude/rules/, a kmctl block into CLAUDE.md and AGENTS.md, and a first decision; the briefing stays the cross-harness path.
- [ADR 0012: Releases come from CI](0012-releases-come-from-ci.md): A hand-run release workflow opens a version pull request and a tag workflow publishes the GitHub Release; the plugin manifest is the one version source, with no PyPI and no hatch-vcs.
- [ADR 0013: kmctl installs through APM too](0013-kmctl-installs-through-apm-too.md): APM installs kmctl's skills, agent and hook from the apm subfolder package as a second route beside kmctl plugin install; the CLI is still installed with uv tool install. (superseded by ADR 0014)
- [ADR 0014: APM is the only install route](0014-apm-is-the-only-install-route.md): kmctl's skills, audit agent and knowledge rules ship only as the APM package in apm/, which kmctl plugin install --harness writes into apm.yml and installs with APM; kmctl writes the SessionStart hook and okf's MCP server itself.
- [ADR 0015: Antigravity gets skills and rules from APM and a kmctl plugin folder](0015-antigravity-gets-skills-and-rules-from-apm-and-a-kmctl-plugin-folder.md): kmctl plugin install --harness antigravity installs the skills and rules with APM and writes .agents/plugins/kmctl/ itself, holding the translated agents, the SessionStart hook and okf's MCP server.
- [ADR 0016: Antigravity rules come from the kmctl plugin folder](0016-antigravity-rules-come-from-the-kmctl-plugin-folder.md): kmctl writes its four knowledge rules for Antigravity into .agents/plugins/kmctl/rules/ in the form agy reads, and deletes the copies APM writes to .agents/rules/.
- [ADR 0017: kmctl runs okf's Stop check for Antigravity](0017-kmctl-runs-okf-s-stop-check-for-antigravity.md): kmctl's plugin folder runs okf's Stop check from the repository root and in Antigravity's format, and takes APM's broken copy out of .agents/hooks.json.
