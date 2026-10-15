---
name: rule-creator
description: >
  Creates a "rule" — a short, always-on guidance file (Markdown with
  name/description frontmatter, optionally path-scoped) that is injected into an
  agent's context to enforce or nudge a standing behavior. Writes it either into
  this repo's rules/ library or a project's .claude/rules/ directory, walking
  from intent through a fit check, interactive follow-ups (path scope,
  enforce-vs-nudge, save location, duplicate check), and a terse draft. Use
  whenever the user wants to create, write, add, scaffold, or draft a rule /
  constraint / guardrail / coding convention / standing instruction / always-on
  guidance / .claude/rules entry, or turn a repeated correction ("stop doing X",
  "always do Y") into a permanent rule. NOT for: authoring a reusable multi-step
  procedure (use skill-creator); a subagent (use agent-creator);
  editing settings.json, hooks, or permissions (use update-config); or recording
  project-specific facts like build commands and directory layout (those belong
  in CLAUDE.md / AGENTS.md, not a rule).
compatibility: >
  The interactive follow-ups use the AskUserQuestion tool. If it is unavailable,
  follow the no-question fallback in Step 3 — draft with inferred answers and
  ask the user to correct them.
---

# Rule Creator

A skill for writing a good **rule** and placing it where it will actually be
loaded. It is the sibling of `skill-creator` and `agent-creator`, but a rule is
a different kind of artifact, so lead with what makes it different.

> A **rule** is *ambient guidance* — text injected into an agent's context that
> shapes behavior on every relevant turn, with no procedure to invoke and no
> delegation. A skill is a procedure you *pull in on demand*; an agent is a
> worker you *delegate to*; a rule is just *present*, steering the work while
> it happens. Two consequences drive every decision below: **(1) the body is
> what reaches the agent** — when a rule lives in `.claude/rules/`, the harness
> injects its Markdown body, so all load-bearing guidance goes there and the
> frontmatter is catalog metadata, not a trigger. **(2) A rule pays permanent
> context rent** — it costs tokens on every matching turn, forever, so it has to
> earn that by being short, high-signal, and non-overlapping with rules that
> already exist.

## How rules are loaded (so you place them correctly)

- **`.claude/rules/*.md`** (project) and **`~/.claude/rules/*.md`** (global) are
  read by Claude Code and injected as standing instructions. The body is what
  the agent sees — a rule here works even with no frontmatter at all.
- **This repo's top-level `rules/`** is a curated, version-controlled *library*
  of rules. Nothing auto-loads it; rules live here to be shared, reviewed, and
  copied into a `.claude/rules/` when adopted. Frontmatter is the catalog entry.
- **`paths`** is an optional glob array (e.g. `["**/*.py"]`). Path-aware setups
  use it to scope a rule to matching files so it doesn't burn context on
  unrelated edits. Where scoping isn't supported, the rule is simply always-on.
  Treat `paths` as *tightening*, never as a trigger the rule depends on.

## Where you are in the process

- **"Add a rule that does X" / "stop doing Y from now on"** → start at Step 1.
- **"Here's a rule, tighten it"** → skim Step 2's fit check, then go to Step 4
  (write) and Step 5 (self-review).

Be flexible — if the user says "just write it," infer the follow-ups, state
your assumptions, and skip the questions.

## Step 1 — Capture intent

Get clear, in a sentence, on the behavior the rule should produce and *why it
keeps needing saying*. Rules are usually born from a repeated correction, so
mine the conversation first: what did the user have to tell the agent more than
once? Note whether the behavior is universal or only matters for certain files.

## Step 2 — Fit check: is a rule the right artifact?

A quick gate, not a formality. A rule earns its permanent context cost only when
the guidance is short, standing, and worth injecting on the median relevant turn
— not the rare one. Route by the sharpest discriminator:

| If the thing is… | it's a… |
|---|---|
| a short, always-on constraint or nudge with no steps to run | **rule** |
| a procedure you invoke on demand (steps, tools, a workflow) | **skill** (skill-creator) |
| a worker you hand an isolated task and get a result back | **agent** (agent-creator) |
| a fact about *this specific* project (build command, layout, ports) | **CLAUDE.md / AGENTS.md** |
| harness config (permissions, hooks, env, automation) | **settings.json** (update-config) |

Two tells worth stating out loud:
- **Rule vs CLAUDE.md**: a rule is a *reusable principle* that would hold in
  other repos too; CLAUDE.md is for facts true only *here*. "Write tests for
  every change" is a rule; "run tests with `uv run pytest`" is closer to a
  project fact.
