---
name: practices-review
description: The review instructions for .okf/practices/ pages, used by the audit skill and its kmctl-auditor agent - does each practice still have the count or code site it cites as evidence? Use through /audit; read directly when someone asks how practices are judged.
---

# Practices review: is the evidence still there?

A practice is a lesson learned the hard way, backed by a count or a code site.
It is not checked for whether people follow it; it is checked for whether
its evidence still stands.

For each practice:

1. Find its evidence: a count (with how it was counted), a file and line, a
   test, a commit, a prototype in `.okf/prototypes/`.
2. Check the evidence still exists where it says: the file and the code it
   names are there, the prototype folder holds the script behind the count,
   the test still asserts what the practice says.
3. Check nothing later contradicts it: a decision that reverses it, or code
   that now makes the lesson moot.

`holds` when the evidence is where it says. `drifted` when a cited site moved
or is gone, or a later decision reverses the lesson. A count with no way to
rerun it is `unsure`.
