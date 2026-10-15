<p align="center">
  <img src="docs/assets/logo.png" alt="kmctl logo: an owl with glasses holding a folder, next to the word kmctl" width="480">
</p>

# kmctl

kmctl keeps a repository's knowledge current: `docs/` for people who use the
project and an `.okf/` knowledge bundle for people and agents working on it.
At the start of every Claude Code session its plugin gives the agent a
briefing on where knowledge lives, what is due for review and the rules for
writing it. Its GitHub Action checks indexes and links on every pull request
at no model cost, and an opt-in audit agent reports knowledge that has drifted from the code
without changing anything.

## Install

```
uv tool install git+https://github.com/JasperHG90/Knowledge-management
```

The kmctl repository is private for now, so this needs a GitHub account
with access to it; uv clones it with your git credentials.

Then, in a repository:

```
kmctl plugin install
```

This needs the `claude` CLI on your PATH. The steps, with the CI action, are
in [Install the plugin and the CI action](docs/how-to/install-the-plugin-and-the-ci-action.md).

## Documentation

The [docs index](docs/README.md) lists every page:

- Tutorial: [Get started with kmctl](docs/tutorials/get-started-with-kmctl.md)
- How-to: [Install the plugin and the CI action](docs/how-to/install-the-plugin-and-the-ci-action.md)
- Reference: [Commands](docs/reference/commands.md)
- Explanation: [Why one hook and report-only audits](docs/explanation/why-one-hook-and-report-only-audits.md)

Working on kmctl itself? Start at [`.okf/index.md`](.okf/index.md).
