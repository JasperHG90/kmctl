---
paths: [".okf/**", "src/kmctl/**/*.py", "plugin/hooks/**"]
---

# Diagrams stay current

The design diagrams in `.okf/architecture/` are believed the way an index is
believed, so a stale one is worse than none.

<constraint name="a-design-change-updates-its-diagram">
WHY: a diagram nobody updates in the same change is wrong by the next one.

Each diagram lists what it depicts in its front matter (`depicts:`, with
invariant ids from `.okf/manifesto.md` and structure check ids from
`.okf/proposals/v2-build-plan.md`). A change to anything a diagram depicts
updates that diagram in the same change: a stage or transition, an
invariant, a store, a write path, a hook entry, a CLI verb in a flow, or a
module boundary. A new invariant or write path that no diagram depicts gets
added to one.
</constraint>

<constraint name="diagrams-are-checked">
WHY: v2's lesson is that a rule nobody checks is a wish.

Until M1, whoever changes a diagram runs the id check by hand: every
`depicts:` id resolves, and every invariant appears in at least one list.
From M1, ST-08 runs it as a gate. From M3, ST-08 also checks that the
lifecycle diagram's stages and edges equal the code's stage enum and
transition table. Any review of a design change compares the changed
diagrams with the manifesto.
</constraint>
