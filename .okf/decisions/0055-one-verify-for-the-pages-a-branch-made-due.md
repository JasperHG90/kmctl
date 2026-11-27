---
type: decision
title: "ADR 0055: One verify for the pages a branch made due"
description: "kmctl review due --base lists what a branch made due, and kmctl verify takes several ids and writes nothing if one is refused."
tags: [decision]
generated:
  by: process:kmctl/0.16.1
  at: 2026-11-26T08:25:25Z
status: stable
sources:
  - resource: "packages/kmctl/src/kmctl/review_due.py"
  - resource: "packages/kmctl/src/kmctl/verify.py"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0055: One verify for the pages a branch made due

## Context

Before review, the author needs the pages their change made due, and the
reviewer verifies the ones they read. `kmctl review due` lists every page
that is due, whatever change made it due. In a repository that used kmctl,
it listed 48 pages, and that repository wrote its own script to keep only
the pages a branch made due. `kmctl verify` took one id, so a reviewer who
read 10 pages ran it 10 times, each with the full id and `--by`.

## Decision

- `kmctl review due --base REF` lists only what the branch made due since
  it split from `REF`, by the files `git diff REF...HEAD` names. It keeps a
  `source changed` reason for a source the branch changed, any other reason
  for a page the branch added or edited, and the summary when the branch
  changed a concept the summary's reason names. A `REF` git cannot compare
  with `HEAD` exits 2.
- `kmctl verify ID ID ... --by human:<id>` verifies several pages in one
  command. Every id is checked before any file is written, so one refused id
  writes nothing. An id given twice is verified once. With `--json`, it
  prints one object per id, one per line, so the output for one id is the
  same as before.
- kmctl's CI action shows the `--base` list in the job summary of a pull
  request.

We rejected two other ways:

- **An interactive picker, `kmctl verify --pick`.** A reviewer usually tells
  an agent which pages they read, and an agent cannot use a picker. Several
  ids work the same in a terminal and for an agent.
- **`kmctl verify --base origin/main` verifies everything the branch made
  due.** It would record checks for pages nobody named. Only a person
  verifies, page by page
  ([ADR 0023](0023-kmctl-verify-records-a-person-s-check.md)).

## Consequences

- A project's own script that filters `kmctl review due` by a branch can be
  replaced by `kmctl review due --base origin/main`.
- `verify()` stays for one id. `verify_all()` takes a list.
- The knowledge rules name both commands, so the okf-bundle hash in
  `OLD_RULES` in `packages/kmctl/tests/test_apm_package.py` moved, with its
  comment naming this record.

## Correction, 2026-11-27

`kmctl verify` also takes a folder, such as `decisions`, for every page
under it that `kmctl review due` lists, and a repository-root path with
`.md`. Why that does not undo the `--base` rejection above is in
[ADR 0059](0059-kmctl-verify-takes-a-folder-id.md).
