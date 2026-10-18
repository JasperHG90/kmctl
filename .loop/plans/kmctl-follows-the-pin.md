---
type: plan
title: 'Plan: kmctl-follows-the-pin'
description: The kmctl on PATH runs the project's pinned kmctl through uv, just kmctl stops replacing it, and the briefing says when a newer release is out.
tags:
- plan
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T18:45:35+00:00'
slug: kmctl-follows-the-pin
epic: null
depends_on: []
priority: 1
---

# kmctl-follows-the-pin

Relayed from: none

## Intent

The operator (2026-10-18, ask j-20261018T184534+0000-5cbf86c6): "Just
bootstrap installs kmctl at a specific version, but if I have three projects
that all run at slightly different versions then it will install/uninstall
across projects", then "do your suggested fix", and "kmctl should complain if
a new version is out and the user is using an old version (when using agent
that is)".

Measured: the template's `kmctl` recipe (`starter/justfile.jinja`) runs
`uv tool install --force` at the project's pin, which replaces the one
`kmctl` on PATH, so of N projects on different pins, N-1 run a kmctl that
is not theirs. The hooks and skills call the `kmctl` on PATH
(`apm/antigravity/.apm/hooks/hooks.json`, `src/kmctl/opencode.py`'s plugin,
the skills' `kmctl check`), and `kmctl doctor` fails `HARNESS.lock` when the
CLI and the lock differ (`src/kmctl/doctor.py`, `_lock`). The operator runs
three such projects. Timed on this machine: `uvx --from
git+https://github.com/JasperHG90/kmctl@<commit> kmctl --version` takes 160
to 180 ms once uv has the commit cached, as much as the `kmctl` on PATH
(160 ms), and works with `--offline`; pinned by tag it takes 2.3 s, because
uv asks GitHub for the tag each time, and fails offline.

What changes:

- **The hand-off.** Before any command runs, `main` in `src/kmctl/__init__.py`
  finds the project: the `--path` value when the arguments carry one
  (`--path X` or `--path=X`), otherwise the current directory, then up from
  there to the first folder holding `apm.lock.yaml`, stopping at the first
  folder with `.git`. The walk up matters for Antigravity, whose hooks run in
  `.agents/` (`apm/antigravity/.apm/hooks/hooks.json`; the Stop hook starts
  with `cd ..`), and `--path` for `kmctl check --path ../other`. When that
  lock names kmctl's package (`kmctl_package` in `src/kmctl/plugin.py`) at a
  `resolved_ref` other than this CLI's `package_ref()`, kmctl runs `uvx
  --from git+https://github.com/JasperHG90/kmctl@<resolved_commit> kmctl
  ARGS` as a child, in the same directory, with stdin, stdout and stderr
  inherited (kmctl reads none of stdin, so Antigravity's hook JSON reaches
  the pinned briefing), `KMCTL_PINNED=1` set so the child runs as itself,
  and exits with the child's code. A child rather than exec: on Windows
  `os.execvp` starts a new process and the caller loses the exit code. No
  lock, no kmctl entry, a matching ref, no `resolved_commit`,
  `KMCTL_PINNED` set, or no `uvx` on PATH: kmctl runs as itself.
  `LockDependency` gains `resolved_commit`. A pinned release from before
  this one has no hand-off and needs none: only the copy on PATH hands off.
- **The CI action runs its own tag.** `action.yml` sets `KMCTL_PINNED=1`,
  so the action runs the kmctl of the tag it is used at, as today, and needs
  no access to fetch another.
- **The briefing never waits for a build.** The session hooks allow 10 s
  (`apm/claude/.apm/hooks/hooks.json`, `apm/antigravity/.apm/hooks/hooks.json`,
  `HOOK_TIMEOUT` for OpenCode), and with an empty uv cache the first
  commit-pinned run took 8.8 s from a local clone, more from GitHub
  (spike:kmctl-follows-the-pin/1). So for `kmctl briefing` the hand-off
  first probes `uvx --offline --from ...@COMMIT kmctl --version` (about
  200 ms when cached, 60 ms on a miss, no network either way): the exit code
  alone cannot tell a miss from the child failing, but a probe of
  `--version` fails only on a miss. When the probe passes, kmctl execs the
  briefing through `uvx --offline`; when it fails, kmctl gives the briefing
  itself and adds a line: "This project pins kmctl
  vA.B.C, which is not installed yet; run `just install` (or `uvx --from
  git+https://github.com/JasperHG90/kmctl@COMMIT kmctl --version`)." Other
  commands hand off as above and may build, since a person runs them.
  A tag-pinned run or `uv tool install`, which `just install` and `just
  kmctl` do, warms the commit-pinned copy (spike:kmctl-follows-the-pin/1).
- **just kmctl stops replacing it.** `starter/justfile.jinja`'s `kmctl`
  recipe installs the pinned kmctl only when no `kmctl` is on PATH or the
  one there is older than the pin (the `kmctl --version` output and the pin
  stripped to bare versions and compared with `packaging.version` through
  `uv run --no-project --with packaging`, which orders pre-releases right,
  unlike `sort -V`; `KMCTL_PINNED=1` so `--version` reports the copy on
  PATH, not the pin), never
  downgrading, so a second project leaves a newer install alone and an
  install from before the hand-off is replaced by one that has it; then it runs
  `kmctl --version` in the project, so uv builds the pinned copy during
  bootstrap rather than at the first session start.
- **The briefing says when a release is newer than the pin, from the copy
  on PATH.** The line has to reach projects pinned to releases from before
  this one, whose own briefing has no such check, so the outer kmctl (the
  one with `KMCTL_PINNED` unset) adds it, never the pinned child. For
  `briefing` it captures the child's stdout and adds the line in the
  output's own form: text, a last line; `--json`, a `newer_release` key
  (`{"latest": "vX.Y.Z", "pinned": "vA.B.C"}`) added to the object;
  `--format antigravity`, appended to the systemMessage text. When it runs as
  itself, it adds the line the same way. The line: "kmctl vX.Y.Z is out;
  this project pins vA.B.C. Tell the user; `just upgrade vX.Y.Z` moves it."
  The newest tag comes from a cache file in the user's cache folder; when
  the cache is older than a day or missing, kmctl starts a detached `git
  ls-remote --tags https://github.com/JasperHG90/kmctl` refresh (stdio
  closed, its own session) and does not wait for it, so the line appears
  from the next session on and no session start waits on the network
  (spike:kmctl-follows-the-pin/2: Claude Code neither waits for nor kills
  the child). A failed refresh leaves the cache and the briefing as they
  were. Pre-release tags are not counted. `KMCTL_NO_UPDATE_CHECK=1` turns
  the check off.
- **Tests.** The hand-off with a fake `uvx` on PATH that records its
  arguments, directory, stdin and environment (args, `KMCTL_PINNED`, the
  commit), each case where kmctl runs as itself, the exit code passed back,
  the walk up from `.agents/` with hook JSON on stdin reaching the child,
  and `--path` choosing the pin; the newer-release line added by the outer
  copy in each format, over a fake pinned child's output as an old release
  prints it; an
  integration test that hands off to this tree's commit through a real
  `uvx` with git rewriting GitHub's URL, as `tests/test_starter.py` does;
  the briefing line from a seeded cache (newer, same, older, pre-release,
  stale cache starts a refresh without waiting, refresh failure). The suite
  sets `KMCTL_PINNED=1` for tests whose fixture locks name other refs, so no
  test reaches GitHub by accident.
- **Docs.** The install how-to and README say the `kmctl` on PATH runs each
  project's pinned kmctl, and what the briefing line means; a decision
  records the hand-off and the alternatives rejected (hooks calling uvx by
  tag, per-directory PATH tools, a newest CLI that serves older packages).

Done when: in a project whose lock pins another release, `kmctl ARGS` runs
that release through uvx with the args, streams and exit code intact; the
template's bootstrap no longer replaces an existing kmctl; and the briefing
names a newer release from the cache without waiting on the network.

Out of scope: a shell launcher to save the second Python start-up (about
0.3 s a command); user-scope installs (`~/.apm`).

## Could invalidate this plan

- `uvx --offline` with no cached copy of the pinned commit may hang, try the
  network, or fail slowly, or may fail in a way kmctl cannot tell from the
  pinned briefing failing, so the briefing's offline hand-off would not stay
  inside the hooks' 10 s. spike:kmctl-follows-the-pin/4 (a miss fails in
  about 60 ms with no connects; cold and warm timings and the tag warm-up:
  spike:kmctl-follows-the-pin/1; warm probe and exit codes:
  spike:kmctl-follows-the-pin/3)
- A detached refresh started from a session hook may hold the hook's stdout
  open or be killed with the hook, so Claude Code waits for it or the cache
  never fills. spike:kmctl-follows-the-pin/2
