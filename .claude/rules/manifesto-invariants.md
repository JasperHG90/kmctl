---
paths: [".okf/manifesto.md", ".okf/proposals/v2-build-plan.md", "tests/replay/**"]
---

# Manifesto invariants

`.okf/manifesto.md` separates invariants (mechanically enforced) from values
(held by discipline). v1 kept that split honest with an enforcer lock
(`tests/test_manifesto_enforcers.py` and `.manifesto/lock.json` in
`loop-harness-plugin`), which failed when a cited enforcer stopped resolving.
v2 keeps the idea and changes what an invariant cites.

<constraint name="an-invariant-names-its-replay-case">
WHY: an invariant nobody can point at is a wish, and v1 showed that a check
can exist, be cited, and still never fire.

Every invariant in `.okf/manifesto.md` names at least one replay case id
(`RC-NN`) from `.okf/proposals/v2-build-plan.md`, and carries a status:

- `planned`: the case is specified but not yet written. Allowed until the
  milestone that builds the invariant lands.
- `enforced`: the case exists in the replay suite and passes.

A test (ported from v1's enforcer lock in M1) fails when an `enforced`
invariant names a case that does not exist, or when a case is removed while
an invariant still names it. Moving an invariant from `planned` to `enforced`
happens in the same change that adds its case.
</constraint>

<constraint name="replay-cases-test-from-outside">
WHY: v1's tests mostly pinned internals, so cutting the internals would have
deleted the evidence that the behavior held.

A replay case drives the CLI, a hook entry or `git commit` from outside and
asserts refuse, allow or stale. It imports no harness module. A case that
must pass against both v1 and v2 is pinned at the git-commit and hook
boundary, because v2 renames stages and `loopctl advance` cases cannot run
unchanged against v1.
</constraint>

<constraint name="a-value-is-not-an-invariant">
WHY: calling a discipline an invariant makes a reader trust a check that
does not exist.

A rule with no replay case goes under Values in `.okf/manifesto.md`,
labeled as such. Promoting a value to an invariant means writing its case.
</constraint>
