---
paths: ["plugin/**", "src/kmctl/hooks/**", "src/kmctl/cli/**", "pyproject.toml", ".github/workflows/**"]
---

# The CLI version floor

The plugin is only as safe as the CLI its hooks call. v1 discovered a missing
or old CLI after the fact. v2 installs the plugin through the CLI and makes
the plugin declare the oldest CLI it works with. The design is
`.okf/architecture/cli-and-plugin.md`.

<constraint name="the-plugin-is-installed-by-the-cli">
WHY: a plugin installed on its own leaves the CLI's presence and version
unknown to every hook.

Docs and skills install the plugin only with `loopctl plugin install`. They
never instruct a marketplace install of the plugin by itself.
</constraint>

<constraint name="the-floor-covers-every-verb-the-plugin-uses">
WHY: a skill that calls a verb the user's CLI lacks fails mid-task, after
the agent has already done work.

The plugin's `min-cli-version` names the oldest CLI release that has every
`loopctl` verb and option named in a skill, agent prompt or hook entry. A
change that makes the payload use a new verb or option raises the floor in
the same change. ST-11 fails when the floor is too low, and a release with a
floor that is too low is refused.
</constraint>

<constraint name="below-the-floor-gating-refuses">
WHY: a gate that cannot evaluate its policy must not silently allow (V17).

Every hook command starts with the preflight prelude
(`.okf/architecture/cli-and-plugin.md`), because a hook that simply calls a
missing `loopctl` fails open. When the CLI is absent, below the plugin's
floor, or no longer serves the entry, gating entries exit 2 with the install,
upgrade or `loopctl plugin update` command, and advisory entries print it and
exit 0. RC-24 drives the real hook command strings from the manifest.
</constraint>

<constraint name="the-cli-declares-the-oldest-plugin-it-serves">
WHY: upgrading the CLI without updating the plugin leaves hooks calling
entries that may have changed.

The CLI declares the oldest plugin release it serves. Renaming or removing a
hook entry raises that floor in the same change. The probe refuses an entry
the CLI does not serve, and SessionStart warns when the plugin is older than
the floor.
</constraint>
