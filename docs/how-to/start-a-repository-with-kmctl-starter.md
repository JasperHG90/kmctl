---
description: "Start a new repository from kmctl's copier template, keep it current with just upgrade, and move a project made from the old kmctl-starter repository."
---

# Start a repository with kmctl-starter

kmctl-starter is a [copier](https://copier.readthedocs.io/) template for a
new repository that keeps its knowledge with kmctl: user docs in `docs/`, a
knowledge bundle for people and agents in `.okf/`, and kmctl's skills, rules
and session briefing installed for your agent harness through
[APM](https://github.com/microsoft/apm) (Agent Package Manager). It sets up no
language; add your language's tooling on top.

The template lives in the kmctl repository: `copier.yml` at its root, the
files in `starter/`. Copier takes the template's versions from kmctl's
release tags, so each kmctl release is also a template release, and its
`kmctl_ref` default is that release.

## Generate a project

Needs [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/).

```
uvx copier copy gh:JasperHG90/kmctl my-project
cd my-project
git init
just bootstrap
```

Use copier rather than GitHub's "Use this template" button: the button
copies the whole kmctl repository.

copier asks:

| Question | Becomes |
|---|---|
| `project_name` | The name in `apm.yml` and the README. |
| `project_description` | The first line of the README and `AGENTS.md`. |
| `codeowners` | `.github/CODEOWNERS`, the reviewers of every change. |
| `harnesses` | Claude Code, Antigravity, OpenCode (2.x only), or any of them together: the targets in `apm.yml`. |
| `kmctl_ref` | The kmctl release tag, by default the release the template comes from, used for the package in `apm.yml`, the kmctl the justfile runs and the CI checks, so all three match. v0.4.0 or later (the first release with `kmctl plugin patch`), v0.5.1 or later for OpenCode. A branch is refused. |
| `apm_version` | The APM version the justfile runs through `uvx`. |

## What a generated project holds

| File | What it does |
|---|---|
| `apm.yml` | APM's manifest, with kmctl's package at `kmctl_ref` and the harnesses as targets. Commit `apm.lock.yaml` after the first install. |
| `justfile` | `bootstrap` (the three below), `kmctl` (install the CLI on your PATH, which the session hooks call), `install` (`apm install` for `apm.yml`'s targets, then `kmctl plugin patch` for what APM cannot install yet), `init` (`kmctl init`: `docs/`, `.okf/` and kmctl's block in `AGENTS.md`), `upgrade` (move to another kmctl release), plus `install-frozen` (exactly what the lock records), `lock`, `outdated`, `check` (`kmctl check` and `kmctl doctor`) and `lint` (the pre-commit hooks). The recipes run APM and kmctl at the pinned versions through `uvx`. |
| `AGENTS.md` | The project's name and description. `just init` adds kmctl's section on where knowledge lives, and writes `CLAUDE.md`, which imports `AGENTS.md` for Claude Code; Antigravity and OpenCode read `AGENTS.md` directly. |
| `.github/workflows/ci.yml` | Two jobs: the pre-commit hooks, and kmctl's checks (`kmctl check` fails the job on a broken bundle; `kmctl review due` goes to the job summary). |
| `.github/CODEOWNERS` | The owners you named. |
| `.pre-commit-config.yaml` | Generic hooks only: whitespace, line endings, YAML, TOML and JSON syntax, merge markers, large files, private keys. They skip the agent files APM and `kmctl plugin patch` install (`.agents/`, `.claude/agents/`, `rules/` and `skills/`, `.opencode/`, `opencode.json`), which `apm install` writes again. Run with `just lint` ([prek](https://github.com/j178/prek)). |
| `.gitignore` | APM's package cache, `apm_modules/`. |
| `.copier-answers.yml` | Your answers, so `uvx copier update` can bring in a newer template. |

## Keep a project current

Run `just upgrade vX.Y.Z` on a clean tree to move to another kmctl release,
newer or older. It runs `uvx copier update --defaults --data
kmctl_ref=vX.Y.Z`, which brings in the newest template and rewrites
`apm.yml`, the justfile, CI and `.copier-answers.yml` for that pin, then
`just kmctl install`. Commit the changes, `apm.lock.yaml` among them.

The template always follows the newest kmctl release, while `kmctl_ref`
picks the CLI and package. A new kmctl release is a new template version
even when the template did not change; `uvx copier update` then changes
only `_commit` in `.copier-answers.yml`, a one-line change to commit.

Releases before v0.6.0 have no template, so copier cannot render from them.

## Move a project made from kmctl-starter

Until v0.6.0 the template lived in its own repository, JasperHG90/kmctl-starter,
now archived. A project made from it records `_src_path:
gh:JasperHG90/kmctl-starter` in `.copier-answers.yml`, and a `_commit` from
that repository. Move it once, on a clean tree.

If `_commit` is older than v0.3.0, kmctl-starter's last release, update to
that first:

```
uvx copier update --defaults --skip-answered --vcs-ref v0.3.0
```

Then point the answers at kmctl, at v0.6.0, the first release with the
template:

```
sed -i -e 's|^_src_path: .*|_src_path: gh:JasperHG90/kmctl|' \
  -e 's|^_commit: .*|_commit: v0.6.0|' .copier-answers.yml
git commit -am "Take the starter template from kmctl"
```

v0.6.0's template is kmctl-starter v0.3.0's plus one change. Make that
change by hand: add these lines to `.pre-commit-config.yaml`, above
`repos:`, so the hooks leave the agent files APM
installs as they are:

```
# APM and kmctl plugin patch write the agent files below, and apm install
# writes them again, so the hooks leave them as installed.
exclude: ^(\.agents/|\.claude/(agents|rules|skills)/|\.opencode/|opencode\.json$)
```

From here `just upgrade` and `uvx copier update --defaults --skip-answered`
work as above, and keep your own changes to the files the template writes.
Change `_commit` along with `_src_path`: with only `_src_path` changed,
copier looks up v0.3.0 in kmctl, finds kmctl's own v0.3.0 tag, which has no
template, and leaves conflicts.
