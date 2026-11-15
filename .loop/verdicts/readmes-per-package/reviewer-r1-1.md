---
type: verdict
title: 'Verdict: readmes-per-package reviewer round 1'
description: 'reviewer verdict for round 1 of readmes-per-package: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T19:11:46+00:00'
slug: readmes-per-package
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. The root README is a 42-line map, kmctl's README carries all of the old root content with working `../../docs` links, kmaudit's reference moved with `git mv` to `docs/reference/kmaudit-commands.md` with front matter, `packages/kmaudit/docs/` is gone, and the release scripts, workflow and tests follow. The gates are green on my own run. One small consistency gap stays: two CLI strings still point at "the README's install section", which the root README no longer has. It is a plain wording fix, so the label is fix.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and integration all pass, eval rows r1 to r5 all pass, `stamp green: 8d6f88d8732f7a1f8bc06c8f3c8702be74ec31810cc6b571036e1d690f5c1df9`.
- `uv run kmctl check`: "all checks passed".
- Nothing lost: I diffed the old root README (HEAD) against the new packages/kmctl/README.md. The only differences are the link prefixes (`../../docs/...`, logo `../../docs/assets/logo.png`), the "Two packages" section shortened to one paragraph linking `../kmaudit/README.md`, and "Working on kmctl" moved into the new root README's "Working on this repository" with the same facts (uv sync, just lint/test/integration, kmaudit tests under the root pytest). The old 11-line package stub's content is covered by the new file.
- Links: tests/test_readmes.py resolves every relative link and img src in all three READMEs. I checked the anchors by hand: `#mcp-server` exists in packages/kmaudit/README.md, `#kmaudit-mcp` and all in-page anchors in kmaudit-commands.md are unchanged, `#before-you-start` exists in the APM how-to. Paths are all file-relative, so they resolve the same way on GitHub.
- Leftover old paths: `git grep` for `packages/kmaudit/docs` and `docs/commands.md` finds only `.loop/` history and the ADR 0012 correction that names the move on purpose. The release skill names neither file.
- r1: tests/test_readmes.py asserts fewer than 80 lines, links to both package READMEs and into docs/, and that each link resolves. It would fail on each `fails_when` case.
- r2: test_readme_install_and_links reads packages/kmctl/README.md and asserts the install line, the apm.yml entry (`git:` and `path: packages/kmctl/apm`), the four harness headings, Upgrade, Remove and `--undo`, and that every kmctl docs page is linked and every link exists. The other tests that read kmctl's README (doctor, opencode, pin, plugin_patch, starter) now read the package file.
- r3: test_mcp asserts every listed tool and every kept command heading in the moved page, that `packages/kmaudit/docs` does not exist, and that the README links the new path. test_docs_frontmatter runs `run_checks(ROOT)` on the real tree, which covers "kmctl check passes".
- r4: test_release pins in the new files (DOC_FILES, KMAUDIT_DOCS) and checks that the root README has no install line. test_release_paths has rows for `kmaudit-*` pages and near-misses (`x-kmaudit-y.md`, `packages/kmctl/kmaudit-x.md`). test_workflows compares the bump's `git add` lines against the constants in release.py, so a stale workflow path would fail.
- r5: `_install_lines` sorts kmaudit lines by name, tag or subdirectory, and `_wrong_install_lines` holds them to `packages/kmaudit` at a `kmaudit-v` tag or `$tag`. test_install_lines_pass_after_a_kmaudit_pin runs the real `release.py --package kmaudit set 0.2.0` on a copy, then asserts exactly the two expected files are pinned, kmctl's lines did not change, and the check passes. Before this change, the old test would have failed here because `subdirectory_fragment('kmaudit-v0.2.0')` returns kmctl's folder.
- owns() in scripts/release_paths.py: only `docs/` paths whose base name starts with `kmaudit-` go to kmaudit, and kmctl's branch excludes them. The docstring, the docs-layout rule and the ADR 0012 correction all say the same thing.
- Prose: the root README, the ADR correction, the log line and the rule edits are plain and accurate.

## Findings

- f1 (docs, not blocking): `kmctl plugin patch --help` and the "lists no kmctl package" refusal in plugin.py still say "the README's install section". Since the root README is now a map, a user who follows that hint lands on a page with no install steps. The fix is to name kmctl's README, as commands.md now does.

## Notes

- The builder's noted gap is real but small. When someone adds or retitles a kmaudit page, `kmctl check --fix` rewrites the generated `docs/reference/README.md` index, which kmctl owns, so that commit appears in both packages' notes. A body edit to the kmaudit page goes to kmaudit only. The commit still lands in kmaudit's notes as the rule promises, so the cost is one extra line in kmctl's draft notes, which the release rule already has people review. I do not ask for a change.
- ADR 0021 line 54 still says "The README's install section". It is a decision record from when that was true, so I leave it.
