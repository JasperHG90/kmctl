---
type: eval
title: 'Eval: apm-only-install'
description: 'Definition of done for apm-only-install: 13 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev173+ga4f6ce93a.d20261016
  at: '2026-10-16T20:31:14+00:00'
slug: apm-only-install
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 26880e71148f890fb2a1c69eae70facc4eb436c509165fa1e1cc3a11e1c8510a
  at: '2026-10-16T20:31:14+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The package is apm/: apm/apm.yml (name, version, only scaccogatto/okf-skills pinned to a full commit, no git: parent), the 7 skills under apm/.apm/skills/, kmctl-auditor.md under apm/.apm/agents/, and the 4 rules as apm/.apm/instructions/NAME.instructions.md whose applyTo equals the old paths: globs and whose bodies equal the old rule bodies; plugin/, .claude-plugin/marketplace.json and src/kmctl/repo_rules/ are gone.
  Fails when: any of those files is missing or differs, apm/apm.yml has another dependency or an unpinned okf-skills, or plugin/, the marketplace file or repo_rules/ still exists
- r2: apm/apm.yml is the one version source: scripts/release.py set writes it and the root apm.yml, current refuses when they differ, pyproject.toml reads the version from it, and the built wheel reports it and carries the skills for the briefing.
  Fails when: after set 9.8.7 either apm.yml is not 9.8.7, current exits 0 on a mismatch, or the wheel's version or skills folder is wrong
- r3: The Claude hook writer merges exactly one kmctl SessionStart entry (the briefing command, description and timeout, never blocking: I1) into .claude/settings.json: other keys and hooks are kept, a second run leaves one entry, an old kmctl entry is replaced in place, and a missing file is created.
  Fails when: another key or hook is lost or changed, there are zero or two kmctl entries, the command differs from the one I1 tests, or a missing settings file is not created
- r4: kmctl plugin install --harness claude [--source URL] [--force] writes the kmctl dependency {git: URL, path: apm, ref: v<cli version>} and targets: [claude] into the repository's apm.yml (keeping other entries), runs uvx --from apm-cli==0.33.0 apm install --target claude, writes the hook, and on success ends with a Next: line; --source defaults to the GitHub repository; an unknown harness is refused naming the accepted values.
  Fails when: the apm.yml entry, ref or targets differ, other apm.yml entries are lost, the APM command line differs, the hook is not written, or an unknown harness is accepted
- r5: When APM's output says it skipped local files not managed by APM, kmctl plugin install fails (exit 1) naming the skipped paths and kmctl plugin install --force; with --force it passes --force to APM; a failed APM run fails with APM's cause.
  Fails when: a skip exits 0 or names no path or no fix, --force is not passed through, or an APM failure loses its cause
- r6: When claude plugin list --json shows kmctl@kmctl for this repository, kmctl plugin install runs claude plugin uninstall kmctl@kmctl, claude plugin prune and claude plugin marketplace remove kmctl at that scope and says so; when apm.yml names JasperHG90/Knowledge-management/apm in another form, it runs apm uninstall on that entry before writing its own; with claude not on PATH it skips the claude step and says so.
  Fails when: any of those commands is missing, runs at the wrong scope or out of order (apm uninstall after the apm.yml rewrite), runs silently, or a missing claude CLI fails the install
- r6b: kmctl declares okf's MCP server for Claude: it merges one okf-bundle entry into the repository's .mcp.json (claude mcp add-json --scope user at user scope), keeping other servers, running uv run of okf_mcp.py's raw URL at the sha apm/apm.yml pins through a sh launcher that walks up to the first folder holding .okf/. When an okf server already exists under any name (its command or args name okf_mcp.py), kmctl adds none and says which one it kept. kmctl's own okf-bundle entry is replaced by name on every install (so a new okf pin reaches it); only another server naming okf_mcp.py makes kmctl skip.
  Fails when: other servers are lost, the entry is missing or duplicated after two installs, the sha differs from the pin, or the launcher run from a repository subfolder does not resolve the repository's .okf/, or a second okf server is added next to an existing one, or a reinstall with a changed okf pin leaves okf-bundle at the old sha
- r7: --scope user runs apm install -g and writes the hook to the user settings file under CLAUDE_CONFIG_DIR (default ~/.claude); project scope stays the default.
  Fails when: user scope does not pass -g, writes the hook into the repository, or ignores CLAUDE_CONFIG_DIR
- r8: kmctl plugin status reports the kmctl ref in apm.lock.yaml against the CLI version and whether the hook entry is present, each problem naming its fix, with --json; kmctl init no longer writes .claude/rules/ and its next step points at kmctl plugin install.
  Fails when: a mismatched ref or missing hook goes unreported, a problem names no fix, or kmctl init writes any rule file
- r9: In a scratch consumer, with HOME and CLAUDE_CONFIG_DIR pointed at scratch folders, kmctl plugin install --harness claude --source <tree served from a local git server> leaves the 7 skills and the agent byte for byte in .claude/, the 4 rules with paths: equal to the old globs, okf's skills, exactly one briefing SessionStart entry in .claude/settings.json, none of this repository's 16 dev items, and kmctl plugin status reports no problems.
  Fails when: the install fails, any listed item is missing or differs, a dev item lands, or status reports a problem
- r10: The CI audit (action.yml, .github/workflows/knowledge-audit.yml, action/knowledge-audit.sh) reads the skills and agent from apm/.apm, and the repository's own rules that scoped to plugin/** scope to apm/.apm/**.
  Fails when: any of them still names plugin/
- r11: A new decision (kmctl schema decision shape) records APM as the only install route wrapped by kmctl plugin install --harness, the hook written by kmctl, the rules shipped in the package, the --source, --force and old-plugin removal choices; ADR 0013 and ADR 0003 are marked superseded by it, ADR 0011 and ADR 0012 and ADR 0001 name what changed; the manifesto, architecture overview, commands reference and both install how-tos describe the new route, and the APM how-to says a hand-added APM entry gets no hook.
  Fails when: the decision is missing or malformed, a superseded record is not marked, or any of those pages still describes the claude marketplace route or plugin/
- r12: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
