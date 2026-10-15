---
name: agent-creator
description: >
  Creates a Claude subagent definition file (a .md agent spawned via the
  Agent/Task tool) and iteratively improves it — the way skill-creator does for
  skills, but adapted to the physics of subagents (isolated context, return
  value is data not chat, tool allowlist as guardrail, name and description as
  delegation trigger). Walks you from intent through the design dimensions, writing the
  file, testing it on realistic delegation prompts, and tuning its trigger. Use
  whenever the user wants to create, design, write, scaffold, draft, or improve
  a subagent / sub-agent / custom agent / agent definition, build an agent for a
  skill's agents/ directory, set up a specialized agent to delegate to, or tune
  an existing agent's description / tools / model. NOT for: creating a skill (use
  skill-creator); orchestrating a multi-phase multi-agent build or "agent team"
  (use dev-team); writing a one-off Agent-tool prompt you will not reuse; or
  authoring a multi-agent Workflow script.
compatibility: >
  The test/iterate loop (steps 4-6) spawns subagents via the Agent/Task tool.
  In an environment without it, follow the no-Agent fallback in step 4 — the
  design phase (steps 1-3) needs no special tools.
metadata:
  flavors: registered, body-only
---

# Agent Creator

A skill for designing well-engineered Claude **subagents** and improving them
through a test/iterate loop. It is the sibling of `skill-creator`: same spirit
(draft → test → review → improve → tune the trigger), but every step is bent
around the things that make a *subagent* different from a skill or from inline
work.

If you have not internalised those differences, the skill collapses into a
generic "fill in name/description/tools" checklist that produces mediocre
agents. So lead with the physics. The one paragraph to hold in your head:

> A subagent runs in a **fresh, isolated context** — it never sees the parent's
> conversation. Everything it knows arrives through two channels: its **static
> body** (written once, reused every run) and the **spawn prompt** the parent
> writes at call time. Its final message is **not shown to the user** — it is
> *data returned to the caller*. Its **tool allowlist** is a hard boundary. And
> for a *registered* agent, its **name and description are the only things the
> parent reads when deciding whether to delegate** — and the description also
> shapes what the parent writes into the spawn prompt. Design each of these
> deliberately.

## Where you are in the process

Figure out where the user is and jump in there. Common entry points:

- **"I want an agent that does X"** → start at *Capture intent* and go through
  the whole loop.
- **"Here's a draft agent, make it better"** → skim the design dimensions for
  gaps, then go straight to *Test it* and *Iterate*.
- **"My agent never gets called / gets called for the wrong things"** → this is
  a triggering problem; go to *Tune the trigger*.

Be flexible. If the user says "just draft it, skip the testing," do that.

## The two flavors (decide this first)

There are two kinds of subagent in play, and they are designed differently. Pin
down which one before anything else.

