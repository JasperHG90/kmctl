---
paths: ["apm/**", "src/kmctl/**", "pyproject.toml", ".github/workflows/**"]
---

# The package matches the CLI

kmctl's skills, audit agent and knowledge rules ship in its APM package,
`apm/`. The user adds its `apm.yml` entry at the tag of the CLI's own
version, `ref: v<cli version>`, runs `apm install`, then `kmctl plugin patch`,
so the package and the CLI match (ADR 0001, ADR 0014, ADR 0021). Neither
of the two hooks kmctl's package ships, the SessionStart briefing and the
PostToolUse summary nudge, ever blocks (ADR 0028, invariant I1 in
`.okf/manifesto.md`).

<constraint name="the-package-is-installed-at-the-cli-tag">
WHY: a package at another tag than the CLI calls verbs the CLI may lack,
and an install without `kmctl plugin patch` leaves Antigravity without its
agents and with a Stop hook that fails.

Docs and skills install the package only with the `apm.yml` entry
`{git, path: apm, ref: v<cli version>}`, `apm install`, then
`kmctl plugin patch`, as the README's install section gives them.
</constraint>

<constraint name="the-hook-survives-a-missing-cli">
WHY: a hook that fails on a missing `kmctl` breaks every session start, or
every tool call, without telling the user why.

Each hook command checks that `kmctl` is on PATH before calling it. When it
is missing or fails, the SessionStart hook prints how to install or upgrade
`kmctl`, the PostToolUse nudge prints `{}`, and both exit 0.
</constraint>

<constraint name="skills-name-only-shipped-verbs">
WHY: a skill that calls a verb the user's CLI lacks fails mid-task, after
the agent has already done work.

Every `kmctl` verb and option a skill or the hook names exists in the
release that ships them. A change that makes a skill use a new verb adds
the verb in the same change.
</constraint>
