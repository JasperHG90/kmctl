---
paths: ["src/kmctl/**", "tests/**/test_*cli*.py", "tests/**/test_*help*.py", "docs/reference/**"]
---

# The CLI interface

`kmctl` is read by agents more than by people, and an agent that cannot
tell from `--help` what a value should be will guess it. Its audiences are
named in `.claude/rules/interface-audience.md`.

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
docs is where sessions wander and burn tokens.

A verb that writes files ends with one `Next: kmctl ...` line naming the
step that usually follows, built by one shared function rather than a
hand-written string in each verb.
</constraint>

<constraint name="a-refusal-names-the-fix">
WHY: "invalid input" sends the reader back to guessing.

A refusal is one line on stderr naming what was refused, the value and where
it came from, and the exact command that fixes it. It raises the one
exception base and exits nonzero. stdout carries only results, and every
verb that prints results takes `--json` for scripts and the CI action.
</constraint>

<constraint name="help-is-tested">
WHY: help text drifts the moment nobody checks it.

Changing a verb, option or help string keeps the help tests green: each
verb's help names what it produces, every input has an example, help renders
at 80 columns, and `--help` loads no command logic.
</constraint>
