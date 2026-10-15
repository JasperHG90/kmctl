# Subagent Design Guide

Deep treatment of the six design dimensions from `SKILL.md`, plus a gotchas
list. Read a section when that decision gets hard. The framing throughout: a
subagent is not a smaller chat and not a function call — it is a worker with an
**isolated context**, a **data-shaped return value**, a **tool boundary**, and
(if registered) a **name and description that are all a caller reads before
delegating**. Every dimension below falls out of one of those facts.

## Contents

- [0. Should this agent exist at all?](#0-should-this-agent-exist-at-all)
- [1. Single responsibility](#1-single-responsibility)
- [2. Prompt/body split + injected-context contract](#2-promptbody-split--injected-context-contract)
- [3. Output contract](#3-output-contract)
- [4. Tool allowlist as guardrail](#4-tool-allowlist-as-guardrail)
- [5. Parallelism & isolation](#5-parallelism--isolation)
- [6. Trigger (registered only)](#6-trigger-registered-only)
- [Gotchas](#gotchas)

---

## 0. Should this agent exist at all?

The first job is sometimes to talk the user *out* of an agent. The golden rule
that settles most cases: **does the intermediate work matter to the parent?**
If the parent only needs the conclusion — a verdict, a summary, a location —
delegating is a clear win: the searching, the false starts, the noisy logs all
stay out of the parent's window. If the parent needs to *see* the work unfold
(to steer it, build on it, or reuse pieces of it), an agent hides exactly what
matters — keep it inline.

Past that rule, an agent only makes sense when it does something the main
thread **cannot** do for itself:

- **A different system prompt.** The main thread can't change its own stance
  mid-conversation. An adversarial reviewer needs a genuinely skeptical prompt
  and a fresh perspective untainted by the parent's reasoning — this is why
  adversarial reviews work best as subagents, and it generalises to any job
  needing a distinct tone or role.
- **Keeping intermediate work separate.** A big search or noisy scan produces
  context the parent shouldn't have to carry.

If neither holds, the agent is overhead in a costume. Isolation is not free:

- The agent starts with **no memory of the parent conversation**. Every call
  pays a re-briefing tax.
- Its result must be **marshalled back** into the parent's context, costing
  tokens proportional to how much it returns.
- It **cannot spawn its own subagents** (one-level nesting). An "agent" that
  needs to fan out further is mis-modelled.

Reach for an agent when at least one of these holds:

- **Independent scope** — the work is a self-contained unit with a clean input
  and output, not deeply interleaved with the parent's reasoning.
- **Parallelizable** — you want several of these running at once (the blueprint
  skill fans out four analysts), or you want this off the critical path.
- **Context hygiene** — the work reads/produces a lot that the parent doesn't
  need to keep (a big search, a noisy log scan); isolating it protects the
  parent's window.

One shape deserves an explicit warning because it looks so natural: the
**multi-step pipeline** — agent A researches, hands to agent B who designs,
hands to agent C who implements. Each handoff pays the full re-briefing tax,
and whatever A learned that didn't fit its return value is simply gone by the
time C runs. Sequential stages that build on each other belong inline (one
context accumulating knowledge) or in a Workflow script; subagents shine for
*fan-out*, not *relay*. The precise anti-pattern is relaying context through
return values alone — orchestrations that persist context by other means
(dev-team's long-lived agents and on-disk artifact trail, a Workflow passing
structured results) are a different shape and can legitimately sequence
agents.

If none holds, prefer **inline** work. If the thing is really a *reusable
procedure* a human or agent invokes ("how we do X here"), it's a **skill**, not
an agent — point the user at `skill-creator`. Saying "this shouldn't be an
agent, here's why" is a valid and valuable outcome of this skill.

## 1. Single responsibility

One nameable job. The test: state the responsibility in a sentence with no
"and". "Maps the external API surface of a repo" passes. "Maps the API and
fixes inconsistencies and writes docs" is three agents.

Why it matters beyond tidiness: a single responsibility is what makes the agent
**triggerable** (the caller can tell when it applies) and **verifiable** (you
can write assertions about a narrow job). A sprawling agent triggers
unpredictably and fails in ways no assertion catches. When scope creeps, split
into sibling agents that a parent composes, rather than one agent that does
everything.

## 2. Prompt/body split + injected-context contract

The dimension people most often get wrong. A subagent receives instructions
from **two** places and you must decide what goes where:

- **The body** (static, written once, identical every run): role, method,
  constraints, output shape, quality bar. Things true of *every* invocation.
- **The spawn prompt** (written by the parent at call time): the specific task,
  the target path/file/PR, facts the parent already discovered and wants to
  share so the agent doesn't re-derive them, and where to put outputs.

Worked example — the blueprint skill's spawn block hands each analyst the repo
directory and a Phase-1 facts summary, while the analyst body
(`agents/pattern-analyst.md`) contains only the generic "how to analyse
patterns" method. The body never hardcodes a repo path; the parent never
re-explains how to analyse.

Make the contract explicit in the body. A short **"Inputs (provided at spawn)"**
section listing what every caller must supply turns an implicit assumption into
a checkable interface. Two failure modes this prevents:

- **Body assumes un-injected context** — e.g. references "the file you were
  given" when no spawn prompt named a file. The agent hallucinates or stalls.
- **Body hardcodes what should be injected** — e.g. a fixed path or a baked-in
  task, making the agent un-reusable.

## 3. Output contract

The agent's final message is **consumed by the caller**, not shown to the user.
Three consequences:

1. **Define the shape.** Give the body an explicit output template (markdown
   sections, or a JSON schema when a Workflow consumes the result and validates
   it). This is not optional polish: agents do the research fine and then
   *struggle to land the ending* — without a template they trail off into
   unstructured prose or keep investigating past the point of usefulness. For
   research/review agents, the default section set that works:

   - **Summary** — the two-sentence answer.
   - **Critical issues** — must-fix / blocks-the-caller findings.
   - **Major issues** — significant but not blocking.
   - **Recommendations** — what the caller should do next.
   - **Obstacles encountered** — see below; don't skip this one.

   `pattern-analyst.md` and `feature-planner.md` both end with a concrete
   output format — copy that discipline.
2. **Report obstacles, not just results.** The agent must surface what it
   *couldn't* do — files it couldn't find, tools it was denied, approaches that
   dead-ended, assumptions it had to make. If it stays quiet about these, the
   main thread either trusts a silently-incomplete result or spends its own
   turns re-discovering the same walls. An "Obstacles encountered" section
   makes the failure surface part of the contract; an empty section is itself
   information.
3. **Summarise, don't dump.** The caller pays context for everything returned.
   A tight, structured verdict (the 3 findings that matter) beats a 500-line
   transcript of everything the agent looked at. Tell the agent to return
   conclusions and evidence, not its working notes. For a fan-out where the
   parent aggregates N results, this is the difference between a usable
   synthesis and a blown context window.

If the result feeds a deterministic Workflow step, prefer **structured output**
(JSON matching a schema) so the parent can branch on it without parsing prose.

## 4. Tool allowlist as guardrail

`tools:` is least-privilege *and* a contract-enforcer. The cleanest examples in
this repo are the read-only reviewers: `feature-planner.md` and
`adversarial-reviewer.md` both omit `Edit`/`Write` so they *physically cannot*
mutate the repo — the boundary is enforced by the harness, not by the agent
remembering to behave.

Guidelines:

- Grant the **narrowest set** the method actually needs. A research agent:
  `Read, Grep, Glob` (+ read-only `Bash` if it runs `git`/`ls`). A reviewer:
  add `Bash` for running tests/linters but still no `Edit`. A migration agent:
  `Edit`/`Write` + whatever it builds with.
- **Be explicit.** Omitting `tools` means "inherit everything" — which hides the
  boundary and over-grants. List the tools so a reader sees the agent's reach at
  a glance.
- For a **body-only** agent, the file has no `tools` field; the parent grants
  tools at spawn (`subagent_type`). State the intended restriction in the body's
  prose and make sure the parent honours it.

## 5. Parallelism & isolation

If the agent **writes files** and might run **concurrently** with siblings or
copies of itself, plan for collisions:

- **Idempotency** — writing to a deterministic, per-task path so two runs don't
  clobber each other, and re-running is safe.
- **Worktree isolation** — when agents mutate a shared tree in parallel, each
  gets its own git worktree so edits don't conflict; the cost is real, so only
  do it for genuinely parallel writers.

Other isolation facts to design around:

- **No mid-run user interaction.** A subagent generally can't stop to ask the
  user a question. Design it to make the reasonable call and **flag the
  ambiguity in its output** (an "Open questions" section), so the parent or user
  resolves it after. Blocking on a question it can't ask is a hang.
- **One-level nesting.** It can't spawn subagents. If the job needs further
  fan-out, that orchestration belongs in the parent (or a Workflow), not the
  agent.

## 6. Trigger (registered only)

For a registered agent, the `name` and `description` are the *entire* basis on
which a caller decides to delegate — and each does a different job. Treat both
as the product surface.

- **The name steers when the agent is spawned.** In practice the name weighs
  heavily in the caller's delegation choice — a vague or overly broad name
  mis-fires even under a sharp description. If the agent triggers at the wrong
  moments, *renaming* is often the highest-leverage fix — `code-reviewer`
  poaches everything review-shaped; `security-reviewer` fires where you meant
  it to.
- **The description shapes the spawn prompt.** The parent doesn't just read the
  description to decide *whether* to delegate — it uses it to decide *what to
  tell* the agent. A description that names the inputs the agent expects ("give
  it the PR number and the files changed") produces better-briefed spawn
  prompts than one that only describes behavior. This is the trigger-side twin
  of dimension 2's injected-context contract.
- **Lead with the artifact/verb** so it's unmistakable ("Adversarially review
  work produced by another agent…", "Produces a high-level feature ticket…").
- **Cover when to use** with the phrasings a user/parent would actually say.
- **Invest in anti-conditions — for genuine near-misses.** The "NOT for…"
  clauses carry equal weight to the triggers — they're what stop the agent
  firing on adjacent-but-wrong tasks. Name sibling agents it might be confused
  with and draw the line (e.g. "NOT for orchestrating a multi-agent build —
  that's dev-team"). But they earn their place only when the confusion is
  plausible: a clause excluding something no caller would ever route here
  ("NOT for planning" on a reviewer) is noise, not a guardrail. No near-miss →
  no clause.
- **Model tier** is the knob here: `haiku` for mechanical/cheap, `sonnet` for
  the default, `opus` for deep reasoning, architecture, or adversarial work.
  Match it to the hardest thing the agent must do; don't over-think it.
- **Color** (`color:` in frontmatter) is purely cosmetic — it colors the agent
  in the task list and transcript UI. Worth setting when several agents run
  side by side so the user can tell whose work is whose at a glance.

A body-only agent has no description — its triggering is the parent skill's
spawn logic. Don't try to encode a trigger in a frontmatter-less file.

---

## Gotchas

- **The agent can't see this conversation.** Anything obvious to you right now
  (which repo, which file, what the user just said) is invisible to the agent
  unless the body states it or the spawn prompt injects it.
- **The result isn't a user message.** Don't write bodies that say "tell the
  user…" — there is no user on the other end, only the caller consuming data.
- **Context budget is shared at aggregation.** N agents each returning a wall of
  text can overflow the parent that collects them. Cap and summarise.
- **Description over-pushiness causes mis-fires.** Making a description aggressive
  to fight under-triggering can make it poach tasks meant for a sibling agent.
  Balance pushy triggers with sharp anti-conditions.
- **Inheriting all tools is a silent over-grant.** An agent with no `tools:`
  field can edit, delete, and run anything — easy to miss in review. Prefer an
  explicit list even when it's long.
- **An agent that goes quiet about failure looks like success.** A result with
  no obstacles section reads as "everything worked" even when the agent hit
  walls and guessed its way past them. Make obstacle reporting part of the
  output contract so silence is a checkable violation, not the default.
- **"Make it an agent" is sometimes wrong.** Re-run dimension 0 whenever the job
  is small, deeply interleaved with the parent, or really a reusable procedure
  (→ skill). Pipelines especially: agents chained in sequence lose context at
  every handoff — fan out with agents, but relay inline.
