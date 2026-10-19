---
type: eval
title: 'Eval: doctor-correct-setups'
description: 'Definition of done for doctor-correct-setups: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:33:44+00:00'
slug: doctor-correct-setups
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: e9c1dab834c6da237d5d4668a3a60cabbc4d11964bda6f55557d3a8317f85a97
  at: '2026-10-19T14:33:44+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: In a repository installed for claude and antigravity, kmctl doctor with neither claude nor agy on PATH exits 0 and prints warn dep.claude and warn dep.agy.
  Fails when: doctor exits nonzero, or either line is not a warn line
- r2: With agy on PATH and the folder missing from its trustedWorkspaces, doctor exits 0 with warn antigravity.trust, and the detail says trust given in the Antigravity IDE is not checked.
  Fails when: doctor exits nonzero, the line is not warn, or the detail does not mention the IDE
- r3: With okf@scaccogatto enabled only in the user settings.json under CLAUDE_CONFIG_DIR, a project-scope run exits 1 with fail claude.old-plugin naming that file and the fix claude plugin uninstall okf@scaccogatto --scope user.
  Fails when: the check passes, does not name the user settings file, or prints another fix
- r4: kmctl doctor --json gives each check a status of ok, warn or fail, with ok true for a warning.
  Fails when: a check lacks status, or a warning has ok false
- r5: A user-scope kmctl@kmctl does not mark the claude harness as installed in the project.
  Fails when: harnesses_found or _kmctl_mark at project scope reports claude from a user-scope plugin alone
- r6 (judgment): docs/reference/commands.md and the doctor epilog describe the warn outcome, the status field and the changed checks, and no doctor test reads the real ~/.claude or ~/.gemini.
  Fails when: the docs or epilog still say a missing harness CLI fails, or a test reads the real home folders
