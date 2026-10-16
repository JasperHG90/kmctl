---
paths: ["apm/**", "src/kmctl/**", "pyproject.toml", ".github/workflows/**"]
---

# The CLI installs its package

kmctl's skills, audit agent and knowledge rules ship in its APM package,
`apm/`, and `kmctl plugin install` installs that package at the tag of the
CLI's own version, so the package and the CLI always match (ADR 0001,
ADR 0014). The one hook kmctl writes never blocks (ADR 0004, invariant I1 in
`.okf/manifesto.md`).

<constraint name="the-package-is-installed-by-the-cli">
WHY: a package installed on its own leaves the CLI's presence and version
unknown to its skills, and brings no session hook.

Docs and skills install the package only with `kmctl plugin install`. The
one exception is the APM how-to, which says what a hand-added APM entry
leaves out and how to get it.
</constraint>

<constraint name="the-hook-survives-a-missing-cli">
WHY: a SessionStart hook that fails on a missing `kmctl` breaks every
session start without telling the user why.

The hook command checks that `kmctl` is on PATH before calling it. When it
is missing or fails, the hook prints how to install or upgrade `kmctl` and
exits 0.
</constraint>

<constraint name="skills-name-only-shipped-verbs">
WHY: a skill that calls a verb the user's CLI lacks fails mid-task, after
the agent has already done work.

Every `kmctl` verb and option a skill or the hook names exists in the
release that ships them. A change that makes a skill use a new verb adds
the verb in the same change.
</constraint>
