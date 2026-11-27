---
description: "Add kmctl's skills, rules and session hook for Claude Code or Antigravity with APM and kmctl plugin patch, and the GitHub Action, with the opt-in audit."
verified:
  - by: human:jasper
    at: 2026-11-27T20:44:03Z
---

# Install the plugin and the CI action

This page adds kmctl to one repository: kmctl's skills, audit agent and
knowledge rules for Claude Code, Antigravity or both, with a session hook that
gives every session a briefing on where knowledge lives and what is due for
review, and the GitHub Action, which checks docs/ and .okf/ on every pull
request. A last, optional step turns on the LLM audit of each pull request.

How the commands below were run:

- `kmctl doctor` was run with kmctl 0.3.0 in a scratch repository with
  `CLAUDE_CONFIG_DIR`, `HOME` and `XDG_DATA_HOME` pointed at scratch
  folders, so no real Claude Code config was touched, after installing
  kmctl's package from a local git server that held this repository's files
  at the tag `v0.3.0`. The output is what it printed there. `claude` and
  `agy` were stand-ins that do nothing, since doctor only looks them up on
  PATH; the folder paths in doctor's `dep.` and `antigravity.trust` lines
  are left out below. The `kmctl plugin patch` output is the text kmctl
  prints for the same install, with the same stand-ins.
- The workflow files are quoted from this repository's `action.yml` and its
  shipped workflows, `.github/workflows/ci.yml` (its `knowledge` job) and
  `.github/workflows/knowledge-audit.yml`. Those steps run only on GitHub, so
  their output on GitHub is not shown. The job summary shown in step 4 comes
  from running the script the action runs, `action/knowledge-ci.sh`, locally,
  and the refusal in step 5 from running `action/agent.py` locally.

## Before you start

