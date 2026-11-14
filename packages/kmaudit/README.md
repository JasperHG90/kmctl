# kmaudit

kmaudit audits what a folder of markdown docs claims about the repository
it sits in. A coding agent reads each section, lists the claims it makes,
and writes a check for each claim: steps kmaudit reruns with no model
whenever the files the check reads change. People review the claims and
checks on a local page.

kmaudit calls no model itself, except the optional `kmaudit judge`. The
agent you already work with does the reading and writing through
kmaudit's commands.

kmaudit lives in the kmctl repository as a package of its own. It does not
need kmctl, though the two work well together: kmctl keeps an `.okf/`
knowledge bundle current, and kmaudit checks that bundle against the code.

## Install

```bash
uv tool install 'kmaudit @ git+https://github.com/JasperHG90/kmctl#subdirectory=packages/kmaudit'
```

Add the `tracing` extra (`kmaudit[tracing]`) to trace `kmaudit judge` calls
to LangSmith.

## Commands

Every command takes `--help` and prints `--json` for scripts. The full
reference is [`docs/commands.md`](docs/commands.md).

| Command | What it does |
|---|---|
| `kmaudit claims todo`, `submit`, `list` | Hand an agent the sections to read, store its claims, read them back |
| `kmaudit checks todo`, `try`, `submit`, `run`, `list` | Hand an agent claims to check, test a draft check, store it, rerun what changed |
| `kmaudit judge failure\|claim\|link` | Ask an optional decision model about stored checks (off by default) |
| `kmaudit coverage` | How much of the code the checks match |
| `kmaudit ui` | A local page to review claims and checks and give feedback |
| `kmaudit guard --allow claims\|checks` | A Claude Code PreToolUse hook that holds an agent to kmaudit commands |

State lives in `.kmctl/audit.sqlite` in the repository, which ignores itself
in git. Today kmaudit audits an OKF bundle (a folder whose `index.md`
carries `okf_version`, or a repository's `.okf/`).

## Agents and skills

kmctl's APM package ships the `extract-claims` and `write-checks` skills and
the `kmctl-claims-extractor` and `kmctl-check-writer` agents that drive
these commands.
