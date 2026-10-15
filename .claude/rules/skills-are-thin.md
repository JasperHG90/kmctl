---
paths: ["plugin/skills/**", "plugin/agents/**"]
---

# Skills are thin

v1's `create-ticket` skill grew to 643 lines because it validated, explained
and sequenced what the CLI could have done itself. A prompt that long is
read on every run, and the rules in it drift from the code that enforces
them. The design is `.okf/architecture/cli-and-plugin.md`.

<constraint name="skills-route-the-cli-decides">
WHY: logic in a prompt is untested, re-read on every run, and drifts from the
code.

A skill routes and sequences: preflight, settle the inputs only the operator
can decide, run the verb, quote the CLI's result and its `Next:` line, map
exit codes to actions, and name the sibling skill for other tasks. A skill
never parses or writes a state file, never validates a schema, and never
restates a rule the CLI enforces. A review finding that a skill does any of
these is fixed by moving the logic into the CLI.
</constraint>

<constraint name="skills-name-only-real-verbs">
WHY: a skill naming a verb or flag that does not exist teaches the agent to
invent one.

Every `loopctl` command in a skill exists in the CLI at the plugin's
`min-cli-version` (ST-11, `.claude/rules/cli-version-floor.md`).
</constraint>
