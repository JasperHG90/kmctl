---
type: decision
title: "ADR 0048: kmctl summary ack writes one file per ack, so branches merge without a conflict"
description: "kmctl summary ack writes a file with its own name under .okf/.acks/ and no longer the checked block in the summary, which every ack rewrote, so two branches that both acked always conflicted."
tags: [decision]
generated:
  by: process:kmctl/0.14.0
  at: 2026-11-19T09:07:20Z
status: stable
sources:
  - resource: "packages/kmctl/src/kmctl/summary.py"
  - resource: ".okf/prototypes/bookkeeping-merge-conflicts/"
---

# ADR 0048: kmctl summary ack writes one file per ack, so branches merge without a conflict

## Context

Before this decision, `kmctl summary ack` wrote a `checked` block into the
front matter of `.okf/summary.md` (ADR 0027):

```yaml
checked:
  at: 2026-11-19T08:12:43Z
  against:
    - decisions/0002-use-a-queue
```

The block has one job: it changes the file. kmctl decides whether the summary
is behind by looking at which commit last changed the summary, so any change
to the file clears it. No rule reads what the block says.

Every ack rewrites the same lines. When two branches both ack, git cannot
merge those lines, and the branch that merges second gets a conflict. Where
several people have pull requests open, this happens each time `main` moves:
every open pull request has to merge `main` and resolve the block again. A
user reported it on 2026-11-19, from a repository where about ten people work
on one bundle.

We measured it in that repository by replaying its merges ([Bookkeeping merge
conflicts](../prototypes/bookkeeping-merge-conflicts/README.md)):

- Of 45 pairs of open pull requests, 28 conflicted in `.okf/summary.md`. 26 of
  those 28 conflicted only in the `checked` block.
- A branch merged `main` into itself 66 times, and 14 of those merges
  conflicted in the summary. With the `checked` block merged by a script, 3
  were left. In those 3, two branches had rewritten the same sentence of the
  summary's text.

A git merge driver could merge the block in a local merge. It would not help
on the pull request page, because GitHub does not read a repository's
`.gitattributes` when it merges.

## Decision

`kmctl summary ack` writes one new file per ack and leaves the summary alone.

- **The file.** Its path is `.okf/.acks/TIME-DIGEST.yaml`, for example
  `.okf/.acks/20261119T081243Z-b7375c5d.yaml`. It holds what the block held:
  `at`, the UTC time to the second, and `against`, the ids of the concepts
  that had changed.
- **Every branch gets its own file name.** `TIME` is `at` without punctuation.
  `DIGEST` is the first eight characters of a SHA-256 hash of the `HEAD`
  commit and the ids. Two branches have a different `HEAD`, so they write two
  different files, and git merges two new files without a conflict.
- **An ack file clears the summary, as an edit to the summary does.** The
  summary is behind when a concept changed in a commit after the last commit
  that changed the summary or an ack file. An ack file that is not committed
  yet counts like an edit to the summary that is not committed yet. Nothing
  else in the rule of ADR 0027 changes.
- **Each ack deletes the ack files it finds.** On a branch without merges the
  folder then holds one file. After a merge it holds one file per merged
  branch, until the next ack.
- **kmctl stops writing `checked`.** The first ack with this change deletes
  the `checked` block from the summary. The summary's schema and invariant I4
  still allow the field, so a bundle that still has the block validates. For
  such a block, `kmctl check` still warns about an id that is not in the
  bundle, and `kmctl mv` still rewrites the ids.
- **The bundle checks do not see the folder.** `kmctl check` and the OKF
  validator skip a folder whose name starts with a dot, so neither treats
  `.acks` as a section of the bundle.
- **`--json` gains `file`.** `kmctl summary ack --json` also prints the path
  of the ack file, or null when it wrote nothing.

Rejected:

- **A git merge driver for the `checked` block.** Git does not read a driver's
  command from the repository, so every clone would have to register it by
  hand. GitHub would ignore it.
- **A trailer in the commit message.** `kmctl check` and the pre-commit hook
  run before the commit exists, so they could not see the trailer. A squash
  merge can also drop it.
- **One ack file with a fixed name.** Both branches would change the same file
  and conflict as before.
- **A random file name.** A digest is as unlikely to repeat. A digest is also
  the same for the same commit and the same ids, which a test can rely on.
- **Keeping every ack file.** Nothing reads an old ack. A busy bundle is acked
  several times a day, so the folder would only grow.
- **Asking for an ack less often.** The summary would be listed as behind most
  of the time, and people stop reading a warning that is always there.

## Consequences

- **Two branches that both ack merge without a conflict.** After the merge the
  folder holds both ack files, and kmctl reports the summary as current. Each
  branch checked the summary against its own changes.
- **One case goes unnoticed.** Branch A acks and then edits a decision without
  a second ack. Branch B acks too. After both are merged, kmctl reports the
  summary as current, although nobody read it against A's last edit. The merge
  commit joins the two ack files, so kmctl takes it as the newest ack, and A's
  edit is older than the merge commit. kmctl missed the same case before this
  decision, whenever a person resolved the conflict in `checked` by hand.
- **The upgrade causes one last conflict.** A branch that an older kmctl acked
  rewrites the `checked` block, and the first ack by the new kmctl deletes it.
  Git reports a conflict in the summary when the second of the two is merged,
  once.
- **`kmctl mv` leaves ack files alone.** After a rename, an ack file can still
  name the old id. No rule reads those ids, and the next ack deletes the file.
- **Two edits to the same text still conflict.** When two branches rewrite the
  same sentence of the summary, a person has to choose.
- **The log and the indexes still conflict.** Every change adds a line at the
  end of `.okf/log.md` and at the end of an index. This decision does not
  cover them.
