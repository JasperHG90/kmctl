---
description: "Every kmaudit command and MCP tool, with their options."
sources:
  - packages/kmaudit/src/kmaudit/cli.py
  - packages/kmaudit/src/kmaudit/mcp_server.py
verified:
  - by: human:jasper
    at: 2026-11-27T20:44:03Z
---

# kmaudit commands

kmaudit is in beta: its MCP tools, the format of its stores and its CLI
may change between minor releases, and the release notes say when they do.

kmaudit has two ways in. Agents drive the audit through the tools of its
MCP server, [`kmaudit mcp`](#kmaudit-mcp): they extract claims, write and
test checks, rerun them and ask the decision model. People review the
claims and checks, and rerun stale checks, on the page
[`kmaudit ui`](#kmaudit-ui) serves. The rest of the CLI reads: the two list
commands, [`kmaudit namespaces`](#kmaudit-namespaces) and
[`kmaudit briefing`](#kmaudit-briefing). Every command takes `--help`;
every command that prints results takes `--json`. Each audited folder is a
namespace with its own store under `.kmaudit/` in the repository; see
[which namespace a path means](#which-namespace-a-path-means).

## Summary

| Command | What it does |
|---|---|
| `kmaudit mcp` | Serve kmaudit's verbs as MCP tools over stdio, for a harness that speaks MCP. |
| `kmaudit ui` | Serve a local page to review claims and checks, give feedback and rerun stale checks. |
| `kmaudit claims list` | Show the stored claims: counts per concept and kind, or each claim. |
| `kmaudit checks list` | Show each claim's check status, strength and why. |
| `kmaudit namespaces` | List the repository's namespaces: each audited folder with its counts. |
| `kmaudit briefing` | Print each namespace's audit state and the next step, changing nothing. |

The CLI once carried the verbs that write: `claims todo` and `submit`,
`checks todo`, `try`, `submit` and `run`, `judge`, `coverage` and `guard`.
Typed now, each exits 2 with one line on stderr naming what replaced it: the
MCP tool of the same name, the `/extract-claims` or `/write-checks` skill,
or a button on `kmaudit ui`. `guard`, a hook that held an agent's shell to
kmaudit commands, has no replacement: kmaudit's agents call the MCP tools
and have no shell.

## `kmaudit mcp`

`kmaudit mcp`

Serve kmaudit's verbs as the tools of an MCP server over stdio. A harness
that speaks MCP starts it and talks to it over stdin and stdout; you do not
run it by hand. kmaudit's [README](../../packages/kmaudit/README.md#mcp-server)
says how to add it to Claude Code, Codex, Antigravity and a LangGraph agent.

Every tool takes `folder`, the namespace: absolute, or relative to the
directory the harness starts the server in. Pass an absolute path when the
harness may start the server outside the repository. Each tool returns
JSON. A call refused as a whole (a folder that does not exist, answers that
are not JSON) comes back as a tool error, `refused: REASON`, naming the
fix, and the server keeps running. A submit that stores some answers and
refuses others is not an error: its result lists each refused answer under
`refused`, with the fix. The verbs run in a worker thread, except `judge`,
which awaits its model calls on the event loop; every subprocess they start
gets no stdin, since stdin carries the MCP messages.

| Tool | Arguments | Returns |
|---|---|---|
| [`namespaces`](#kmaudit-namespaces) | `folder` (default `.`) | what `kmaudit namespaces --json` prints |
| [`claims_todo`](#claims_todo) | `folder`, `limit` (default 5), `brief` | the sections to read and how to answer them |
| [`claims_submit`](#claims_submit) | `folder`, `answers` (a list of section answers, or its JSON text), `by` | `stored` and `refused` |
| [`claims_list`](#kmaudit-claims-list) | `folder`, `kind`, `claims` | what `kmaudit claims list --json` prints |
| [`checks_todo`](#checks_todo) | `folder`, `limit` (default 5), `brief` | the claims to check, with their lines |
| [`checks_try`](#checks_try) | `folder`, `answers` | each draft's result; stores nothing |
| [`checks_submit`](#checks_submit) | `folder`, `answers`, `by` | `stored` and `refused` |
| [`checks_run`](#checks_run) | `folder`, `all` | each claim's status after the rerun |
| [`checks_list`](#kmaudit-checks-list) | `folder`, `status` | what `kmaudit checks list --json` prints |
| [`coverage`](#coverage) | `folder` | how much of the code the checks match |
| [`judge`](#judge) | `folder`, `question` (`failure`, `claim` or `link`), `ids`, `lines` (the claim question's lines) | one entry per id: `{entries: [{id, judgement}` or `{id, error}]}` |

The todo tools hand out 5 items unless given `limit`, so one result stays
well under a harness's limit on tool output (Claude Code warns past about
25,000 tokens). Pass `brief` after the first round to leave out the
instructions and answer schema the agent already has. `checks_run` can take
minutes on a large folder; raise the harness's tool timeout if it gives up
first.

### `claims_todo`

List the folder's sections that have no claims extracted for their current
text. `folder` is the folder of markdown docs to audit, or a folder or page
inside one to narrow the scope; see
[which namespace a path means](#which-namespace-a-path-means).

It cuts each live concept into its `#`, `##` and `###` sections (a `#`
inside a code fence is not a header) and splits each into numbered
sentences: a code block or table is one sentence. In an OKF bundle,
deprecated concepts, `index.md`, `log.md` and `prototypes/` are skipped; any
other folder hands out every `.md` file. Each section has an id,
`concept#slug`, and a key covering its text, its concept's id, title,
status and type, the earlier sections and the extraction instructions.
The earlier sections are in the key because a claim may cite their
sentences, so editing one section also hands out the sections after it in
the same concept.

It then refreshes the store: a section whose key moved, or that is gone,
loses its stored claims. It lists the sections with no extraction at their
current key.

It returns one JSON object: `instructions` (left out with `brief`, with any
key whose value is null), `counts` (`up_to_date`, `pending`, `new`,
`changed`, `removed`), `concepts` (each concept with pending sections:
`concept`, `path`, `sections`, beyond `limit` too), `sections` (each with
`id`, `key`, `concept`, `type`, `status`, `title`, `section`, `sentences`
as `n` and `text`, `earlier`, `corrections`; a correction section's
`corrections` holds only the corrections after it), `namespace` and `next`,
which names `claims_submit` and the folder to pass it.

### `claims_submit`

Store an agent's verdicts and claims. `answers` is a list of section
answers, or its JSON text:

```json
{"section": "manifesto#parts", "key": "f21d0132d11e1d33", "sentences": [
  {"n": 1, "how_to_check": "read src/kmctl/__init__.py", "reason": "names the CLI",
   "kind": "point", "claims": [{"claim": "kmctl is a standalone CLI.",
   "quantifier": "exists", "refers_to": []}]}
]}
```

`kind` is `point`, `structural`, `broad`, `subjective`, `external` or
`none`; `quantifier` is `exists`, `all` or `none`. A claim's id is a hash of
its concept and text. `by` names who wrote the answers, recorded with each
section (default: `agent`).

It refuses, naming the fix, a section the store does not know or whose key
is stale (call `claims_todo` again), an answer that leaves a sentence
without a verdict (naming the numbers), gives one twice or names one out of
range, a kind other than `none` with no claim, and a malformed answer. The
good sections of the same call are still stored. It returns `stored`
(`section`, `claims`) and `refused` (`section`, `reason`).

### `checks_todo`

List the stored point, structural and broad claims with no check, and those
whose reason is stale because a file the claim's anchors named changed. A
claim's id follows its text. When re-extraction rewords a claim, its check
or reason moves to the one claim made from the same sentence and is run
again; with no such claim, or more than one, the answer is dropped and the
claim comes back here.

It returns one JSON object: `instructions` and `answer_schema` (left out
with `brief`), `counts` (`claims`, `checks`, `reasons`, `pending`,
`pruned`, `carried`), `concepts` (`concept`, `path`, `claims`), `claims`
(each with `id`, `concept`, `section`, `kind`, `quantifier`, `claim`,
`sentence`, `how_to_check`, `anchors` and `lines`; a sentence over 800
characters, usually a table, is cut to the lines that share the most words
with the claim, and a claim with no backticked span of its own resolves
only those lines' spans), `namespace` and `next`.

Each claim's `anchors` are its backticked spans resolved to a path, a
command, a flag or a name; `lines` are the lines around them, or keyword
windows from its concept's `sources` and the files it names.

### `checks_try`

Run draft answers. For each check it says whether every step holds and what
it saw, and, when it holds, changes the lines it matched in memory (flip a
boolean, change a number or string, swap `==`, negate a condition, delete a
statement, rename a definition or YAML key, change a YAML value) to see
whether it notices. It writes nothing, not even the store. It returns a
list: per draft its `claim`, `kind`, `holds`, `steps`, `weak`, `mutants`,
`killed`, `missed` and `error`.

An answer is a check, or a reason no check fits:

```json
{"claim": "5daa573f16f0", "strength": "exact", "why": "the write itself",
 "steps": [{"op": "code", "pattern": "open(\"out.txt\", $$$A)", "paths": "src/tool.py"}]}
{"claim": "0369c52d377b", "reason": "No code reads config.toml."}
```

Steps: `file` (`path`, `exists`), `grep` (`pattern`, `paths`, `present`),
`code` (an ast-grep `pattern` and `paths`; presence only), `query` (a
JMESPath `query` over YAML, TOML or JSON `paths`, with `expect` and
`value`), `definition` (`name`, `paths`, `defined`), `imports` (`path`,
`module`, `imported`) and `help` (`command`, `pattern`, `present`). A step
reads only git-tracked files outside the audited folder, `.okf/`, `docs/`,
`.kmctl/` and `.kmaudit/`, and
never a `README.md`, `CLAUDE.md`, `AGENTS.md` or `CHANGELOG.md`, which
restate the knowledge. Other markdown, such as a skill, an agent file or a
prompt, is read: it is what the code runs. A `help` step runs a
tracked argparse script through `uv run --no-project --offline --script`, or
a pyproject script from the repository's `.venv` or `PATH`; it never runs
`uv run` on the project, which would create `.venv` or rewrite `uv.lock`. A
check that fails because the claim is wrong carries
`drift`, one sentence on what the code does instead.

### `checks_submit`

Run and measure each answer as `checks_try` does, and store it. It refuses,
naming the fix:

- a weak check: one that holds but noticed none of the changes, or matched
  only comments or docstrings; the reason names the changes it missed;
- a failing check without `drift`, a holding check with `drift`, and
  `drift` on a check whose step could not run;
- an unknown or stale claim id;
- a code or query step whose library is missing;
- a malformed answer.

The other answers in the same call are stored, reasons included. A check
with no change to try is stored as not measured. It returns `stored`
(`claim`, `kind`, `status`, `mutants`, `killed`) and `refused` (`claim`,
`reason`).

### `checks_run`

Rerun each stored check whose files changed: the content of a file it
reads, or the files its globs match (`all` reruns every one). A holding
check is measured again when its steps or reads moved, and a skipped check
reruns once the extra is there. It calls no model. Each claim's status is
`holds`, `not measured` (holds, but had no change to try), `weak`, `fails`,
`drift`, `skipped` (needs the extra), `reason`, `stale reason` (a file the
claim's anchors named changed, so `checks_todo` hands it out again) or
`no check`. It returns `counts`, `rerun`, `measured` and `claims` (`claim`,
`concept`, `status`, `rerun`, `measured`, `detail`). A failing check is a
result, not an error (audits report only, ADR 0005).

The Rerun stale checks button on [`kmaudit ui`](#kmaudit-ui) calls the same
function for the namespace on screen. A CI job reruns through an MCP
client, or in Python:

```python
from pathlib import Path

from kmaudit.check_verbs import run

print(run(Path(".okf")).counts)
```

### `coverage`

Show how much of the repository's code the claims' checks match. A line is
covered when the last run of a stored check matched it: a grep line, the
whole node a code pattern matched, a definition or an import. A file that
file, query and help steps only read is "read", not covered. The code is
every file a check may read that is on disk, without tests, fixtures,
evals, lock files and the folders harnesses install packages into
(`.github/skills/`, `.github/agents/`, `.agents/`, `.opencode/`); blank
lines do not count. A check whose files changed since its last run is
stale: its lines are not counted, and `stale` says how many, until a rerun
(`checks_run`, or Rerun stale checks on the page). Checks stored before
kmaudit recorded matched lines have none until they run again: call
`checks_run` with `all` once.

It returns `lines`, `covered`, `files`, `files_read`, `stale`, and
`by_file` with each file's `lines`, `covered`, `hits` (per line: `claims`,
`drift`) and `read_by`. The Code tab on `kmaudit ui` shows the same numbers
line by line.

### `judge`

Ask a decision model one question; the one model call kmaudit makes, and
only for a question switched on in the [settings file](#settings-audittoml).

| Question | Takes | Returns |
|---|---|---|
| `failure` | check ids of failed checks | `chance` the claim is false, `cause`: `claim_false`, `check_wrong` or `unclear` |
| `claim` | one claim id, with the lines to judge on in `lines` | `chance` the lines show it true, `verdict`: `true`, `false` or `not_shown` |
| `link` | check ids | `score` from 0 (unrelated) to 1 (tests the claim itself), `level`: `unrelated`, `keyword`, `nearby` or `the claim` (the most likely), and `levels`, the model's probability for each; finding the exact text or value a claim describes counts as testing the claim |

kmaudit builds the state from the store: the claim, its sentence, the check's
steps and what its last run saw. It posts `{model, state, questions}` to the
provider's `base_url` with the key as a bearer token, retries timeouts, 429
(after its `Retry-After`, up to a minute) and 5xx, and keeps at most `max_calls` requests in flight. Each answer is
kept in the namespace's store under a hash of the question, model and
state, so asking again sends nothing (`cached: true`) until the check, its
result or the model changes. A question that is off, a missing key
variable, a 4xx and an answer missing a question each comes back as that id's
`error`, one line naming the fix; a question that is off refuses the whole call.

Each judgement holds `question`, `id`, `model`, `cached`, and `chance` and
`cause`, `chance` and `verdict`, or `score` and `level`.

#### Settings: `audit.toml`

The file is `$XDG_CONFIG_HOME/kmctl/audit.toml` (`~/.config/kmctl/audit.toml`
when the variable is unset), or the file `kmaudit ui --config` or `KMCTL_AUDIT_CONFIG`
names. With no file, every question is off. An unknown key refuses, naming
it.

```toml
[decisions]
timeout = 60     # seconds one call may take
max_calls = 4    # calls in flight at once

[decisions.providers.clef]
base_url = "https://gateway.example/v1/decisions"
api_key_env = "CLEF_API_KEY"   # the variable that holds the key

[decisions.failure]   # also [decisions.claim] and [decisions.link]
enabled = true
provider = "clef"     # a name under [decisions.providers]
model = "jev-latest"
```

A question switched on must name a provider under `[decisions.providers]`
and a model. The key is read only from the variable `api_key_env` names,
and is never printed, stored or put in an error.

#### Tracing

Set `LANGSMITH_TRACING=true` to trace each call as a LangSmith `llm` span;
LangSmith reads `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT` itself. It is off
otherwise.

### Dependencies

Code steps need ast-grep-py, query steps jmespath, and the `judge` tool
tenacity; kmaudit installs all three. Tracing needs langsmith, in the
`tracing` extra:

```
uv tool install --force 'kmaudit[tracing] @ git+https://github.com/JasperHG90/kmctl@kmaudit-v0.1.0#subdirectory=packages/kmaudit'
```

When one of them is missing, those steps report `skipped`, `checks_submit`
refuses them, and `judge` refuses naming the install command.

## `kmaudit ui`

`kmaudit ui [PATH] [--port PORT] [--by NAME] [--config FILE] [--no-open]`

Serve a page on 127.0.0.1 that shows each page of the audited folder with its
claims, their checks and how sure each check is, read live from
the namespace's store. It opens the page in a browser and runs until
Ctrl-C.

On each claim you can:

| Control | What it does |
|---|---|
| Thumbs up or down on the claim | Rates the extracted claim. A thumbs down hands its section out again in `claims_todo` (the next `/extract-claims`), with your note. |
| Thumbs up or down on the check or reason | Rates the answer. A thumbs down hands the claim out again, first, in `checks_todo` (the next `/write-checks`), with your note. |
| Note | Free text kept with the rating. It goes to the agent the next time the item is handed out; on its own it sends nothing back. |
| Your verdict: Claim holds, Claim is false | Your own reading of the claim. It counts over the check's while the files it was given on are unchanged (those the check read, or the files behind the claim's lines when no check read any). When the check says the opposite, or you say false and no check decides the claim yet, the claim goes back to `checks_todo`. |
| Ask for a second opinion | Asks the decision model the `judge` tool uses: `link` for a check that holds, `failure` for one that fails, `claim` for a reason or no answer. Needs the `kmaudit` extra and the question switched on in `audit.toml`. The page shows the answer as a guess; for `link`, when no level gets 70% it says the model is unsure and gives its two likeliest levels. |

The top bar holds two buttons. Reload reads the store again, after an
agent's run. Rerun stale checks reruns every check of the namespace on
screen whose files changed since its last run, through the function the
`checks_run` tool calls, then reads the store again and says how many it
reran. It can take minutes on a large folder.

The controls show only feedback given under your `--by` name; feedback from
anyone else, such as a check sent back on the decision model's word, shows
below them, read-only, with who gave it.

The agent's next submit for that section or claim marks the feedback
answered, whatever it answered; the page then says so, and still shows a
verdict the check disagrees with. In what `claims_todo` and `checks_todo`
return, an item with feedback no agent has answered carries `feedback`
(what you said and, for a check, the answer you judged), and `examples`
lists answers people gave a thumbs up. Each page load refreshes the stored
sections as `claims_todo` does. Each save is a new row in the store's
`feedback` table, so the history stays.

The Code tab shows the repository's code instead: each file with the share
of its lines a check matched, the file with matched lines marked (red where
a matching check fails), and, for a clicked line, the claims whose
checks matched it. A check's card lists the lines it matched, each a link
into the code, and its View code button shows those lines in the card with
three lines around them; for a check that tests whole files, it shows each
file it read (up to four, 400 lines each), and it warns when a file
changed since the check ran. The `coverage` tool gives the same numbers.

The server answers only requests whose Host is `127.0.0.1` or `localhost`,
takes writes (feedback, a second opinion, a rerun) only as JSON from its
own page, and serves the text only of files a check may read.

| Option | Meaning |
|---|---|
| `PATH` | The namespace: its folder or a path in it (default: the current directory). |
| `--port PORT` | The port on 127.0.0.1; `0` picks any free one (default: `8765`). A taken port refuses, naming `--port 0`. |
| `--by NAME` | The name your feedback is stored under (default: `human`). |
| `--config FILE` | The `audit.toml` to read for a second opinion, instead of the per-user one. |
| `--no-open` | Print the address without opening a browser. |

## `kmaudit claims list`

`kmaudit claims list [PATH] [--kind KIND] [--claims] [--json]`

Show the stored claims. It reads only the store (creating it when absent),
as the last extraction left it; `/extract-claims` brings it in line with
the pages.

| Option | Meaning |
|---|---|
| `--kind KIND` | Only claims of this kind. |
| `--claims` | Each claim, with its sentence, kind, quantifier, how to check and reason. |
| `--json` | One JSON object: `documents` (`concept`, `sections`, `extracted`, `claims` per kind) and `totals`; with `--claims`, `claims` (each with `id`, `section`, `concept`, `n`, `sentence`, `kind`, `claim`, `quantifier`, `how_to_check`, `reason`, `refers_to`). |

## `kmaudit checks list`

`kmaudit checks list [PATH] [--status STATUS] [--json]`

Show each claim's status as the last rerun or `checks_submit` left it, with
its strength, why, drift or reason and mutation score (`killed/mutants`, or
`not measured`). `--status` keeps one status. For the current state, press
Rerun stale checks on `kmaudit ui` first, or call `checks_run`.

## `kmaudit briefing`

`kmaudit briefing [PATH] [--json]`

Print, for each namespace, its sections and how many are pending, its
claims, its checks by status and its open notes from people, then the one
thing to do next: `/extract-claims FOLDER` while sections are pending,
`/write-checks FOLDER` while claims lack a current answer, `kmaudit ui
FOLDER` while checks show drift, fail or are weak, or notes are open.

It is meant for a session-start hook and changes no store: it opens each
store read-only (SQLite may create its `-wal` and `-shm` sidecars) and
counts pending sections by cutting the pages, where `claims_todo` would
refresh and drop the claims of changed sections. A store at an older
schema step is read through an in-memory copy, migrated there, so it
briefs like a current one. With no namespace it prints nothing (with
`--json`, an empty `namespaces` list); on any error it prints one line
saying the briefing is unavailable (with `--json`, an `unavailable` key
holding the reason). It always exits 0.

| Option | Meaning |
|---|---|
| `PATH` | A path in the repository (default: the current directory). |
| `--json` | One JSON object: `namespaces`, each with `namespace`, `sections`, `pending`, `claims`, `checks` (per status), `feedback` and `next`; on an error, `namespaces` is empty and `unavailable` holds the reason. |

## `kmaudit namespaces`

`kmaudit namespaces [PATH] [--json]`

List the repository's namespaces: each audited folder with its store's
counts of sections, claims and checks. It writes nothing.

| Option | Meaning |
|---|---|
| `PATH` | A path in the repository (default: the current directory). |
| `--json` | One JSON object: `namespaces`, each with `namespace`, `folder`, `sections`, `claims` and `checks`. |

### Which namespace a path means

A namespace is an audited folder, named by its path below the repository
root (`.okf`, `docs`, `handbook/guides`). Which namespace a path means:

- A folder or page inside an existing namespace means that namespace,
  narrowed to the pages under the path; it never opens a store of its own.
- A page inside an OKF bundle means the bundle.
- A folder with no namespace above it opens one, unless a namespace already
  sits inside it: that is refused, naming the namespace it would overlap.
  Audit that folder instead, or delete its store to start over higher up.
- A page with no namespace or bundle above it is refused: give its folder
  first.
- The repository root holding `.okf/` means `.okf`.

The tools that write (`claims_submit`, `checks_try`, `checks_submit`,
`judge`) take their namespace as `folder`, as the todo tools' `namespace`
and `next` give it.

## The store

Each namespace keeps its state in its own SQLite file,
`.kmaudit/<namespace>.sqlite` at the repository root (git's top level). kmaudit
creates `.kmaudit/` with a `.gitignore` holding `*`, so git ignores the
folder and your own `.gitignore` is never edited. Each checkout has its own
stores, and the verbs write nothing else: never the audited folder.

A repository audited before kmaudit had namespaces kept one store at
`.kmctl/audit.sqlite`. The first command or tool on `.okf` copies it into the `.okf`
namespace, with SQLite's backup API, and leaves the old file as it was.
