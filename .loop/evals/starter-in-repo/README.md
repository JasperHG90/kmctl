---
type: eval
title: 'Eval: starter-in-repo'
description: 'Definition of done for starter-in-repo: 8 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T10:04:35+00:00'
slug: starter-in-repo
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 1562cf24d3947b9abe2797f66dd4fd81135f3687774f3ba9135035afe687a067
  at: '2026-10-18T10:04:35+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Rendering this tree with copier (copier.yml at the root, _subdirectory: starter) and --defaults, for each of [claude], [antigravity], [opencode], [claude, antigravity] and [claude, antigravity, opencode], writes the template's files and nothing from kmctl's root: an apm.yml whose targets are that set and whose kmctl entry is https://github.com/JasperHG90/kmctl.git, path apm, ref v<kmctl's version>; a justfile and .github/workflows/ci.yml pinned to that same tag; and apm.yml, .pre-commit-config.yaml and ci.yml parse as YAML.
  Fails when: copier fails, a target or pin differs, a pin is not v<the version apm/apm.yml holds>, a file of kmctl's own (src/, pyproject.toml, apm/, a kmctl README) appears in the output, or a file does not parse
- r2: copier.yml's kmctl_ref default is v followed by the version apm/apm.yml holds, so the template a tag carries pins that tag.
  Fails when: the default differs from v<apm/apm.yml's version>
- r3: copier refuses kmctl_ref set to a branch (main), and refuses harnesses [opencode] with kmctl_ref v0.5.0, naming v0.5.1; [claude] with v0.5.0 renders, and so does a pre-release tag such as v0.6.0rc1, the form release.py set writes for a pre-release.
  Fails when: a refused case renders, the OpenCode refusal does not name v0.5.1, or [claude] with v0.5.0 or a pre-release tag is refused
- r5: scripts/release.py set VERSION also writes copier.yml's kmctl_ref default as vVERSION, changing no other line of copier.yml, and lists copier.yml among the files it wrote; with no kmctl_ref default in copier.yml it refuses, naming copier.yml, and writes no file; release.yml's bump step stages copier.yml.
  Fails when: the default is not vVERSION after set, another copier.yml line changes, copier.yml is not listed, a copier.yml with no default is not refused or any file is written then, or release.yml's git add line omits copier.yml
- r6: In a project rendered from this tree for [claude, antigravity, opencode], under a scratch HOME and with git rewriting https://github.com/JasperHG90/kmctl to a file:// bare clone of this tree tagged v<version>, just bootstrap exits 0, the generated project's pre-commit hooks pass, kmctl check exits 0, and kmctl doctor fails no check except dep.claude, dep.agy, dep.opencode and antigravity.trust; the served copy, not GitHub, answered the fetches.
  Fails when: any step exits nonzero, doctor fails another check, or kmctl or kmctl's package came from anywhere but that clone
- r7: .github/workflows/ci.yml has a starter job that installs uv and just and runs uv run pytest tests/test_starter.py -m integration, so CI bootstraps a generated project from the checkout.
  Fails when: the job is missing, does not install just, or runs another command
- r8: A how-to page, docs/how-to/start-a-repository-with-kmctl-starter.md, gives uvx copier copy gh:JasperHG90/kmctl my-project, what copier asks and what a generated project holds, that the template follows the newest kmctl release while kmctl_ref picks the CLI and package (just upgrade vX.Y.Z moves the pin, older or newer, and brings the newest template), and how to move a project made from JasperHG90/kmctl-starter (_src_path to gh:JasperHG90/kmctl, then uvx copier recopy --defaults --skip-answered --overwrite, restoring local edits from git diff); README.md's starter paragraph and docs/how-to/README.md link it, and no tracked file outside .loop/ and that migration section names gh:JasperHG90/kmctl-starter; a decision records that the template lives in kmctl and shares its release tags, the costs, and that tags before the first release with the template have none; kmctl check passes.
  Fails when: any of those is missing, an old gh:JasperHG90/kmctl-starter command is left elsewhere, the decision does not match kmctl schema decision, or kmctl check fails
- r9: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
