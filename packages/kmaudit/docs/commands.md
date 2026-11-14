# kmaudit commands

Every command takes `--help`; every command that prints results takes
`--json`. Each audited folder is a namespace with its own store under
`.kmaudit/` in the repository; see [Namespaces](#namespaces).

## Summary

| Command | What it does |
|---|---|
| `kmaudit` | Audit what a folder of markdown docs claims about its repository. Groups: `claims` and `checks`; verbs: `judge`, `ui` and `coverage`. kmaudit calls no model except `judge`: a coding agent reads what these verbs hand out and submits its answers. |
| `kmaudit claims todo` | List the folder's sections that have no claims extracted for their current text. |
| `kmaudit claims submit` | Store an agent's verdicts and claims for sections that `todo` handed out. |
| `kmaudit claims list` | Show the stored claims: counts per concept and kind, or each claim. |
| `kmaudit checks todo` | List the stored claims that have no check or current reason, with the lines they are about. |
| `kmaudit checks try` | Run draft checks and show whether each holds and which changes it would miss. |
| `kmaudit checks submit` | Store checks and reasons for claims, refusing weak and failing checks. |
| `kmaudit checks run` | Rerun the stored checks whose files changed, with no model, and report each claim's status. |
| `kmaudit checks list` | Show each claim's check status, strength and why. |
| `kmaudit judge` | Ask the configured decision model one question about stored checks or a claim. |
| `kmaudit coverage` | Show how much of the repository's code the claims' checks match, line by line. |
| `kmaudit ui` | Serve a local page to review claims and checks and give feedback on them. |
| `kmaudit namespaces` | List the repository's namespaces: each audited folder with its counts. |
| `kmaudit briefing` | Print each namespace's audit state and the next step, changing nothing. |
| `kmaudit guard` | Allow a Bash call only when it is one `kmaudit` command, as a PreToolUse hook. |

## `kmaudit claims todo`

`kmaudit claims todo [PATH] [--limit N] [--json]`

List the folder's sections that have no claims extracted for their current
text. `PATH` is the folder of markdown docs to audit, or a folder or page
inside one to narrow the scope (default: the current directory); see
[Namespaces](#namespaces) for which namespace a path means.

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

| Option | Meaning |
|---|---|
| `--limit N` | Hand out at most N sections; the counts still cover all. |
| `--json` | One JSON object: `instructions` (once), `counts` (`up_to_date`, `pending`, `new`, `changed`, `removed`), `concepts` (each concept with pending sections: `concept`, `path`, `sections`, beyond `--limit` too), `sections` (each with `id`, `key`, `concept`, `type`, `status`, `title`, `section`, `sentences` as `n` and `text`, `earlier`, `corrections`; a correction section's `corrections` holds only the corrections after it), `namespace` and `next`, which spells `--path NAMESPACE`. |

Without `--json` it prints the counts, a `pending FILE  (N sections)` line
per concept with pending sections and, when any are pending, a `Next:` line
naming `kmaudit claims submit`.

## `kmaudit claims submit`

`kmaudit claims submit [FILE|-] [--path PATH] [--by NAME] [--json]`

Store an agent's verdicts and claims. The input, from `FILE` or stdin
(`-`, the default), is one section answer or a JSON list of them:

```json
{"section": "manifesto#parts", "key": "f21d0132d11e1d33", "sentences": [
  {"n": 1, "how_to_check": "read src/kmctl/__init__.py", "reason": "names the CLI",
   "kind": "point", "claims": [{"claim": "kmctl is a standalone CLI.",
   "quantifier": "exists", "refers_to": []}]}
]}
```

`kind` is `point`, `structural`, `broad`, `subjective`, `external` or
`none`; `quantifier` is `exists`, `all` or `none`. A claim's id is a hash of
its concept and text.

It refuses, as one stderr line naming the fix, a section the store does not
know or whose key is stale (run `todo` again), an answer that leaves a
sentence without a verdict (naming the numbers), gives one twice or names
one out of range, a kind other than `none` with no claim, and a malformed
answer. The good sections of the same input are still stored. It exits 1
when any section is refused.

| Option | Meaning |
|---|---|
| `--path PATH` | The repository whose store to write (default: the current directory). |
| `--by NAME` | Who wrote the answers, recorded with each section (default: `agent`). |
| `--json` | One JSON object: `stored` (`section`, `claims`) and `refused` (`section`, `reason`). |

## `kmaudit claims list`

`kmaudit claims list [PATH] [--kind KIND] [--claims] [--json]`

Show the stored claims. It reads only the store (creating it when absent);
run `todo` first to bring it in line with the bundle.

| Option | Meaning |
|---|---|
| `--kind KIND` | Only claims of this kind. |
| `--claims` | Each claim, with its sentence, kind, quantifier, how to check and reason. |
| `--json` | One JSON object: `documents` (`concept`, `sections`, `extracted`, `claims` per kind) and `totals`; with `--claims`, `claims` (each with `id`, `section`, `concept`, `n`, `sentence`, `kind`, `claim`, `quantifier`, `how_to_check`, `reason`, `refers_to`). |

## `kmaudit checks todo`

`kmaudit checks todo [PATH] [--limit N] [--brief] [--json]`

List the stored point, structural and broad claims with no check, and those
whose reason is stale because a file the claim's anchors named changed. A
claim's id follows its text. When re-extraction rewords a claim, its check
or reason moves to the one claim made from the same sentence and is run
again; with no such claim, or more than one, the answer is dropped and the
claim comes back here.

| Option | Meaning |
|---|---|
| `--limit N` | Hand out at most N claims; the counts still cover all. |
| `--brief` | Leave `instructions` and `answer_schema` out of `--json`, for an agent's rounds after the first. |
| `--json` | One JSON object: `instructions` and `answer_schema` (once), `counts` (`claims`, `checks`, `reasons`, `pending`, `pruned`, `carried`), `concepts` (`concept`, `path`, `claims`), `claims` (each with `id`, `concept`, `section`, `kind`, `quantifier`, `claim`, `sentence`, `how_to_check`, `anchors` and `lines`; a sentence over 800 characters, usually a table, is cut to the lines that share the most words with the claim, and a claim with no backticked span of its own resolves only those lines' spans) and `next`. |

Each claim's `anchors` are its backticked spans resolved to a path, a
command, a flag or a name; `lines` are the lines around them, or keyword
windows from its concept's `sources` and the files it names.

## `kmaudit checks try`

`kmaudit checks try [FILE|-] [--path PATH] [--json]`

Run draft answers. For each check it says whether every step holds and what
it saw, and, when it holds, changes the lines it matched in memory (flip a
boolean, change a number or string, swap `==`, negate a condition, delete a
statement, rename a definition or YAML key, change a YAML value) to see whether it
notices. It writes nothing, not even the store, and exits 0.

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

## `kmaudit checks submit`

`kmaudit checks submit [FILE|-] [--path PATH] [--by NAME] [--json]`

Run and measure each answer as `try` does, and store it. It refuses, as one
stderr line naming the fix:

- a weak check: one that holds but noticed none of the changes, or matched
  only comments or docstrings; the line names the changes it missed;
- a failing check without `drift`, a holding check with `drift`, and
  `drift` on a check whose step could not run;
- an unknown or stale claim id;
- a code or query step without the `kmaudit` extra;
- a malformed answer.

The other answers in the same input are stored, reasons included. A check
with no change to try is stored as not measured. It exits 1 when any answer
is refused.

## `kmaudit checks run`

`kmaudit checks run [PATH] [--all] [--json]`

Rerun each stored check whose files changed: the content of a file it
reads, or the files its globs match (`--all` reruns every one). A holding
check is measured again when its steps or reads moved, and a skipped check
reruns once the extra is there. It calls no model. Each claim's status is
`holds`, `not measured` (holds, but had no change to try), `weak`, `fails`,
`drift`, `skipped` (needs the extra), `reason`, `stale reason` (a file the
claim's anchors named changed, so `todo` hands it out again) or `no check`. It exits 0 whatever the checks find,
and 1 only when it cannot run.

## `kmaudit checks list`

`kmaudit checks list [PATH] [--status STATUS] [--json]`

Show each claim's status as the last `run` or `submit` left it, with its
strength, why, drift or reason and mutation score (`killed/mutants`, or
`not measured`). `--status` keeps one status.

## `kmaudit ui`

`kmaudit ui [PATH] [--port PORT] [--by NAME] [--config FILE] [--no-open]`

Serve a page on 127.0.0.1 that shows each page of the audited folder with its
claims, their checks and how sure each check is, read live from
the namespace's store. It opens the page in a browser and runs until
Ctrl-C.

On each claim you can:

| Control | What it does |
|---|---|
| Thumbs up or down on the claim | Rates the extracted claim. A thumbs down hands its section out again in `kmaudit claims todo`, with your note. |
| Thumbs up or down on the check or reason | Rates the answer. A thumbs down hands the claim out again, first, in `kmaudit checks todo`, with your note. |
| Note | Free text kept with the rating. It goes to the agent the next time the item is handed out; on its own it sends nothing back. |
| Your verdict: Claim holds, Claim is false | Your own reading of the claim. It counts over the check's while the files it was given on are unchanged (those the check read, or the files behind the claim's lines when no check read any). When the check says the opposite, or you say false and no check decides the claim yet, the claim goes back to `kmaudit checks todo`. |
| Ask for a second opinion | Asks the decision model `kmaudit judge` uses: `link` for a check that holds, `failure` for one that fails, `claim` for a reason or no answer. Needs the `kmaudit` extra and the question switched on in `audit.toml`. The page shows the answer as a guess; for `link`, when no level gets 70% it says the model is unsure and gives its two likeliest levels. |

The controls show only feedback given under your `--by` name; feedback from
anyone else, such as a check sent back on the decision model's word, shows
below them, read-only, with who gave it.

The agent's next `submit` for that section or claim marks the feedback
answered, whatever it answered; the page then says so, and still shows a
verdict the check disagrees with. In the `--json` output of both `todo`
verbs, an item with feedback no agent has answered carries `feedback`
(what you said and, for a check, the answer you judged), and `examples`
lists answers people gave a thumbs up. Each page load refreshes the stored
sections as `kmaudit claims todo` does. Each save is a new row in the store's `feedback` table,
so the history stays.

The Code tab shows the repository's code instead: each file with the share
of its lines a check matched, the file with matched lines marked (red where
a matching check fails), and, for a clicked line, the claims whose
checks matched it. A check's card lists the lines it matched, each a link
into the code, and its View code button shows those lines in the card with
three lines around them; for a check that tests whole files, it shows each
file it read (up to four, 400 lines each), and it warns when a file
changed since the check ran. `kmaudit coverage` gives the same numbers.

The server answers only requests whose Host is `127.0.0.1` or `localhost`,
takes writes only as JSON from its own page, and serves the text only of
files a check may read.

| Option | Meaning |
|---|---|
| `PATH` | The namespace: its folder or a path in it (default: the current directory). |
| `--port PORT` | The port on 127.0.0.1; `0` picks any free one (default: `8765`). A taken port refuses, naming `--port 0`. |
| `--by NAME` | The name your feedback is stored under (default: `human`). |
| `--config FILE` | The `audit.toml` to read for a second opinion, instead of the per-user one. |
| `--no-open` | Print the address without opening a browser. |

## `kmaudit coverage`

`kmaudit coverage [PATH] [--files N] [--json]`

Show how much of the repository's code the claims' checks match. A line is
covered when the last run of a stored check matched it: a grep line, the
whole node a code pattern matched, a definition or an import. A file that
file, query and help steps only read is "read", not covered. The code is
every file a check may read that is on disk, without tests, fixtures,
evals, lock files and the folders harnesses install packages into
(`.github/skills/`, `.github/agents/`, `.agents/`, `.opencode/`); blank
lines do not count. A check whose files changed since its last run is
stale: its lines are not counted, and the output says how many, until
`kmaudit checks run` reruns it.

```
2,101 of 18,642 lines of code matched by a check (11.3%); 104 of 107 files read by one
no line matched  scripts/next_release_version.py  (144 lines)
```

Checks stored before kmaudit recorded matched lines have none until they run
again: run `kmaudit checks run --all` once.

| Option | Meaning |
|---|---|
| `PATH` | The namespace: its folder or a path in it (default: the current directory). |
| `--files N` | How many of the largest files with no matched line to list (default: 5). |
| `--json` | One JSON object: `lines`, `covered`, `files`, `files_read`, `stale`, and `by_file` with each file's `lines`, `covered`, `hits` (per line: `claims`, `drift`) and `read_by`. |

## `kmaudit briefing`

`kmaudit briefing [PATH] [--json]`

Print, for each namespace, its sections and how many are pending, its
claims, its checks by status and its open notes from people, then the one
thing to do next: `/extract-claims FOLDER` while sections are pending,
`/write-checks FOLDER` while claims lack a current answer, `kmaudit ui
FOLDER` while checks show drift, fail or are weak, or notes are open.

It is meant for a session-start hook and changes no store: it opens each
store read-only (SQLite may create its `-wal` and `-shm` sidecars) and
counts pending sections by cutting the pages, where `claims todo` would
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

## `kmaudit guard`

`kmaudit guard --allow claims|checks`

A Claude Code PreToolUse hook. The `kmctl-claims-extractor` and
`kmctl-check-writer` agents run it from their front matter before each Bash
call. It reads the hook's JSON on stdin and lets the call through only when
it is one `kmaudit claims` (or `checks`) command, optionally after
`cd DIR &&`, optionally fed by one quoted heredoc (`<<'ANSWERS'`) whose body
is data. A pipe, redirect, second command, unquoted heredoc or command
substitution is blocked: exit 2, with the reason on stderr. Calls to other
tools pass. Antigravity and OpenCode have no per-agent hook, so there the
agents' instructions hold the same rule.

| Option | Meaning |
|---|---|
| `--allow GROUP` | The `kmaudit` group the agent may run: `claims` or `checks`. Anything else exits 2. |

## `kmaudit judge`

`kmaudit judge QUESTION ID... [--path PATH] [--config FILE] [--json]`

Ask a decision model one question; the one model call kmaudit makes, and only
for a question switched on in the settings file.

| Question | Takes | Prints |
|---|---|---|
| `failure` | check ids of failed checks | `chance` the claim is false, `cause`: `claim_false`, `check_wrong` or `unclear` |
| `claim` | one claim id, with the lines to judge on stdin | `chance` the lines show it true, `verdict`: `true`, `false` or `not_shown` |
| `link` | check ids | `score` from 0 (unrelated) to 1 (tests the claim itself), `level`: `unrelated`, `keyword`, `nearby` or `the claim` (the most likely), and `levels`, the model's probability for each; finding the exact text or value a claim describes counts as testing the claim |

kmaudit builds the state from the store: the claim, its sentence, the check's
steps and what its last run saw. It posts `{model, state, questions}` to the
provider's `base_url` with the key as a bearer token, retries timeouts, 429
(after its `Retry-After`, up to a minute) and 5xx, and keeps at most `max_calls` requests in flight. Each answer is
kept in the namespace's store under a hash of the question, model and
state, so asking again sends nothing (`cached: true`) until the check, its
result or the model changes. A question that is off, a missing key
variable, a 4xx and an answer missing a question each refuse in one stderr
line; exit 1 when any id is refused.

| Option | Meaning |
|---|---|
| `--path PATH` | The repository whose store to read (default: the current directory). |
| `--config FILE` | The settings file to read instead of the per-user one, for CI. |
| `--json` | A JSON list: per id `question`, `id`, `model`, `cached`, and `chance` and `cause`, `chance` and `verdict`, or `score` and `level`. |

### Settings: `audit.toml`

The file is `$XDG_CONFIG_HOME/kmctl/audit.toml` (`~/.config/kmctl/audit.toml`
when the variable is unset), or the file `--config` or `KMCTL_AUDIT_CONFIG`
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

### Tracing

Set `LANGSMITH_TRACING=true` to trace each call as a LangSmith `llm` span;
LangSmith reads `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT` itself. It is off
otherwise.

### Dependencies

Code steps need ast-grep-py, query steps jmespath, and `kmaudit judge`
tenacity; kmaudit installs all three. Tracing needs langsmith, in the
`tracing` extra:

```
uv tool install --force 'kmaudit[tracing] @ git+https://github.com/JasperHG90/kmctl#subdirectory=packages/kmaudit'
```

When one of them is missing, those steps report `skipped`, `submit` refuses
them, and `kmaudit judge` refuses naming the install command.

### The store

Each namespace keeps its state in its own SQLite file,
`.kmaudit/<namespace>.sqlite` at the repository root (git's top level). kmaudit
creates `.kmaudit/` with a `.gitignore` holding `*`, so git ignores the
folder and your own `.gitignore` is never edited. Each checkout has its own
stores, and the verbs write nothing else: never the audited folder.

A repository audited before kmaudit had namespaces kept one store at
`.kmctl/audit.sqlite`. The first verb on `.okf` copies it into the `.okf`
namespace, with SQLite's backup API, and leaves the old file as it was.

## Namespaces

`kmaudit namespaces [PATH] [--json]`

List the repository's namespaces: each audited folder with its store's
counts of sections, claims and checks. It writes nothing.

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

The verbs that write (`claims submit`, `checks try`, `checks submit`,
`judge`) name their namespace with `--path`, as `todo` prints it.

| Option | Meaning |
|---|---|
| `PATH` | A path in the repository (default: the current directory). |
| `--json` | One JSON object: `namespaces`, each with `namespace`, `folder`, `sections`, `claims` and `checks`. |