- [uv](https://docs.astral.sh/uv/) and `git` on your PATH.
- Claude Code, or Antigravity (Google's agent IDE and its `agy` CLI).
- APM (Agent Package Manager), which installs kmctl's package. You need not
  install it: `uvx --from apm-cli==0.33.0 apm` runs it through uv, as the
  steps below do. If APM is on your PATH, write `apm` instead. APM needs a
  GitHub token with access to the kmctl repository; see
  [Install kmctl with APM](install-kmctl-with-apm.md#before-you-start).
- A git repository set up with `kmctl init`. If you have not done that, follow
  [Get started with kmctl](../tutorials/get-started-with-kmctl.md) first.
- For the CI action: the repository on GitHub.

## Steps

### 1. Install kmctl

```
uv tool install git+https://github.com/JasperHG90/kmctl@v0.18.0#subdirectory=packages/kmctl
```

The kmctl repository is private for now, so this needs a GitHub account
with access to it; uv clones it with your git credentials.

### 2. Install kmctl's skills and hook in the repository

Add kmctl's package to `apm.yml` in the repository root, at the tag of the
kmctl you installed (`kmctl --version` prints it; put `v` before it). A new
`apm.yml` looks like this:

```yaml
name: my-project
version: 0.1.0
dependencies:
  apm:
    - git: https://github.com/JasperHG90/kmctl.git
      path: packages/kmctl/apm
      ref: vX.Y.Z
```

Releases after v0.12.2 keep the package in `packages/kmctl/apm`; for
v0.12.2 and older, write `path: apm`.

In an existing `apm.yml`, add only the entry under `dependencies.apm`. If
it limits which packages may run hooks and MCP servers (an `executables:`
block, or the older `allowExecutables:`), `apm approve --pending` lists
kmctl's package; approve it with `apm approve`. Run `kmctl plugin patch` before
adding the entry and it refuses, naming the exact entry for your kmctl.

Then, from the repository root, install the package with APM and run
`kmctl plugin patch`, which adds what APM cannot install yet:

```
uvx --from apm-cli==0.33.0 apm install --target claude
kmctl plugin patch
```

`kmctl plugin patch` prints:

```
patched kmctl's package v0.3.0 for claude (project scope)
Next: start a new Claude Code session, then kmctl doctor
```

APM writes kmctl's eight skills and okf's four to `.claude/skills/`, the
audit agent to `.claude/agents/`, the four knowledge rules to
`.claude/rules/`, the SessionStart hook into `.claude/settings.json`, and
okf's MCP server, `bundle`, into `.mcp.json`. Commit `apm.yml` and
`apm.lock.yaml`; APM adds its download folder, `apm_modules/`, to
`.gitignore`.

To install for every repository instead, put the entry in
`~/.apm/apm.yml` and run:

```
uvx --from apm-cli==0.33.0 apm install -g --target claude
kmctl plugin patch --scope user
```

Running `kmctl plugin patch` again changes nothing. If the repository still
has the old claude plugin `kmctl@kmctl`, or the hook an older kmctl wrote
itself, patch removes them and prints a `note:` line for each, so APM's
copies are the only ones.

If `apm.yml` still names kmctl the way kmctl 0.3.0 and older did, patch
refuses and names the `apm uninstall` to run first; see
[Install kmctl with APM](install-kmctl-with-apm.md#older-installs).

#### For Antigravity

From the repository root:

```
uvx --from apm-cli==0.33.0 apm install --target antigravity
kmctl plugin patch
```

`kmctl plugin patch` prints:

```
note: wrote .agents/plugins/kmctl/ (the agents, which APM does not install for Antigravity yet); Antigravity loads it once you trust this folder
note: took APM's okf Stop handler out of .agents/hooks.json, where it cannot run; kmctl's package runs okf's check instead
patched kmctl's package v0.3.0 for antigravity (project scope)
Next: open this folder in Antigravity, trust it and start a new session, then kmctl doctor
```

APM writes kmctl's eight skills and okf's four to `.agents/skills/`, the
four knowledge rules to `.agents/rules/`, okf's MCP server, `bundle`, to
`.agents/mcp_config.json`, and two hooks to `.agents/hooks.json`: one
SessionStart hook that runs `kmctl briefing --format antigravity`, and one
Stop hook that runs okf's bundle check (it keeps the agent working only when
`.okf/index.md` sets `upkeep: enforced`). `kmctl plugin patch` then writes
the folder `.agents/plugins/kmctl/`, which it owns and replaces on every
run, with the audit agent and okf's two agents in Antigravity's format, and
takes out of `.agents/hooks.json` a broken copy of okf's Stop check that APM
also writes. APM writes that copy again on every `apm install`, so run
`kmctl plugin patch` after each one. Because of that, `apm audit --ci`
reports `.agents/hooks.json` as drift; step 4 says what to run in CI
instead. okf's MCP server runs with `uv run`, so
it needs `uv` on PATH wherever Antigravity runs. Antigravity installs per
repository only, so there is no user-scope install for it.

For both harnesses at once:

```
uvx --from apm-cli==0.33.0 apm install --target claude,antigravity
kmctl plugin patch
```

Antigravity loads a repository's `.agents/` only once you trust the
folder. In the IDE, open the repository folder and accept its trust prompt.
With the CLI, run `agy` in the repository root and choose "Yes, I trust
this folder". Trust matches the exact folder, so trust the repository root.

### 3. Start a new session

Start a new Claude Code session in the repository. Claude Code asks once
whether to use the `bundle` server from `.mcp.json`. The SessionStart
hook prints `kmctl briefing` at the start of each session.

For Antigravity, open the trusted repository folder and start a new
session. The SessionStart hook in `.agents/hooks.json` adds the same
briefing to the session.

Then run `kmctl doctor` in the repository. It checks every piece the
install left and prints one `ok` or `fail` line each; see
[Check it worked](#check-it-worked).

### 4. Add the checks workflow

Create `.github/workflows/knowledge.yml`. This is the `knowledge` job of
the shipped `.github/workflows/ci.yml`, with `uses: ./` (which only works
inside kmctl's own repository) replaced by the action's repository and a
ref, and `actions/checkout@v4` in place of the pinned commit SHA:

```yaml
name: knowledge

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
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
      - uses: JasperHG90/kmctl@v0.18.0
```

While the kmctl repository is private, GitHub runs this action only in
repositories its Actions access setting allows (Settings, Actions, General,
Access). The ref is a release tag, `vX.Y.Z`. Keep it the same as the tag you
installed kmctl from in step 1.

`fetch-depth: 0` gives `kmctl review due` the git history it reads. Per
`action.yml`, this default `checks` mode installs kmctl, runs `kmctl check` and
`kmctl review due`, writes both to the job summary, and fails when
`kmctl check` fails or `kmctl review due` crashes, never because a concept is
due. It needs no API key.

The reasons for a failure are in the job summary, not the job log. When the
job fails, the log ends with an error that names the command that failed and
gives a link to the run's summary page, for example
`kmctl check failed; the reasons are on the run's summary page: https://github.com/OWNER/REPO/actions/runs/ID/attempts/1`.

On a pull request that is ready for review, it runs `kmctl check --no-drafts`,
so a decision record that is still a draft fails the job (ADR 0050). A draft
pull request and a push to `main` pass with drafts. The `ready_for_review` type
in `on.pull_request` makes GitHub run the job again when you mark a pull
request ready; without it, the drafts are only checked on the next push. Set
the action's `drafts` input to `fail` to fail on drafts everywhere, or to
`pass` to never check them.

It also runs `kmctl check --summary-current`, so the job fails when
`.okf/summary.md` is behind the concepts that changed after it (ADR 0056).
Update the summary, or run `kmctl summary ack` when it still holds, and push.
A `kmctl verify` alone does not put the summary behind, and neither does a
draft decision you add, edit or delete. Accepting the draft does (ADR 0058).
Set the action's `summary` input to `pass` to only warn.

On a pull request, the job summary first lists the pages that pull request
made due, from `kmctl review due --base origin/BASE` (ADR 0055). Those are
the pages to read before review. A person who checked them records it with
one `kmctl verify ID ID ... --by human:<id>`.

Run locally on the repository from the tutorial, with two decisions, the script behind this step
writes this summary and exits 0:

````
## kmctl check

Draft decisions pass here (drafts: fail-when-ready).
A summary behind its concepts fails (summary: fail); run kmctl summary ack when it is still right.

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

To also check in CI that the committed agent files match `apm.lock.yaml`,
add a job that runs APM's audit, the one that fits your harnesses:

- **Claude Code only:** `uvx --from apm-cli==0.33.0 apm audit --ci`
  passes on a clean install.
- **Antigravity:** run `uvx --from apm-cli==0.33.0 apm audit --ci --no-drift`
  and the install check below. The audit's `drift` check always reports
  `.agents/hooks.json`, because `kmctl plugin patch` takes okf's broken
  Stop handler out of it after every install (ADR 0018). `--no-drift`
  skips that check, and the install check catches the drift it would
  have caught.
- **OpenCode:** run the install check alone. `apm audit --ci` fails even
  with `--no-drift`: both `drift` and `content-integrity` report the three
  agents in `.opencode/agents/` that `kmctl plugin patch` rewrites into
  OpenCode's format, and no option skips `content-integrity`.

The install check runs a frozen install and `kmctl plugin patch` on the
fresh checkout, then fails if git sees any change:

```
uvx --from apm-cli==0.33.0 apm install --frozen
kmctl plugin patch
test -z "$(git status --porcelain)" || { git status --porcelain; exit 1; }
```

It works because the project commits what APM installs (ADR 0030), so a
committed hand edit to an installed skill shows as a change. Run it
only on a clean checkout, as CI has: on a working tree, the frozen install
overwrites an uncommitted edit without a word. A project made from the
starter template has it as `just check-install`. While the kmctl repository
is private, the job needs a token that can read it for the install to fetch
kmctl's package, which is why the starter's workflow leaves the job out.

### 5. Optional: turn on the audit

Audit mode sends pages and code from your repository to a model, so it is
off unless you add it. Per `action.yml`, it runs `action/agent.py`, a small
agent built on [PydanticAI](https://ai.pydantic.dev), on a pull request from
the same repository, and does one thing
([ADR 0060](../../.okf/decisions/0060-the-ci-agent-only-rereads-the-pages-a-pull-request-changed.md)).
It lists every page under `.okf/` and `docs/` with a `resource:` entry in
its `sources` that names a file the pull request changed, compared with the
base branch from the commit where the two split. That takes in decisions
(drafts the pull request adds too), architecture pages, practices and docs
pages, and leaves out deprecated and superseded decisions, handoffs, the
log and `index.md` pages. A model then rereads each page against the change.
When no page names a changed file, the agent writes an empty report and
calls no model, so that run costs nothing.

The report lists each page the agent checked and what it compared it
against, and has a finding only for a mismatch: the claim (`path:line`), the
lines that contradict it and a suggested fix. For a stable decision the fix
is a dated Correction section, a new draft decision that supersedes it, or a
change to the code; for any other page, an edit. The summary ends with the
pages that still hold, and the `kmctl verify ID ... --by human:<id>` command
to record that once you have read them; the agent never runs it. The script
checks every citation: one that names a line the agent did not read or find
by search goes back to the agent, and after five retries the run fails with
no report. It writes its report to the job summary and keeps it as an
`agent-report` artifact (`report.json`, `report.md` and the full
`transcript.json`). A second job, with `mode: publish`, posts it as one
comment on the pull request when there is a finding at `low` or above (or
the severity you choose), and replaces that comment on each run. A finding
never fails the check.

To try the agent on your machine first and learn to read its report, follow
[Audit your repository with the agent](../tutorials/audit-your-repository-with-the-agent.md).

The agent can only read, search and list files in your repository. It has no
shell, so text in the pull request cannot make it run a command. It is told
never to change, commit or push a file, and nothing it changes is committed:
the checkout keeps no credentials, and only the publish job gets a GitHub
token that can write. That job runs on a fresh runner and gets nothing from
the agent's job but the artifact.

It works with any provider. Name a PydanticAI provider in `model`, or give
`base_url` for any OpenAI-compatible endpoint: Ollama, Bifrost, OpenRouter, a
vendor's own API, or your own server.

| Input | What it is |
|---|---|
| `model` | Required. Without `base_url`, PydanticAI's `provider:model`, such as `openai:gpt-5` (set the provider's own key variable, such as `OPENAI_API_KEY`). With `base_url`, the model name the endpoint serves |
| `base_url` | an OpenAI-compatible endpoint's base URL, usually ending in `/v1` |
| `api_key_env` | with `base_url`, the name of the variable that holds the key; leave it out for an endpoint that takes no key |
| `timeout` | how long the agent may run; default `30m` |
| `report_name` | the artifact's name, in audit and publish mode alike; default `agent-report` |
| `base`, `head` | on a dispatch, the pull request's base branch and head commit, from the previous job's outputs; on a `pull_request` they come from the event |

Previous mode, in a job of its own before the audit, takes `pr` (on a
dispatch, the pull request's number; on a `pull_request` it comes from the
event) and `title`. On a dispatch it looks the pull request up, refuses one
that is closed, a draft, from a fork, or not at the run's commit, and sets
the outputs `pr`, `base` and `head`.

Publish mode takes two more:

| Input | What it is |
|---|---|
| `min_severity` | the lowest severity (`info`, `low`, `medium` or `high`) that posts or updates the comment; default `low` |
| `title` | the comment's heading, which also marks it so the next run replaces it; default `Knowledge audit` |
| `pr` | on a dispatch, the pull request to post to, from the previous job's `pr` output |

1. Add a repository secret named `AUDIT_API_KEY` with your provider's API
   key. Skip this for an endpoint that takes no key.
2. Create `.github/workflows/knowledge-audit.yml`. It uses DeepSeek V4.1
   Flash on [Ollama Cloud](https://ollama.com/library/deepseek-v4.1-flash),
   so `AUDIT_API_KEY` holds an Ollama API key; change `model` and
   `base_url` for another provider:

   ```yaml
   name: knowledge audit

   # A model rereads each .okf/ and docs/ page whose sources a pull request
   # changed. Start it on a ready pull request's branch:
   #   gh workflow run knowledge-audit.yml --ref BRANCH -f pr=NUMBER
   # Findings never fail the check; a refusal does.
   on:
     workflow_dispatch:
       inputs:
         pr:
           description: The pull request to audit; run on its branch.
           required: true

   # A composite action cannot set token permissions; the calling workflow does.
   permissions:
     contents: read

   jobs:
     # Looks the pull request up, refuses one that is closed, a draft, from
     # a fork or not at this run's commit, and hands the report of the run
     # the audit comment links to the audit job.
     previous:
       runs-on: ubuntu-latest
       permissions:
         contents: read
         pull-requests: read
         actions: read
       outputs:
         pr: ${{ steps.kmctl.outputs.pr }}
         base: ${{ steps.kmctl.outputs.base }}
         head: ${{ steps.kmctl.outputs.head }}
       steps:
         - uses: JasperHG90/kmctl@v0.18.0
           id: kmctl
           with:
             mode: previous
             pr: ${{ inputs.pr }}

     # Never skipped: a skipped job passes a required check.
     audit:
       needs: previous
       if: ${{ !cancelled() }}
       runs-on: ubuntu-latest
       steps:
         - name: Stop unless the pull request was resolved
           env:
             RESULT: ${{ needs.previous.result }}
           run: '[ "$RESULT" = success ] || { echo "previous job: $RESULT" >&2; exit 1; }'
         # No token left in git config for the agent to read; full history to
         # find where the branch split from the base branch.
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0
             persist-credentials: false
         - uses: JasperHG90/kmctl@v0.18.0
           timeout-minutes: 40
           env:
             AUDIT_API_KEY: ${{ secrets.AUDIT_API_KEY }}
           with:
             mode: audit
             base_url: https://ollama.com/v1
             model: deepseek-v4.1-flash
             api_key_env: AUDIT_API_KEY
             base: ${{ needs.previous.outputs.base }}
             head: ${{ needs.previous.outputs.head }}

     # A fresh runner that gets only the report, so nothing the agent
     # changed runs with the token.
     publish:
       needs: [previous, audit]
       if: ${{ !cancelled() && needs.previous.result == 'success' }}
       runs-on: ubuntu-latest
       permissions:
         contents: read
         pull-requests: write
       steps:
         - uses: actions/checkout@v4
           with:
             persist-credentials: false
         - uses: JasperHG90/kmctl@v0.18.0
           with:
             mode: publish
             pr: ${{ needs.previous.outputs.pr }}
   ```

A project made from the copier template gets this workflow by answering
yes to `pr_audit`
([Start a repository with kmctl-starter](start-a-repository-with-kmctl-starter.md)).

`timeout-minutes` on the step is a second limit after `timeout`, so a stuck
run cannot hold the runner for GitHub's six-hour default.

**Run it once the pull request is ready.** The workflow runs on
`workflow_dispatch` only. Start it on the pull request's branch, so its
check lands on the pull request's head commit:

```
gh workflow run knowledge-audit.yml --ref BRANCH -f pr=NUMBER
```

or pick the branch and enter the number in the Actions tab. Then make it
mandatory: in branch protection, mark `audit` a required check. A push after
a run leaves the new commit without the check, so the pull request waits for
another run. The previous job refuses a pull request that is closed, a
draft, from a fork, or whose head is not the run's commit (a run on the
wrong branch, or before the latest push), and the audit job then fails
rather than skips, since GitHub counts a skipped job as passing a required
check. A fork's pull request cannot be dispatched, so a required check
blocks it. Publish runs only once the pull request was resolved, and posts
nothing when the audit failed.

**Each run starts from the last.** The `mode: previous` job, which needs
`pull-requests: read` and `actions: read`, finds the audit comment, follows
its run link and downloads that run's report; the audit job gets it as an
artifact of the same run, so it still holds no token. The agent answers each
earlier finding: still open, keeping its title, or fixed. It raises a new
finding only on a page that changed since the last report, or whose sources
did, and the run sends back any other. The comment then opens with what is
fixed, still open and new. The first run on a pull request, or one after a
rebase or force push that removed the last report's commit, starts fresh.

The comment is short: a count, one bullet per finding at or above
`min_severity` (title, where, and one sentence), the pages that still hold,
and a folded block with each fix, its evidence and the `kmctl verify`
command for the holding pages. It says how many findings below
`min_severity` it left out. A later run replaces it; when a run finds
nothing at that severity, the comment says so. A run that fails or is skipped makes no report, so it leaves the last
comment as it was, which may then be out of date. To title the comment
differently, set `title` under the publish step's `with:`.

Each run on a pull request that changes a file a page names costs one model
run; a run on one that changes none calls no model.

`uv run --no-config --script action/agent.py run --help` lists every option
the agent takes, with its default, and `publish --help` the publish options.

This repository's own `.github/workflows/knowledge-audit.yml` runs the same
commands as separate steps instead of `uses:`: in the previous job,
`action/agent.py previous --pr N --resolve SHA` and the upload of the
previous report; in the audit job, `action/agent.py run --base origin/BASE
--head HEAD` and the upload of the report; in the publish job, the download
and `action/agent.py publish REPORT --pr N`. Read
it to see exactly what the audit runs.

**Ollama.** Ollama Cloud, as in the example, needs only the API key: its
OpenAI-compatible endpoint is `https://ollama.com/v1`, and the model name has
no `:cloud` suffix. For a server of your own, set the model's context size
high enough for the audit, with `PARAMETER num_ctx 65536` in a Modelfile or
`OLLAMA_CONTEXT_LENGTH=65536` for the server. Ollama serves a smaller context
than the model reports unless you set it, so a long conversation is cut
without warning. A GitHub-hosted runner cannot reach Ollama on your own
machine; use a self-hosted runner or a URL the runner can reach.

Audit mode runs on a `workflow_dispatch` that passes the `base` input, as
the example does, or on a `pull_request` from the same repository, for a
workflow that keeps that trigger. Never use `pull_request_target`: it runs
with your secrets for a fork's pull request too. On any other event,
`schedule` included, the action stops with:

```
kmctl audit: refused for event 'pull_request_target'; audit mode runs on a pull_request from the same repository or a workflow_dispatch.
```

Keep `persist-credentials: false` on the checkout, and do not set `GH_TOKEN`
or `GITHUB_TOKEN` for the job. The agent has no shell, but `read_file`
reaches `.git/config`, so it refuses to start when either variable is set or
git config holds checkout's token. Run locally with `GH_TOKEN` set, it prints
this and exits 2:

```
agent: refused: GH_TOKEN is set, and the agent could read the token. Give it only to the publish job, which runs no agent.
```

Only the publish job gets `pull-requests: write` and the token, and it runs
no agent. Keep the two jobs apart: on a self-hosted runner that reuses its
machine between jobs, the agent could leave behind code that the publish
job then runs with the token.

The API key reaches the model provider, never the agent's tools. Still use
a key made for the audit, with a spending limit.

The agent reads your repository's files, so anything checked into it,
secrets included, is in its view, and its findings quote what it read into
the pull request comment.

`pull-requests: write` lets the publish job post and replace its comment.
When the audit fails or is skipped, publish finds no report, posts nothing
and passes, and the last comment stays as it was.

### 6. Later: upgrade to a newer release

Once kmctl has releases, the repository's Releases page lists each one with
its `vX.Y.Z` tag. To move to a newer one:

1. Install kmctl at the new tag, replacing `vX.Y.Z` with it:

   ```
   uv tool install --force git+https://github.com/JasperHG90/kmctl@vX.Y.Z#subdirectory=packages/kmctl
   ```

   `--force` replaces the kmctl you have. `kmctl --version` then prints the
   new version, except in a repository whose `apm.lock.yaml` still pins the
   old one: there it prints the pinned version, followed by
   `(pinned by apm.lock.yaml; kmctl X.Y.Z is on PATH)`, until step 2 moves
   the pin.

2. In each repository where you installed kmctl's package, set `ref` in
   kmctl's `apm.yml` entry to the same tag (moving from v0.12.2 or older to
   a later release, also change `path: apm` to `path: packages/kmctl/apm`),
   then run the `apm install` line
   you installed with and `kmctl plugin patch` again, for example:

   ```
   uvx --from apm-cli==0.33.0 apm install --target claude
   kmctl plugin patch
   ```

   For a user-scope install, change `~/.apm/apm.yml` and run
   `apm install -g` and `kmctl plugin patch --scope user`.
   `kmctl doctor` then reports `claude.lock` (and `antigravity.lock`) as
   `ok` at the new version.

3. Change the ref in each workflow's `uses: JasperHG90/kmctl@`
   line to the same tag.

### 7. To remove kmctl

From the repository root:

```
kmctl plugin patch --undo
uvx --from apm-cli==0.33.0 apm uninstall github.com/JasperHG90/kmctl/packages/kmctl/apm
```

`kmctl plugin patch --undo` deletes what patch wrote:
`.agents/plugins/kmctl/` (it prints `note: deleted .agents/plugins/kmctl/`)
and, for OpenCode, the agents it rewrote, `.opencode/rules/`, the
`instructions` entry in `opencode.json` and `.opencode/plugins/kmctl.js`.
Run it first: `apm uninstall` stops on an agent patch rewrote.
`apm uninstall` takes kmctl's entry out of `apm.yml` and removes the
package for every harness: the skills, agent, rules, hooks and okf's MCP
server. The name is the host, owner and repository of the entry's `git:`
URL, then its `path`: `packages/kmctl/apm`, or `apm` for a release at
v0.12.2 or older.

For a user-scope install, run `apm uninstall -g` with the same name, then
remove okf's MCP server, which APM leaves in your user `.claude.json`:

```
claude mcp remove bundle --scope user
```

Run `kmctl doctor` afterwards to see what is left.

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
ok   claude.okf-mcp: .mcp.json declares okf's MCP server bundle
ok   claude.old-plugin: no settings file enables kmctl@kmctl or okf@scaccogatto
ok   antigravity.lock: apm.lock.yaml has kmctl's package at v0.3.0
ok   antigravity.files: 32 kmctl paths match apm.lock.yaml
ok   antigravity.okf-skills: 19 okf-skills paths match apm.lock.yaml
ok   antigravity.plugin: .agents/plugins/kmctl/ holds what this kmctl writes
ok   antigravity.hook: .agents/hooks.json holds kmctl's SessionStart hook and okf's Stop check
ok   antigravity.apm-hooks: .agents/hooks.json runs no okf Stop check
ok   antigravity.okf-mcp: .agents/mcp_config.json declares okf's MCP server bundle
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
fail kmctl.harness: no kmctl harness in this repository; run apm install --target claude (kmctl's package must be in apm.yml), then kmctl plugin patch
```

Each `fail` line names what is wrong and, after the `;`, the command that
fixes it. With one skill file deleted, it printed
`fail claude.files: .claude/skills/audit/SKILL.md is missing; run apm install --target claude (kmctl's package must be in apm.yml), then kmctl plugin patch`.
A `warn` line has the same shape but fails nothing, so doctor still exits 0.
It is for what doctor cannot judge from here. Without `agy` on PATH, for
example, it prints
`warn dep.agy: agy is not on PATH (needed only by someone who uses antigravity, which is installed here); install the Antigravity CLI so agy is on PATH`:
the harnesses installed are shared by everyone on the repository, so only
someone who uses Antigravity needs `agy`. `antigravity.trust` warns the same
way, because doctor reads only the agy CLI's trusted folders and does not
check trust given in the Antigravity IDE.
For an install made with `apm install -g`, run `kmctl doctor --scope user`.
After you upgrade kmctl, `claude.lock` fails until you move the `apm.yml`
ref to the new tag, as in step 6.

For the action, open a pull request: the `knowledge` job runs and its summary
shows the `kmctl check` and `kmctl review due` reports. For the audit, open a
pull request that changes a file a page names in its `sources`: the
"knowledge audit" workflow runs and, when it has a finding, comments on the
pull request.

All options of these commands are in [Commands](../reference/commands.md).
Why kmctl has one hook and the audit only reports is in
[Why one hook and report-only audits](../explanation/why-one-hook-and-report-only-audits.md).
