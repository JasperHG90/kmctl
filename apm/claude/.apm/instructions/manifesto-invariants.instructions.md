---
applyTo: ".okf/manifesto.md, tests/**, test/**"
---

# Manifesto invariants

`.okf/manifesto.md` separates invariants (checked by a test) from values
(held by discipline). The values are the operator's to write; an agent
proposes them and does not decide them.

<constraint name="an-invariant-names-its-test">
WHY: an invariant nobody can point at is a wish, and a check can exist, be
cited, and still never fire.

Every invariant in `.okf/manifesto.md` carries a status:

- `planned`: no test pins it yet. Allowed until the change that builds the
  behaviour lands.
- `enforced`: it names the test that pins it, and that test passes.

Moving an invariant from `planned` to `enforced` happens in the same change
that adds its test, and the test drives the project from outside, as a user
would.
</constraint>

<constraint name="a-value-is-not-an-invariant">
WHY: calling a discipline an invariant makes a reader trust a check that
does not exist.

A rule with no test goes under Values in `.okf/manifesto.md`. Promoting a
value to an invariant means writing its test.
</constraint>
