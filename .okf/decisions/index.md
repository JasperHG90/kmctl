# Decisions

- [ADR 0001](0001-standalone-cli-installs-its-plugin.md): kmctl is a
  standalone Typer CLI that installs its own plugin, with thin skills.
- [ADR 0002](0002-briefing-and-rules-injected-by-the-cli.md): The CLI serves
  one briefing with state, routing and rules; the hook injects it.
- [ADR 0003](0003-claude-code-plugin-first-depends-on-okf.md): The Claude Code
  plugin comes first and depends on okf@scaccogatto.
- [ADR 0004](0004-sessionstart-is-the-only-hook.md): SessionStart is the only
  hook.
- [ADR 0005](0005-audits-report-only.md): Audits report only; CI runs free
  checks on every PR and an opt-in LLM audit.
- [ADR 0006](0006-staleness-from-okf-fields.md): Staleness comes from OKF's
  own fields; a covers field is out of scope.
