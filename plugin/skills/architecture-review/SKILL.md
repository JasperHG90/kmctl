---
name: architecture-review
description: The review instructions for .okf/architecture/ pages, used by the audit skill and its kmctl-auditor agent - does each design page and diagram still match the code it describes? Use through /audit; read directly when someone asks how architecture pages are judged.
---

# Architecture review: does the design still match the code?

An architecture page describes the parts of the system and how they connect.
It has drifted when the code no longer does what it says.

For each page:

1. List its concrete claims: module and file names, functions, commands, the
   order of a flow, which part calls which, data shapes, and the items in its
   `## Depicts` section if it has one.
2. Check each claim in the code: find the file, the function, the call. A
   renamed or removed thing, a flow in a different order, or a part that now
   calls something else is drift.
3. Check its lists. A list of keys, verbs, files, hooks, streams, stages or
   modules that a reader would take as complete (it says "every", "the", or
   gives a count, or it is the page's only list of them) must match the
   code's full list. A real item it leaves out is drift, even when every item
   it does name is right.
4. Check the page against the manifesto's invariants it names: an invariant
   the page says it shows must still exist in `.okf/manifesto.md`.

`holds` needs every checked claim found and every list complete. One false
claim or one missing list item is `drifted`, with the claim and the code
location that contradicts it. A diagram whose boxes and
arrows you cannot map to code is `unsure`; say which ones.
