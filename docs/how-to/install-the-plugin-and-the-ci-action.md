# Install the plugin and the CI action

This page adds kmctl to one repository: the Claude Code plugin, which gives
every session a briefing on where knowledge lives and what is due for review,
and the GitHub Action, which checks docs/ and .okf/ on every pull request. A
last, optional step turns on the LLM audit.

How the commands below were run:

- `kmctl plugin install` and `kmctl plugin status` were run in a scratch
  repository with `CLAUDE_CONFIG_DIR`, `HOME` and `XDG_DATA_HOME` pointed at
  scratch folders, so no real Claude Code config was touched. The output is
  what they printed there.
- The workflow files are quoted from this repository's `action.yml` and its
  shipped workflows, `.github/workflows/knowledge.yml` and
  `.github/workflows/knowledge-audit.yml`. Those steps run only on GitHub, so
  their output on GitHub is not shown. The job summary shown in step 4 comes
  from running the script the action runs, `action/knowledge-ci.sh`, locally,
  and the refusal in step 5 from running `action/knowledge-audit.sh` locally.

## Before you start

- [uv](https://docs.astral.sh/uv/) and `git` on your PATH.
- The `claude` CLI (Claude Code) on your PATH; `kmctl plugin` needs it.
- A git repository set up with `kmctl init`. If you have not done that, follow
  [Get started with kmctl](../tutorials/get-started-with-kmctl.md) first.
- For the CI action: the repository on GitHub.

## Steps

### 1. Install kmctl

```
uv tool install git+https://github.com/JasperHG90/Knowledge-management
```

The kmctl repository is private for now, so this needs a GitHub account
with access to it; uv clones it with your git credentials.

### 2. Install the plugin in the repository

From the repository root:

```
kmctl plugin install
```

It prints:

```
kmctl 0.1.0; plugin 0.1.0
Next: start a new Claude Code session or run /reload-plugins, then kmctl plugin status
```

This installs the `kmctl` plugin and the `okf` plugin it depends on for this
repository only, and writes both to `.claude/settings.json`. kmctl keeps the
plugin files it installs from in `$XDG_DATA_HOME/kmctl/marketplace`
(`~/.local/share/kmctl/marketplace` when `XDG_DATA_HOME` is unset). To install
the plugin for every repository instead, add `--scope user`.

Running it again at the same version changes nothing.

### 3. Start a new session

Start a new Claude Code session in the repository, or run `/reload-plugins` in
an open one. The plugin's SessionStart hook prints `kmctl briefing` at the
start of each session.

### 4. Add the checks workflow

Create `.github/workflows/knowledge.yml`. This is the shipped
`.github/workflows/knowledge.yml`, with `uses: ./` (which only works inside
kmctl's own repository) replaced by the action's repository and its `main`
branch:

```yaml
name: knowledge

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  knowledge:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: JasperHG90/Knowledge-management@main
```

While the kmctl repository is private, GitHub runs this action only in
repositories its Actions access setting allows (Settings, Actions, General,
Access). There is no release tag yet, so the line pins `main`.

`fetch-depth: 0` gives `kmctl review due` the git history it reads. Per
`action.yml`, this default `checks` mode installs kmctl, runs `kmctl check` and
`kmctl review due`, writes both to the job summary, and fails only when
`kmctl check` fails. It needs no API key.

Run locally on a repository with one decision, the script behind this step
writes this summary and exits 0:

````
## kmctl check

```
all checks passed
```

## kmctl review due

```
due     decisions/0001-store-data-in-sqlite  (unverified)
due     manifesto  (unverified)
```
````

Concepts that are due are reported, never failed.

### 5. Optional: turn on the audit

Audit mode sends your repository to a model, so it is off unless you add it.
Per `action.yml`, it runs the kmctl audit agent through
[Hermes Agent](https://hermes-agent.nousresearch.com) on the architecture
pages, decisions and practices that are due, and writes its findings to the
job summary and to one open issue titled "Knowledge audit". The model gets
three tools only: read a file, search files for text, and list files. They
refuse any path outside the repository, and none of them can write. The
audit never edits files.

It works with any OpenAI-compatible endpoint: Ollama, Bifrost, OpenRouter, a
vendor's own API, or your own server. You give it four settings:

| Input | What it is |
|---|---|
| `provider` | `custom` (the default) for any OpenAI-compatible endpoint; a Hermes provider name also works |
| `model` | the model name, as the endpoint's API names it |
| `base_url` | the endpoint's base URL, usually ending in `/v1` |
| `api_key_env` | the name of the variable that holds the key; leave it out for an endpoint that takes no key |

1. Add a repository secret named `AUDIT_API_KEY` with your provider's API
   key. Skip this for an endpoint that takes no key.
2. Create `.github/workflows/knowledge-audit.yml`. Change `model` and
   `base_url` to your provider's:

   ```yaml
   name: knowledge audit

   # Audit mode sends the repository to a model with the API key, so it runs only
   # by hand or on a schedule, never on a pull request (ADR 0005).
   on:
     workflow_dispatch:
     schedule:
       - cron: "0 6 * * 1"

   # A composite action cannot set token permissions; the calling workflow does.
   permissions:
     contents: read
     issues: write

   jobs:
     audit:
       runs-on: ubuntu-latest
       steps:
         # No token left in git config for the model to read; full history for review due.
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0
             persist-credentials: false
         - uses: JasperHG90/Knowledge-management@main
           timeout-minutes: 40
           env:
             AUDIT_API_KEY: ${{ secrets.AUDIT_API_KEY }}
           with:
             mode: audit
             provider: custom
             base_url: https://openrouter.ai/api/v1
             model: qwen/qwen3-coder
             api_key_env: AUDIT_API_KEY
   ```

The action installs Hermes Agent 0.19.0 and stops it after 30 minutes; set
`KMCTL_AUDIT_TIMEOUT` (such as `45m`) in the step's `env` to change that.
`timeout-minutes` on the step is a second limit, so a stuck run cannot hold
the runner for GitHub's six-hour default. The config the action writes for
Hermes names `AUDIT_API_KEY`, never the key itself.

This repository's own `.github/workflows/knowledge-audit.yml` runs the same
commands as separate steps instead of `uses:`: install kmctl, install Hermes
Agent, run `action/knowledge-audit.sh`, then `action/knowledge-audit-issue.sh`.
Read it to see exactly what the audit runs.

**Ollama.** Set the model's context size to 64K tokens or more, with
`PARAMETER num_ctx 65536` in a Modelfile or `OLLAMA_CONTEXT_LENGTH=65536` for
the server. Ollama serves a smaller context than the model reports unless you
set it, so a long prompt is cut without warning, and Hermes refuses an
endpoint that reports less than 64K. A GitHub-hosted runner cannot reach
Ollama on your own machine; use a self-hosted runner or a URL the runner can
reach.

Keep the `on:` and `permissions:` blocks as they are. Audit mode runs only on
`workflow_dispatch` or `schedule`; on any other event the script stops. Run
locally with `GITHUB_EVENT_NAME=pull_request`, it prints this and exits 1:

```
kmctl audit: refused for event 'pull_request'; audit mode runs only on workflow_dispatch or schedule.
```

Keep `persist-credentials: false` on the checkout, and do not set `GH_TOKEN`
or `GITHUB_TOKEN` for the job. Either would sit in the model's process, so
the audit refuses to start when it finds one. The action hands the token only
to its own later step, which posts the report.

The model reads your repository's files, so anything checked into it,
secrets included, is in its view, and its findings quote what it read into
the "Knowledge audit" issue in the same repository.

`issues: write` lets that step open or update the "Knowledge audit" issue.

## Check it worked

In the repository, run:

```
kmctl plugin status
```

When the plugin is installed, it prints:

```
kmctl 0.1.0; plugin 0.1.0
```

Before the install, the same command printed:

```
kmctl 0.1.0; plugin not installed
problem: kmctl@kmctl is not installed here; run kmctl plugin install
```

Each problem it reports names the command that fixes it. After you upgrade
kmctl, run `kmctl plugin update`.

For the action, open a pull request: the `knowledge` job runs and its summary
shows the `kmctl check` and `kmctl review due` reports. For the audit, run the
"knowledge audit" workflow by hand from the repository's Actions tab.

All options of these commands are in [Commands](../reference/commands.md).
Why the plugin has one hook and the audit only reports is in
[Why one hook and report-only audits](../explanation/why-one-hook-and-report-only-audits.md).
