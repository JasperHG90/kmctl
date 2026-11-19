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

`kmctl summary ack` wrote `checked: {at, against}` into the front matter of
`.okf/summary.md` (ADR 0027). That is an edit to the summary, so the
commit-order rule cleared it with no special case, and no rule reads
`checked` itself.

Every ack rewrites the same block. Two branches that both touch a concept
both ack, so they change the same lines, and the second one to merge
conflicts. On 2026-11-19 a user reported this from a repository where about
ten people open pull requests against one bundle: each time `main` moved,
every open pull request had to merge `main` and resolve the block again.

Measured there by replaying merges
([Bookkeeping merge conflicts](../prototypes/bookkeeping-merge-conflicts/README.md)):

- A branch merged `main` into itself 66 times. 14 of those merges conflicted
  in `.okf/summary.md`. With the `checked` block merged by a script, 3 still
  conflicted, each because two branches rewrote one sentence of the text.
- 28 of the 45 pairs of open pull requests conflicted in `.okf/summary.md`,
  and 26 of the 28 only in the `checked` block.

GitHub does not read a repository's `.gitattributes` when it merges, so a
merge driver for the block would help a local merge and leave the pull
request marked as conflicting.

## Decision

- **One ack, one file.** `kmctl summary ack` writes
  `.okf/.acks/TIME-DIGEST.yaml`, which holds `at` (the UTC time to the
  second) and `against` (the ids of the concepts that had changed and are
  still in the bundle). `TIME` is `at` without punctuation, and `DIGEST` is
  the first eight characters of the SHA-256 of `HEAD` and those ids. Two
  branches have a different `HEAD`, so they write different files and
  change no common bytes.
- **An ack file counts as the summary.** The summary is behind when a
  concept changed in a commit after the last commit that changed the summary
  or an ack file, or is changed in the working tree while neither is. The
  rest of the rule in ADR 0027 holds.
- **An ack replaces the ack files before it.** It removes the ack files that
  were there, so the folder holds one file after a linear history and one
  per merged branch after a merge, until the next ack.
- **`checked` is no longer written.** The first ack removes a `checked`
  block from the summary's front matter. The field stays in the summary's
  schema and in invariant I4, so a bundle that still has it validates.
  `kmctl check` still warns about an id in it that is not in the bundle, and
  `kmctl mv` still rewrites it.
- **The folder's name starts with a dot.** `kmctl check` and the OKF
  validator read sections and concepts, and skip a folder whose name starts
  with a dot.
- `kmctl summary ack --json` gains `file`, the ack file's path, null when
  nothing was written.

Rejected:

- **A merge driver for the `checked` block.** Git does not read a driver's
  command from the repository, so every clone would have to register it, and
  GitHub ignores it.
- **A trailer in the commit message.** `kmctl check` and the pre-commit hook
  run before the commit exists, so they could not see it, and a squash merge
  can drop a trailer.
- **One ack file with a fixed name.** Two branches would both change that
  file, which is the conflict this decision removes.
- **A random name.** A digest of `HEAD` and the ids is as unlikely to clash,
  and the same ack on the same commit writes the same file.
- **Keeping every ack file.** Nothing reads an old ack, and a busy bundle
  is acked several times a day, so the folder would only grow.
- **Asking for an ack less often.** The summary would be listed as behind
  most of the time, and a list that is always there is not read.

## Consequences

- Two branches that both ack merge without a conflict in the summary. The
  merge commit differs from both parents under `.okf/.acks/`, so it counts
  as the last change, and the summary is current after the merge. Each side
  vouched for its own concepts.
- A concept that changed on a branch after that branch's ack is not listed
  after such a merge, because the merge commit is newer. A merge whose
  conflict in `checked` was resolved by hand had the same gap.
- The first ack after the upgrade deletes the `checked` block. A branch that
  an older kmctl acked rewrites that block, so the two conflict once, when
  the second is merged.
- `kmctl mv` does not rewrite the ids in an ack file. No rule reads them,
  and the next ack removes the file.
- The summary conflicts that remain are two edits to the same text, which a
  person has to settle.
- `.okf/log.md` and the index files still conflict, for the same reason:
  every change adds a line at their end. They are not part of this decision.
