---
paths: ["src/kmctl/cli/**", "src/kmctl/commands/**", "tests/**/test_*cli*.py", "tests/**/test_*help*.py", "docs/reference/**"]
---

# The CLI interface

`loopctl` is read by agents more than by people, and an agent that cannot
tell from `--help` what a value should be will guess it. The design is
`.okf/architecture/cli-and-plugin.md`.

<constraint name="help-answers-before-anyone-guesses">
WHY: a wrong guess at an input costs a refusal and a retry, or worse, a run
that succeeds on the wrong value.

- The docstring is one line naming what the verb produces.
- Each input's help answers: why it is required, what it becomes, where the
  value comes from, and what is legal. A concrete example goes in `metavar`.
- Detail and worked examples go in the epilog. Examples never derive from
  each other.
- A group's help names its prerequisites and the verb that creates each.
- A help string used by several verbs is one shared constant.
</constraint>

<constraint name="every-success-names-the-next-step">
WHY: an agent that finishes a step and has to work out the next one from the
docs is where loops wander and burn tokens.

A state-changing verb ends with one `Next: loopctl ...` line taken from the
shared `next_step` function, never a hand-written string. Adding a stage or a
transition updates `next_step` in the same change (ST-10).
</constraint>

<constraint name="a-refusal-names-the-fix">
WHY: "invalid input" sends the reader back to guessing.

A refusal is one line on stderr naming what was refused, the value and where
it came from, and the exact command that fixes it. It raises the one
exception base, and the exit code follows the table in
`.okf/architecture/cli-and-plugin.md` (ST-04). stdout carries only results.
</constraint>

<constraint name="help-is-tested">
WHY: help text drifts the moment nobody checks it, and v1's command
reference fell 14 commands behind.

Changing a verb, option or help string keeps ST-09 green: each verb's help
names what it produces, every input has an example, help renders at 80
columns, and `--help` loads no command logic.
</constraint>
