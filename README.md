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

## Why

Agents write code faster than anyone updates the documents around it. The
design page stops matching the code, a decision quietly gets reversed, and the
next agent works from the stale version. No hook can tell whether a page is
still true; that takes judgment. So kmctl does two things instead:

- **It puts the right knowledge in front of the agent** at the start of each
  session: where knowledge lives, how to write it, and what is due for review.
- **It audits.** A separate agent checks, on request or in CI, that decisions
  still hold, architecture pages still match the code and practices still have
  their evidence. It reports; a person decides.

## Where knowledge lives

| Kind | Where | Reader |
|---|---|---|
| Docs for people who use the project | `docs/`, sorted into `tutorials/`, `how-to/`, `reference/` and `explanation/` | users |
| Decisions, architecture, practices, proposals, handoffs | `.okf/`, an OKF v0.2 bundle | people and agents working on the project |
| Repeatable tasks | skills | agents |
| Standing guidance | rules in `.claude/rules/` | agents |

## What you get

- **The `kmctl` CLI** sets a repository up, creates new decisions, docs pages
  and other concepts with their index entries, checks that indexes and links
  agree, and lists what is due for review.
- **A Claude Code plugin** with one SessionStart hook that prints the
  briefing, an audit agent, a skill for writing `docs/` pages, and
  `/handoff` and `/continue` to save and resume work between sessions.
  Claude Code is the only harness today. The plugin's skills, agent and
  hook also install with [APM](https://microsoft.github.io/apm); see
  [Install kmctl with APM](docs/how-to/install-kmctl-with-apm.md).
- **A GitHub Action** that runs `kmctl check` on every pull request for free,
  and an opt-in audit you run by hand or on a schedule.

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

## Quick start

```
kmctl init                       # docs/, a starter .okf/ bundle, rules and a CLAUDE.md block
kmctl new decision 'Store data in SQLite' --description 'One SQLite file, no database server.'
kmctl new doc how-to 'Back up the database' --description 'Copy the SQLite file safely.'
kmctl check                      # indexes agree with their folders, links resolve
kmctl review due                 # what is unverified or stale
```

`kmctl init` keeps files that already exist. Every command takes `--help`,
and most take `--json` for scripts and agents. The
[tutorial](docs/tutorials/get-started-with-kmctl.md) walks through this in one
sitting.

## What it does not do

kmctl cannot force knowledge to stay true. An agent can read the briefing and
still forget to update a decision, and an audit can miss drift. kmctl makes
stale knowledge visible and cheap to find. It also stops at the edge of one
repository: sharing skills across repositories, searching across projects
and syncing to a central place are left to other tools. See
[Where kmctl fits in knowledge management](docs/explanation/where-kmctl-fits-in-knowledge-management.md).

## Documentation

The [docs index](docs/README.md) lists every page:

- Tutorial: [Get started with kmctl](docs/tutorials/get-started-with-kmctl.md)
- How-to: [Install the plugin and the CI action](docs/how-to/install-the-plugin-and-the-ci-action.md)
- How-to: [Install kmctl with APM](docs/how-to/install-kmctl-with-apm.md)
- Reference: [Commands](docs/reference/commands.md)
- Explanation: [Why one hook and report-only audits](docs/explanation/why-one-hook-and-report-only-audits.md)
- Explanation: [Where kmctl fits in knowledge management](docs/explanation/where-kmctl-fits-in-knowledge-management.md)

## Working on kmctl

Start at [`.okf/index.md`](.okf/index.md); the design is
[`.okf/manifesto.md`](.okf/manifesto.md). `just lint`, `just test` and
`just integration` run the checks.
