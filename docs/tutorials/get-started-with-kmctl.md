---
description: "Set a repository up, record a first decision and check it, in one sitting."
---

# Get started with kmctl

## What you will build

A new repository with a `docs/` folder, an `.okf/` knowledge bundle with two
decision records in it, and a clean `kmctl check`. Along the way you will see
`kmctl check` catch a docs folder with no index, and `kmctl check --fix` write
it. It takes about ten minutes.

Every command in the steps below was run in a scratch folder with the kmctl
release this page ships with, and the output shown is what it printed.

## Before you start

- `git` and [uv](https://docs.astral.sh/uv/) on your PATH.
- kmctl installed:

  ```
  uv tool install git+https://github.com/JasperHG90/kmctl@v0.5.0
  ```

  The kmctl repository is private for now, so this needs a GitHub account
  with access to it; uv clones it with your git credentials.

  `kmctl --version` then prints `kmctl` followed by the version you
  installed.

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
created CLAUDE.md
created .okf/decisions/index.md
created .okf/decisions/0001-keep-project-knowledge-in-an-okf-bundle.md
Next: install kmctl's package with APM for the skills and the knowledge rules (the kmctl README's install section: an apm.yml entry, apm install, kmctl plugin patch), then fill the purpose and invariants in .okf/manifesto.md (its values are the operator's to write), then add a diagram page to .okf/architecture/ once there is code, then record each choice as you make it with kmctl new decision
```

`docs/README.md` is the index of the docs for people who use your project. It
links each docs folder, and each folder gets its own `README.md` listing its
pages, which kmctl writes.
`.okf/` is the knowledge bundle for people and agents working on it:
`index.md` is where a reader starts, `log.md` records each change, and
`manifesto.md` is where your project's design will go. You can write the
manifesto later; this tutorial leaves it as kmctl wrote it.

The rest is for an agent such as Claude Code working in the repository.
`CLAUDE.md` holds a block that says where each kind of knowledge lives and
what the agent should do as it works. The rules for writing knowledge come
with kmctl's skills in its APM package, the first step the `Next:` line
names; this tutorial does not need them. Decision 0001 records the first choice: keep the
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

When a record describes code, name that code with `--source`, for example
`--source src/db.py`, and `kmctl review due` lists the record once a commit
changes the file. Give anything that goes out of date on a known day a
`--stale-after`, such as `6m` or `2027-01-15`.

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
warning  index  docs/README.md  does not link how-to/; add '- [How-to guides](how-to/README.md)'
error  index  docs/how-to  folder has no README.md index; run kmctl check --fix
1 failed, 1 warning
```

The new folder has no index, so a reader would never find the page. kmctl
writes each folder's index from its pages, so let it:

```
kmctl check --fix
```

```
fixed docs/how-to/README.md
warning  index  docs/README.md  does not link how-to/; add '- [How-to guides](how-to/README.md)'
all checks passed, 1 warning
```

The check passes now. The warning is about `docs/README.md`, which is yours to
write: kmctl never changes it. Add the link it suggests:

```
echo '- [How-to guides](how-to/README.md)' >> docs/README.md
kmctl check
```

```
all checks passed
```

To add a page the right way, `kmctl new doc` writes it, its folder's index and
the folder's link in `docs/README.md` together.

## What you learned

- `kmctl init` sets up `docs/`, `.okf/` and a `CLAUDE.md` block, and keeps a
  file that is already there, apart from its block in `CLAUDE.md`. After
  upgrading kmctl, `kmctl update` refreshes the block.
- `kmctl new decision` writes the structure of a record (number, front matter,
  index entry, log line) and you write the prose.
- `kmctl check` fails when an index and its folder disagree, and
  `kmctl check --fix` writes the docs folder indexes for you.

Next:

- [Install the plugin and the CI action](../how-to/install-the-plugin-and-the-ci-action.md),
  so Claude Code gets a briefing at each session start and every pull request
  is checked.
- [Commands](../reference/commands.md) lists every command and option.
- [Why one hook and report-only audits](../explanation/why-one-hook-and-report-only-audits.md)
  explains how kmctl keeps knowledge current without blocking anyone.
