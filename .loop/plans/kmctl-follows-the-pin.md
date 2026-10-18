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
  reads `apm.lock.yaml` in the current directory. When it names kmctl's
  package (`kmctl_package` in `src/kmctl/plugin.py`) at a `resolved_ref`
  other than this CLI's `package_ref()`, kmctl replaces itself (exec) with
  `uvx --from git+https://github.com/JasperHG90/kmctl@<resolved_commit> kmctl
  ARGS`, with the same stdin, stdout, stderr and exit code, and
  `KMCTL_PINNED=1` set so the pinned copy runs as itself. No lock, no kmctl
  entry, a matching ref, `KMCTL_PINNED` set, or no `uvx` on PATH: kmctl runs
  as itself. `LockDependency` gains `resolved_commit`. A pinned release from
  before this one has no hand-off and needs none: only the copy on PATH
  hands off.
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
  one there is older than the pin (compared with `sort -V`), never
  downgrading, so a second project leaves a newer install alone and an
  install from before the hand-off is replaced by one that has it; then it runs
  `kmctl --version` in the project, so uv builds the pinned copy during
  bootstrap rather than at the first session start.
- **The briefing says when a release is newer than the pin.** `kmctl
  briefing` (`src/kmctl/briefing.py`), which every harness's session hook
  runs, adds one line when the newest kmctl release tag is newer than the
  pin: "kmctl vX.Y.Z is out; this project pins vA.B.C. Tell the user; `just
  upgrade vX.Y.Z` moves it." It reads the newest tag from a cache file in
  the user's cache folder; when the cache is older than a day or missing, it
  starts a detached `git ls-remote --tags` refresh and does not wait for it,
  so the line appears from the next session on and no session start waits
  on the network. A failed refresh leaves no line and no error. Pre-release
  tags are not counted. `KMCTL_NO_UPDATE_CHECK=1` turns the check off.
- **Tests.** The hand-off with a fake `uvx` on PATH that records its
  arguments and environment (exec, args, `KMCTL_PINNED`, the commit), each
  case where kmctl runs as itself, and the exit code passed back; an
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
