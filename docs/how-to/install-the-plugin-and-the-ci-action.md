# Install the plugin and the CI action

This page adds kmctl to one repository: kmctl's skills, audit agent and
knowledge rules for Claude Code, Antigravity or both, with a session hook that
gives every session a briefing on where knowledge lives and what is due for
review, and the GitHub Action, which checks docs/ and .okf/ on every pull
request. A last, optional step turns on the LLM audit.

How the commands below were run:

- `kmctl plugin install` and `kmctl doctor` were run with kmctl 0.3.0
  in a scratch repository with `CLAUDE_CONFIG_DIR`, `HOME` and
  `XDG_DATA_HOME` pointed at scratch folders, so no real Claude Code config
  was touched, and with `--source` naming a local git server that held this
  repository's files at the tag `v0.3.0`. The output is what they printed
  there. `claude` and `agy` were stand-ins that do nothing, since doctor
  only looks them up on PATH; the folder paths in doctor's `dep.` and
  `antigravity.trust` lines are left out below.
- The workflow files are quoted from this repository's `action.yml` and its
  shipped workflows, `.github/workflows/knowledge.yml` and
  `.github/workflows/knowledge-audit.yml`. Those steps run only on GitHub, so
  their output on GitHub is not shown. The job summary shown in step 4 comes
  from running the script the action runs, `action/knowledge-ci.sh`, locally,
  and the refusal in step 5 from running `action/agent.py` locally.

## Before you start

