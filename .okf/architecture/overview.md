---
type: architecture
title: "Architecture overview"
description: "The parts of kmctl (the CLI modules, the Claude Code plugin and the GitHub Action) and how they connect."
generated:
  by: claude-opus/5.5
  at: 2026-10-16
tags: [architecture, diagram]
status: stable
---

# Architecture overview

kmctl has three parts (manifesto, Parts). The CLI in `src/kmctl/` does every
step a script can do and is the only part that writes knowledge. The plugin
in `plugin/` and the action in `action.yml` and `action/` call the CLI; they
hold no logic of their own beyond relaying it, and the audit they run reads
and reports only. `apm/apm.yml` packages the plugin for APM, a second install
route (ADR 0013). Releases come from two workflows and the scripts in
`scripts/` (ADR 0012).

```mermaid
flowchart LR
    subgraph plugin["plugin/ (Claude Code plugin)"]
        hook["hooks/hooks.json<br/>SessionStart"]
        writeDocs["skills/write-docs"]
        handoff["skills/handoff"]
        cont["skills/continue"]
        audit["skills/audit"]
        reviews["skills/architecture-review<br/>decision-log-review<br/>practices-review"]
        auditor["agents/kmctl-auditor<br/>Read, Grep, Glob"]
    end

    subgraph cli["src/kmctl/ (kmctl CLI)"]
        app["__init__.py<br/>Typer app"]
        scaffold["scaffold.py<br/>init"]
        repoRules["repo_rules/*.md"]
        checks["checks.py<br/>check"]
        briefing["briefing.py<br/>briefing"]
        rules["rules/*.md"]
        reviewDue["review_due.py<br/>review due"]
        handoffs["handoffs.py<br/>handoffs"]
        concepts["concepts.py<br/>new decision|practice|<br/>proposal|prototype|handoff"]
        docs["docs.py<br/>new doc"]
        supersede["supersede.py<br/>decision supersede"]
        pluginPy["plugin.py<br/>plugin install|update|status"]
        okf["okf.py<br/>reads front matter"]
        kinds["kinds.py<br/>schema; the table of kinds"]
    end

    subgraph action["action.yml (GitHub Action)"]
        ci["action/knowledge-ci.sh<br/>mode: checks"]
        auditSh["action/knowledge-audit.sh<br/>mode: audit"]
        batchesPy["action/audit-batches.py"]
        report["action/audit-report.py"]
        readTools["action/hermes/kmctl-read<br/>kmctl_read_file, kmctl_search_files,<br/>kmctl_list_files"]
        issueSh["action/knowledge-audit-issue.sh<br/>own step, GH_TOKEN"]
    end

    subgraph release["releases (ADR 0012)"]
        releaseYml[".github/workflows/release.yml<br/>by hand: version pull request"]
        releaseTag[".github/workflows/release-tag.yml<br/>on a manifest change on main"]
        releasePy["scripts/release.py<br/>current, set, compare"]
        nextVersion["scripts/next_release_version.py"]
        wheelChecks["scripts/check_wheel.py<br/>scripts/smoke_wheel.py"]
    end

    manifest[("plugin/.claude-plugin/plugin.json<br/>the one version")]
    apmPkg["apm/apm.yml<br/>APM package"]
    apmCli["apm CLI<br/>in the consumer"]
    okfSkills["scaccogatto/okf-skills<br/>pinned commit"]
    ghRelease["v* tag and GitHub Release<br/>wheel, sdist, SHA256SUMS"]
    repo[("docs/ and .okf/")]
    agentFiles[(".claude/rules/ and<br/>CLAUDE.md, AGENTS.md")]
    claude["claude CLI"]
    hermes["hermes CLI<br/>any OpenAI-compatible endpoint"]
    summary["job summary and<br/>Knowledge audit issue"]

    hook -- "kmctl briefing" --> briefing
    writeDocs -- "kmctl new doc, kmctl check" --> app
    handoff -- "kmctl new handoff" --> app
    cont -- "kmctl handoffs --json" --> handoffs
    audit -- "kmctl review due --json" --> reviewDue
    audit --> reviews
    audit -- "dispatches" --> auditor
    auditor -. "reads only" .-> repo

    app --> scaffold & checks & briefing & reviewDue & handoffs & concepts & docs & supersede & pluginPy & kinds
    briefing --> reviewDue & handoffs & rules
    briefing -- "skills_dir: names the plugin's skills" --> pluginPy
    concepts & handoffs & reviewDue & supersede --> okf
    docs & supersede --> concepts
    scaffold & concepts & docs & supersede -- "skeletons, status values" --> kinds
    kinds -- "ALLOWED_FIELDS" --> okf
    scaffold -- "first decision" --> concepts
    scaffold --> repoRules
    scaffold & concepts & docs & supersede -- "write" --> repo
    scaffold -- "write: .claude/rules/,<br/>CLAUDE.md / AGENTS.md block" --> agentFiles
    checks & okf -. "read" .-> repo
    pluginPy -- "stages plugin/, then<br/>claude plugin install" --> claude
    apmCli -- "apm install<br/>.../apm#vX.Y.Z" --> apmPkg
    apmPkg -- "git: parent, path: plugin" --> plugin
    apmPkg --> okfSkills

    ci -- "kmctl check,<br/>kmctl review due" --> app
    auditSh -- "kmctl review due --json" --> reviewDue
    auditSh -. "puts their text in the prompt" .-> audit & reviews & auditor
    auditSh -- "splits the due list,<br/>merges each batch's findings" --> batchesPy
    auditSh -- "hermes -z -t kmctl_read per batch<br/>fresh HOME, under timeout" --> hermes
    hermes --> readTools
    readTools -. "reads only, inside the repository" .-> repo
    auditSh --> report --> summary
    report -- "body in RUNNER_TEMP" --> issueSh
    issueSh -- "gh issue create or edit" --> summary
    ci --> summary

    releaseYml -- "next version from v* tags" --> nextVersion
    releaseYml -- "set: version, docs' install lines" --> releasePy
    releasePy -- "write" --> manifest
    releasePy -- "write: version copy" --> apmPkg
    releaseYml -- "uv build, then check" --> wheelChecks
    releaseYml -- "commits it on release/vX.Y.Z,<br/>gh pr create" --> manifest
    manifest -- "merged to main" --> releaseTag
    releaseTag -- "compare old and new" --> releasePy
    releaseTag -- "uv build, then check" --> wheelChecks
    releaseTag -- "tag after the build,<br/>gh release create" --> ghRelease
    app -. "kmctl --version reads it<br/>through pyproject's regex source" .-> manifest
```

