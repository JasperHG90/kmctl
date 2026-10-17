---
name: write-docs
description: Write one page in a repository's docs/ for the people who use the project, filed by Diataxis type (tutorial, how-to, reference or explanation). Use this whenever someone asks to document a feature, write a guide, a getting-started walkthrough, a how-to, a CLI or config reference, or a page explaining why something works the way it does, in a repository with a docs/ folder or a kmctl set-up. Not for decisions, design notes, spikes or handoffs; those go in .okf/.
---

# Write a docs/ page

`docs/` is for people who use the project. Each page has one job, named by its
Diataxis type, and lives in that type's folder. kmctl writes the structure (the
folder, the page's front matter and skeleton, the folder's `README.md` index and
the folder's link in `docs/README.md`); you write the prose.

## 1. Check this belongs in docs/

A decision, a proposal, a design note, a spike's results or a handoff is not a
docs/ page. Those go in `.okf/` with `kmctl new decision|proposal|prototype|handoff`.
A page about a feature that does not exist yet waits until the feature does.

## 2. Pick the type from what the reader is trying to do

| The reader wants to | Type | Read |
|---|---|---|
| learn, by doing something that works in one sitting | `tutorial` | `references/tutorial.md` |
| get one task done, and already knows the basics | `how-to` | `references/how-to.md` |
| look up a fact: a command, an option, a config key | `reference` | `references/reference.md` |
| understand why it is shaped this way | `explanation` | `references/explanation.md` |

If a request mixes two of these ("explain how auth works and show how to set it
up"), it is two pages. Write the one asked for most and offer the other. Read the
reference file for the type you picked before writing.

## 3. Create the page with kmctl

```
kmctl new doc TYPE 'Title' --description 'One line for the index.'
```

It prints the path it wrote. It refuses when `docs/README.md` is missing (run
`kmctl init` first) or the page already exists (pick another title, or edit the
existing page instead). Do not create the file, the folder or the index entry
yourself: kmctl's format is what `kmctl check` reads.

The page starts with front matter: `description` (its index entry), a
`stale_after` three months ahead and an empty `sources`. List in `sources` the
files the page describes (`- src/cli.py`), so `kmctl review due` flags the page
when they change. Never add `verified` yourself, and never edit a folder's
`README.md` index: it is generated. If you change a page's title or
description, run `kmctl check --fix` to write the index again.

## 4. Write the prose

Fill in the sections of the skeleton kmctl wrote, following the reference file.
Read the code, `--help` output or config the page describes, so every command
and value on the page is real. Run the commands the page tells a reader to run,
in a scratch copy, and paste what they really print. Keep the title; change
headings only when the content needs it.

Never guess a fact you cannot find in the repository, such as an install URL, a
package name or a version. A reader follows the page literally, so a guessed
command fails them at that step. Look for it (README, `pyproject.toml`, plugin
manifests, hook messages); if it is not there, ask the user, or write
`TODO: <what is missing>` in its place and name it in your report.

## 5. Check and report

Run `kmctl check` (`kmctl check --fix` when it says a folder index is out of
date). It must pass. Report the path of the page and its type in one
line, and name any second page the request suggested.
