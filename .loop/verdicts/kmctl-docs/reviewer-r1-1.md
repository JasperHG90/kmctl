---
type: verdict
title: 'Verdict: kmctl-docs reviewer round 1'
description: 'reviewer verdict for round 1 of kmctl-docs: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T13:39:34+00:00'
slug: kmctl-docs
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The pages are accurate and well built: every command and output I re-ran matched the page exactly, the reference matches `--help` apart from one field list, and the how-to's workflows match action.yml and the shipped workflows. One blocking problem: the change marks invariant I2 enforced, which the plan did not ask for and the manifesto-invariants rule does not allow as done (f2). Two docs fixes do not block: the pages never say the repository is private (f1), and the briefing's skills are left off the pages (f3).

## Checked

- Gates: `loopctl gate stamp` from the worktree printed `pass` for lint, format, tests and eval rows r1 to r5, then `stamp green: ba854778f9ada0614cc2f35e8629f3428ed4ce7d698bf26ea672b4dc4368dea3`.
- Rows r1 to r5: read tests/test_docs.py. Each assertion matches its row's fails_when: install string and plugin step present and every docs/*.md linked (r1); one non-index page per Diataxis folder plus `kmctl check` exit 0 on the root (r2); every Typer command path as `kmctl ...` and every `--option` in backticks (r3); the Depicts I-ids equal the manifesto's set exactly (r4); okf_validate return code and the root index link (r5). None of them is skipped or mocked.
- r6 (judgment): built a wheel from the worktree into a scratch venv and ran the tutorial step by step in a fresh git repo. `--version`, `init`, `check`, `new decision`, the skeleton, the failing check (`error  index  docs/how-to/deploy.md  not listed in docs/README.md` / `1 failed`, exit 1) and the recovery all matched byte for byte. The index, log and decisions/index changes the tutorial describes are real. Ran action/knowledge-ci.sh on that repo after one commit and got the summary the how-to shows, exit 0. Ran knowledge-audit.sh with GITHUB_EVENT_NAME=pull_request and got the quoted refusal, exit 1. Ran `kmctl plugin status`, `plugin install`, `plugin status` with HOME, CLAUDE_CONFIG_DIR and XDG_DATA_HOME pointed at scratch folders; the output matched the how-to and .claude/settings.json got both plugins. Pages follow the `kmctl new doc` skeleton headings for each type (checked by generating all four), and the docs/README.md entries have its format. The how-to says which steps come from action.yml and the workflows.
- Reference against `uv run kmctl <cmd> --help` for all 19 commands: options, defaults, exit codes and examples agree, except the briefing JSON field list (f3).
- How-to audit section against action.yml, .github/workflows/knowledge-audit.yml, knowledge-audit.sh and knowledge-audit-issue.sh: the workflow YAML is the shipped file with only `uses:` changed. The event gate, token refusals (GH_TOKEN/GITHUB_TOKEN, extraheader), the separate issue step with GH_TOKEN, and `--tools Read,Grep,Glob,Agent` are all as described.
- Architecture: checked each module edge against the imports in src/kmctl and each skill edge against plugin/skills/*/SKILL.md. All correct except the briefing -> plugin edge (f3). Mermaid read by hand: quoted labels, `&` fan-out, `-. "..." .->` and `-- "..." -->` forms are valid flowchart syntax, and no node id is a reserved word. I could not render it because there is no network for mermaid-cli.
- Repo privacy: `gh repo view` reports `isPrivate: true`; an anonymous `git ls-remote` prints "Repository not found".

## Findings

- f1: README.md, the tutorial and the how-to give `uv tool install git+https://github.com/JasperHG90/Knowledge-management` with no note that it needs read access. The how-to's `uses: JasperHG90/Knowledge-management@main` only works for repositories the owner allows under the private repo's Actions access setting. Add one sentence to the README and how-to (access needed while the repository is private; the action works only from repositories that setting allows), or drop it when the repository goes public. `@main` with no tag is fine for now, since no tag exists.
- f2: .okf/manifesto.md I2 now says enforced. Per .claude/rules/manifesto-invariants.md that move belongs in the change that adds the test, and the test must drive kmctl or the plugin from outside. test_claude_runs_read_only does drive the action's script from outside. test_auditor_tools_are_read_only only parses front matter. Neither pins "its skills never edit": in an interactive `/audit` the audit skill runs in the main session, which has Edit and Write. Either revert I2 to planned here and leave the flip to a ticket that adds the test, or narrow the I2 wording to what the two tests pin (the auditor agent and the CI action) and say why the front-matter check is the outside check. The log line moves with whichever you choose. Blocking because this is a manifesto invariant, and I want to see which fix is chosen.
- f3: docs/reference/commands.md:90 lists `routing`, `state`, `rules`; the help and briefing.py also have `skills`. .okf/architecture/overview.md:94 and the diagram leave out that briefing.py imports `skills_dir` from plugin.py to list the plugin's skills. Add the field, the table entry and a `briefing --> pluginPy` edge (or a skills node).

## Notes

`kmctl plugin install` writes an absolute path into this machine's XDG data folder into .claude/settings.json. The how-to describes that correctly, but a reader might commit the file for teammates. Not a finding for this ticket.