## The CLI

`src/kmctl/__init__.py` holds the Typer app and only parses, prints and sets
exit codes. Each verb calls one module:

| Verb | Module | Writes |
|---|---|---|
| `kmctl init` | `scaffold.py`, with the packaged `repo_rules/` and `concepts.py` for the first decision | `docs/README.md`, a starter `.okf/`, the four knowledge rules in `.claude/rules/`, the kmctl block in `CLAUDE.md` and `AGENTS.md`, and decision "Keep project knowledge in an OKF bundle"; it keeps every file that exists except for that block and the decision's index entry and log line (ADR 0011) |
| `kmctl check` | `checks.py` | nothing |
| `kmctl briefing` | `briefing.py`, with `review_due.py`, `handoffs.py`, the packaged `rules/`, and `plugin.py` for the skills it names | nothing |
| `kmctl review due` | `review_due.py` | nothing |
| `kmctl handoffs` | `handoffs.py` | nothing |
| `kmctl schema` | `kinds.py`, with `okf.py` for the field names | nothing |
| `kmctl new decision`, `practice`, `proposal`, `prototype`, `handoff` | `concepts.py`, with `okf.py` to find each `--source` the way `review_due.py` does | the concept, its section index entry and a log line; `--stale-after` and `--source` write its `stale_after` and `sources` |
| `kmctl new doc` | `docs.py` | the page and its `docs/README.md` entry |
| `kmctl decision supersede` | `supersede.py` | both decision records and a log line |
| `kmctl plugin install`, `update`, `status` | `plugin.py` | the staged plugin in `$XDG_DATA_HOME/kmctl/marketplace`, then `claude plugin` installs it |

`kinds.py` holds the one table of document kinds: each kind's front matter
fields, its status values and its `##` sections. `kmctl new`, `kmctl new doc`,
`kmctl init` and `kmctl decision supersede` take their skeletons, the
manifesto's sections and the status they write from it, and `kmctl schema`
prints a JSON Schema built from it, so the schema is what kmctl writes.

`okf.py` is the one reader of OKF front matter. `concepts.py`, `handoffs.py`,
`review_due.py` and `supersede.py` read fields through it, so the fields kmctl
uses are the ones the OKF v0.2 spec defines plus `handoff_key` (I4, ADR 0006,
ADR 0009).

## The plugin

The plugin ships inside the kmctl wheel (ADR 0001), so `kmctl plugin install`
always installs the plugin of the same release. It depends on the `okf`
plugin from the scaccogatto marketplace (ADR 0003).

- **One hook.** `hooks/hooks.json` has one SessionStart hook. It runs
  `kmctl briefing` and exits 0 even when kmctl is missing or fails (I1,
  ADR 0004). The briefing is whatever the CLI prints, so upgrading the CLI
  updates it, and its word count has a fixed budget (I3, ADR 0002).
- **Skills route; kmctl writes.** `write-docs`, `handoff` and `continue` call
  `kmctl new doc`, `kmctl new handoff` and `kmctl handoffs`, so the file
  structure always comes from the CLI.
- **A second route through APM.** `apm/apm.yml` depends on
  `{git: parent, path: plugin}` and a pinned `scaccogatto/okf-skills`, so
  `apm install JasperHG90/Knowledge-management/apm#vX.Y.Z` writes the skills,
  the agent and the hook into the consumer's `.claude/`, with okf's skills.
  It does not install the CLI or check its version, so `kmctl plugin
  install` stays the main route (ADR 0013). `plugin/` has no apm.yml of its
  own.
