---
type: decision
title: "ADR 0014: APM is the only install route"
description: "kmctl's skills, audit agent and knowledge rules ship only as the APM package in apm/, which kmctl plugin install --harness writes into apm.yml and installs with APM; kmctl writes the SessionStart hook and okf's MCP server itself."
tags: [adr, decision, install]
generated:
  by: claude-opus/5.5
  at: 2026-10-16T20:52:21Z
status: stable
sources:
  - resource: "apm"
  - resource: "src/kmctl/plugin.py"
---

# ADR 0014: APM is the only install route

- Status: Accepted
- Date: 2026-10-16

## Context

On 2026-10-16 a repository got kmctl's pieces in two commands and through
three routes, each with part of them. `kmctl plugin install` staged
`plugin/` and installed it as the Claude Code plugin `kmctl@kmctl`
([ADR 0001](0001-standalone-cli-installs-its-plugin.md),
[ADR 0003](0003-claude-code-plugin-first-depends-on-okf.md)): the 7 skills,
the audit agent and the SessionStart hook, but none of the 4 knowledge rules.
The APM package in `apm/` ([ADR 0013](0013-kmctl-installs-through-apm-too.md))
gave the same, also without the rules. The rules came only from `kmctl init`
([ADR 0011](0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code.md)).
The claude plugin route works only for Claude Code.

