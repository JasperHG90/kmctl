---
paths: [".okf/**", "src/**", "lib/**", "app/**", "pkg/**", "cmd/**"]
---

# Diagrams stay current

The design diagrams in `.okf/architecture/` are believed the way an index is
believed, so a stale one is worse than none. The `paths:` above name common
source folders; change them to where this repository's code lives.

<constraint name="a-design-change-updates-its-diagram">
WHY: a diagram nobody updates in the same change is wrong by the next one.

Each diagram ends with a `## Depicts` section listing what it shows:
invariant ids such as `I1` from `.okf/manifesto.md`, entry points such as
commands or routes, and modules or files. It is a body section, not front
matter, so it adds no OKF field. A change to anything a diagram depicts
updates that diagram in the same change: an invariant, an entry point in a
flow, or a module boundary. A new invariant that no diagram depicts gets
added to one. Once there is code, there is at least one diagram.
</constraint>

<constraint name="diagrams-are-checked">
WHY: a rule nobody checks is a wish.

Until a test does it, whoever changes a diagram checks by hand that every
id in its Depicts section resolves and every invariant appears in at least
one diagram. Any review of a design change compares the changed diagrams
with the manifesto.
</constraint>
