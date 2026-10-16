# Install kmctl with APM

This page installs kmctl's skills, its audit agent and its SessionStart hook
into one repository with [APM](https://microsoft.github.io/apm), the Agent
Package Manager, instead of `kmctl plugin install`. APM also installs the okf
skills kmctl's skills use.

`kmctl plugin install` stays the main route; see
[Install the plugin and the CI action](install-the-plugin-and-the-ci-action.md).
Use APM when the repository already manages its agent files with APM. The
APM route leaves out two things:

- **The kmctl CLI.** Most of the skills and the hook run `kmctl` commands, so
  you install the CLI yourself, in step 1. Nothing checks that the CLI and
  the skills come from the same release, as `kmctl plugin status` does on
  the main route, so install both from the same tag.
- **okf's MCP server.** APM skips it because it comes from a dependency of
  kmctl's package, not from your apm.yml. To get it, run `apm install
  --trust-transitive-mcp`, or add `scaccogatto/okf-skills` to your apm.yml
  yourself.

How the commands below were run: with APM 0.33.0 in a scratch repository,
installing the package from a local git server that held this repository's
files, and with okf-skills from GitHub. `tests/test_apm_package.py` runs the
same install.

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
uv tool install git+https://github.com/JasperHG90/Knowledge-management@v0.2.0
```

### 2. Add the kmctl package

From the repository root, at the same tag as the CLI:

```
apm install JasperHG90/Knowledge-management/apm#v0.2.0
```

This adds the package to the repository's `apm.yml` and installs it. If you
edit `apm.yml` by hand instead, the entry is:

```yaml
dependencies:
  apm:
    - JasperHG90/Knowledge-management/apm#v0.2.0
```

and then run `apm install`.

Install it in the repository only. `apm install -g`, which installs for your
user, refuses this package: it pulls in `plugin/` from its own repository
with `git: parent`, which APM does not allow at user scope.

### 3. Start a new session

Start a new Claude Code session in the repository. The SessionStart hook
prints the kmctl briefing at the start of each session.

## Check it worked

APM writes kmctl's seven skills to `.claude/skills/` (`architecture-review`,
`audit`, `continue`, `decision-log-review`, `handoff`, `practices-review`,
`write-docs`) next to okf's (`okf`, `validate`, `backfill`, `visualize`),
the agent to `.claude/agents/kmctl-auditor.md`, and the hook to
`.claude/settings.json`. In the repository, run:

```
kmctl briefing
```

It prints the same briefing the hook prints. If it says `kmctl: command not
found`, go back to step 1.

To upgrade, change the tag in `apm.yml` and run `apm install`, and install
the CLI at the same tag with `uv tool install --force`.
