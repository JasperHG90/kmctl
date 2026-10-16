---
paths: ["apm/.apm/skills/**", "apm/.apm/agents/**"]
---

# Skills are thin

A skill that validates, explains and sequences what the CLI could do itself
grows long, is read on every run, and drifts from the code that enforces the
same rules. The manifesto puts it in one line: skills route; `kmctl` decides
and writes (`.okf/manifesto.md`).

<constraint name="skills-route-the-cli-decides">
WHY: logic in a prompt is untested, re-read on every run, and drifts from the
code.

A skill routes and sequences: settle the inputs only the user can decide,
run the verb, quote the CLI's result and its `Next:` line, map exit codes to
actions, and name the sibling skill for other tasks. A skill never writes
front matter or an index entry itself, never validates a schema, and never
restates a rule the CLI enforces. A review finding that a skill does any of
these is fixed by moving the logic into the CLI.
</constraint>

<constraint name="skills-name-only-real-verbs">
WHY: a skill naming a verb or flag that does not exist teaches the agent to
invent one.

Every `kmctl` command in a skill exists in the CLI that ships with the
package (`.claude/rules/cli-version-floor.md`).
</constraint>
