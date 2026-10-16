# Install kmctl with APM

This page adds kmctl's APM package to a repository's `apm.yml` by hand, for a
repository that already manages its agent files with
[APM](https://microsoft.github.io/apm), the Agent Package Manager. The
package holds kmctl's skills, its audit agent and its four knowledge rules,
and brings the okf skills they use.

`kmctl plugin install --harness claude` does all of this for you and more;
see [Install the plugin and the CI action](install-the-plugin-and-the-ci-action.md).
A hand-added entry leaves out what kmctl writes itself:

- **The session hook.** The package has no SessionStart hook, so a session
  gets no kmctl briefing until you run `kmctl plugin install --harness
  claude` once in the repository. It writes the hook into
  `.claude/settings.json`.
- **okf's MCP server.** APM skips it because it comes from a dependency of
  kmctl's package. `kmctl plugin install --harness claude` declares it in
  `.mcp.json`.
- **The kmctl CLI.** Most of the skills and the hook run `kmctl` commands, so
  you install the CLI yourself, in step 1, at the same tag as the package.

How the commands below were run: with APM 0.33.0 in a scratch repository,
installing the package from a local git server that held this repository's
files, and with okf-skills from GitHub. `tests/test_apm_package.py` runs the
same install through `kmctl plugin install`.

## Before you start

- [uv](https://docs.astral.sh/uv/) and `git` on your PATH.
- APM 0.33.0 or later on your PATH, for example from
  `uv tool install apm-cli`.
- A git repository to install into.
- GitHub access to the kmctl repository. It is private for now, so APM
  needs a GitHub token with access to it. APM reads one from
  `GITHUB_APM_PAT`, `GITHUB_TOKEN` or `GH_TOKEN`, then from `gh auth token`,
  then from your git credential helper.

## Steps

### 1. Install the kmctl CLI

```
uv tool install git+https://github.com/JasperHG90/Knowledge-management@v0.3.0
```

### 2. Add the kmctl package

Add the package to the repository's `apm.yml`, at the same tag as the CLI:

```yaml
dependencies:
  apm:
    - JasperHG90/Knowledge-management/apm#v0.3.0
```

and then, from the repository root:

```
apm install --target claude
```

### 3. Optional: hand the entry to kmctl for the session hook

Skip this step to keep your own entry; the session then gets no briefing.
To get the hook and okf's MCP server, run:

```
kmctl plugin install --harness claude
```

This writes the SessionStart hook and okf's MCP server. It also replaces
your entry with the one kmctl writes, `{git: ..., path: apm, ref: v0.3.0}`,
after running `apm uninstall` on yours, so the two never install the package
twice.

### 4. Start a new session

Start a new Claude Code session in the repository. The SessionStart hook
prints the kmctl briefing at the start of each session.

## Check it worked

APM writes kmctl's seven skills to `.claude/skills/` (`architecture-review`,
`audit`, `continue`, `decision-log-review`, `handoff`, `practices-review`,
`write-docs`) next to okf's (`okf`, `validate`, `backfill`, `visualize`),
the agent to `.claude/agents/kmctl-auditor.md`, and the rules to
`.claude/rules/`. In the repository, run:

```
kmctl briefing
```

It prints the same briefing the hook prints. If it says `kmctl: command not
found`, go back to step 1. If you skipped step 3, `kmctl doctor` fails
`claude.hook`, saying there is no SessionStart hook, and names the command
that adds it.

To upgrade, install the CLI at the new tag with `uv tool install --force`,
then run `kmctl plugin update`.
