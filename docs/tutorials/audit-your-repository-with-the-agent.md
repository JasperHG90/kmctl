---
description: "Run the CI agent on your machine, read its report and check a finding, then give it a task of your own."
sources:
  - action/agent.py
---

# Audit your repository with the agent

## What you will build

An audit report made on your machine by the agent the CI action runs,
`action/agent.py`. You will break one line of kmctl's command reference,
ask the agent to check that page against the code, read the finding it
returns and check it yourself, then give it a second task that uses a
folder of your own rules. It takes about fifteen minutes, most of it
waiting for the agent.

Every command below was run on a fresh clone of kmctl's `main` branch with
Gemini 3.8 Flash, and the output shown is what it printed. A model's
wording varies from run to run, so yours will not match word for word.

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
access to it. The agent is one file, `action/agent.py`. It lists its own
dependencies, so `uv run` installs them the first time you run it.

### 2. Set your key

```
export GEMINI_API_KEY=your-key-here
unset GH_TOKEN GITHUB_TOKEN
```

The agent can run shell commands, so it refuses to start while a GitHub
token is in reach.

### 3. Break one line of the docs

The reference page says `kmctl review due` takes `--json`. Rename it on the
page only:

```
sed -i.bak 's/| `--json` | Print one JSON object (`due`/| `--as-json` | Print one JSON object (`due`/' docs/reference/commands.md
grep -n 'as-json' docs/reference/commands.md
```

```
256:| `--as-json` | Print one JSON object (`due`, `notices`, `expired_handoffs`, `history_skipped`). | off |
```

The code still says `--json`, so the page is now wrong in one place. `sed`
kept the original as `docs/reference/commands.md.bak`.

### 4. Write a task

The agent does whatever its prompt asks. Save this as `../task.md`, next to
your clone:

```
Check the `kmctl review due` section of docs/reference/commands.md against
the code in src/kmctl/ that defines that command: its options, their
defaults and what it prints.
```

### 5. Run it

```
uv run --script action/agent.py run \
  --model gemini-3.8-flash \
  --base-url https://generativelanguage.googleapis.com/v1beta/openai/ \
  --api-key-env GEMINI_API_KEY \
  --prompt-file ../task.md \
  --out ../report
```

`--base-url` and `--model` pick the provider and model, and `--api-key-env`
names the variable that holds the key. The agent reads, searches and runs
commands for a few minutes, then prints its report and ends with:

```
agent: wrote report.json, report.md and transcript.json to ../report
```

### 6. Read the report

Open `../report/report.md`. Under its heading it starts with a summary and
a count by severity:

```
Checked the `kmctl review due` section of docs/reference/commands.md
against src/kmctl/__init__.py and src/kmctl/review_due.py. The command
behavior, exit code, docs due criteria, and output formatting match the
implementation, but the options table documents `--as-json` instead of
`--json`.

1 high, 0 medium, 0 low, 0 info.
```

Then comes one row per finding. A finding is always a mismatch: the claim
that does not hold, the lines that contradict it, and a fix. Without its
summary column:

| Severity | Finding | Claim | Contradicted by | Fix |
|---|---|---|---|---|
| high | Incorrect option name `--as-json` in options table | `docs/reference/commands.md:256` | `src/kmctl/__init__.py:276`, `src/kmctl/__init__.py:292-298` | Change `--as-json` to `--json` in the options table for `kmctl review due`. |

That is the line you broke. Last comes the checked list: what the agent
compared, what it compared it against and the lines it read. Something that
holds goes here, not in the findings. This run checked five things, for
example:

```
- `Exit code of `kmctl review due`` against Command implementation and CLI
  epilog in src/kmctl/__init__.py: `docs/reference/commands.md:258`,
  `src/kmctl/__init__.py:277`, `src/kmctl/__init__.py:301-319`
```

### 7. Check the finding yourself

Every citation is a `path:line`, so you can look at it. Print the claim and
the lines that contradict it, using the numbers in your own report:

```
sed -n 256p docs/reference/commands.md
sed -n 292,298p src/kmctl/__init__.py
```

```
| `--as-json` | Print one JSON object (`due`, `notices`, `expired_handoffs`, `history_skipped`). | off |
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (due, notices, expired_handoffs, history_skipped), for scripts.",
        ),
    ] = False,
```

The agent cannot make up a citation. The script notes each line that its
`read_file` and `search_files` tools returned, and sends back any report
that cites another line. After five retries the run fails with no report.

### 8. Give it your own rules

The agent can read folders besides the repository. Make one next to your
clone:

```
mkdir ../context
```

Save this as `../context/docs-rules.md`:

```
# Our docs rules

1. A tutorial says how long it takes, near the top.
2. A tutorial lists what the reader needs before they start.
3. Every command a reader runs is in a fenced code block.
```

Save this as `../task2.md`:

```
Check every page in docs/tutorials/ against our docs rules, in the
docs-rules.md file of the context folder you were given.
```

Run it with `--context`:

```
uv run --script action/agent.py run \
  --model gemini-3.8-flash \
  --base-url https://generativelanguage.googleapis.com/v1beta/openai/ \
  --api-key-env GEMINI_API_KEY \
  --prompt-file ../task2.md \
  --context ../context \
  --out ../report2
```

Open `../report2/report.md`. The agent read the rules from the context
folder and cites them like any other file:

```
Checked every page in docs/tutorials/ against the documentation rules in
context/docs-rules.md. docs/tutorials/README.md is the auto-generated
section index and contains no reader commands.
docs/tutorials/get-started-with-kmctl.md satisfies rule 1 (time estimate
near the top) and rule 2 (prerequisites listed before starting), but has 1
low-severity mismatch against rule 3 where 'kmctl --version' in the
prerequisites verification is written inline rather than in a fenced code
block.

0 high, 0 medium, 1 low, 0 info.
```

| Severity | Finding | Claim | Contradicted by | Fix |
|---|---|---|---|---|
| low | Command not in fenced code block | `docs/tutorials/get-started-with-kmctl.md:29` | `../context/docs-rules.md:5` | Put the kmctl --version command in a fenced code block. |

Your clone also has this page, so your agent checks it too and may report
on it.

## What you learned

- The agent does the task its prompt gives it, and returns a report: a
  checked list, and findings that are mismatches only.
- Every finding names the claim, the lines that contradict it and a fix, and
  you can check each citation with the file and the line number.
- `--context` gives it more folders to read, such as rules or architecture
  documents your workflow fetches.
- Instead of a task of your own, `--audit` runs one of the three shipped
  audits: `okf-vs-code` (`.okf/` against the code, the default),
  `docs-vs-code` (`docs/` against the code) or `okf-vs-docs` (`docs/`
  against `.okf/`). Their prompts are in `action/prompts/`.

`report.json` holds the same report as data, for a script to read:

| Field | What it holds |
|---|---|
| `summary` | A short summary of the run. |
| `checked` | One entry per thing compared: `subject`, `against` (what it was compared with) and `evidence` (`path:line` strings). |
| `findings` | One entry per mismatch: `title`, `severity`, `path` (the file it is about), `summary`, `claim` (`path:line`), `contradicted_by` (`path:line` strings) and `fix`. |

A finding's `severity` is `high` for something wrong that someone must fix,
`medium` for something probably wrong or that the agent could not check,
`low` for something minor, and `info` for a note that needs no fix.

To run the agent in CI, and post its findings to an issue, follow step 5 of
[Install the plugin and the CI action](../how-to/install-the-plugin-and-the-ci-action.md).
`uv run --script action/agent.py run --help` lists every option.