- **The audit reads only.** The `audit` skill takes the due list from
  `kmctl review due --json`, batches it, and dispatches the `kmctl-auditor`
  agent with one of the three review skills. The auditor's tools are Read,
  Grep and Glob (I2, ADR 0005).

## The action

`action.yml` is a composite action with two modes. Both install kmctl from the
action's own checkout.

- **checks** (the default) runs `action/knowledge-ci.sh`: `kmctl check` and
  `kmctl review due` into the job summary, failing when `kmctl check` fails
  or `kmctl review due` crashes, never because a concept is due.
- **audit** (opt-in) runs `action/knowledge-audit.sh`, only on
  `workflow_dispatch` or `schedule`. It filters `kmctl review due --json` to
  architecture, decisions and practices, and runs Hermes Agent against any
  OpenAI-compatible endpoint (ADR 0010). It writes Hermes' config into a
  fresh HOME, installs kmctl's Hermes plugin there, and passes
  `-t kmctl_read`, so the model's only tools are the plugin's
  `kmctl_read_file`, `kmctl_search_files` and `kmctl_list_files`. They are
  plain Python, start no program and refuse any path outside the repository.
  `action/audit-batches.py` splits the due list by kind into batches of at
  most ten, and Hermes runs once per batch. Each prompt carries the audit
  skill, the kmctl-auditor instructions and that kind's review skill as text.
  `timeout` gives each run the time left of one budget for the whole audit.
  `action/audit-batches.py` merges each run's last json block, and
  `action/audit-report.py` turns the merged list into the job summary and an
  issue body (I2). It
  never edits or pushes, and it refuses to start when the model could read a GitHub token
  (`GH_TOKEN` or `GITHUB_TOKEN` set, or checkout's credentials in git config).
  A later step of its own, `action/knowledge-audit-issue.sh`, is the only one
  that gets `GH_TOKEN`; it posts the body to the one "Knowledge audit" issue.

## Releases

The version is written once, in `plugin/.claude-plugin/plugin.json`;
`pyproject.toml` reads it with hatchling's `regex` version source, so
`kmctl --version`, the plugin stamp and a build from a download with no `.git`
agree (ADR 0012).

- `.github/workflows/release.yml` runs by hand. It works out the version with
  `scripts/next_release_version.py`, refuses a real run off `main` or a tag
  that exists, runs the lint and the tests, and builds and checks the wheel
  with `scripts/check_wheel.py` and `scripts/smoke_wheel.py`. A real run
  commits `scripts/release.py set` (the manifest, the version copies in
  `apm.yml` and `apm/apm.yml`, the docs' five install lines and the APM
  how-to's pin) on `release/vX.Y.Z` and opens the version pull request.
- `.github/workflows/release-tag.yml` runs when a push to `main` changes the
  manifest. When `scripts/release.py compare` says the version went up, it
  builds and checks first, then pushes the tag `vX.Y.Z` and publishes the
  GitHub Release with the wheel, the sdist and `SHA256SUMS`. Nothing goes to
  PyPI.

## Depicts

- Invariants: I1 (the SessionStart hook never blocks), I2 (the auditor and
  the action's audit mode read only), I3 (the hook prints `kmctl briefing`),
  I4 (`okf.py` reads OKF fields for every module).
- Verbs: `kmctl init`, `kmctl check`, `kmctl briefing`, `kmctl review due`,
  `kmctl handoffs`, `kmctl new decision`, `kmctl new practice`,
  `kmctl new proposal`, `kmctl new prototype`, `kmctl new handoff`,
  `kmctl new doc`, `kmctl schema`, `kmctl decision supersede`, `kmctl plugin install`,
  `kmctl plugin update`, `kmctl plugin status`.
- Modules: `src/kmctl/__init__.py`, `scaffold.py`, `checks.py`,
  `briefing.py`, `rules/`, `repo_rules/`, `review_due.py`, `handoffs.py`, `concepts.py`,
  `docs.py`, `supersede.py`, `plugin.py`, `okf.py`, `kinds.py`; `plugin/hooks/hooks.json`,
  `plugin/skills/` (write-docs, handoff, continue, audit and the three review
  skills), `plugin/agents/kmctl-auditor.md`; `action.yml`,
  `action/knowledge-ci.sh`, `action/knowledge-audit.sh`,
  `action/hermes/kmctl-read/`, `action/audit-batches.py`,
  `action/audit-report.py`,
  `action/knowledge-audit-issue.sh`; `.github/workflows/knowledge-audit.yml`.
- Releases: `.github/workflows/release.yml`, `.github/workflows/release-tag.yml`,
  `scripts/release.py`, `scripts/next_release_version.py`,
  `scripts/check_wheel.py`, `scripts/smoke_wheel.py`,
  `plugin/.claude-plugin/plugin.json`.
- APM: `apm/apm.yml`, its `git: parent` dependency on `plugin/` and its
  pinned `scaccogatto/okf-skills`.
