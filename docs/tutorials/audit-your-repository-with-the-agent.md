---
description: "Run the CI agent on your machine against a branch, read its report on the pages your change touched, and check a finding."
sources:
  - resource: "action/agent.py"
  - resource: "action/prompt.md"
---

# Audit your repository with the agent

## What you will build

A report made on your machine by the agent the CI action runs on a pull
request, `action/agent.py`. You will run it once on a branch with no change
and see it skip the model, then change one line of kmctl's code that two
pages describe, run it again, read the finding it returns and check it
yourself. It takes about fifteen minutes, most of it waiting for the agent.

The agent does one thing
([ADR 0060](../../.okf/decisions/0060-the-ci-agent-only-rereads-the-pages-a-pull-request-changed.md)):
it lists every page under `.okf/` and `docs/` whose `sources` name a file
your branch changed since it split from the base branch, and has a model
reread each page against the change. A model's wording varies from run to
run, so this page shows the shape of its report, not a copy of one run.

## Before you start

- `git` and [uv](https://docs.astral.sh/uv/) on your PATH. You do not need
  kmctl itself installed.
- A Gemini API key, from [Google AI Studio](https://aistudio.google.com/apikey).
  Any provider with an OpenAI-compatible API works, but this tutorial uses
  Gemini.

## Steps

### 1. Get the agent

```
git clone https://github.com/JasperHG90/kmctl kmctl
cd kmctl
```

The kmctl repository is private for now, so this needs a GitHub account with
access to it. The agent is one file, `action/agent.py`, and its task is
`action/prompt.md` beside it. The script lists its own dependencies, so
`uv run` installs them the first time you run it.

### 2. Set your key

```
export GEMINI_API_KEY=your-key-here
unset GH_TOKEN GITHUB_TOKEN
```

The agent can read any file in the repository, so it refuses to start while
a GitHub token is set or git config holds one.

### 3. Run it with nothing to reread

Make a branch and run the agent against `main`:

```
git switch -c try-the-audit
uv run --no-config --script action/agent.py run \
  --model gemini-3.8-flash \
  --base-url https://generativelanguage.googleapis.com/v1beta/openai/ \
  --api-key-env GEMINI_API_KEY \
  --base main \
  --out ../report0
```

`--base main` is the branch to compare with, `--base-url` and `--model` pick
the provider and model, and `--api-key-env` names the variable that holds
the key. `--no-config` stops uv from reading a `uv.toml` or `pyproject.toml`
from the checkout, as the action does.

The branch has no commit of its own yet, so no page is in scope. The agent
writes an empty report without calling the model, and prints:

```
## Agent report

No page under .okf/ or docs/ names a file this change touched (compared with main) in its sources, so nothing was reread.

0 high, 0 medium, 0 low, 0 info.

| Severity | Finding | Summary | Claim | Contradicted by | Fix |
|---|---|---|---|---|---|

### Checked (0)

agent: wrote report.json, report.md and transcript.json to ../report0
```

In CI, a push like this costs nothing.

### 4. Change a line three pages cover

`kmctl decision candidates` lists the changes since the newest decision
record. Make it start from the oldest one instead, and commit:

```
sed -i.bak 's/records\[-1\]/records[0]/' packages/kmctl/src/kmctl/candidates.py
rm packages/kmctl/src/kmctl/candidates.py.bak
git commit -am "Start decision candidates at the oldest record"
```

The agent compares commits, so it sees only what you commit. Two pages
name `packages/kmctl/src/kmctl/candidates.py` in their `sources`: the how-to
`docs/how-to/find-unrecorded-decisions.md` and ADR 0047
(`.okf/decisions/0047-unrecorded-decisions-are-listed-by-kmctl-and-judged-by-a-skill-that-only-reports.md`).
A third, ADR 0046, which says which package the file belongs in, names the
folder `packages/kmctl/`; the agent matches a folder source as a prefix, so
it is in scope too. The how-to and
ADR 0047 say the list starts at the newest record, so both are now wrong.
ADR 0046 still holds.

### 5. Run it again

```
uv run --no-config --script action/agent.py run \
  --model gemini-3.8-flash \
  --base-url https://generativelanguage.googleapis.com/v1beta/openai/ \
  --api-key-env GEMINI_API_KEY \
  --base main \
  --out ../report
```

The agent reads the three pages and the changed code for a few minutes, then
prints its report and ends with:

```
agent: wrote report.json, report.md and transcript.json to ../report
```

### 6. Read the report

Open `../report/report.md`. Under its heading it starts with a summary and
a count by severity. The summary says how many pages and claims the agent
checked, and ends with the pages that still hold and the
`kmctl verify ID ... --by human:<your id>` command to record that once you
have read them. The agent never runs that command itself.

Then comes one row per finding. A finding is always a mismatch: the claim
that does not hold, the lines that contradict it, and a fix. Expect one for
each page, citing its line about the newest record as the claim and
`packages/kmctl/src/kmctl/candidates.py:180` as what contradicts it. The fix
depends on the page:

- For the how-to, an edit to the page.
- For ADR 0047, a stable decision, never an edit to its body: a dated
  Correction section, a new draft decision that supersedes it, or a change
  to the code. Here the right fix is to undo the code change.

Last comes the checked list: each page the agent compared, what it compared
it against and the lines it read. A page that holds goes here, not in the
findings.

### 7. Check a finding yourself

Every citation is a `path:line`, so you can look at it. Print the claim and
the lines that contradict it, using the numbers in your own report, for
example:

```
grep -n 'newest' docs/how-to/find-unrecorded-decisions.md
sed -n 179,181p packages/kmctl/src/kmctl/candidates.py
```

```
29:   With no starting point, it looks at the changes since the newest
    added = _git(
        root, "log", "--follow", "--diff-filter=A", "--format=%H", "--", records[0]
    ).split()
```

The agent cannot make up a citation. The script notes each line that its
`read_file` and `search_files` tools returned, and sends back any report
that cites another line. After five retries the run fails with no report.

### 8. Clean up

```
git switch main
git branch -D try-the-audit
```

## What you learned

- The agent rereads only the pages whose `sources` name a file your branch
  changed: decisions (drafts included), architecture pages, practices and
  docs pages. A deprecated or superseded decision, handoffs, the log and
  `index.md` pages stay out.
- With nothing in scope it writes an empty report and calls no model.
- Every finding names the claim, the lines that contradict it and a fix, and
  you can check each citation with the file and the line number.

`report.json` holds the same report as data, for a script to read:

| Field | What it holds |
|---|---|
| `summary` | A short summary of the run. |
| `checked` | One entry per page compared: `subject`, `against` (what it was compared with) and `evidence` (`path:line` strings). |
| `findings` | One entry per mismatch: `title`, `severity`, `path` (the file it is about), `summary`, `claim` (`path:line`), `contradicted_by` (`path:line` strings) and `fix`. |

A finding's `severity` is `high` for a claim the code contradicts that
would lead a reader to act wrongly, `medium` for a claim probably wrong or
that the agent could not check, `low` for a claim that is wrong but would
still leave a reader acting correctly, and `info` for a note that needs no
fix. The comment on a pull request lists every finding at
`low` or above.

To run the agent on your pull requests and post its report as a comment,
follow step 5 of
[Install the plugin and the CI action](../how-to/install-the-plugin-and-the-ci-action.md).
`uv run --no-config --script action/agent.py run --help` lists every option.
