---
type: plan
title: 'Plan: kmctl-doctor'
description: "kmctl doctor checks, per harness and without writing or using the network, that kmctl's dependencies, APM-installed files, hook, okf skills and MCP server and the kmctl init files are in place, printing one ok or fail line with its fix per check and exiting nonzero on any failure."
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T19:45:20+00:00'
slug: kmctl-doctor
epic: multi-harness
depends_on:
- apm-only-install
- antigravity-harness
priority: 3
---

# kmctl-doctor

Relayed from: none

## Intent

The operator asked (2026-10-16): "kmctl needs doctor to check if everything (including deps) is installed."

After apm-only-install and antigravity-harness, `kmctl plugin install --harness claude,antigravity` runs `uvx --from apm-cli==0.33.0 apm install JasperHG90/Knowledge-management/apm#v<cli version> --target ...`. APM writes kmctl's 7 skills, the kmctl-auditor agent (Claude only), 4 knowledge rules and the pinned okf skills into `.claude/` and `.agents/`. kmctl itself writes the SessionStart hook into `.claude/settings.json` and the Antigravity workspace plugin `.agents/plugins/kmctl/` (plugin.json, hooks.json, the translated agent, and mcp_config.json running okf's MCP server with `uv run <pinned raw URL>`).

Measured on 2026-10-16: a repository with both harnesses holds about 20 installed pieces per harness (7 skills, the agent, 4 rules, the hook, the okf skills, the okf MCP entry, the lock ref) plus 4 tools (uv, git, apm through uvx, claude or agy) and the `kmctl init` files. The one checking verb today, `kmctl plugin status` (`src/kmctl/plugin.py`), checks 3 things (the version `claude plugin list` reports for `kmctl@kmctl`, the staged copy's version, the marketplace folder), none of them a file APM writes, and once apm-only-install drops the `claude plugin` route its first check always fails. 5 of the plans in `.loop/plans/` built or fixed install steps (plugin-install-verb, plugin-install-known-marketplace, plugin-error-keeps-cause, network-tests-retry, update-refreshes-rules); none added a way to see what a repository is missing.

What changes:

- **The verb.** `kmctl doctor [--path DIR] [--json] [--online]` runs every check and prints one line each, shaped like `loopctl doctor`: `ok   <check>: <detail>` or `fail <check>: <what is wrong>; <the command that fixes it>`. It exits 0 when every check is ok and 1 when any fails (2 stays Typer's usage error). `--json` prints one object `{"ok": bool, "checks": [{"id", "harness", "ok", "detail", "fix"}]}`; ids are stable dotted names such as `dep.uv`, `dep.git`, `dep.apm`, `dep.claude`, `dep.agy`, `kmctl.version`, `init.okf`, `init.docs`, `claude.lock`, `claude.files`, `claude.hook`, `claude.okf-skills`, `claude.okf-mcp`, and the same under `antigravity.`, with `antigravity.plugin` for `.agents/plugins/kmctl/`. Human lines go to stdout as results; nothing goes to stderr unless doctor itself cannot run. The help and epilog list every id and say doctor writes nothing and uses no network unless `--online` (per `.claude/rules/cli-interface.md` and `.claude/rules/interface-audience.md`).
- **The checks**, in `new:src/kmctl/doctor.py`, a function returning a list of check results with no printing, so tests and the CI action can call it:
  - Tools on PATH: `uv` and `git` always; `claude` when the Claude harness is installed here, `agy` when Antigravity is. APM runnable at the pinned version: `uv tool run --offline --from apm-cli==0.33.0 apm --version` (uv's cache only, no network); fail names the `uvx --from apm-cli==0.33.0 apm --version` line that fetches it.
  - `kmctl.version`: always ok, its detail the CLI version every other check compares against.
  - `init.okf` and `init.docs`: `.okf/index.md` and `docs/README.md` exist; fix `kmctl init`. Bundle content stays `kmctl check`'s job.
  - Per harness found (see below): the APM lock's ref for the kmctl package equals `v<cli version>` (fix `kmctl plugin update`); every file the lock lists as deployed for that harness exists and matches its recorded sha256, which covers the skills, the agent, the rules and the okf skills without a hard-coded list (fix `kmctl plugin install --harness H`), with okf's skills also reported under their own id; the hook entry equals what this CLI's install writes, built by the same function apm-only-install and antigravity-harness use, not a copy; the okf MCP server entry equals what that harness's install writes, built by the same function (Claude: the `okf-bundle` entry apm-only-install merges into `.mcp.json`, or the user-scope entry; Antigravity: the plugin's `mcp_config.json`); for Antigravity, every file under `.agents/plugins/kmctl/` (plugin.json, hooks.json, mcp_config.json and the 3 translated agents) is compared with what this CLI would write, using antigravity-harness's comparison, so a missing, extra, edited or stale file fails `antigravity.plugin` naming the file. When `apm_modules/` is missing (a fresh clone: it is git-ignored), the okf agents cannot be rebuilt for comparison, so `antigravity.plugin` fails with `apm_modules/ is missing; run kmctl plugin install --harness antigravity` instead of guessing. With `--online` only, Antigravity also checks that `uv` can fetch the pinned MCP script URL.
  - No harness found: one fail, `no kmctl harness in this repository; run kmctl plugin install --harness claude`.
- **User scope.** apm-only-install keeps `kmctl plugin install --scope user` (apm `-g`, state in `~/.apm/`, files under `$CLAUDE_CONFIG_DIR`, default `~/.claude/`). `kmctl doctor --scope user` runs the same checks against that install. With no `--scope`, doctor checks the project; when the project has no harness but a user-scope install exists, it reports `claude.scope: ok, installed at user scope; run kmctl doctor --scope user` instead of failing and suggesting a second project install.
- **Which harnesses are here.** Doctor reads it from what the install leaves, never from what is missing: the apm.yml `targets:` list when the install records one, the lock's deployed paths (`.claude/` or `.agents/`), the kmctl hook in `.claude/settings.json`, and `.agents/plugins/kmctl/`. Any one marks the harness present, so deleting one piece still names that piece rather than hiding the harness (risk 1).
- **Read only.** Doctor opens files for reading and runs only `--version`-style commands; a test runs it in a scratch repository and checks that no file's bytes or mtime changed.
- **Tests and docs.** `new:tests/test_doctor.py` builds the installed layout from fixtures (no network, no real APM) and checks each id's ok and fail case, the exit codes, the JSON shape, and the no-write property; `tests/test_help.py` covers the new verb. An integration test (marked as the repo marks network tests) runs the real install in a scratch repo. `docs/reference/commands.md` gets the verb; `docs/how-to/install-the-plugin-and-the-ci-action.md` ends its install steps with `kmctl doctor`, and `kmctl plugin install` ends with `Next: kmctl doctor`.

`kmctl plugin status` folds into doctor (the operator's choice, 2026-10-16): this ticket removes the `plugin status` verb, its help and docs, and `kmctl plugin install` and `update` end with `Next: kmctl doctor`. Old installs: doctor also fails `claude.old-plugin` when the repository's `.claude/settings.json` (or, with `--scope user`, the user settings file under `$CLAUDE_CONFIG_DIR`) lists `kmctl@kmctl` or `okf@scaccogatto` as enabled in `enabledPlugins`. It reads the file and never runs `claude plugin list`: spike:kmctl-doctor/4 showed that command opens network connections and writes `.claude.json` under `$CLAUDE_CONFIG_DIR`, so it would break doctor's read-only, offline promise. The only external command doctor runs is `uv tool run --offline --from apm-cli==0.33.0 apm --version`, which the same spike showed makes no connection and writes nothing (the new install removes it; doctor catches a repository that was not reinstalled), fix `kmctl plugin install --harness claude`. Antigravity trust: when `agy` is on PATH, doctor fails `antigravity.trust` when the repository is not in `trustedWorkspaces` of the agy CLI settings file under ~/.gemini/antigravity-cli/ (fix: open the folder in Antigravity and trust it) (spike:antigravity-harness/3: workspace customizations load only in a trusted folder).

Done when: in a scratch repository after `kmctl plugin install --harness claude,antigravity` and `kmctl init`, `kmctl doctor` exits 0 with every check ok and makes no network call; deleting any one installed piece (a skill, the hook entry, the `.agents/plugins/kmctl/` folder, the lock file) or editing the lock's kmctl ref to another version makes it exit 1 with a fail line naming that piece and its fix, and the same in `--json` under a stable id; no file in the repository changes; and the gates pass.

## Could invalidate this plan

- Harness detection: doctor might not be able to tell which harnesses a repository uses once a piece is gone, if APM 0.33.0 neither records `--target` in the consumer's apm.yml nor lists `.agents/` paths as deployed in apm.lock.yaml. Then a deleted lock plus a deleted hook would look like "no Claude harness" rather than a failure, and the plan would need the install (apm-only-install) to write its own record, which changes that ticket's contract. Settled by spike:kmctl-doctor/1: APM records the targets in the lock (`deployments[].target`, with `.agents/` paths and sha256 hashes listed like `.claude/` ones), and in apm.yml `targets:` only when it creates apm.yml. So apm-only-install writes `targets:` into the consumer's apm.yml itself, and doctor treats a missing lock as a failure of its own.
- Lock hashes after kmctl's merges: kmctl writes its hook into `.claude/settings.json`, a file APM also writes, so the lock's sha256 check might report drift on every correct install. Settled by spike:kmctl-doctor/3: the lock lists hook scripts but never `.claude/settings.json`, the .agents/hooks.json file or `apm-hooks.json`, and after a kmctl-style merge all 32 listed hashes matched. So doctor checks the hook entries by parsing those files itself.
