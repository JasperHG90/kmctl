---
type: eval
title: 'Eval: kmctl-doctor'
description: 'Definition of done for kmctl-doctor: 10 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev173+ga4f6ce93a.d20261016
  at: '2026-10-16T20:27:16+00:00'
slug: kmctl-doctor
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: b21bbfadf20f6bb767bc9d21e2e745b47a8828b43509914ae1625b33680168cb
  at: '2026-10-16T20:27:16+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: In a repository holding a complete install for claude and antigravity (lock, deployed files, the Claude hook, .agents/plugins/kmctl/, .okf/ and docs/), with uv, git, claude and agy found on PATH, kmctl doctor prints one ok line per check and exits 0.
  Fails when: any check prints fail, or the exit code is not 0
- r2: Removing or breaking one installed piece makes doctor exit 1 with a fail line that names that piece and a fix command: a deployed skill file, a deployed file whose sha256 differs from the lock, the kmctl SessionStart entry in .claude/settings.json, a missing, extra or edited file under .agents/plugins/kmctl/ (compared with what the CLI would write), a missing apm_modules/, the okf-bundle MCP entry, apm.lock.yaml itself, a lock ref at a version other than the CLI's, a missing .okf/ or docs/.
  Fails when: for any of those cases doctor exits 0, or the fail line does not name the piece, or it carries no fix command
- r3: A missing dependency fails its own check with an install hint: uv or git not on PATH, claude not on PATH when the claude harness is installed, agy not on PATH when antigravity is installed; a harness that is not installed has no checks and no failures.
  Fails when: a missing dependency passes, its line has no fix, or a harness that is not installed reports a failure
- r3b: With --scope user, doctor checks the user-scope install (state in ~/.apm/, files and hook under CLAUDE_CONFIG_DIR); without --scope, a repository with no project harness but a user-scope install reports claude.scope ok naming kmctl doctor --scope user, not a failure.
  Fails when: a broken user-scope install passes with --scope user, or a user-scope install makes a project run fail or suggest a project install
- r4: kmctl doctor --json prints one JSON object {ok, checks:[{id, harness, ok, detail, fix}]} with the stable ids the plan lists, and the same exit codes as the text output.
  Fails when: the output is not valid JSON, a field is missing, an id differs from the plan's list, or the exit code differs from the text run
- r5: kmctl doctor writes nothing and opens no network connection unless --online is given; the only external command it runs is uv tool run --offline --from apm-cli==0.33.0 apm --version; the doctor logic lives in src/kmctl/doctor.py, returns results and prints nothing.
  Fails when: any file under the repository or HOME changes during a doctor run, a socket is opened without --online, any other external command runs, or src/kmctl/doctor.py prints or exits
- r6: The help and docs name the command: kmctl doctor --help says what it checks, its exit codes and --json/--online; docs/reference/commands.md documents it; kmctl plugin install and update end with a Next: kmctl doctor line; kmctl plugin status no longer exists (folded into doctor, the operator's choice).
  Fails when: the help or reference lacks doctor, its exit codes or its flags; install or update does not point to doctor; or kmctl plugin status still runs or is still documented
- r6b: Doctor fails claude.old-plugin when .claude/settings.json (or the user settings file under CLAUDE_CONFIG_DIR with --scope user) enables kmctl@kmctl or okf@scaccogatto, reading the file and never running claude plugin list; and fails antigravity.trust when agy is on PATH and the repository is not in trustedWorkspaces of agy's CLI settings; each with its fix.
  Fails when: either case passes, its line has no fix, or doctor runs claude plugin list
- r7: After a real kmctl plugin install --harness claude,antigravity into a scratch consumer (package served from a local git server at this tree, APM 0.33.0) and kmctl init, kmctl doctor exits 0.
  Fails when: the install fails or doctor exits nonzero
- r8: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
