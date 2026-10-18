---
type: eval
title: 'Eval: opencode-harness-reviewer-f6'
description: 'Definition of done for opencode-harness-reviewer-f6: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T05:32:50+00:00'
slug: opencode-harness-reviewer-f6
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 3408de1f710508d18fb968f83bdd37bd7db18902c410e96af4831353eaa8e7b8
  at: '2026-10-18T05:32:50+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl plugin patch --undo --scope user, run in a repository holding a patched OpenCode install and an Antigravity plugin folder, deletes and changes no file in it, exits 0, and prints one note naming the project-scope files it left and saying to run kmctl plugin patch --undo there without --scope user.
  Fails when: any file in the repository is deleted or changes, the exit code is not 0, or the note is missing, names none of the files, or does not name kmctl plugin patch --undo
- r2: kmctl plugin patch --undo at project scope still deletes the Antigravity plugin folder and OpenCode's kmctl files as before, and --undo --scope user in a folder with no kmctl files prints nothing to undo.
  Fails when: a project-scope undo leaves a kmctl file, or a user-scope undo with nothing here prints a note or exits nonzero
- r3: The --undo help and docs/reference/commands.md say that with --scope user it leaves the repository's Antigravity and OpenCode files alone and names them.
  Fails when: either the help or the reference does not say so
- r4: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
