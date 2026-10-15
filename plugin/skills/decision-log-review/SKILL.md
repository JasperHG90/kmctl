---
name: decision-log-review
description: The review instructions for .okf/decisions/ records, used by the audit skill and its kmctl-auditor agent - does each decision still hold, or has a later decision or the code overtaken it? Use through /audit; read directly when someone asks how decision records are judged.
---

# Decision-log review: does the decision still hold?

A decision record says what was chosen, why, and what was rejected. Records
are never rewritten; a decision that no longer holds is superseded by a new
one (`kmctl decision supersede`).

For each record:

1. List every concrete thing the decision commits the code or the process
   to: a tool, a file layout, a rule, a field, a command, and any claim about
   another part ("the briefing names which skill to use"). Check each one,
   not just the headline.
2. Check the code still does that. Code that does what the record rejected,
   or that contradicts its decision, is drift.
3. Check later records (higher numbers) and the manifesto for anything that
   reverses or narrows it without a supersede link. A later record that
   changes it without saying so is drift on the older record.
4. Check the record itself against the repository's rules for decision
   records (for example `.claude/rules/okf-bundle.md`, or the bundle's own
   index): the sections it must have (such as Context, Decision with the
   rejected alternative, and Consequences), and front matter fields the spec
   or an ADR does not allow. A missing section or an unapproved field is drift.
5. A record a later one changed must link to it, and the later one back. A
   record with `status: deprecated` and a Correction section naming its
   successor is fine as it is; check only that the successor exists and that
   no other field still says it is in force.

`holds` when the code and later records agree with it. `drifted` names what
overtook it and where, and suggests whether it needs a superseding record. A
decision about process you cannot see in the repository is `unsure`.
