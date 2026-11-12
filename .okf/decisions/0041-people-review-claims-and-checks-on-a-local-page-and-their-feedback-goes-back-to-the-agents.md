---
type: decision
title: "ADR 0041: People review claims and checks on a local page, and their feedback goes back to the agents"
description: "kmctl audit ui serves a page on 127.0.0.1 where a person gives a claim or its check a thumbs up or down and a note, says whether the claim holds, and asks the decision model for a second opinion; feedback is appended to the audit store, a thumbs down or a verdict the check disagrees with puts the work back in todo with the note until the agent's next answer, and liked answers become examples."
tags: [decision, audit]
generated:
  by: claude-opus/5.5
  at: 2026-11-12T07:00:00Z
status: draft
sources:
  - resource: "src/kmctl/claims/feedback.py"
  - resource: "src/kmctl/claims/ui.py"
  - resource: "src/kmctl/claims/ui.html"
  - resource: "src/kmctl/claims/store.py"
  - resource: "src/kmctl/claims/check_verbs.py"
  - resource: "src/kmctl/claims/verbs.py"
---

# ADR 0041: People review claims and checks on a local page, and their feedback goes back to the agents

## Context

The pipeline of
[ADR 0036](0036-claims-are-extracted-by-the-agent-through-kmctl-audit-claims.md)
and [ADR 0038](0038-checks-are-step-data-that-kmctl-reruns-and-only-checks-that-notice-a-change-are-stored.md)
has no place for a person's judgment. Reading its output in the
[audit UI prototype](../prototypes/audit-ui/README.md) showed claims that
were badly extracted (one fact and one opinion in a single claim), reasons
given for claims one step could test, and checks that hold while testing a
word rather than the claim. A person who sees this can only edit the store
by hand, and the agents never learn from it. The prototype was a static
file reading an exported `data.js`, so it could show the store but not
write to it.

## Decision

`kmctl audit ui` serves the page from the package on 127.0.0.1 and reads
the store live. On each claim a person can:

- give the claim, and separately its check or reason, a thumbs up or down
  and a note;
- say whether the claim holds or is false, whatever the check says;
- ask the decision model of [ADR 0039](0039-kmctl-audit-judge-asks-an-optional-decision-model-off-by-default.md)
  for a second opinion: `link` for a check that holds, `failure` for one
  that fails, `claim` (on the lines `checks todo` would show) for a reason
  or no answer.

Each save appends a row to a `feedback` table, keeping the claim text,
sentence and the check or reason judged, so the latest row per claim and
target is the current judgment and earlier ones are history. Any vote,
verdict or note no agent has answered yet rides along whenever `todo`
hands its item out, with a short `feedback_instructions` text. Some of it
also sends the item back: a thumbs down on a claim hands its section out
again in `kmctl audit claims todo`; a thumbs down on a check or reason, a
verdict the check contradicts, or "false" on a claim no check decides yet
hands the claim out again, first, in `kmctl audit checks todo`. A note
alone sends nothing back; the page says it waits for the next time the
item is handed out. The next submit for that section or claim marks its
feedback answered, whatever the agent answered, so a disagreement never
loops; the page shows a disagreement that remains.

A verdict counts while the files it was given on are unchanged: those the
check read, or, for a claim with no check or a reason that read none, the
files behind the lines `checks todo` shows for it. While it counts it
outranks the check in what the page marks and can send the claim back;
once stale it does neither, and the page asks the person to look again.
Answers people liked are handed to agents as `examples`. Feedback follows
its claim when re-extraction rewords it into one claim of the same
sentence, as answers do since ADR 0040; otherwise it stays as history.

The server listens on 127.0.0.1 only, answers only requests whose Host is
127.0.0.1 or localhost, and accepts writes only as JSON from its own
Origin, so another site in the browser cannot write through it.

Rejected:

- **A static page that exports feedback for `kmctl audit feedback import`.**
  No server, but two manual steps per review, and the page cannot show a
  second opinion or what the agent did since.
- **Feedback only through CLI verbs.** The page would fill in a command to
  copy. Least code, but the person reviewing is on the page, and copying a
  command per click is where reviews stop.
- **One "fail" button.** A person saying the claim is false and a person
  saying the check is wrong ask the agent for different things, so the
  verdict and the check's thumbs down are separate.
- **Putting the feedback rules in the extraction instructions.** Every
  section key covers those instructions, so changing them would hand out
  the whole bundle again; the rules travel as `feedback_instructions` only
  when the output carries feedback.

## Consequences

- The store gains schema step 5, the `feedback` table.
- `kmctl audit checks list` rows carry `human` and `disagrees`.
- Each page load refreshes the stored sections, as `kmctl audit claims
  todo` does, so the page shows which sections need extraction.
- Taking feedback in on any next submit means an agent can resubmit the
  same answer and close it; the page then shows the disagreement, and the
  person can send it back again.
- The page is the first kmctl surface that runs a server. It is local and
  ends with Ctrl-C; nothing in CI starts it.
- The decision model is still asked only when a person switches a question
  on in `audit.toml`; the button says so when it is off.
