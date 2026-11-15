---
name: continue
description: Resume work from earlier /handoff notes in .okf/handoffs/. Offers the live handoffs as a pick list, loads the ones chosen, sums them up together and asks what to do next. Use at the start of a session, or when the user says "continue", "pick up where we left off", "what was I working on", "resume", "catch me up", or runs /continue.
---

# /continue: pick the work back up

Handoffs are concepts in `.okf/handoffs/`, written by `/handoff`. This skill
lists the live ones, lets the user choose, and briefs them on the chosen work.
It reads only; it changes nothing until the user says what to do.

## 1. List the live handoffs

```
kmctl handoffs --json
```

It prints the live handoffs newest first, each with `id`, `path`, `title`,
`description` and `date`. Expired ones are left out. If `$ARGUMENTS` names a
topic, keep the ones whose title or description match it, and fall back to
the full list when none do. If the list is empty, say there are no live
handoffs, suggest `/handoff` at the end of the next session, and stop.

## 2. Let the user choose

Ask with AskUserQuestion, `multiSelect: true`, so they can pick several. A
question holds at most four options, so offer the three newest handoffs plus a
fourth option, `more`:

- `label`: a number and the handoff's title;
- `description`: its description and date.

If they pick `more`, ask again with the next three. If they pick nothing, ask
once more, then stop. Never pick for them. When you cannot ask (no
AskUserQuestion), show the same choice as text: the three newest as numbered
lines plus "more", and stop for their reply. If the user already named the
handoffs they want in their message, skip the question and go to step 3.

## 3. Load and sum up

Read the chosen handoffs at their `path`. Give one combined brief: what each
piece of work is, where it stands, threads that connect or conflict, and the
open next steps. Name the handoffs by title so the user knows what fed it.

## 4. Ask what to do next

End with the question: continue one of these threads, start something new, or
refine the summary? Take no action before the answer.
