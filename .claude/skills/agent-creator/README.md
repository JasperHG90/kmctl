# /agent-creator

A Claude Code skill for designing well-engineered **subagents** — the `.md`
agent definitions spawned via the Agent/Task tool — and improving them through a
test/iterate loop. It is the sibling of `skill-creator`: same draft → test →
review → improve → tune-the-trigger rhythm, but every step is adapted to what
makes a subagent different from a skill or from inline work.

## When to use it

- "I want an agent that does X" — design one from scratch.
- "Here's a draft agent, make it better" — review and iterate.
- "My agent never gets called / fires on the wrong things" — tune its trigger.

**Not** for creating a skill (use `skill-creator`), orchestrating a multi-agent
build (use `dev-team`), a throwaway one-off Agent prompt, or a Workflow script.

## The two flavors it handles

| | **Registered subagent** | **Skill-bundled (body-only)** |
|---|---|---|
| File | full YAML frontmatter + body | body only, no frontmatter |
| Lives in | `agents/` or `~/.claude/agents/` | `<skill>/agents/foo.md` |
| Triggered by | its own `description` | the parent skill's spawn block |
| Tools limited by | its `tools:` allowlist | whatever the parent grants |

The design discipline is shared; only the frontmatter and where triggering lives
differ. The skill routes the work accordingly.

## What "well-designed" means here

The skill is organized around the physics of subagents, not a generic checklist:

1. **Should it exist at all?** — isolation has a cost; sometimes keep work inline
   or make it a skill.
2. **Single responsibility** — one nameable job.
3. **Prompt/body split** — static body vs. context the parent injects at spawn.
4. **Output contract** — the return value is data for the caller; summarise,
   don't dump.
5. **Tool allowlist** — least privilege, enforced by the harness.
6. **Parallelism & isolation** — idempotency/worktrees for concurrent writers;
   no mid-run user questions; one-level nesting.
7. **Trigger** (registered only) — a description that delegates correctly.

## Prerequisites

- The **design phase** (capture intent → run the dimensions → write the file)
  needs no special tools.
- The **test/iterate loop** spawns candidate agents via the **Agent/Task tool**.
  Without it, the skill falls back to a manual design review (it says so
  explicitly rather than pretending to test).

## Usage example

```
You: I want an agent that audits a PR for missing test coverage.
→ The skill: confirms it's a registered, read-only agent; runs the design
  dimensions; writes agents/coverage-auditor.md (tools: Read, Grep, Glob, Bash;
  no Edit); then spawns it on 2-3 sample PRs plus a near-miss, grades against
  failure-mode assertions, and shows you the results to refine.
```

## How to validate

- `name: agent-creator` matches the directory; SKILL.md frontmatter is valid.
- Run the skill on a small throwaway agent idea and confirm each step is
  followable end to end.
- The generated agent file passes the checklist in
  `references/agent-template.md`.

## Skill files

```
agent-creator/
├── SKILL.md                       # Workflow + the six design dimensions
├── README.md                      # This file
├── references/
│   ├── agent-design-guide.md      # Dimensions in depth + gotchas
│   └── agent-template.md          # Annotated registered + body-only templates
└── agents/
    └── grader.md                  # Body-only grader for the test loop
```