- **Rule vs skill — the length tripwire**: if the guidance needs more than a
  handful of paragraphs, multiple procedures, or a decision tree, it has
  outgrown a rule. Injecting all that on every turn is expensive; make it a
  skill and let it load on demand.

If it isn't a rule, say so and point at the right tool rather than forcing it.

## Step 3 — Interactive follow-ups

Before writing, resolve the decisions that change the file. Prefer
`AskUserQuestion` so the user picks from concrete options; group them into one
prompt. The load-bearing questions:

1. **Check for duplication first.** Scan existing rules — `rules/*.md` and, if
   present, `.claude/rules/*.md` — for one that already covers this ground
   (CONTRIBUTING requires this). If a near-match exists, surface it and ask
   whether to **extend the existing rule** instead of adding a competing one.
   Overlap is the main way an always-on rule turns into noise. When two rules
   are related but distinct, cross-reference rather than restate — as
   `python-testing` points at `pre-existing-issues` instead of duplicating it.
2. **Scope — when does this actually apply?** If it only matters for certain
   files, capture that and derive a tight `paths` glob (e.g. `["**/*.py"]`). A
   Python-only rule left global taxes every Markdown and YAML edit for nothing.
   If it genuinely applies everywhere, leave `paths` off.
3. **Enforce-hard or nudge?** This sets the tone. A hard rule states a
   non-negotiable ("every change ships with a test"); a nudge leans the agent a
   direction it can override with reason (`pre-existing-issues` nudges; the
   user can always say otherwise). Don't dress a preference up as a mandate.
4. **Save location.** This repo's `rules/` library (shareable, reviewed) or the
   active project's `.claude/rules/` (loaded now). Offer both; default to
   `rules/` unless the user wants it live immediately.

Infer the name and description from intent and let the user edit the draft —
don't turn confirming them into a separate ceremony.

**No-question fallback.** If `AskUserQuestion` isn't available, draft with your
best inferences, state each assumption plainly (scope, hardness, location), and
ask the user to correct them in one pass.

## Step 4 — Write the rule file

**Filename**: a kebab-case slug of the topic (`python-testing.md`,
`pre-existing-issues.md`). Confirm it doesn't collide with an existing file.

**Frontmatter** — always at least these two:

```yaml
---
name: <kebab-case identifier matching the filename>
description: <one line: what it constrains + when it's relevant>
paths: ["**/*.py"]   # optional — include only if the rule is file-scoped
---
```

The `description` is a human-facing summary and a "when to read" hint (e.g.
"Read before adding or changing Python code"), not a trigger — routing lives in
`paths`, and the behavior lives in the body. New rules use `name` (matching how
skills and agents are keyed); you'll see some legacy rules keyed on `title` —
leave those as they are, don't churn them.

**Body** — keep it terse; it's injected on every relevant turn. Match the
repo's voice: declarative sentences that *explain why the constraint matters*,
so the agent can apply it to cases you didn't foresee. Avoid stacking
shouty `MUST`/`ALWAYS`/`NEVER` in caps — a reason generalizes where a bare
command doesn't.

Choose the body shape to fit the rule; propose it, don't default blindly:
- **A single directive** → one or two plain sentences is enough (see
  `uv-installer`). A wrapper adds nothing.
- **A hard core amid explanation** → wrap the non-negotiable clause in a
  `<constraint name="...">…</constraint>` block so it stands out from the prose
  around it, and use `<example name="...">` for a concrete illustration (see
  `python-testing`). These tags are a repo readability convention, not magic the
  loader interprets — use them to make the enforceable part visible, not by rote.
- **All nudge / short guidance** → plain prose or bullets, no blocks (see
  `prek-code-quality`).

## Step 5 — Self-review against the quality bar

Read the draft cold and check:

- **Earns its rent** — worth injecting on the median relevant turn, not a rare
  edge case. If it's niche, scope it with `paths` or reconsider it as a skill.
- **Scoped tightly** — file-specific rules carry a `paths` glob; global rules
  genuinely apply everywhere.
- **No overlap** — doesn't restate an existing rule; cross-references where it
  relates to one.
- **Terse** — no filler; every line pulls weight, because every line costs
  context forever.
- **Explains why** — the reasoning is present, not just the command, and the
  tone matches enforce-hard vs nudge.
- **Placed right** — landed in the location the user chose, filename matches
  `name`, frontmatter is valid YAML.

## Quality bar

A good rule states one short standing behavior, explains why it matters, is
scoped so it only costs context where it's relevant, and doesn't duplicate a
rule that already exists. When the guidance is too big, too procedural, or too
project-specific to earn a permanent slot in context, say so and route it to a
skill, an agent, or CLAUDE.md instead.