The operator asked (2026-10-16) for kmctl to reach more harnesses than Claude
Code through APM (Microsoft's Agent Package Manager, `apm-cli` 0.33.0), with
`kmctl plugin install` kept as a thin wrapper around it, and hooks, rules,
skills and agents all delivered. This is the first of three tickets in that
work; it does Claude Code on the new layout.

What APM 0.33.0 does, from the ticket's spikes:

- A package `apm/apm.yml` with the skills, agent and rules as
  `*.instructions.md` under `apm/.apm/` installs the 7 skills and the agent
  byte for byte, and the rules into `.claude/rules/` with their `paths:`
  equal to the comma-joined `applyTo:` (spike:apm-only-install/1).
- `apm install -g` of that package writes the same under `$CLAUDE_CONFIG_DIR`
  (default `~/.claude/`), the folders Claude Code reads at user scope
  (spike:apm-only-install/2).
- The CLI form `apm install PACKAGE` cannot name a subfolder of a repository
  on a host other than GitHub, and APM writes `targets:` into apm.yml only
  when it creates the file (spike:apm-only-install/1, spike:kmctl-doctor/1).
- APM overwrites a rule file it did not write, but leaves a skill folder it
  did not write in place, printing only a count, `N file skipped -- local
  files exist` (spike:apm-only-install/3, spike:apm-only-install/5).
- APM skips okf's MCP server, because okf-skills is a dependency of kmctl's
  package, and okf's entry points at `${CLAUDE_PLUGIN_ROOT}`, which only a
  Claude plugin fills in.
- Old installs leave duplicates. Swapping an ADR 0013 apm.yml entry keeps the
  old package's SessionStart hook; only `apm uninstall` removes it
  (spike:apm-only-install/6). Uninstalling the claude plugin `kmctl@kmctl`
  leaves `okf@scaccogatto` enabled until `claude plugin prune`
  (spike:apm-only-install/7).

## Decision

The APM package in `apm/` is the only way kmctl's skills, agent and rules
reach a repository. `kmctl plugin install --harness claude` installs it:

- **The package.** `apm/apm.yml` names kmctl, carries the release version
  and depends only on `scaccogatto/okf-skills` pinned to a commit. The 7
  skills sit in `apm/.apm/skills/`, the auditor in `apm/.apm/agents/`, and the
  4 knowledge rules in `apm/.apm/instructions/` as `NAME.instructions.md`, with
  their old `paths:` written as a comma-joined `applyTo:`. `plugin/`,
  `.claude-plugin/marketplace.json` and `src/kmctl/repo_rules/` are gone.
- **The install.** `kmctl plugin install --harness claude` writes the entry
  `{git: SOURCE, path: apm, ref: v<cli version>}` and the harnesses as
  `targets:` into the repository's apm.yml, keeping its other entries and
  comments, then runs `uvx --from apm-cli==0.33.0 apm install --target claude`.
  The ref is the CLI's own version, so the CLI still installs the content of
  its own release (ADR 0001). `--harness` takes a comma list; `claude` is the
  only value so far. `--source GIT_URL` (default
  `https://github.com/JasperHG90/Knowledge-management.git`) points it at a
  fork, a local server or an unreleased tree; the operator chose an option
  over an environment variable. `kmctl plugin update` runs the same steps.
  `--scope user` runs `apm install -g` with the entry in `~/.apm/apm.yml`.
- **The hook.** kmctl writes the one SessionStart hook itself, merging one
  entry that runs `kmctl briefing` into `.claude/settings.json` (at user
  scope, the settings file under `$CLAUDE_CONFIG_DIR`). It finds its own entry
  by that command, replaces it in place, and leaves every other key and hook
  alone. ADR 0004 still holds.
- **okf's MCP server.** kmctl declares it too: one server, `okf-bundle`, in
  the repository's `.mcp.json` (at user scope with `claude mcp add-json
  --scope user`), running `uv run` of okf's `okf_mcp.py` at the pinned commit
  through a short `sh` launcher that finds the nearest `.okf/` folder. When
  another server already runs `okf_mcp.py`, kmctl adds none and says which it
  kept.
- **Skipped files.** When APM says it left local files in place, the install
  fails with the skill folders it worked out from `apm.lock.yaml` and the fix,
  `kmctl plugin install --force`, which passes `--force` to APM and replaces
  those folders whole. Without `--force` kmctl never overwrites a file the
  user wrote.
- **Old installs.** Before writing apm.yml, the install runs `apm uninstall`
  on an entry that names `JasperHG90/Knowledge-management/apm` another way.
  Once `apm install` has succeeded, it removes the claude plugin
  `kmctl@kmctl` where it applies (`claude plugin uninstall`, then
  `claude plugin prune` and `claude plugin marketplace remove kmctl`, at the
  plugin's scope), so a failed install leaves the old plugin working; it
  skips this with a note when `claude` is not on PATH. The operator chose to
  remove old installs rather than only report them.
- **The rules leave `kmctl init`.** Init no longer writes the 4 rules; its
  next step names `kmctl plugin install`. This replaces ADR 0011's first
  decision bullet and its rule refresh; its CLAUDE.md block and first
  decision stay.
- **One version source.** `apm/apm.yml`'s `version:` replaces the plugin
  manifest as the one place the version is written
  ([ADR 0012](0012-releases-come-from-ci.md)). The wheel carries only the
  skills folder, for `kmctl briefing` to list.
- `kmctl plugin status` reports the kmctl ref in `apm.lock.yaml` against the
  CLI version and whether the hook is there, each problem naming its fix.

This supersedes ADR 0013 (APM as a second route) and ADR 0003 (a Claude Code
plugin with an okf plugin dependency).

Rejected:

- Keep the claude plugin route beside APM. Two routes deliver different
  pieces, and only APM can serve a second harness.
- Let APM install the hook from the package. An ADR 0013 swap showed APM
  leaves a package's old hook behind, and APM writes hooks only in the shapes
  it knows; kmctl finding its own entry by its command keeps exactly one.
- Run `apm install JasperHG90/Knowledge-management/apm#vX` without writing
  apm.yml. It cannot point at another host's subfolder, so `--source` and the
  integration test would not work, and APM would not record the targets.
- Uninstall `okf@scaccogatto` by name when removing the old plugin. Prune
  removes it only when kmctl alone pulled it in, so an okf the user installed
  on purpose stays.

## Consequences

- One command gives a Claude Code repository everything: the 7 skills, the
  agent, the 4 rules, okf's skills, the hook and okf's MCP server.
- Every install needs `uv` on PATH, since kmctl runs APM with `uvx`; the
  `claude` CLI is needed only at user scope for the MCP server and to remove
  the old plugin.
- An apm.yml entry added by hand still gets the skills, agent and rules, but
  no SessionStart hook and no okf MCP server;
  `docs/how-to/install-kmctl-with-apm.md` says so and how to get them.
- Claude Code asks the user to approve a project `.mcp.json` server once.
- The next tickets build on this: `antigravity-harness` adds `--harness
  antigravity` and reuses the MCP launcher, and `kmctl-doctor` folds
  `kmctl plugin status` into `kmctl doctor`, reusing the hook and MCP writers.
- `tests/test_plugin.py` checks the install with fake `uvx` and `claude`, and
  `tests/test_apm_package.py` runs it with the real APM 0.33.0 against this
  tree served from a local git server.

Supersedes [ADR 0013](0013-kmctl-installs-through-apm-too.md).

Supersedes [ADR 0003](0003-claude-code-plugin-first-depends-on-okf.md).

### Amended, 2026-10-17

[ADR 0020](0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest.md):
kmctl's package now ships the SessionStart hooks, okf's MCP server and the
rules for each harness, and APM writes them; kmctl writes only the
Antigravity agents and removes APM's broken okf Stop handler.

### Amended again, 2026-10-17

[ADR 0021](0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest.md):
users install, upgrade and remove the package with APM's own verbs;
`kmctl plugin install`, `update` and `remove` are gone, and
`kmctl plugin patch` adds what APM cannot install yet.

## Correction, 2026-10-19

Five statements above no longer match the code; the decision, that APM is
the only install route, stands.

- **The package.** The Decision says `apm/apm.yml` depends only on
  okf-skills and that the 4 rules sit in `apm/.apm/instructions/`. Since
  [ADR 0020](0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest.md)
  `apm/.apm/` holds only the skills and the auditor. The rules sit in the
  sub-package `apm/claude/.apm/instructions/`, with a copy for Antigravity
  in `apm/antigravity/.apm/instructions/` that
  `scripts/sync_antigravity_rules.py` writes, and `apm/apm.yml` depends on
  `./claude` and `./antigravity` as well as the pinned okf-skills.
- **The wheel.** It carries more than the skills folder. `pyproject.toml`
  force-includes `apm/.apm/skills` as `kmctl/_skills`, for `kmctl
  briefing`; `apm/.apm/agents` as `kmctl/_agents`, for the Antigravity and
  OpenCode agents `kmctl plugin patch` writes; and
  `apm/claude/.apm/instructions` as `kmctl/_rules`, for the OpenCode rules.
- **`kmctl plugin status`** is gone. The `kmctl-doctor` ticket folded it
  into `kmctl doctor`, whose `claude.lock` check compares the kmctl ref in
  `apm.lock.yaml` with the CLI's version and whose `claude.hook` check
  looks for the hook. `kmctl plugin patch` is the only `plugin` command
  left (ADR 0021).
- **The tests.** `tests/test_plugin.py` no longer checks an install with a
  fake `uvx` and `claude`; it tests the hooks the package ships and okf's
  MCP launcher. No test runs a kmctl install, since kmctl no longer has one
  (ADR 0021). `tests/test_plugin_patch.py` tests `kmctl plugin patch` with
  a fake `uvx` and `claude` and checks that it never runs `uvx`. The
  `integration` tests in `tests/test_apm_package.py` and
  `tests/test_plugin_patch.py` add kmctl's entry to a scratch `apm.yml`,
  run the real APM 0.33.0 against this tree served from a local git server,
  then run `kmctl plugin patch`.
- **okf's MCP server's name.** The Decision names it `okf-bundle`.
  kmctl's package now declares it as `bundle`, okf's own name for it
  (`apm/apm.yml`, `MCP_NAME` in `src/kmctl/plugin.py`). okf-skills declares
  its own server `bundle`, APM skips a dependency's server, and
  `apm audit --ci` then failed `config-consistency` on `bundle`, "in
  manifest but not in lockfile", for every harness (issue #28,
  spike:antigravity-apm-audit/3). With one direct server of that name,
  holding kmctl's launcher, the check passes, and APM writes kmctl's
  launcher to `.mcp.json` and `.agents/mcp_config.json`
  (spike:antigravity-apm-audit/4).
