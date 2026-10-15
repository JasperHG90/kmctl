# Log

## 2026-10-15

- Seeded the bundle: the manifesto and six decisions from the design
  discussion in loop-harness, which this repository formalizes.
- Added `decisions/0007-skills-are-made-with-skill-creator` and
  `decisions/0008-handoffs-are-okf-concepts` at the operator's request, and
  named both in `manifesto`: the plugin gains /handoff and /continue, and
  every skill is made with skill-creator.
- Added `decisions/0009-handoff-key-extension-field` and reworded I4 in
  `manifesto` to allow extension fields an ADR names, after the
  handoff-and-continue-skills plan review found the key broke I4.
- Marked invariants I1 and I3 in `manifesto` enforced, naming the tests
  that pin them: the plugin's hook tests and the briefing word budget.
- Marked invariant I4 in `manifesto` enforced by tests/test_okf_fields.py.
- Removed `decision_status` and `decided_on` from
  `decisions/0001-standalone-cli-installs-its-plugin`, which no ADR allows
  (I4) and appended a Correction with the Consequences it lacked, after the
  first audit of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0002-briefing-and-rules-injected-by-the-cli`, which no ADR allows
  (I4) and appended a Correction with the Consequences it lacked, after the
  first audit of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0003-claude-code-plugin-first-depends-on-okf`, which no ADR
  allows (I4) and appended a Correction with the Consequences it lacked, after
  the first audit of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0004-sessionstart-is-the-only-hook`, which no ADR allows (I4) and
  appended a Correction with the Consequences it lacked, after the first audit
  of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0005-audits-report-only`, which no ADR allows (I4) and appended a
  Correction with the Consequences it lacked, after the first audit of this
  bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0006-staleness-from-okf-fields`, which no ADR allows (I4) and
  appended a Correction with the Consequences it lacked, after the first audit
  of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0007-skills-are-made-with-skill-creator`, which no ADR allows
  (I4), after the first audit of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0008-handoffs-are-okf-concepts`, which no ADR allows (I4) and
  appended a Correction with the Consequences it lacked, after the first audit
  of this bundle.
- Removed `decision_status` and `decided_on` from
  `decisions/0009-handoff-key-extension-field`, which no ADR allows (I4),
  after the first audit of this bundle.
- Added the architecture section with `architecture/overview`: the CLI
  modules, the plugin and the action, with a diagram whose Depicts section
  names I1 to I4. Linked it from the root index.
