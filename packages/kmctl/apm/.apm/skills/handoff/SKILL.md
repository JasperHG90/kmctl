---
name: handoff
description: Write a technical handoff of the current work to .okf/handoffs/ so you, or another agent, can pick it up later with /continue. Use at the end of a work session, when wrapping up a long conversation, or whenever the user says "hand this off", "write up where we are", "save this so I can continue later", "I'll come back to this", or runs /handoff.
---

# /handoff: write where the work stands

A handoff is a short technical brief for someone picking the work up cold: what
it is, what was decided and why, where it stands, and what comes next. It is a
concept in `.okf/handoffs/`, so it travels with the repository and `/continue`
can find it. It expires after two weeks (`kmctl review due` lists it then).

## 1. Reconstruct the work

Read back over the conversation, and `$ARGUMENTS` if the user named a focus.
Capture the substance: the goal, the approach, the decisions and their reasons,
what is done, what is half done or untested, and the open questions. Name real
files, branches, commands and tickets; vague summaries save nobody any work.

## 2. Save it with kmctl

```
kmctl new handoff 'Short title of the work' --description 'One sentence: what and where it stands.' ${CLAUDE_CODE_SESSION_ID:+--key "$CLAUDE_CODE_SESSION_ID"} --json
```

The key ties the handoff to this Claude Code session, so a second `/handoff`
in the same session updates the same handoff instead of adding another. Pass
`--key` only when `CLAUDE_CODE_SESSION_ID` is set and not empty (the
`${CLAUDE_CODE_SESSION_ID:+...}` form above does this); kmctl refuses an empty
key. kmctl writes the front matter, the index entry and the log
line, and prints the path. If it refuses because `.okf/` is missing, say so and
suggest `kmctl init`; do not write the file yourself.

## 3. Write the four sections

Fill in the sections kmctl wrote at that path, in prose a capable colleague can
act on:

- **Summary**: what the work is, the approach, and the key decisions with why.
- **Where it stands**: done and working; in progress; untested or uncertain.
- **Next steps**: the concrete threads to pick up, specific enough to start on.
- **Key references**: files, branches, PRs, tickets, commands, links.

## 4. Confirm

Run `kmctl check`, then tell the user the handoff's title and path in one line,
and that `/continue` will offer it in a later session.
