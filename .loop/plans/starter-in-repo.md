---
type: plan
title: 'Plan: starter-in-repo'
description: The kmctl-starter copier template moves into the kmctl repository, versioned and tested with kmctl itself.
tags:
- plan
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T09:51:39+00:00'
slug: starter-in-repo
epic: multi-harness
depends_on: []
priority: 2
---

# starter-in-repo

Relayed from: none

## Intent

The operator asked (2026-10-18) to fold kmctl-starter (a separate repository,
/home/vscode/kmctl-starter, JasperHG90/kmctl-starter) into kmctl, accepting
the costs: copier.yml at kmctl's root, an update in generated projects at
every kmctl release, a one-time move for existing projects, and the starter
being exactly as public as kmctl. "When releasing, also bump the kmctl
version in copier immediately." The operator is away, so the loop is steered
without questions.

Measured over kmctl-starter's history (git log and `gh run list`, 2026-10-18):
5 of its 10 commits only move `kmctl_ref`'s pin to a kmctl release, and 2 more
(8ec63a6, the rename; 0796415, OpenCode) follow a kmctl change and needed a
kmctl ticket of their own. So 7 of 10 commits exist because the two repos are
apart, and this change makes 5 of them part of the release and the other 2
part of the kmctl ticket. Its CI failed 6 of its last 9 test runs, and its
one bump-kmctl run, because the runner cannot fetch private kmctl; the
bootstrap check is off. Built from this checkout, that check runs again.

Copier takes a template's versions from the tags of the repository it lives
in. Once the template is in kmctl, a kmctl release tag is the template's
version too, and the release sets `kmctl_ref`'s default to that same tag, so
`uvx copier copy gh:JasperHG90/kmctl` renders a project pinned to the
release it came from.

What changes:

- **The template.** kmctl-starter's `template/` moves to `new:starter/apm.yml.jinja`
  and `new:starter/justfile.jinja`, and the rest of its files under starter/, unchanged except as below.
  `new:copier.yml` at the root holds kmctl-starter's questions with
  `_subdirectory: starter`. Copier cannot point at a subfolder of a repository
  (spike 1 checks a root copier.yml with a subdirectory renders from a local
  clone and from a tag).
- **The release bumps the default.** `scripts/release.py` `set` also writes
  `kmctl_ref`'s default in copier.yml as `vVERSION` and lists it among the
  files it wrote; `.github/workflows/release.yml` stages copier.yml. So the
  version pull request, and the tag release-tag.yml puts on its merge,
  carry the bumped default. A pre-release writes a tag such as v0.6.0rc1,
  which `kmctl_ref`'s validator refuses today (it takes vX.Y.Z only), so the
  validator also takes an a, b or rc suffix. kmctl-starter's daily bump-kmctl workflow is not
  carried over: nothing is left for it to do.
- **just upgrade stays as it is.** It runs `copier update --defaults --data
  kmctl_ref=REF`: the template moves to the newest kmctl release and the pin
  to REF, which may be older (v0.4.0 or later, v0.5.1 or later for OpenCode,
  as the validator says today). Tying the template to REF with `--vcs-ref`
  would break moving to an older release, since copier refuses a downgrade,
  and no tag before this release has a template (plan review round 1, p1).
  The docs say so: the template follows the newest release, `kmctl_ref`
  picks the CLI and package.
- **Tests, built from this checkout.** `new:tests/test_starter.py` renders the
  template from this tree with copier (a dev dependency, `uv add --dev`) for
  each harness set kmctl-starter's CI ran ([claude], [antigravity], [opencode],
  [claude, antigravity], [claude, antigravity, opencode]), with `--vcs-ref
  HEAD` so copier reads the working tree rather than the newest tag, and checks the
  generated apm.yml, justfile and CI workflow; the validator refusals (a
  branch, OpenCode on a tag before v0.5.1) are checked too. An integration
  test runs `just bootstrap` in a generated project under a scratch HOME,
  with git rewriting https://github.com/JasperHG90/kmctl to a file:// bare clone of this tree,
  tagged at kmctl's version, then `kmctl check`
  and `kmctl doctor` with only the harness CLI, trust and dep checks left
  out. That replaces kmctl-starter's CI bootstrap, which was off because
  kmctl is private (spike 5: uv and APM 0.33.0 both follow a rewrite to a file:// bare
  clone, with both the .git and the bare form rewritten; APM refuses one to
  http://, spike 4). `.github/workflows/ci.yml` gains a starter job that runs the
  integration test, with just installed, so CI runs the bootstrap again.
- **Docs.** kmctl-starter's README becomes
  `new:docs/how-to/start-a-repository-with-kmctl-starter.md`, with the
  command `uvx copier copy gh:JasperHG90/kmctl my-project` and a section for
  projects made from kmctl-starter: point `_src_path` in .copier-answers.yml
  at gh:JasperHG90/kmctl and run `uvx copier recopy --defaults --skip-answered --overwrite`
  (spike 2: a plain `copier update` there leaves conflicts, because kmctl has
  its own v0.3.0 tag; recopy overwrites local edits to template files, so
  the page says to restore them from `git diff`).
  `README.md`'s starter paragraph and `docs/how-to/README.md` point at it.
  A decision, `new:.okf/decisions/0025-the-starter-template-lives-in-kmctl-and-shares-its-release-tags.md`,
  records why, the costs the operator accepted, and that tags before this
  release have no template.
- **The release and the old repository.** After landing: push main, run the
  release workflow (MINOR, a new thing ships: v0.6.0), merge its version pull
  request, and check `uvx copier copy gh:JasperHG90/kmctl` renders from
  v0.6.0 with `kmctl_ref` v0.6.0. Then kmctl-starter's README says it moved
  and how to move a project, that commit is pushed, and the repository is
  archived on GitHub (reversible).

Done when: the starter tests pass in the gates and in CI, the release is out
with copier.yml's default at its own tag, `uvx copier copy gh:JasperHG90/kmctl`
renders from it, and kmctl-starter is archived with a pointer.

Out of scope: changing the template's questions or the files it generates,
beyond the pre-release tags the validator takes and one defect the bootstrap
test found while building: in a bootstrapped project `just lint` fails on
files APM installs (okf's SPEC.md and SKILL.md whitespace, APM's JSON with no
final newline), which apm install writes again, so the template's
.pre-commit-config.yaml excludes the installed agent files.

## Could invalidate this plan

- Copier may not render a template whose copier.yml is at the root with
  `_subdirectory: starter` from a repository whose other tags (v0.5.1 and
  older) have no copier.yml, picking the newest tag. spike:starter-in-repo/1
- uv or APM 0.33.0 may not follow a git `url.<base>.insteadOf` rewrite from
  https://github.com/JasperHG90/kmctl to a local http server (APM may use
  GitHub's API for github.com), which leaves no way to bootstrap a generated
  project from this checkout. spike:starter-in-repo/5 (file:// works for
  both; spike:starter-in-repo/4: APM refuses a rewrite to http://)
- A project made from kmctl-starter records `_commit: v0.3.0`, a tag kmctl
  does not have, so `copier update` may fail after `_src_path` moves and no
  command may bring such a project onto the new template. spike:starter-in-repo/2