- [uv](https://docs.astral.sh/uv/) and `git` on your PATH.
- Claude Code, or Antigravity (Google's agent IDE and its `agy` CLI).
  `kmctl plugin install` runs APM (Agent Package Manager) with `uvx`, so it
  needs uv, not a separate APM install.
- A git repository set up with `kmctl init`. If you have not done that, follow
  [Get started with kmctl](../tutorials/get-started-with-kmctl.md) first.
- For the CI action: the repository on GitHub.

## Steps

### 1. Install kmctl

```
uv tool install git+https://github.com/JasperHG90/Knowledge-management@v0.3.0
```

The kmctl repository is private for now, so this needs a GitHub account
with access to it; uv clones it with your git credentials.

### 2. Install kmctl's skills and hook in the repository

From the repository root:

```
kmctl plugin install --harness claude
```

Run bare `kmctl plugin install` and it asks which harnesses to install
for; `--harness` answers that up front, and a script or an agent must pass it.

It prints:

```
installed kmctl's package v0.3.0 for claude (project scope)
Next: start a new Claude Code session, then kmctl doctor
```

This adds kmctl's APM package to the repository's `apm.yml`, at the tag of
the kmctl you installed, and installs it with APM. APM writes kmctl's seven
skills and okf's four to `.claude/skills/`, the audit agent to
`.claude/agents/`, the four knowledge rules to `.claude/rules/`, the
SessionStart hook into `.claude/settings.json`, and okf's MCP server,
`okf-bundle`, into `.mcp.json`. Commit `apm.yml` and `apm.lock.yaml`; APM
adds its download folder, `apm_modules/`, to `.gitignore`. To install for
every repository instead, add `--scope user`.

Running it again at the same version changes nothing. If the repository
still has the old claude plugin `kmctl@kmctl`, or an `apm.yml` entry for
kmctl written by hand, the install removes it first and prints a `note:` line
saying so. It also removes the hook and `okf-bundle` server an older kmctl
wrote itself, so APM's copies are the only ones.

If your `apm.yml` has an `allowExecutables` block, allow kmctl's package
there; otherwise APM installs no hook or MCP server from it.

If a skill folder with one of kmctl's skill names is already there and APM
did not write it, the install stops and names it; run
`kmctl plugin install --harness claude --force` to replace it. `--force`
replaces the whole folder, so any file you added there goes.

If the repository manages its agent files with APM and you would rather add
the package entry yourself, see
[Install kmctl with APM](install-kmctl-with-apm.md). That route gets the
session hook and okf's MCP server from APM too.

#### For Antigravity

From the repository root:

```
kmctl plugin install --harness antigravity
```

It prints:

```
note: wrote .agents/plugins/kmctl/ (the agents, which APM does not install for Antigravity yet); Antigravity loads it once you trust this folder
installed kmctl's package v0.3.0 for antigravity (project scope)
Next: open this folder in Antigravity, trust it and start a new session, then kmctl doctor
```

APM writes kmctl's seven skills and okf's four to `.agents/skills/`, the
four knowledge rules to `.agents/rules/`, okf's MCP server, `okf-bundle`, to
`.agents/mcp_config.json`, and two hooks to `.agents/hooks.json`: one
SessionStart hook that runs `kmctl briefing --format antigravity`, and one
Stop hook that runs okf's bundle check (it keeps the agent working only when
`.okf/index.md` sets `upkeep: enforced`). kmctl then writes the folder
`.agents/plugins/kmctl/`, which it owns and replaces on every run, with the
audit agent and okf's two agents in Antigravity's format, and takes out of
`.agents/hooks.json` a broken copy of okf's Stop check that APM also writes.
okf's MCP server runs with `uv run`, so it needs `uv` on PATH wherever
Antigravity runs. For both harnesses at once, run
`kmctl plugin install --harness claude,antigravity`. Antigravity installs
per repository only; `--scope user` is refused for it.

Antigravity loads a repository's `.agents/` only once you trust the
folder: open the repository folder in Antigravity and accept its trust
prompt. Trust matches the exact folder, so trust the repository root, the
folder you open.

### 3. Start a new session

Start a new Claude Code session in the repository. Claude Code asks once
whether to use the `okf-bundle` server from `.mcp.json`. The SessionStart
hook prints `kmctl briefing` at the start of each session.

For Antigravity, open the trusted repository folder and start a new
session. The SessionStart hook in `.agents/hooks.json` adds the same
briefing to the session.

Then run `kmctl doctor` in the repository. It checks every piece the
install left and prints one `ok` or `fail` line each; see
[Check it worked](#check-it-worked).

### 4. Add the checks workflow

Create `.github/workflows/knowledge.yml`. This is the shipped
`.github/workflows/knowledge.yml`, with `uses: ./` (which only works inside
kmctl's own repository) replaced by the action's repository and a ref:

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
      - uses: JasperHG90/Knowledge-management@v0.3.0
```

While the kmctl repository is private, GitHub runs this action only in
repositories its Actions access setting allows (Settings, Actions, General,
Access). The ref is the newest release tag, `vX.Y.Z`, once kmctl has a
release, and `main` until then. Keep it the same as the tag you installed kmctl
from in step 1.

`fetch-depth: 0` gives `kmctl review due` the git history it reads. Per
`action.yml`, this default `checks` mode installs kmctl, runs `kmctl check` and
`kmctl review due`, writes both to the job summary, and fails only when
`kmctl check` fails. It needs no API key.

Run locally on the repository from the tutorial, with two decisions, the script behind this step
writes this summary and exits 0:

````
## kmctl check

```
all checks passed
```

## kmctl review due

```
due     decisions/0001-keep-project-knowledge-in-an-okf-bundle  (unverified)
due     decisions/0002-store-data-in-sqlite  (unverified)
due     manifesto  (unverified)
```
````

Concepts that are due are reported, never failed.

### 5. Optional: turn on the audit

Audit mode sends your repository to a model, so it is off unless you add it.
Per `action.yml`, it runs `action/agent.py`, a small agent built on
[PydanticAI](https://ai.pydantic.dev). By default it audits the architecture
pages, decisions and practices that are due, following kmctl's audit skill.
It writes its report to the job summary and keeps it as an `agent-report`
artifact (`report.json`, `report.md` and the full `transcript.json`). A
second job, with `mode: publish`, posts it to one issue titled "Knowledge
audit" when a finding is high (or the severity you choose): it opens the
issue, or updates it and adds a comment, @-mentioning the owners of the
last `*` rule in your CODEOWNERS. When a later run finds nothing at that
severity, it closes the issue.

The agent can read, search and list files in your repository and in any
folders you add, and run shell commands, so it can use the scripts skills
ship. It is told never to change, commit or push a file, and nothing it
changes is committed: the checkout keeps no credentials, and only the
publish job gets a GitHub token that can write. That job runs on a fresh
runner and gets nothing from the agent's job but the artifact.

It works with any provider. Name a PydanticAI provider in `model`, or give
`base_url` for any OpenAI-compatible endpoint: Ollama, Bifrost, OpenRouter, a
vendor's own API, or your own server.

| Input | What it is |
|---|---|
| `model` | Required. Without `base_url`, PydanticAI's `provider:model`, such as `openai:gpt-5` (set the provider's own key variable, such as `OPENAI_API_KEY`). With `base_url`, the model name the endpoint serves |
| `base_url` | an OpenAI-compatible endpoint's base URL, usually ending in `/v1` |
| `api_key_env` | with `base_url`, the name of the variable that holds the key; leave it out for an endpoint that takes no key |
| `prompt` or `prompt_file` | the agent's task; leave both out for the knowledge audit |
| `system_prompt_file` | a file that replaces the shipped system prompt |
| `context` | folders the agent can read besides the repository, one per line |
| `skills` | skill folders (subfolders with a `SKILL.md`), one per line; default kmctl's own |
| `timeout` | how long the agent may run; default `30m` |

Publish mode takes three more:

| Input | What it is |
|---|---|
| `min_severity` | the lowest severity (`info`, `low`, `medium` or `high`) that opens or updates the issue; default `high` |
| `mention` | users or teams to @-mention, one per line; default the owners of the last `*` rule in CODEOWNERS |
| `issue_title` | the issue's title; default `Knowledge audit` |

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

   jobs:
     audit:
       runs-on: ubuntu-latest
       steps:
         # No token left in git config for the agent to read; full history for review due.
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0
             persist-credentials: false
         - uses: JasperHG90/Knowledge-management@v0.3.0
           timeout-minutes: 40
           env:
             AUDIT_API_KEY: ${{ secrets.AUDIT_API_KEY }}
           with:
             mode: audit
             base_url: https://openrouter.ai/api/v1
             model: qwen/qwen3-coder
             api_key_env: AUDIT_API_KEY

     # A fresh runner that gets only the report, so nothing the agent
     # changed runs with the token.
     publish:
       needs: audit
       runs-on: ubuntu-latest
       permissions:
         contents: read
         issues: write
       steps:
         # Only to read CODEOWNERS.
         - uses: actions/checkout@v4
           with:
             persist-credentials: false
         - uses: JasperHG90/Knowledge-management@v0.3.0
           with:
             mode: publish
   ```

`timeout-minutes` on the step is a second limit after `timeout`, so a stuck
run cannot hold the runner for GitHub's six-hour default.

**Your own task.** To check the repository against something else, such as
your enterprise architecture docs, fetch them in a step before the action's,
such as `- run: ./scripts/fetch-ea-docs.sh context/`, and add a task, the
folder and any skills of your own under the action step's `with:`:

```yaml
             prompt_file: .github/ea-review.md
             context: context
             skills: |
               .github/skills
```

`uv run --script action/agent.py run --help` lists every option the agent
takes, with its default.

This repository's own `.github/workflows/knowledge-audit.yml` runs the same
commands as separate steps instead of `uses:`: in the audit job, install
kmctl, run `action/agent.py run` and upload the report; in the publish job,
download it and run `action/agent.py publish`. Read it to see exactly what
the audit runs. `uv run --script action/agent.py publish --help` lists the
publish options.

**Ollama.** Set the model's context size high enough for the audit, with
`PARAMETER num_ctx 65536` in a Modelfile or `OLLAMA_CONTEXT_LENGTH=65536` for
the server. Ollama serves a smaller context than the model reports unless you
set it, so a long conversation is cut without warning. A GitHub-hosted runner
cannot reach Ollama on your own machine; use a self-hosted runner or a URL
the runner can reach.

Keep the `on:` block as it is. Audit mode runs only on `workflow_dispatch`
or `schedule`, since on a pull request code from the pull request would run
with your API key; on any other event the action stops with:

```
kmctl audit: refused for event 'pull_request'; audit mode runs only on workflow_dispatch or schedule.
```

Keep `persist-credentials: false` on the checkout, and do not set `GH_TOKEN`
or `GITHUB_TOKEN` for the job. The agent runs shell commands, so it refuses
to start when it finds either. Run locally with `GH_TOKEN` set, it prints
this and exits 2:

```
agent: refused: GH_TOKEN is set, and the agent could read the token. Give it only to the publish job, which runs no agent.
```

Only the publish job gets `issues: write` and the token, and it runs no
agent. Keep the two jobs apart: on a self-hosted runner that reuses its
machine between jobs, the agent could leave behind code that the publish
job then runs with the token.

The agent's shell commands run without the API key in their environment, but
as the same user, so a determined command could still read the key from the
agent's own process. Use a key made for the audit, with a spending limit.

The agent reads your repository's files, so anything checked into it,
secrets included, is in its view, and its findings quote what it read into
the "Knowledge audit" issue in the same repository.

`issues: write` lets the publish job open, update and close the
"Knowledge audit" issue. Without a CODEOWNERS file and `mention`, it
mentions no one. When the audit job fails, the publish job is skipped and
the issue stays as it was.

### 6. Later: upgrade to a newer release

Once kmctl has releases, the repository's Releases page lists each one with
its `vX.Y.Z` tag. To move to a newer one:

1. Install kmctl at the new tag, replacing `vX.Y.Z` with it:

   ```
   uv tool install --force git+https://github.com/JasperHG90/Knowledge-management@vX.Y.Z
   ```

   `--force` replaces the kmctl you have. `kmctl --version` then prints the
   new version.

2. In each repository where you ran `kmctl plugin install`, update it to
   the same release:

   ```
   kmctl plugin update
   ```

   It asks which harnesses to update; press Enter for the ones already
   installed. In a script, pass them: `kmctl plugin update --harness
   claude,antigravity`. It moves the `apm.yml` entry to the new
   tag and reinstalls.
   `kmctl doctor` then reports `claude.lock` (and `antigravity.lock`) as
   `ok` at the new version.

3. Change the ref in each workflow's `uses: JasperHG90/Knowledge-management@`
   line to the same tag.

### 7. To remove kmctl from a harness

```
kmctl plugin remove
```

It asks which harnesses to remove kmctl from; press Enter for all of them,
or pass `--harness antigravity` to keep Claude Code. It runs `apm uninstall`
for you, so APM need not be on your PATH; APM takes out the hook and okf's
MCP server with the rest of the package, and kmctl removes any copy APM
leaves, such as `okf-bundle` in the user `.claude.json` after a
`--scope user` remove. The harnesses you keep are installed again at the
version they had. Run `kmctl doctor` afterwards to see what is left.

## Check it worked

In the repository, run:

```
kmctl doctor
```

It checks the tools kmctl needs, the `kmctl init` files and, for each
harness installed, the APM lock, every file the lock lists, the hook,
okf's skills and MCP server, and for Antigravity the
`.agents/plugins/kmctl/` folder and the folder's trust. It writes nothing
and uses no network. After both installs and trusting the folder in
Antigravity, it printed, and exited 0:

```
ok   kmctl.version: kmctl 0.3.0
ok   dep.uv: …/bin/uv
ok   dep.git: /usr/bin/git
ok   dep.apm: APM runs from uv's cache: Agent Package Manager (APM) CLI version 0.33.0
ok   dep.claude: …/bin/claude
ok   dep.agy: …/bin/agy
ok   init.okf: .okf/index.md exists
ok   init.docs: docs/README.md exists
ok   kmctl.harness: installed for claude, antigravity
ok   claude.lock: apm.lock.yaml has kmctl's package at v0.3.0
ok   claude.files: 33 kmctl paths match apm.lock.yaml
ok   claude.okf-skills: 21 okf-skills paths match apm.lock.yaml
ok   claude.hook: .claude/settings.json holds the SessionStart hook kmctl's package ships
ok   claude.okf-mcp: .mcp.json declares okf's MCP server okf-bundle
ok   claude.old-plugin: no settings file enables kmctl@kmctl or okf@scaccogatto
ok   antigravity.lock: apm.lock.yaml has kmctl's package at v0.3.0
ok   antigravity.files: 32 kmctl paths match apm.lock.yaml
ok   antigravity.okf-skills: 19 okf-skills paths match apm.lock.yaml
ok   antigravity.plugin: .agents/plugins/kmctl/ holds what this kmctl writes
ok   antigravity.hook: .agents/hooks.json holds kmctl's SessionStart hook and okf's Stop check
ok   antigravity.apm-hooks: .agents/hooks.json runs no okf Stop check
ok   antigravity.okf-mcp: .agents/mcp_config.json declares okf's MCP server okf-bundle
ok   antigravity.trust: …/repo is in trustedWorkspaces of ~/.gemini/antigravity-cli/settings.json
```

Before the install, the same command printed, and exited 1:

```
ok   kmctl.version: kmctl 0.3.0
ok   dep.uv: …/bin/uv
ok   dep.git: /usr/bin/git
ok   dep.apm: APM runs from uv's cache: Agent Package Manager (APM) CLI version 0.33.0
fail init.okf: .okf/index.md is missing; run kmctl init
fail init.docs: docs/README.md is missing; run kmctl init
fail kmctl.harness: no kmctl harness in this repository; run kmctl plugin install --harness claude
```

Each `fail` line names what is wrong and, after the `;`, the command that
fixes it. With one skill file deleted, it printed
`fail claude.files: .claude/skills/audit/SKILL.md is missing; run kmctl plugin install --harness claude`.
For an install made with `--scope user`, run `kmctl doctor --scope user`.
After you upgrade kmctl, run `kmctl plugin update`.

For the action, open a pull request: the `knowledge` job runs and its summary
shows the `kmctl check` and `kmctl review due` reports. For the audit, run the
"knowledge audit" workflow by hand from the repository's Actions tab.

All options of these commands are in [Commands](../reference/commands.md).
Why kmctl has one hook and the audit only reports is in
[Why one hook and report-only audits](../explanation/why-one-hook-and-report-only-audits.md).
