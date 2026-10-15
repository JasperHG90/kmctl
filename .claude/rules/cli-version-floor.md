---
paths: ["plugin/**", "src/kmctl/**", "pyproject.toml", ".github/workflows/**"]
---

# The CLI installs the plugin

The plugin ships inside the `kmctl` release and is installed by it, so the
plugin and the CLI always match (ADR 0001). Its one hook never blocks
(ADR 0004, invariant I1 in `.okf/manifesto.md`).

<constraint name="the-plugin-is-installed-by-the-cli">
WHY: a plugin installed on its own leaves the CLI's presence and version
unknown to its hook and skills.

Docs and skills install the plugin only with `kmctl plugin install`. They
never tell a reader to install it from a marketplace by itself.
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
release that ships them. A change that makes the plugin use a new verb adds
the verb in the same change.
</constraint>