| | **Registered subagent** | **Skill-bundled (body-only)** |
|---|---|---|
| File | full YAML frontmatter + body | body only, **no frontmatter** |
| Lives in | a project `agents/` dir or `~/.claude/agents/` | `<skill>/agents/foo.md` |
| Triggered by | its own `description` (parent's Agent tool reads it) | the **parent skill's spawn block** — the agent file has no say |
| Tools restricted by | its `tools:` allowlist | whatever the parent grants at spawn |
| Examples in this repo | `agents/feature-planner.md`, `agents/adversarial-reviewer.md` | `skills/architecture/blueprint/agents/*.md` |

This split routes the rest of the work: **dimensions 3–5 below apply to both**;
**dimensions 6 (trigger) and the `tools`/`model` frontmatter apply only to the
registered flavor.** For a body-only agent, "when is it called" and "what tools
does it get" are the *parent skill's* job — note that explicitly and don't try
to bake a trigger into a file that has no frontmatter to hold one.

---

## Step 1 — Capture intent

Understand what the agent is for before designing it. Extract from the
conversation first if the user is mid-task ("turn this into an agent"); fill
gaps by asking. Get clear on:

1. **The one job.** What single, nameable responsibility does this agent own?
   If you cannot say it in a sentence without "and", it is probably two agents.
2. **When the caller delegates to it** (registered) or **where the parent skill
   spawns it** (body-only).
3. **What it returns** — the shape of the data the caller gets back.
4. **Read-only or write-capable?** This decides the tool allowlist and whether
   parallel/isolation concerns apply.

Then run the gate in Step 2 before writing anything.

## Step 2 — Run the design dimensions

These are the load-bearing decisions. For depth, examples, and gotchas, read
`references/agent-design-guide.md` — pull it in when a dimension gets tricky.

**0. Should this agent exist at all?** A real gate, not a formality. The golden
rule: **does the intermediate work matter to the parent?** If the parent only
needs the conclusion — a verdict, a summary, a found location — an agent is
great; if the parent needs to see *how* the work unfolded, keep it inline.
Beyond that, an agent earns its isolation cost only by doing something the main
thread *cannot*: carrying a **different system prompt** (a distinct tone or
stance — an adversarial reviewer is the canonical case) or **keeping noisy
intermediate work out of the parent's window**. Isolation costs something: a
fresh context re-briefed every call, a result marshalled back, and **no ability
to spawn its own subagents** (nesting is one level). One shape that reliably
fails: a **multi-step pipeline** where agent A hands off to agent B hands off
to C with each stage's knowledge carried only in its return value — every
handoff pays the re-briefing tax and loses whatever didn't fit the return.
Sequential stages belong inline or in a Workflow. (Orchestrations like
`dev-team` that persist context another way — long-lived agents, an on-disk
artifact trail — sidestep this; the anti-pattern is relaying through return
values alone.) Otherwise keep it inline, or — if it is a reusable *procedure*
rather than a *delegatable worker* — make it a skill instead. Be willing to
tell the user "this shouldn't be an agent" and why.

**1. Single responsibility.** One clear job. This is what makes the agent
triggerable and verifiable. Agents that try to do everything trigger
unpredictably and fail in ways no assertion catches.

**2. Prompt/body split + injected-context contract.** *The most-missed
dimension.* The body holds **static, reusable** instructions — role, method,
constraints, output shape. The **parent injects per-run context at spawn time** —
the target path, the specific task, shared facts already discovered, where to
write outputs. (See the spawn block in `skills/architecture/blueprint/SKILL.md`:
the body is generic, the parent hands over the repo dir and Phase-1 facts.)
Decide explicitly: *what does the body assume is always true, and what must
every spawn prompt supply?* A body that assumes context it is never given is the
classic failure; so is a body that re-hardcodes what should be injected.

**3. Output contract.** The return value is **data for the caller, not a chat
message to the user** — the user never sees it directly. Define an explicit
shape in the body — agents reliably struggle to wrap up once their research is
done, and a concrete template is what saves them. For research/review agents
the proven default is: **Summary, Critical issues, Major issues,
Recommendations, Obstacles encountered**. The obstacles section matters more
than it looks: the agent must report what it *couldn't* do (missing files,
denied tools, dead ends) so the main thread doesn't burn its own turns
re-discovering them. **Summarise, don't dump**: the caller pays context for
whatever the agent returns, so a 50-line structured verdict beats a 500-line
transcript. State this in the body.

**4. Tool allowlist as guardrail.** Least privilege, and it *enforces the
contract*: a review/research agent omits `Edit`/`Write` by design so it
*cannot* mutate (see `feature-planner.md`, `adversarial-reviewer.md`). Grant the
narrowest set that does the job. Omitting `tools` entirely means "inherit
everything" — prefer an explicit list so the boundary is visible.

**5. Parallelism & isolation.** If the agent writes files and may run alongside
siblings (e.g. fan-out), it needs **idempotency or worktree isolation** so
concurrent runs don't collide. The agent **cannot ask the user a question
mid-run** — design it to make the reasonable call and *flag* the ambiguity in
its output, not block. And remember the **one-level nesting ceiling**: it cannot
spawn its own subagents.

**6. Trigger — registered flavor only.** The `name` and `description` together
are what the parent reads when deciding to delegate — and each is a distinct
knob. The **name** steers *when* the agent gets spawned: if it fires at the
wrong moments, renaming it is often the fix. The **description** also shapes
*what the parent puts in the spawn prompt* — the parent briefs the agent based
on what the description says it needs, so state expected inputs there. Cover
*what it does* + *when to call it* + *when NOT to* — the NOT-for clauses are
for genuine near-misses (tasks that share keywords/shape but belong elsewhere);
skip them when nothing could plausibly be confused. Lead with the artifact/verb.
Model tier (`haiku`/`sonnet`/`opus`) is a *knob* on this dimension — match it
to task depth (mechanical → haiku, default → sonnet, deep
reasoning/architecture → opus), don't agonise. An optional `color` in the
frontmatter distinguishes the agent visually in the UI — cheap and worth
setting when several agents run side by side. For a body-only agent, skip
this — the parent skill owns triggering.

## Step 3 — Write the agent file

Use `references/agent-template.md`, which has an annotated template for **each
flavor**. Match this repo's house style: explanatory prose, a clear role
statement, method as procedure, an explicit output format — explain *why* a
constraint matters rather than stacking bare `MUST`s (smart models follow
reasons better than rules).

Save location:
- **Registered** → default to the repo's top-level `agents/<name>.md` (matching
  `feature-planner.md` / `adversarial-reviewer.md`). Offer `~/.claude/agents/`
  for a personal/global agent.
