<p align="center">
  <img src="../../docs/assets/logo.png" alt="kmctl logo: an owl with glasses holding a folder, next to the word kmctl" width="480">
</p>

# kmctl

![Lifecycle: stable](https://img.shields.io/badge/lifecycle-stable-brightgreen)
[![CI](https://github.com/JasperHG90/kmctl/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/JasperHG90/kmctl/actions/workflows/ci.yml?query=branch%3Amain)
[![kmctl release](https://img.shields.io/github/v/release/JasperHG90/kmctl?filter=v*&sort=semver&label=release)](https://github.com/JasperHG90/kmctl/releases/latest)
[![License: MIT](https://img.shields.io/github/license/JasperHG90/kmctl)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](pyproject.toml)

kmctl keeps a repository's knowledge current: `docs/` for people who use the
project and an `.okf/` knowledge bundle for people and agents working on it.
At the start of every Claude Code session its plugin gives the agent a
briefing on where knowledge lives, what is due for review and which skills
to use; the rules for writing knowledge come with its package. Its GitHub Action checks indexes and links on every pull request
at no model cost, and an opt-in audit agent reports knowledge that has drifted from the code
without changing anything.

kmctl lives in the kmctl repository beside
[kmaudit](../kmaudit/README.md), which checks what a folder of markdown docs
claims against the code. The two work well together and install apart.

## Install

Two ways, depending on whether the repository exists yet. Click one to open
it.

<details>
<summary><strong>Install with copier</strong>: start a new repository</summary>

kmctl-starter, the [copier](https://copier.readthedocs.io/) template in this
repository (`copier.yml` and `starter/`), sets one up with `docs/`, `.okf/`
and kmctl's package for your agent harness (Claude Code, Antigravity or
OpenCode). It needs [uv](https://docs.astral.sh/uv/) and
[just](https://just.systems/):

```
uvx copier copy gh:JasperHG90/kmctl my-project
cd my-project
git init
just bootstrap
```

Move to another kmctl release with `just upgrade vX.Y.Z`.
[Start a repository with kmctl-starter](../../docs/how-to/start-a-repository-with-kmctl-starter.md)
lists what it asks, what it writes, and how to move a project made from the
old kmctl-starter repository.

</details>

<details>
<summary><strong>Install without copier</strong>: add kmctl to an existing repository</summary>

### You need

- [uv](https://docs.astral.sh/uv/) and `git`. uv installs the kmctl CLI and
  runs APM (Agent Package Manager), so you need not install APM. Keep uv
  installed: okf's MCP server, which the package adds, runs with `uv run`.
- Claude Code, Antigravity (the IDE or the `agy` CLI), OpenCode, or more
  than one.
- While the kmctl repository is private: a GitHub account with access to it,
  and a GitHub token APM can use; see
  [Install kmctl with APM](../../docs/how-to/install-kmctl-with-apm.md#before-you-start).

### 1. Install the kmctl CLI

```
uv tool install git+https://github.com/JasperHG90/kmctl@v0.15.0#subdirectory=packages/kmctl
```

One install serves every repository: when a repository's `apm.lock.yaml`
pins another kmctl release, the kmctl on PATH runs that pinned release
through `uvx`. The session briefing says when a newer release is out.

### 2. Set up the repository

In the repository root:

```
kmctl init
```

It writes `docs/`, a starter `.okf/` bundle and a short block in `AGENTS.md`
or `CLAUDE.md`, and keeps any file that already exists. The exceptions are
its own block and entries: in a bundle from an older kmctl, it adds the
index and log lines for the pages it adds, such as `.okf/summary.md`.

### 3. Add kmctl's package to `apm.yml`

Add kmctl's entry to `apm.yml` in the repository root. A new `apm.yml`
looks like this:

```yaml
name: my-project
version: 0.1.0
dependencies:
  apm:
    - git: https://github.com/JasperHG90/kmctl.git
      path: packages/kmctl/apm
      ref: vX.Y.Z
```

Set `ref` to `v` and your kmctl version (`kmctl --version` prints it), so
the package matches the CLI. Releases after v0.12.2 keep the package in
`packages/kmctl/apm`; for v0.12.2 and older, write `path: apm`. Commit
`apm.yml` and `apm.lock.yaml`.

APM installs the package's hooks and MCP server unless `apm.yml` limits
which packages may run them, with an `executables:` block (or the older
`allowExecutables:`). If yours does, `apm approve --pending` lists kmctl's
package; approve it with `apm approve`.

> **Warning: uninstall the okf plugin first.** kmctl's package brings okf's
> skills and its MCP server, `bundle`. If you also have the okf plugin
> for Claude Code (`okf@scaccogatto`), you get okf twice: its skills and a
> second okf MCP server. Remove it at each scope it is installed at:
>
> ```
> claude plugin uninstall okf@scaccogatto --scope user
> claude plugin uninstall okf@scaccogatto --scope project
> ```

### 4. Install it for your harness

APM installs kmctl's skills and the okf skills, the knowledge rules, a
session hook that prints kmctl's briefing at the start of every session,
and okf's MCP server (`bundle`), which lets the agent search `.okf/`.
For OpenCode, `kmctl plugin patch` writes the session hook into kmctl's
plugin instead.
`kmctl plugin patch` then adds what APM cannot install yet. Run it after
every `apm install`.

#### Claude Code

```
uvx --from apm-cli==0.33.0 apm install --target claude
kmctl plugin patch
```

Start a new Claude Code session. To install for every repository instead,
put the entry in `~/.apm/apm.yml` and run
`uvx --from apm-cli==0.33.0 apm install -g --target claude`, then
`kmctl plugin patch --scope user`.

#### Antigravity

```
uvx --from apm-cli==0.33.0 apm install --target antigravity
kmctl plugin patch
```

APM writes the skills, rules, hook and MCP server into `.agents/`.
`kmctl plugin patch` adds kmctl's audit agent and okf's two agents in
`.agents/plugins/kmctl/` (APM does not install agents for Antigravity yet)
and removes a copy of okf's Stop hook that APM writes but Antigravity cannot
run.

Antigravity loads `.agents/` only from a folder you trust, so trust the
repository root once:

- In the IDE, open the repository folder and accept the trust prompt.
- With the CLI, run `agy` in the repository root and choose
  "Yes, I trust this folder".

Antigravity installs per repository only; there is no user-scope install.

#### OpenCode

```
uvx --from apm-cli==0.33.0 apm install --target opencode
kmctl plugin patch
```

APM writes the skills into `.agents/skills/`, the agents into
`.opencode/agents/` and okf's MCP server into `opencode.json`.
`kmctl plugin patch` rewrites the agents into OpenCode's format (APM copies
them in Claude Code's, which OpenCode skips), writes the four rules to
`.opencode/rules/` and lists them in `opencode.json`'s `instructions`, and
adds `.opencode/plugins/kmctl.js`, which adds the briefing to each
session's system prompt. kmctl supports OpenCode 2.x only. OpenCode has no rules scoped to paths, so all four load in every
session. Start a new OpenCode session afterwards. Like Antigravity, OpenCode
installs per repository only.

#### More than one

```
uvx --from apm-cli==0.33.0 apm install --target claude,antigravity,opencode
kmctl plugin patch
```

Then trust the folder in Antigravity, as above. `kmctl doctor` checks the
install; each `fail` line names its fix.

### Upgrade

Set `ref` in `apm.yml` to the new tag and run your `apm install` line and
`kmctl plugin patch` again; the kmctl on PATH then runs the new pinned
release. Install a newer CLI only for its own fixes, except when you move
from v0.12.2 or older, as below. A project made from the starter does all
of it with `just upgrade vX.Y.Z`.

From v0.12.2 or older to a later release, kmctl moved into the repository's
`packages/kmctl` folder, so the steps change and their order matters:

1. Install the new CLI first. A kmctl at v0.12.2 or older looks for kmctl
   at the repository root and cannot run a later pin:

   ```
   uv tool install --force 'git+https://github.com/JasperHG90/kmctl@vX.Y.Z#subdirectory=packages/kmctl'
   ```

2. In `apm.yml`, change kmctl's entry from `path: apm` to the new path and
   tag:

   ```yaml
   - git: https://github.com/JasperHG90/kmctl.git
     path: packages/kmctl/apm
     ref: vX.Y.Z
   ```

3. Run your `apm install` line, then `kmctl plugin patch`.
4. Run `kmctl doctor` to check the install. It runs the release the lock
   names, so run it last, after `apm install` has moved the lock.

The GitHub Action (`uses: JasperHG90/kmctl@vX.Y.Z`) and the pre-commit
hook (`rev: vX.Y.Z`) change only their tag. kmctl's own audit (the
action's `mode: audit`, the `/audit` skill and its agent) is unchanged.
[kmaudit](../kmaudit/README.md) is a new, separate package that checks
what a folder of docs claims against the code; install it apart if you
want it.

### Remove

```
kmctl plugin patch --undo
uvx --from apm-cli==0.33.0 apm uninstall github.com/JasperHG90/kmctl/packages/kmctl/apm
```

The name ends with the entry's `path`: for a release at v0.12.2 or older it
is `github.com/JasperHG90/kmctl/apm`.

`--undo` deletes what patch wrote: `.agents/plugins/kmctl/`, and for
OpenCode the rewritten agents, the rules, their `instructions` entry and
the plugin. Run it first: `apm uninstall` stops on an agent patch rewrote. For
a user-scope install, run `apm uninstall -g` with the same name, then
`claude mcp remove bundle --scope user`, because APM leaves okf's MCP
server in your user `.claude.json`.

Installed kmctl with `kmctl plugin install`, which kmctl 0.3.0 had? Follow
the steps above: `kmctl plugin patch` removes what the old command wrote, or
names the `apm uninstall` to run first. The steps with the CI action are in
[Install the plugin and the CI action](../../docs/how-to/install-the-plugin-and-the-ci-action.md).

</details>

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
| Standing guidance | rules in `.claude/rules/`, `.agents/rules/` or `.opencode/rules/`, by harness | agents |

## What you get

- **The `kmctl` CLI** sets a repository up, creates new decisions, docs pages
  and other concepts with their index entries, checks that indexes and links
  agree, and lists what is due for review.
- **An APM package** for Claude Code, Antigravity and OpenCode, which
  [APM](https://microsoft.github.io/apm) installs: an audit agent, a skill
  for writing `docs/` pages, `/handoff` and `/continue` to save and resume
  work between sessions, and the knowledge rules, plus one SessionStart hook
  that prints the briefing. `kmctl plugin patch` adds the few pieces APM
  cannot install yet.
- **A GitHub Action** that runs `kmctl check` on every pull request for free,
  and an opt-in audit you run by hand or on a schedule.

## Quick start

### With an agent

Install kmctl's package for Claude Code as in [Claude Code](#claude-code),
then start a Claude Code session in the repository. The session opens with a `kmctl briefing`: where knowledge lives,
what is due for review and which skills to use. In a repository with no
`.okf/` yet, the briefing says so and points the agent at `kmctl init`. Until
the manifesto is written and `.okf/architecture/` has a page, the briefing
tells the agent to fill them in with you before any other work. Ask:

> Set this repository up with kmctl.

The agent runs `kmctl init`, which writes `docs/`, a starter `.okf/` bundle
and a `CLAUDE.md` block. Start a new session afterwards so the agent loads
the block. Then ask in plain words:

- "Fill in the manifesto from the code." The agent drafts
  `.okf/manifesto.md`: what the project is for, its invariants and values.
  The values are yours; check them.
- "Record that we store data in SQLite, and why." The agent runs
  `kmctl new decision`, which writes the front matter, index entry and log
  line; the agent writes the prose.
- "Write a how-to for backing up the database." The `write-docs` skill files
  it under `docs/how-to/` with `kmctl new doc`, which lists it in that
  folder's generated `README.md`.
- `/audit` reports knowledge that has drifted from the code. It changes
  nothing; you decide what to fix.
- "Which decisions since v0.13.0 never got a record?" The `decision-gaps`
  skill judges each change `kmctl decision candidates` lists and reports the
  ones that made a decision no record covers. It writes nothing; you decide
  which become records
  ([Find unrecorded decisions](../../docs/how-to/find-unrecorded-decisions.md)).
- `/handoff` at the end of a session saves where the work stands; `/continue`
  at the start of the next picks it up.

### By hand

```
kmctl init                       # docs/, a starter .okf/ bundle and a CLAUDE.md block
kmctl update                     # after upgrading kmctl: refresh the block
kmctl new decision 'Store data in SQLite' --description 'One SQLite file, no database server.'
kmctl new doc how-to 'Back up the database' --description 'Copy the SQLite file safely.'
kmctl check                      # indexes agree with their folders, links resolve
kmctl check --fix                # also rewrite the generated docs/ folder indexes
kmctl review due                 # what is unverified or stale
kmctl decision candidates        # changes since the newest decision, for the decision-gaps skill
kmctl verify manifesto --by human:you  # you read it and it holds: drop it from review due
```

`kmctl init` keeps files that already exist, except the kmctl block, which it
replaces with this release's, and `.gitattributes`, to which it adds only the
union merge lines for the `.okf/` log and indexes that it lacks;
`kmctl update` is the same command. The
knowledge rules come with kmctl's APM package. Every command takes `--help`,
and most take `--json` for scripts and agents. The
[tutorial](../../docs/tutorials/get-started-with-kmctl.md) walks through this in one
sitting.

To run `kmctl check` on every commit, add kmctl's `kmctl-check` hook to your
`.pre-commit-config.yaml`; `args: [--fix]` rewrites the folder indexes as you
commit:

```yaml
repos:
  - repo: https://github.com/JasperHG90/kmctl
    rev: vX.Y.Z  # the kmctl version you run; the hook needs a release after 0.3.0
    hooks:
      - id: kmctl-check
        args: [--fix]
```

## Works better with an adversarial reviewer

kmctl works better when an adversarial reviewer checks the agent's work
before you accept it. A second agent, starting fresh, reads the change
against what was asked, the repository's rules and its `.okf/` knowledge, and
catches what the first agent missed: a decision it never recorded, a diagram
it left stale, a test that proves nothing.

The copier template offers both: answer yes to `adversarial_review` (the
default). It writes the rule into `AGENTS.md` and, for Claude Code, adds the
agent to `apm.yml`.

In an existing repository, add
[`adversarial-reviewer`](https://github.com/JasperHG90/skills/blob/main/agents/adversarial-reviewer.agent.md)
and the rule that tells the agent to call it after each task to `apm.yml`:

```yaml
dependencies:
  apm:
    - jasperhg90/skills/agents/adversarial-reviewer.agent.md
    - jasperhg90/skills/rules/adversarial-reviews.instructions.md
```

Then run `apm install`. The agent lands in `.claude/agents/` and the rule
in `.claude/rules/`. Only Claude Code can load the agent APM installs;
without it, the rule has the agent use a general sub-agent.

## What it does not do

kmctl cannot force knowledge to stay true. An agent can read the briefing and
still forget to update a decision, and an audit can miss drift. kmctl makes
stale knowledge visible and cheap to find. It also stops at the edge of one
repository: sharing skills across repositories, searching across projects
and syncing to a central place are left to other tools. See
[Where kmctl fits in knowledge management](../../docs/explanation/where-kmctl-fits-in-knowledge-management.md).

## Documentation

The [docs index](../../docs/README.md) links each folder's index. The pages:

- Tutorial: [Get started with kmctl](../../docs/tutorials/get-started-with-kmctl.md)
- Tutorial: [Audit your repository with the agent](../../docs/tutorials/audit-your-repository-with-the-agent.md)
- How-to: [Install the plugin and the CI action](../../docs/how-to/install-the-plugin-and-the-ci-action.md)
- How-to: [Install kmctl with APM](../../docs/how-to/install-kmctl-with-apm.md)
- How-to: [Find unrecorded decisions](../../docs/how-to/find-unrecorded-decisions.md)
- Reference: [Commands](../../docs/reference/commands.md)
- Explanation: [Why one hook and report-only audits](../../docs/explanation/why-one-hook-and-report-only-audits.md)
- Explanation: [Where kmctl fits in knowledge management](../../docs/explanation/where-kmctl-fits-in-knowledge-management.md)
