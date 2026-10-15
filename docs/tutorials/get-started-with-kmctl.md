# Get started with kmctl

## What you will build

A new repository with a `docs/` folder, an `.okf/` knowledge bundle with two
decision records in it, and a clean `kmctl check`. Along the way you will see
`kmctl check` catch a page that is missing from the docs index. It takes about
ten minutes.

Every command in the steps below was run in a scratch folder with kmctl 0.1.0,
and the output shown is what it printed.

## Before you start

- `git` and [uv](https://docs.astral.sh/uv/) on your PATH.
- kmctl installed:

  ```
  uv tool install git+https://github.com/JasperHG90/Knowledge-management
  ```

  The kmctl repository is private for now, so this needs a GitHub account
  with access to it; uv clones it with your git credentials.

  `kmctl --version` then prints:

  ```
  kmctl 0.1.0
  ```

You do not need Claude Code or the plugin for this tutorial.

## Steps

### 1. Make a repository

```
mkdir my-project
cd my-project
git init
```

Git prints `Initialized empty Git repository in` and the path of the new
`.git/` folder.

### 2. Set it up with kmctl

```
kmctl init
```

You should see:

```
created docs/README.md
created .okf/index.md
created .okf/log.md
created .okf/manifesto.md
created .claude/rules/okf-bundle.md
created .claude/rules/docs-layout.md
created .claude/rules/diagrams-stay-current.md
created .claude/rules/manifesto-invariants.md
created CLAUDE.md
created .okf/decisions/index.md
created .okf/decisions/0001-keep-project-knowledge-in-an-okf-bundle.md
Next: fill the purpose and invariants in .okf/manifesto.md (its values are the operator's to write), then add a diagram page to .okf/architecture/ once there is code, then record each choice as you make it with kmctl new decision
```

`docs/README.md` is the index of pages for people who use your project.
`.okf/` is the knowledge bundle for people and agents working on it:
`index.md` is where a reader starts, `log.md` records each change, and
`manifesto.md` is where your project's design will go. You can write the
manifesto later; this tutorial leaves it as kmctl wrote it.

The rest is for an agent such as Claude Code working in the repository. The
files in `.claude/rules/` are the rules for writing knowledge. `CLAUDE.md`
holds a block that says where each kind of knowledge lives and what the agent
should do as it works. Decision 0001 records the first choice: keep the
project's knowledge in `.okf/`.

### 3. Check it

```
kmctl check
```

You should see:

```
all checks passed
```

### 4. Record a decision

```
kmctl new decision 'Store data in SQLite' --description 'The app keeps its data in one SQLite file, not a database server.'
```

You should see:

```
created .okf/decisions/0002-store-data-in-sqlite.md
Next: write the sections of .okf/decisions/0002-store-data-in-sqlite.md, then kmctl check
```

kmctl numbered the record after decision 0001, listed it in
`.okf/decisions/index.md`, and added a line to `.okf/log.md`. The record has front matter and three empty
sections:

```
## Context

## Decision

## Consequences
```

### 5. Write the decision

Open `.okf/decisions/0002-store-data-in-sqlite.md` and fill in the three
sections under the front matter, for example:

```
## Context

The app runs on one machine and has one user at a time.

## Decision

Keep all data in one SQLite file next to the app. We rejected PostgreSQL:
it needs a server to install and run, which this app does not need.

## Consequences

Backups are a file copy. If the app ever needs many writers at once, this
decision has to be revisited.
```

Leave the front matter as it is.

### 6. Check again

```
kmctl check
```

You should see:

```
all checks passed
```

### 7. See the check catch a mistake

Add a docs page by hand, without kmctl:

```
mkdir -p docs/how-to
echo '# Deploy the app' > docs/how-to/deploy.md
kmctl check
```

This time the check fails and exits 1:

```
error  index  docs/how-to/deploy.md  not listed in docs/README.md
1 failed
```

The page is not in `docs/README.md`, so a reader of the index would never find
it. Remove it and the check passes again:

```
rm docs/how-to/deploy.md
kmctl check
```

```
all checks passed
```

To add a page the right way, `kmctl new doc` writes it and its index entry
together.

## What you learned

- `kmctl init` sets up `docs/`, `.okf/`, the knowledge rules and a
  `CLAUDE.md` block, and keeps a file that is already there, apart from its
  block in `CLAUDE.md`.
- `kmctl new decision` writes the structure of a record (number, front matter,
  index entry, log line) and you write the prose.
- `kmctl check` fails when an index and its folder disagree.

Next:

- [Install the plugin and the CI action](../how-to/install-the-plugin-and-the-ci-action.md),
  so Claude Code gets a briefing at each session start and every pull request
  is checked.
- [Commands](../reference/commands.md) lists every command and option.
- [Why one hook and report-only audits](../explanation/why-one-hook-and-report-only-audits.md)
  explains how kmctl keeps knowledge current without blocking anyone.