- **Body-only** → `<parent-skill>/agents/<name>.md`, and update the parent
  skill's spawn block to read and dispatch it.

Verify `name` matches the filename, frontmatter is valid, and (registered) the
`tools` list contains exactly what the method needs.

## Step 4 — Test it

You are not shipping a one-off; you are shipping something that will run many
times on prompts you have not seen. So test it like that.

Write **2–3 realistic, self-contained delegation prompts** — the kind a parent
would actually send, with the inputs the body expects injected (per dimension
2). Include at least one **near-miss**: a prompt that is close to the agent's job
but should be handled differently, to see whether the agent stays in scope or
overreaches.

**Grade against failure-mode assertions, not self-authored success criteria.**
You wrote the agent *and* the success criteria in the same breath, so "did it do
what I hoped" is confirmation bias. Instead assert the **anti-behaviors** an
honest grader can check without ground truth:

- used a tool outside its allowlist / that its role forbids,
- tried to ask the user a question mid-run instead of flagging,
- dumped raw context/transcript instead of the contracted output shape,
- exceeded its single-responsibility scope,
- returned prose where a schema/template was required,
- assumed parent context that the spawn prompt never supplied.

**Run the agent** on each prompt and grade with `agents/grader.md` (read it,
spawn it on the outputs + assertions, it returns pass/fail + evidence). Organize
runs under `<skill-or-agent>-workspace/iteration-1/eval-<n>/`. A baseline run
(general-purpose agent, no specialized body, same prompt) is *optional* — useful
to show the agent earns its keep, but with n=2–3 it is weak signal, so don't
treat it as the headline.

**No-Agent fallback.** If the Agent/Task tool isn't available, you cannot spawn
runs. Instead, read the drafted agent aloud against the dimensions and the
failure-mode list yourself, walk one delegation prompt through it by hand, and
present that reasoning to the user. Say plainly that this is a design review, not
an execution test.

Present results to the user inline (this repo has no eval-viewer): for each
prompt, show the delegation prompt, the agent's returned output, and the grade.
Ask what they'd change.

## Step 5 — Iterate

Improve from the feedback, then rerun into `iteration-2/`. The mindset
(borrowed from skill-creator, and it matters):

- **Generalise, don't overfit.** You are tuning on a few prompts to move fast,
  but the agent must work on a million. If a fix only patches one test case,
  it's the wrong fix — reach for a different framing or metaphor instead of a
  fiddly special-case rule.
- **Keep the body lean.** Read the *transcripts*, not just outputs. If the body
  makes the agent waste turns on unproductive work, cut the part causing it.
- **Explain the why.** When you find yourself writing `ALWAYS`/`NEVER` in caps,
  that's a yellow flag — reframe so the agent understands the reason. Reasons
  generalise to edge cases; rules don't.

Repeat until the user is happy, feedback dries up, or you stop making progress.

## Step 6 — Tune the trigger (registered only)

For a registered agent, whether it actually gets used comes down to its `name`
and `description`. Don't armchair this — **spawn the near-miss prompts and
observe** whether delegating to the agent is the right call for each, then
refine. When the agent fires at the wrong moments, try **renaming** before
rewriting the description — a vague or overly broad name poaches
adjacent-but-wrong tasks that no amount of description sharpening fixes.

- Draft ~8–12 prompts split should-delegate / should-NOT-delegate, weighted
  toward genuine near-misses (prompts that share keywords with the agent but
  need something else).
- Lead the description with the concrete artifact/verb; spell out the *when*;
  and invest in **anti-conditions** — they carry equal weight to triggers and
  are what stop the agent from firing on adjacent-but-wrong tasks (note the
  collision risks with sibling agents like `dev-team` and resolve them in
  prose).

For a body-only agent there is no `description` to tune — triggering lives in
the parent skill's spawn logic, so this work belongs to that skill, not here.

---

## Reference files

- `references/agent-design-guide.md` — the six dimensions in depth, with
  worked examples and a gotchas list. Read when a design decision gets hard.
- `references/agent-template.md` — annotated templates for the registered and
  body-only flavors.
- `agents/grader.md` — a body-only grader agent for Step 4; reads run outputs +
  assertions and returns pass/fail with evidence.

## Quality bar

A good agent does one nameable job; assumes nothing its spawn prompt doesn't
give it; returns a tight, contracted result the caller can use without re-deriving
anything; cannot reach for tools its role forbids; and (registered) is named and
described so the parent delegates to it for the right tasks and passes over the
wrong ones.
When you're unsure an agent should exist at all, say so — an honest "keep this
inline" beats a polished agent nobody should call.
