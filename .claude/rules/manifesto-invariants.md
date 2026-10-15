---
paths: [".okf/manifesto.md", "tests/**"]
---

# Manifesto invariants

`.okf/manifesto.md` separates invariants (checked by a test) from values
(held by discipline).

<constraint name="an-invariant-names-its-test">
WHY: an invariant nobody can point at is a wish, and a check can exist, be
cited, and still never fire.

Every invariant in `.okf/manifesto.md` carries a status:

- `planned`: no test pins it yet. Allowed until the ticket that builds the
  behaviour lands.
- `enforced`: it names the test that pins it, and that test passes.

Moving an invariant from `planned` to `enforced` happens in the same change
that adds its test, and the test drives `kmctl` or the plugin's hook from
outside, as a user would.
</constraint>

<constraint name="a-value-is-not-an-invariant">
WHY: calling a discipline an invariant makes a reader trust a check that
does not exist.

A rule with no test goes under Values in `.okf/manifesto.md`. Promoting a
value to an invariant means writing its test.
</constraint>
