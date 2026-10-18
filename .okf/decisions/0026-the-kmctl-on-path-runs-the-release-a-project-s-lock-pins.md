---
type: decision
title: "ADR 0026: The kmctl on PATH runs the release a project's lock pins"
description: "Before any command, kmctl reads apm.lock.yaml and, when it pins another release, runs that release through uvx at the lock's commit with KMCTL_PINNED=1; the copy on PATH adds the briefing's newer-release line."
tags: [adr, decision, cli, release]
generated:
  by: process:kmctl/0.6.0
  at: 2026-10-18T19:13:06Z
status: stable
sources:
  - resource: "src/kmctl/pin.py"
  - resource: "src/kmctl/__init__.py"
  - resource: "starter/justfile.jinja"
  - resource: "action.yml"
---

# ADR 0026: The kmctl on PATH runs the release a project's lock pins

## Context

One `kmctl` sits on a user's PATH, but each repository pins its own kmctl
release: the package's `ref` in `apm.yml`, which `apm.lock.yaml` records
with the commit it resolved to. The hooks and skills call the `kmctl` on
PATH, and `kmctl doctor` fails `HARNESS.lock` when the CLI and the lock
differ (ADR 0001 ties the package tag to the CLI's version). The starter
template's `just kmctl` ran `uv tool install --force` at the pin, so with
three projects on three pins, which the operator runs, whichever was
bootstrapped last owned the PATH and the other two ran the wrong kmctl. The
operator also asked that kmctl say, when an agent is working, that a newer
release is out than the project uses.

Timed on 2026-10-18: `uvx --from git+https://github.com/JasperHG90/kmctl@COMMIT`
runs a cached kmctl in 160 to 180 ms, as fast as the `kmctl` on PATH, and
works with `--offline`; pinned by tag it takes 2.3 s, because uv asks
GitHub for the tag each time, and fails offline. With an empty cache the
first run takes 8.8 s even from a local clone, against the session hooks'
10 s (spike:kmctl-follows-the-pin/1); a cache miss with `--offline` fails in
about 60 ms without touching the network (spike:kmctl-follows-the-pin/4).

## Decision

Before any command, `main` finds the project, from `--path` or the current
folder, walking up to the first `apm.lock.yaml` and stopping at `.git`, so
Antigravity's hooks, which run in `.agents/`, find it. When the lock pins
kmctl at another release than this CLI's, kmctl runs `uvx --from
git+https://github.com/JasperHG90/kmctl@<resolved_commit> kmctl ARGS` as a
child with stdin, stdout and stderr inherited and `KMCTL_PINNED=1`, and
exits with its code. The pinned child runs as itself. It is a child, not
exec, so the exit code survives on Windows. Only the copy on PATH needs this
code: a pinned release from before it runs as it always did.

`kmctl briefing` runs from session hooks, so it hands off only to a cached
release: it probes `uvx --offline ... kmctl --version` first, and on a miss
gives the briefing itself with a line saying to run `just install`. The copy
on PATH, never the pinned child, adds the newer-release line, in the
briefing's own form (a last line, a `newer_release` key in `--json`, the end
of Antigravity's message), so projects pinned to older releases get it. The
newest release comes from a cache file a detached `git ls-remote` refreshes
once a day; the hook never waits for it (spike:kmctl-follows-the-pin/2).

The template's `just kmctl` installs kmctl only when none is on PATH or it
is older than the pin, then runs `kmctl --version` to fetch the pin. The CI
action sets `KMCTL_PINNED=1`, so it runs the kmctl of the tag it is used at.

Rejected:

- **Hooks and skills call `uvx ...@vX.Y.Z` by tag.** The tag is known at
  release time, but each call takes 2.3 s and fails offline, and an agent
  that types `kmctl check` still gets the PATH copy.
- **A per-folder PATH (mise, direnv, a project virtual environment).** It
  works only when the harness starts from a shell that has it switched on,
  which an IDE started from the desktop does not, and every user installs
  and sets up one more tool.
- **One newest kmctl that serves older packages.** It would loosen doctor's
  version check and have `kmctl plugin patch` write a newer release's files
  over an older package, and every release would have to stay backward
  compatible.

## Consequences

- Each kmctl command in a pinned project costs a second Python start-up,
  about 0.3 s; a shell launcher could save it if it ever matters.
- The first command after a pin changes builds that release, which takes
  seconds; `just install`, which runs `kmctl plugin patch` by tag through
  `uvx`, fills the same cache.
- Tests set `KMCTL_PINNED=1` for the whole suite (`tests/conftest.py`), so
  a fixture lock never sends kmctl to GitHub.
- The update check writes one file outside the repository,
  `kmctl/latest-release` in the user's cache folder; `KMCTL_NO_UPDATE_CHECK=1`
  turns it off.
