---
description: "The problems kmctl solves, the kinds of agent memory, and what it leaves to a shared layer above the repository."
---

# Where kmctl fits in knowledge management

## The question

An organisation with many repositories and many agents has a knowledge
problem that no single tool solves. Which part does kmctl solve, and what
does it leave to other tools? This page answers that, so you know what to
expect from kmctl and what you still need around it.

## How it works

**Four ways knowledge breaks down.** Teams that work with agents tend to hit
the same four problems:

1. **Procedures diverge.** Your skills and rules differ from a colleague's,
   so your agents produce different results, and outdated procedures stay in
   use.
2. **Specs drift.** The code and the documents that describe it move apart,
   and agents and people then work from a stale description.
3. **Architecture drifts.** Teams cannot find the current architecture rules
   ("every application needs an API"), so nobody can check that they follow
   them.
4. **Changes don't spread.** There is no one place to see what changed across
   projects, and nothing checks that a central change reached every
   repository.

kmctl works on the second problem inside one repository, and gives the other
three a place to start: knowledge in the same shape in every repository.

**Kinds of memory.** An agent's memory comes in four kinds, and each needs a
different tool:

| Kind | What it holds | Where it lives |
|---|---|---|
| Working | What the agent is focused on now | The context window, `CLAUDE.md` or `AGENTS.md` |
| Episodic | Turn-by-turn conversations and tool traces | Session logs |
| Semantic | Facts about the project and why it is the way it is | `docs/` and `.okf/` |
| Procedural | How to do things: habits, strategies, procedures | Rules, skills and subagents |

kmctl manages semantic memory, and the piece of working memory that points to
it. The briefing that starts each session tells the agent where `docs/` and
`.okf/` are and how to write to them. It does not keep session logs: a whole
session is too noisy to be worth sharing. What is worth keeping from a
session goes into a decision, a practice or a handoff.

**Two readers, two folders.** People who use a project read `docs/`, sorted
by what they are trying to do: learn, finish a task, look up a fact, or
understand. People and agents working on the project read `.okf/`: decisions
with the alternative each rejected, architecture, practices, proposals and
handoffs. One repository, one practice, so every repository produces
knowledge a reader, or a search index, can rely on.

**Three layers, by how fast they move.** Knowledge that changes at different
speeds needs different care:

| Layer | Example | Who writes it |
|---|---|---|
| Foundational | Two to four documents of platform and technology principles | People only |
| Architecture | Shared architecture guidelines and decision records across projects | People, curated by hand |
| Repository | One project's `.okf/` and `docs/` | Mostly agents |

kmctl owns the bottom layer. That layer moves fastest and agents write most
of it, so it is where drift starts and where checking pays off most. The top
two layers change slowly and need a named owner more than they need tooling.

## Why it is this way

**Capture happens where the work is.** The agent that makes a change is the
one best placed to record it, and to notice when it contradicts an earlier
decision. Caught there, a contradiction costs one edit. Caught months later by
a central team, it costs an investigation. So kmctl keeps knowledge in the
repository, next to the code, and puts the rules for writing it into every
session
([ADR 0002](../../.okf/decisions/0002-briefing-and-rules-injected-by-the-cli.md)).

**People must trust what they don't review.** Agents write knowledge faster
than anyone can read it. People cannot check every page, so they need to
trust what the system holds and to know which parts a person has checked.
Every concept in `.okf/` records that: the rules tell an agent to leave what
it writes unverified and a person to add the `verified` stamp, and
`kmctl review due` lists what is unverified or stale
([ADR 0006](../../.okf/decisions/0006-staleness-from-okf-fields.md)). The
audit finds drift but never marks anything verified
([ADR 0005](../../.okf/decisions/0005-audits-report-only.md)), so a stamp
should mean a person looked. Nothing checks who wrote it.

**Full automation is neither possible nor wanted.** No hook can tell whether
an architecture page still matches the code; that takes judgment. And the top
layers, the principles everything else rests on, should stay in people's
hands. kmctl automates what a script can check and leaves the judging to an
agent that reports and a person who decides. See
[Why two hooks and report-only audits](why-one-hook-and-report-only-audits.md).

**Get one repository right first.** A shared layer is only as good as what
feeds it. If every repository keeps `docs/` and `.okf/` in the same shape, a
shared layer can index them all without custom work for each team. If they
don't, no search engine fixes that.

## What kmctl leaves to other tools

kmctl stops at the edge of the repository. A full set-up also needs:

- **Shared procedures.** Rules, skills and subagents are software: they
  start in one repository and, once a second one needs them, move to a shared
  library where each repository pins a version. A package manager such as
  [APM](https://microsoft.github.io/apm) does that, and installs the same
  package into each agent harness in that harness's own format, so no team is
  tied to one vendor. kmctl ships only the rules and skills that keep its own
  knowledge current, as an APM package (a shared package and one per
  harness, in one folder), which APM installs for Claude Code and
  Antigravity.
- **A shared layer and search.** Copying each repository's `docs/` and
  `.okf/` to a shared place on every merge to the main branch, and searching
  across them as the reader, so nobody sees what they may not read. A managed
  search service can cover most of that work: access control, storage and
  embeddings.
- **Documents with no repository.** Slide decks, PDFs and Word files reach a
  shared layer through a connector, not through kmctl. When one contradicts
  a repository's `.okf/`, a sensible order for deciding which one wins is
  the layers above: foundational documents first, then architecture
  guidelines and decision records, then `.okf/`, then uploaded documents.
- **Checking that changes spread.** Whether a central change, such as a new
  architecture rule, reached every repository is a question across
  repositories. kmctl's audit checks one repository at a time.

**The limits.** kmctl keeps one repository's knowledge in a known shape and
makes drift visible. It does not stop procedures diverging between teams,
does not know about other repositories, cannot make a person read what an
agent wrote, and cannot stop an agent from adding a `verified` stamp.
