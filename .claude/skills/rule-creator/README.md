# rule-creator

Creates a **rule** — a short, always-on guidance file that gets injected into an
agent's context to enforce or nudge a standing behavior. It's the sibling of
[`skill-creator`](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
and [`agent-creator`](../agent-creator/README.md), adapted to the physics of a
rule: unlike a skill (a procedure you invoke) or an agent (a worker you delegate
to), a rule is simply *present*, steering work as it happens — so it must be
terse and earn the context it costs on every turn.

## What it does

Given an intent like *"add a rule that every change ships with a test"* or
*"stop reformatting files I didn't touch,"* the skill:

1. **Checks fit** — confirms a rule is the right artifact (not a skill, agent,
   `CLAUDE.md` fact, or `settings.json` change) using a quick decision table.
2. **Asks interactive follow-ups** — via `AskUserQuestion`: is it file-scoped
   (to derive a `paths` glob), enforce-hard or a nudge, and where to save it. It
   scans existing rules for overlap first and offers to extend a near-match
   rather than add a competing rule.
3. **Writes the file** — always with at least `name` and `description`
   frontmatter (plus `paths` when scoped), a kebab-case filename, and a terse
   body in the repo's voice.
4. **Self-reviews** against a quality bar (earns its rent, scoped tightly, no
   overlap, terse, explains why).

## Where rules live

| Location | What it is | When to use |
|---|---|---|
| `rules/` (this repo) | A shared, version-controlled library of rules | Default — shareable and reviewable; copy into `.claude/rules/` when adopted |
| `.claude/rules/` (a project) | Rules Claude Code loads for that project now | When you want the rule active immediately in the current project |
| `~/.claude/rules/` (global) | Personal rules across all your projects | Personal standing preferences (not written by this skill by default) |

`.claude/rules/*.md` is injected by Claude Code directly — the **body** is what
the agent reads, so all load-bearing guidance goes there. The top-level `rules/`
directory is a catalog; nothing auto-loads it.

## Rule frontmatter

```yaml
---
name: python-testing           # required — kebab-case, matches the filename
description: How to write and run tests. Read before changing Python code.  # required
paths: ["**/*.py"]             # optional — scopes the rule to matching files
---
```

- **`name`** / **`description`** are always written. `description` is a
  human-facing summary plus a "when to read" hint — not a trigger.
- **`paths`** is an optional glob array that path-aware harnesses use to keep a
  rule out of context on unrelated edits. Omit it for genuinely global rules.
- Some legacy rules are keyed on `title` instead of `name`; new rules
  standardize on `name` (matching skills and agents) and legacy files are left
  untouched.

## Usage

Invoke the skill and describe the behavior you want to standardize:

> "Create a rule that we always install deps with `uv add`, not `uv pip`."

The skill will confirm it's rule-shaped, ask whether it's Python-scoped and
enforce-hard vs a nudge, check for an existing rule that already covers it, then
write and self-review the file. See existing rules for the two body shapes it
proposes between: `rules/uv-installer.md` (a single directive) and
`rules/python-testing.md` (a hard core marked with `<constraint>` blocks amid
explanatory prose).

## Prerequisites

- The interactive follow-ups use the `AskUserQuestion` tool. Without it, the
  skill drafts with inferred answers and asks you to correct them in one pass.

## Validating

The produced rule is a Markdown file with YAML frontmatter. Confirm the
frontmatter parses, the filename matches `name`, and — if saved to
`.claude/rules/` — that the body carries the guidance you intend, since that's
what gets injected.
