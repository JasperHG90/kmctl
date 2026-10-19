---
description: "Every kmctl command, subcommand and option."
---

# Commands

## Summary

Every `kmctl` command, subcommand and option, taken from
`kmctl --help` and each command's `--help`. Every command takes `--help` (or
`-h`). Commands that read or write a repository take `--path` (default: the
current directory, which must be an existing folder). `--json` prints one
machine-readable result on stdout, for scripts; without it, output is meant
for people. Warnings and refusals go to stderr.

| Command | What it does |
|---|---|
| `kmctl init` | Create `docs/`, a starter `.okf/` bundle and a `CLAUDE.md` block; re-run to refresh the block. |
| `kmctl update` | Same as `kmctl init`. Run it after upgrading kmctl to refresh the `CLAUDE.md` block. |
| `kmctl check` | Check indexes agree with their folders, docs front matter has its shape, prototypes have a `README.md`, and links resolve; `--fix` writes the generated docs folder indexes first. |
| `kmctl handoffs` | List the live handoffs in `.okf/handoffs/`, newest first. |
| `kmctl briefing` | Print the session briefing: where knowledge lives, the skills, what is due, and the rule for reading knowledge. |
| `kmctl schema` | Print the JSON Schema of one document kind, or list the kinds there are. |
| `kmctl review` | Find knowledge that is due for review. Verbs: `due`. |
| `kmctl review due` | List the concepts in `.okf/` and the pages in `docs/` that are due for review, with the reason for each. |
| `kmctl verify` | Record that a person checked a concept or docs page, so `kmctl review due` drops it. |
| `kmctl summary` | Keep `.okf/summary.md`, the bundle's first page, in step with its concepts. Verbs: `ack`. |
| `kmctl summary ack` | Record that `.okf/summary.md` still holds after the concepts that changed since it. |
| `kmctl new` | Create a `.okf/` concept or a `docs/` page with its structure. Needs a repository set up by `kmctl init`. |
| `kmctl new decision` | Create a decision in `.okf/` with its front matter, skeleton, index entry and log line. |
| `kmctl new practice` | Create a practice in `.okf/`, the same way. |
| `kmctl new proposal` | Create a proposal in `.okf/`, the same way. |
| `kmctl new prototype` | Create a prototype in `.okf/`, the same way. |
| `kmctl new handoff` | Create a handoff in `.okf/`, the same way. |
| `kmctl new doc` | Create a `docs/` page in its Diataxis folder with a skeleton and its index entry. |
| `kmctl decision` | Change decision records in `.okf/decisions/`. Verbs: `supersede`. |
| `kmctl decision supersede` | Mark one decision superseded by another and link the two records both ways. |
| `kmctl plugin` | Finish installing kmctl's APM package for an agent harness. APM (Agent Package Manager) installs the package from `apm.yml`: the skills, audit agent, knowledge rules, session hooks and okf's MCP server. Verb: `patch`. `kmctl doctor` checks the install. |
| `kmctl plugin patch` | Add what APM cannot install yet for kmctl's package; run it after `apm install`. |
| `kmctl doctor` | Check kmctl's tools, its installed package per harness and the `kmctl init` files. |

## Details

### `kmctl`

| Option | Meaning |
|---|---|
| `--version`, `-V` | Print the kmctl version and exit. |
| `--install-completion` | Install completion for the current shell. |
| `--show-completion` | Show completion for the current shell, to copy it or customize the installation. |
| `--help`, `-h` | Show the help and exit. |

With no command, `kmctl` prints its help.

### `kmctl init`

Set a repository up. It writes:

- `docs/README.md`, the docs root index, which you write and which links
  each docs folder;
- each Diataxis folder's `README.md` index under `docs/`, generated from its
  pages, when the folder exists and the index is missing or generated and out
  of date (see `kmctl check`);
- a starter `.okf/` bundle: `index.md`, `log.md`, `manifesto.md` and
  `summary.md`, the bundle's first page, which distils what the knowledge
  says as a whole in its four sections (The project, How it works, What it
  has settled, Where it stands), with a line under each saying what goes
  there; the indexes list the concepts;
- a kmctl block between `<!-- kmctl:start -->` and `<!-- kmctl:end -->` in
  each `CLAUDE.md` and `AGENTS.md` that exists. The block lists where each
  kind of knowledge lives, says to start at `.okf/summary.md`, names the
  rules folder of each harness kmctl's package is installed for
  (`.claude/rules/` for Claude Code, `.agents/rules/` for Antigravity,
  `.opencode/rules/` for OpenCode, as `kmctl doctor` finds them), or all
  three with their tools when it finds none, and gives the
  agent six duties: record each
  choice with `kmctl new decision`, name the code a concept describes with
  `--source` and give anything time-bound a `--stale-after`, keep
  `.okf/architecture/` matching the code, give `docs/` pages their front
  matter and never edit a folder index by hand (run `kmctl check --fix`),
  update `.okf/summary.md` after adding or changing a concept (or run
  `kmctl summary ack` when it still holds), and run `kmctl check` before
  finishing. A `CLAUDE.md` that is a
  symlink to `AGENTS.md` gets one block, and stays a symlink;
- a new `CLAUDE.md` when there is none. Beside an `AGENTS.md` it holds only
  `@AGENTS.md`, because Claude Code reads `AGENTS.md` only when there is no
  `CLAUDE.md` or when `CLAUDE.md` imports it; the import loads `AGENTS.md`
  and its block once. With neither file, `CLAUDE.md` holds the block. A
  `CLAUDE.md` with an `@AGENTS.md` line, beside an `AGENTS.md`, gets no
  block;
- the decision "Keep project knowledge in an OKF bundle", with its index
  entry and log line, when no record in `.okf/decisions/` has that title. In
  a fresh bundle it is `0001`.

It writes no rules: the four knowledge rules (`okf-bundle`, `docs-layout`,
`diagrams-stay-current` and `manifesto-invariants`) come with kmctl's skills
in kmctl's APM package, which `apm install` installs, and init never reads
or writes `.claude/rules/`.

A file that already exists is kept, so it is safe to run again, with four
exceptions. The kmctl block is added to an existing `CLAUDE.md` or
`AGENTS.md`, or replaced when it is already there, and no other text in the
file changes. Writing the first decision into a kept bundle adds its entry to
the kept indexes and a line to the kept `log.md`. Writing `summary.md` or
`manifesto.md` into a kept bundle (a bundle from an older kmctl, say) adds
the page's one entry to the kept `.okf/index.md`, where a fresh index has it
(the summary before the first entry, the manifesto after the summary), and
a line to the kept `log.md`, unless they are there already; nothing else in
either file changes, so `kmctl check` passes after it. A docs folder index kmctl
generated is rewritten when it is out of date; a hand-written one is kept. A
second run changes nothing.

A file counts as missing only when there is no directory entry for it, so a
dangling symlink counts as there. A `CLAUDE.md` or `AGENTS.md` symlink that is
dangling or points outside the repository is left alone, with a warning
naming the link and its target; init does not create or change its target.
When `AGENTS.md` is such a link and there is no `CLAUDE.md`, init writes no
`CLAUDE.md`: one with the block would hide the linked `AGENTS.md` from Claude
Code, and one importing it would load no block. Fix the link and run init
again. A symlink inside the repository is written through once.

Output lists each file as `created`, `updated` (its kmctl block, the first
decision's index entry and log line, a new page's root index entry and log
line, or a generated docs folder index) or `kept`, then a `linked PAGE from
.okf/index.md, with a line in .okf/log.md` line for each new page it added
to a kept index, and ends with the next steps:
install kmctl's package with APM for the skills and the knowledge rules
(the README's install section: an `apm.yml` entry, `apm install`,
`kmctl plugin patch`), fill the purpose and invariants in the manifesto (its values are the
operator's), add an architecture page once there is code, and record each
choice with `kmctl new decision`.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to set up: an existing folder. | `.` |
| `--json` | Print one JSON object with `created`, `skipped`, `updated`, `warnings` and `linked` (the new pages it added to a kept `.okf/index.md`) lists. | off |

### `kmctl update`

The same command as `kmctl init`, with the same options and output. Run it
after upgrading kmctl: it replaces the kmctl block with this release's block,
writes each docs folder index that is missing, writes `.okf/summary.md` when
there is none and adds its entry to `.okf/index.md` and a line to
`.okf/log.md`, and keeps every other file.
It leaves your `docs/README.md` alone, so after upgrading from a kmctl that
listed every page there, `kmctl check` warns until you link each folder's
index from it. Bumping kmctl (or the CI action's ref) without running
`kmctl update` or `kmctl check --fix` fails `kmctl check` once, on each
missing folder index, with that fix in the message. To refresh the skills and the knowledge rules,
set kmctl's `ref` in `apm.yml` to the new version, run `apm install` and
then `kmctl plugin patch`.

### `kmctl check`

Check that indexes agree with their folders, that `docs/` page front matter
has its shape, that each prototype has a `README.md`, and that links resolve.
A missing `docs/` or `.okf/` is reported as skipped, not failed.

In `docs/`:

- Each Diataxis folder (`tutorials/`, `how-to/`, `reference/`,
  `explanation/`) has a `README.md` index that kmctl generates: a marker
  line, a heading, then one entry per page with the page's `#` title and its
  `description`. A missing index, or a generated one that does not match the
  folder's pages, is an error; `kmctl check --fix` writes it. Never edit one
  by hand.
- A folder `README.md` without kmctl's marker is hand-written: kmctl leaves
  it alone, warns, and checks it lists every page in its folder.
- `docs/README.md` is yours to write. It must list each page outside the four
  folders (an error otherwise), and should link each folder's index (a
  warning otherwise).
- A page may carry front matter with the OKF fields `description`,
  `stale_after`, `verified` and `sources`. Each one present must have its OKF
  shape (check `front-matter`): `description` a string, `stale_after` a date
  or UTC timestamp, `verified` a list of `{by, at}`, `sources` a list of paths
  or `{resource}` mappings. A page with none passes.

In `.okf/`, the body of `summary.md` (outside its front matter, counted as
words between spaces) holds at most 500 words; over that is an error naming
the count and the limit (check `summary`). A summary behind the concepts
that changed after it is a `warning`, never a failure (see
`kmctl summary ack`).

Each finding has a `level`: `error` fails the check, `warning` is printed but
does not fail it, and `skipped` names a part with nothing to check.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to check: an existing folder. | `.` |
| `--fix` | First write each generated docs folder index that is missing or out of date, printing `fixed PATH` for each (on stderr with `--json`), then check. It changes no other file: not `docs/README.md`, not a hand-written folder index, not `.okf/`. | off |
| `--json` | Print a JSON list of findings (`check`, `file`, `line`, `message`, `level`). | off |

Exit codes: 0 when nothing fails (warnings included), 1 when a check fails.

As a pre-commit hook: kmctl's repository offers the hook `kmctl-check`,
which runs `kmctl check` once per commit, without file names. Add
`args: [--fix]` to rewrite the folder indexes as you commit; pre-commit then
stops the commit so you can stage them.

### `kmctl handoffs`

List the live handoffs in `.okf/handoffs/`, newest first. Handoffs past their
`stale_after` date are left out; `kmctl review due` lists them.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to read: an existing folder. | `.` |
| `--json` | Print a JSON list of handoffs (`id`, `path`, `title`, `description`, `date`), as `/continue` reads it. | off |

### `kmctl briefing`

Print the session briefing: where knowledge lives, what is due, and the
package's skills, in under 500 tokens. Its first line after the title says
whether the repository is set up: `kmctl init` has run, `.okf/manifesto.md`
has text beyond its headings, and `.okf/architecture/` has a page other than
its index. When one is missing, it tells the agent to ask the user to fill
them in together before any other work; `--json` gives the three as `setup`.
The state line counts what is due and the live handoffs, and ends with
`summary current` or `summary behind: N concepts changed` when there is a
`.okf/summary.md` and git history to tell (`--json`: `state.summary_behind`,
null otherwise). The rules for writing knowledge are not
in it: APM puts them in each harness's rules folder with kmctl's package, so
the briefing says only that the rules your tool loads cover them, and adds
the one rule they lack. The SessionStart hook in kmctl's APM package,
which APM writes, prints this: Claude Code's runs `kmctl briefing`,
Antigravity's runs `kmctl briefing --format antigravity`. It reads and never
writes.

With `--format antigravity` it prints
`{"injectSteps": [{"systemMessage": {"systemMessage": "TEXT"}}]}`, where
`TEXT` is the text briefing, the shape an Antigravity SessionStart hook
prints to put text into the session. It takes the repository from
`workspacePaths[0]` of the JSON object on stdin, which Antigravity sends to
every hook, so it does not depend on the folder the hook runs in. When stdin
is a terminal, empty, not that JSON or names no folder, it uses `--path`:

```
echo '{"workspacePaths": ["/home/me/repo"]}' | kmctl briefing --format antigravity
```

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to brief on: an existing folder. | `.` |
| `--json` | Print one JSON object (`routing`, `setup`, `state`, `rules`, `skills`). Not with `--format antigravity`. | off |
| `--format FORMAT` | `text` (the briefing as text) or `antigravity` (the briefing in the JSON an Antigravity SessionStart hook prints, with the repository read from stdin). | `text` |

Exit code: 2 when `--json` and `--format antigravity` are given together.

### `kmctl schema`

`kmctl schema [KIND]`

Print the JSON Schema (draft 2020-12) of one document kind's front matter, or
list the kinds with where each lives and what it is for. The schema is built
from kmctl's own table of kinds (`src/kmctl/kinds.py`) when you run it, so it
is what kmctl writes: the fields by their OKF names, which are required, the
legal values and what each one means. Read it before you write a concept or a
page by hand. Nothing checks a file against it yet.

| Argument or option | Meaning | Default |
|---|---|---|
| `KIND` | The kind whose schema to print: `decision`, `practice`, `proposal`, `prototype`, `handoff` (what `kmctl new` writes); `manifesto`, `summary`, `index`, `section-index`, `log` (the bundle files `kmctl init` writes); `architecture` (a diagram page, which no verb writes); `tutorial`, `how-to`, `reference`, `explanation` (`docs/` pages); `docs-index` (`docs/README.md`, the root index you write by hand), `docs-folder-index` (a Diataxis folder's `README.md`, which `kmctl check --fix` generates). | none: list the kinds |
| `--json` | With no kind, print the list as one JSON object of kind to where it lives and what it is for. A kind's schema is JSON either way. | off |

The body is in `x-kmctl-sections`: a list of the `##` sections in order,
`{"pattern": REGEX}` when every heading has one form (the log's dated
sections), `{"last": "Depicts"}` for an architecture page's free sections
that end with Depicts, or `null` for no fixed sections. When sections may
follow the fixed list, `x-kmctl-then` gives their `{"pattern": REGEX}`: a
decision may end with any number of `Correction, YYYY-MM-DD` sections, which
`kmctl decision supersede` appends. A kind with no front
matter (the indexes below the root, the `docs/` indexes, the log) allows no
properties, the root index allows only `okf_version`, and a `docs/` page
allows only `description`, `stale_after`, `verified` and `sources` (ADR 0022). Dates such as
`generated.at` are a date or a UTC timestamp.

Exit code: 1 for an unknown kind, with the list of kinds on stderr.

### `kmctl review due`

List the concepts in `.okf/` and the pages in `docs/` that are due for
review, with the reason for each. A source that resolves to no tracked file
or folder is listed as a notice, not a reason.

A `docs/` page is due when its `stale_after` has passed, or when a commit
changed one of its `sources` after its last `verified` date or, with none,
after the page's own last commit. A page with no `verified` entry is not due
for that alone. A docs page's id is its path without `.md`, such as
`docs/how-to/install`; a source resolves from the page's folder, then the
repository root. The `README.md` indexes are left out.

The summary, `.okf/summary.md`, is never listed as `unverified` or for
`stale_after`. It is due, with the reason `concepts changed: ID, ...`, when
a concept (the manifesto, a decision, practice, proposal, prototype
`README.md` or architecture page) changed in a commit after the summary's
last commit, or is changed or new in the working tree while the summary is
not. Indexes, `log.md`, handoffs and the summary itself never count. Editing
the summary, or `kmctl summary ack`, clears it. Without full git history (no
repository, or a shallow clone) it is not checked.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to read: an existing folder. | `.` |
| `--json` | Print one JSON object (`due`, `notices`, `expired_handoffs`, `history_skipped`). | off |

When anything is due, the text output ends with a `Next:` line naming
`kmctl verify`, which clears an id once a person has checked it, and, when
the summary is due, updating it or `kmctl summary ack`.

Exit code: always 0. Being due is a report, not a failure.

### `kmctl verify`

`kmctl verify ID --by human:<id>`

Record that a person checked a concept or docs page, so `kmctl review due`
drops it. It appends `{by, at}` to the file's `verified` list, with `at` the
current UTC time (`2026-10-17T21:30:00Z`), and changes no other line. A
`verified` field written as one mapping or a flow list is extended in its
place. A concept also gets a line in `.okf/log.md`. The id then stays off
`kmctl review due` until its `stale_after` passes or one of its `sources` is
committed again.

Only a person verifies (ADR 0023). An agent runs it only when the person named
in `--by` has read the content and asked for it, never on an audit verdict
alone (ADR 0005). Fix a drifted concept's body first.

A `verified` entry does not clear `stale_after passed`: when the file's
`stale_after` has passed, give `--stale-after`, or the verb refuses.

| Argument or option | Meaning | Default |
|---|---|---|
| `ID` | The id as `kmctl review due` prints it: a concept under `.okf/` without `.md` (`decisions/0001-x`, `manifesto`) or a docs page (`docs/how-to/install`). Required. | |
| `--by human:<id>` | The person who read it and confirms it: `human:` and a name or email address. Required. | |
| `--stale-after WHEN` | A new `stale_after`, in the forms `kmctl new --stale-after` takes. Required when the file's `stale_after` has passed. | none |
| `--path DIR` | The repository to write in: an existing folder. | `.` |
| `--json` | Print one JSON object (`id`, `path`, `by`, `at`, `stale_after`). | off |

Output: `verified ID by BY at AT (PATH)`, then `stale_after is now WHEN`
when `--stale-after` was given, then `Next: kmctl review due`.

A comment at the end of the `verified:` line, such as `verified: []  # none`,
stays on that line.

Exit code: 1 when kmctl refuses, with the reason on stderr: `--by` does not
start with `human:`, the id names no file (or holds `..`), the id is a
handoff (handoffs are never verified), the front matter is unreadable or
missing, `stale_after` has passed and no `--stale-after` is given, the
`--stale-after` value is not in the future, or the `verified` field is in a
form kmctl cannot extend (the refusal says to rewrite it as a block list).

### `kmctl summary ack`

Record that `.okf/summary.md` still holds after the concepts that changed
since it, so `kmctl review due` drops it. Run it when you have read the
changed concepts and the summary needs no edit. It writes

```yaml
checked:
  at: 2026-10-18T20:15:04Z
  against:
    - decisions/0002-use-a-queue
```

into the summary's front matter, with `at` the UTC time to the second
(a second later when the last ack wrote the same time and ids, so the file
always changes) and `against`
the ids `kmctl review due` listed, replacing an older `checked`. It changes
no other line and no other file. That is an edit to the summary, so the
summary leaves the list; commit it with the concepts. It is an agent's word
that the summary holds, not a person's review, which is `kmctl verify`
(ADR 0023, ADR 0027). When the summary is current it writes nothing and
prints `nothing to ack`.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to write in: an existing folder. | `.` |
| `--json` | Print one JSON object (`path`, `at`, `against`); `at` is null when nothing was written. | off |

Output: `checked .okf/summary.md at TIME against ID, ...`, then
`Next: kmctl review due`.

Exit code: 1 when kmctl refuses, with the reason on stderr: there is no
`.okf/summary.md`, its front matter is unreadable or lacks `type: summary`,
or there is no git history to tell what changed (not a repository, or a
shallow clone).

### `kmctl new decision`, `kmctl new practice`, `kmctl new proposal`, `kmctl new prototype`, `kmctl new handoff`

`kmctl new KIND 'Title' --description 'One sentence.'`

Create one concept of that kind in `.okf/` with its front matter, heading
skeleton, section index entry and log line. You write the prose. The first
concept of a kind creates its section and links it from `.okf/index.md`.

| Argument or option | Meaning | Default |
|---|---|---|
| `TITLE` | The title; its kebab-case form names the file. Required. | |
| `--description TEXT` | One sentence for the front matter and the index entry. Required. | |
| `--path DIR` | The repository to write in: an existing folder. | `.` |
| `--json` | Print one JSON object (`id`, `path`, `created_section`, `updated`). | off |
| `--key KEY` | Handoffs only: a session key, for example `$CLAUDE_CODE_SESSION_ID`. A handoff with the same key is updated in place instead of refused (ADR 0009). | none |
| `--stale-after WHEN` | When `kmctl review due` lists the concept as due, written as `stale_after`. A duration from now: `30d` days, `12w` weeks, `6m` calendar months, `1y` calendar years (a month end past the new month's last day moves back to it). Or a date: `2027-01-15`, read as its midnight UTC, or a timestamp such as `2027-01-15T08:00:00Z`. It must be in the future, so `0d` and today's date are refused. | `14d` for a handoff, none for the rest |
| `--source PATH` | Not for handoffs: a file or folder the concept describes, written to `sources` as `- resource: PATH`. Repeat it for more; they are written in the order given. It must exist on disk, found the way `kmctl review due` finds sources: from the concept's folder, then `.okf/`, then the repository root, with a leading `/` meaning `.okf/` and `.md` added when needed. Git is not needed, so a file you have not added yet is fine. Once someone verifies the concept, `kmctl review due` lists it when a commit changes a source. | none |

Exit code: 1 when kmctl refuses, with the reason on stderr.

### `kmctl new doc`

`kmctl new doc TYPE 'Title'`

Create a `docs/` page in its Diataxis folder with front matter and a heading
skeleton, write the folder's generated `README.md` index again, and add a
link to the folder to `docs/README.md` when it has none. The front matter is
`description` (when given), `stale_after` three months ahead and an empty
`sources`; it never writes `verified`. When the folder's `README.md` is
hand-written, kmctl leaves it alone and warns that you must add the entry. It
refuses when `docs/README.md` is missing (run `kmctl init` first) or the page
already exists.

| Argument or option | Meaning | Default |
|---|---|---|
| `TYPE` | The Diataxis type: `tutorial` (a lesson), `how-to` (one task), `reference` (facts) or `explanation` (why). Required. | |
| `TITLE` | The page title; its kebab-case form names the file. Required. | |
| `--description TEXT` | An optional line for the page's `description` front matter and its index entry. | none |
| `--path DIR` | The repository to write in: an existing folder. | `.` |
| `--json` | Print one JSON object (`path`, `created_folder`, `warnings`). | off |

Each type goes in its own folder: `tutorial` in `docs/tutorials/`, `how-to` in
`docs/how-to/`, `reference` in `docs/reference/`, `explanation` in
`docs/explanation/`.

Exit code: 1 when kmctl refuses, with the reason on stderr.

### `kmctl decision supersede`

`kmctl decision supersede OLD --by NEW`

Mark one decision superseded by another and link the two records both ways.
The old record keeps its body: it gets `status: deprecated` and an appended
Correction section. Write the new record first with `kmctl new decision`.

| Argument or option | Meaning | Default |
|---|---|---|
| `OLD` | The number of the decision being replaced, for example `3` or `0003`. Required. | |
| `--by NEW` | The number of the decision that replaces it. Required. | |
| `--path DIR` | The repository to write in: an existing folder. | `.` |
| `--json` | Print one JSON object (`old`, `new`) with both concept ids. | off |

Exit code: 1 when kmctl refuses, with the reason on stderr.

### `kmctl plugin patch`

Add what APM cannot install yet for kmctl's package. APM installs,
upgrades and removes the package itself (`apm install`, `apm update`,
`apm uninstall`; the README's install section gives the steps per
harness). Run `kmctl plugin patch` after every `apm install` or
`apm update`, in the repository, or with `--scope user` after
`apm install -g`. It never runs APM, so it needs neither uv nor APM on PATH.

It runs, in order:

1. Refuses when `apm.yml` (`~/.apm/apm.yml` with `--scope user`) still
   names kmctl's package the way kmctl v0.3.0 and older did: the string
   `JasperHG90/Knowledge-management/apm#…` (or `JasperHG90/kmctl/apm#…`,
   the repository's new name), or any kmctl entry when
   `apm.lock.yaml` shows the old layout (`virtual_path: plugin`). That old
   package's SessionStart hook goes only with `apm uninstall`, so the
   refusal names the `apm uninstall` to run first (with `-g` at user
   scope), the `{"git": "https://github.com/JasperHG90/kmctl.git", "path": "apm", "ref": "vVERSION"}`
   entry to add, where `VERSION` is this kmctl's, and the `apm install` to
   run after it.
2. Refuses when `apm.lock.yaml` (`~/.apm/apm.lock.yaml` with
   `--scope user`) lists no kmctl package, naming the same entry to add to
   `dependencies.apm` and the `apm install` to run.
3. Reads from the lock which harnesses APM installed kmctl's package for:
   `claude` when it lists files under `.claude/`, `opencode` when it lists
   files under `.opencode/`, `antigravity` when it lists files under
   `.agents/` other than `.agents/skills/` (APM writes skills there for
   both Antigravity and OpenCode, so a skill alone marks neither). It
   patches those and no others.
4. For `claude`, removes what an older kmctl wrote itself that APM now
   writes, so there is one copy of each:
   - a SessionStart group in `.claude/settings.json` (at user scope, the
     `settings.json` in `$CLAUDE_CONFIG_DIR`) that runs `kmctl briefing`
     and is not recorded in the `apm-hooks.json` APM keeps beside it. Every
     other hook stays.
   - an `okf-bundle` server in `.mcp.json` whose command or args differ from
     the one kmctl's package declares. At user scope it removes the one in
     the user `.claude.json` with `claude mcp remove okf-bundle --scope user`;
     when the `claude` CLI is not on PATH it leaves it and prints a note
     naming that command. APM skips a server that is already there, so
     after removing it the command prints a note to run `apm install` again
     (`apm install -g` at user scope), which writes the package's
     `okf-bundle`. Every other server stays.
   - the old claude plugin `kmctl@kmctl` installed for this repository (or,
     with `--scope user`, for the user): `claude plugin uninstall`, then
     `claude plugin prune`, which also removes an okf plugin only kmctl
     needed, then `claude plugin marketplace remove kmctl`, each at the
     plugin's scope. When the `claude` CLI is not on PATH it skips this and
     says so.
5. For `antigravity`, at project scope only, replaces the folder
   `.agents/plugins/kmctl/`, which kmctl alone owns, with `plugin.json` and
   the agents, which APM does not install for Antigravity yet:
   `agents/kmctl-auditor.md` and okf's `agents/bundle-weaver.md` and
   `agents/event-analyzer.md`, translated from Claude Code's format (okf's
   are read from `apm_modules/scaccogatto/okf-skills/agents/`, so it
   refuses when `apm_modules/` is missing). It then takes okf's own Stop
   handler, `bash ".agents/hooks/okf-skills/hooks/okf-stop-check.sh"`, out
   of `.agents/hooks.json`. APM writes that path from the repository root,
   but Antigravity runs hooks in `.agents/`, so it would fail at the end of
   every turn; the Stop hook in kmctl's package runs okf's check instead.
   Only that exact command goes; every other hook stays. Antigravity loads
   `.agents/` only once you trust the repository folder.
6. For `opencode`, at project scope only (at user scope it leaves OpenCode
   alone and prints a note saying so):
   - rewrites the three agents APM copies into `.opencode/agents/` in
     Claude Code's format, which OpenCode skips: `kmctl-auditor.md` and
     okf's `bundle-weaver.md` and `event-analyzer.md` (okf's read from
     `apm_modules/scaccogatto/okf-skills/agents/`, so it refuses when
     `apm_modules/` is missing). Each keeps its `description` and body and
     gets `mode: subagent` and a `permission` map: `"*": deny`, then
     `allow` for each of its tools (Read to `read`, Grep to `grep`, Glob to
     `glob`, Write and Edit to `edit`, Bash to `shell`). Every other key
     goes. The auditor may only read, grep and glob.
   - writes kmctl's four rules to `.opencode/rules/`, without their
     `applyTo` front matter, and adds `.opencode/rules/*.md` to the
     `instructions` list of `opencode.json`, creating the file when it is
     missing and keeping every other key, `mcp` included. OpenCode has no
     rules scoped to paths, so it loads every rule in every session.
   - writes `.opencode/plugins/kmctl.js`, a plugin that runs
     `kmctl briefing --path REPO` once per OpenCode start, without waiting
     for it, and adds its output to the system prompt. kmctl supports
     OpenCode 2.x only. Without a working `kmctl` it adds nothing and
     throws nothing.

   `apm install` writes APM's agents back over the rewritten ones, so run
   patch after every `apm install`. It refuses, leaving every file as it
   was, when `opencode.json` is not a JSON object or its `instructions`
   key is not a list.

Running it again changes nothing. Output: a `note:` line for each thing it
removed or wrote, or a step it skipped, then a line naming the package ref
`apm.lock.yaml` records, the harnesses and the scope, then a `Next:` line
ending with `kmctl doctor` (`kmctl doctor --scope user` at user scope). For
a project install for both harnesses it prints:

```
note: wrote .agents/plugins/kmctl/ (the agents, which APM does not install for Antigravity yet); Antigravity loads it once you trust this folder
note: took APM's okf Stop handler out of .agents/hooks.json, where it cannot run; kmctl's package runs okf's check instead
patched kmctl's package v0.3.0 for claude, antigravity (project scope)
Next: start a new Claude Code session, then open this folder in Antigravity, trust it and start a new session, then kmctl doctor
```

For OpenCode alone the first run prints:

```
note: wrote 9 OpenCode files (.opencode/agents/kmctl-auditor.md, .opencode/agents/bundle-weaver.md, .opencode/agents/event-analyzer.md, .opencode/rules/diagrams-stay-current.md, .opencode/rules/docs-layout.md, .opencode/rules/manifesto-invariants.md, .opencode/rules/okf-bundle.md, .opencode/plugins/kmctl.js, opencode.json): the agents in OpenCode's format, the rules, their .opencode/rules/*.md entry in opencode.json and the briefing plugin; apm install puts APM's agents back, so run kmctl plugin patch after every apm install
patched kmctl's package v0.4.1 for opencode (project scope)
Next: start a new OpenCode session, then kmctl doctor
```

With `--undo` it deletes what patch wrote in this repository and nothing
else: `.agents/plugins/kmctl/`, and for OpenCode the agents while they are
still kmctl's translation, the four rules, the `.opencode/rules/*.md` entry
(and `opencode.json` when nothing else is left in it) and
`.opencode/plugins/kmctl.js`. It prints a `note:` line for each, or
`nothing to undo: kmctl wrote nothing here`, then `Next: kmctl doctor`.
`apm uninstall` removes the rest of kmctl's package. For OpenCode, run
`--undo` first: `apm uninstall` stops on an agent patch rewrote.
With `--scope user` it deletes nothing in this repository: it leaves
`.agents/plugins/kmctl/` and the OpenCode files, which are patched at
project scope only, and prints a note naming them and saying to run
`kmctl plugin patch --undo` here without `--scope user`.

| Option | Meaning | Default |
|---|---|---|
| `--scope SCOPE` | `project` (this repository's `apm.yml`, `apm.lock.yaml`, `.claude/`, `.mcp.json`, `.agents/`, `.opencode/` and `opencode.json`) or `user` (`~/.apm/apm.yml` and `~/.apm/apm.lock.yaml`, and Claude Code's folder, `$CLAUDE_CONFIG_DIR` or `~/.claude`, for a package installed with `apm install -g`). Antigravity and OpenCode are patched at project scope only. | `project` |
| `--undo` | Delete what patch wrote, and nothing else: `.agents/plugins/kmctl/`, and for OpenCode the agents it rewrote, `.opencode/rules/`, the `instructions` entry and `.opencode/plugins/kmctl.js`. Run it before `apm uninstall`. | off |
| `--json` | Print one JSON object: `scope`, `harnesses`, `package_ref` (the ref `apm.lock.yaml` records for the kmctl package; `null` with `--undo`) and `notes`. | off |

Exit code: 1 when kmctl refuses, with
`kmctl plugin patch: refused: REASON; FIX` on stderr; for example an old
`apm.yml` entry, a lock with no kmctl package, an `apm.yml` or
`settings.json` or `opencode.json` that does not parse, an `opencode.json`
whose `instructions` is not a list, a missing
`apm_modules/`, or a failed `claude` command (with its cause).

#### What `apm install` writes, and patch leaves to it

`apm install --target HARNESSES` (with `-g` at user scope) writes every
piece of kmctl's package, merging hooks and MCP servers into the files that
already hold yours:

- For `claude`: the skills to `.claude/skills/`, the agent to
  `.claude/agents/`, the rules, with their `paths:`, to `.claude/rules/`,
  one SessionStart hook that runs `kmctl briefing` into
  `.claude/settings.json` (recorded in `.claude/apm-hooks.json`), and
  okf's MCP server as `okf-bundle` into `.mcp.json`. At user scope the
  hook goes into the `settings.json` in `$CLAUDE_CONFIG_DIR` (by default
  `~/.claude/`) and the server into the user `.claude.json`. The hook
  prints how to install kmctl, at the release the package came from
  (`uv tool install git+https://github.com/JasperHG90/kmctl@vX.Y.Z`), and
  exits 0 when kmctl is missing or fails.
  Claude Code asks you to approve a project `.mcp.json` server once.
- For `antigravity`: the skills to `.agents/skills/`; the four rules to
  `.agents/rules/`, each with its globs as one `globs:` string, every
  glob starting with `**/` (Antigravity matches globs against absolute
  paths); and, in `.agents/hooks.json`, one SessionStart hook that runs
  `kmctl briefing --format antigravity` and prints `{}` and exits 0 when
  kmctl is missing or fails, and one Stop hook that runs okf's Stop check
  from the repository root on the first stop of each turn and turns
  okf's `block` into Antigravity's `continue` (it does anything only when
  `.okf/index.md` sets `upkeep: enforced`, and prints `{}` and exits 0
  otherwise); and okf's MCP server as `okf-bundle` in
  `.agents/mcp_config.json`. APM also writes okf's own Stop handler there,
  which patch takes out.
- For `opencode`: the skills to `.agents/skills/`, the same folder as
  Antigravity's; the agents to `.opencode/agents/` unchanged, which patch
  rewrites; and okf's MCP server as `okf-bundle` into the `mcp` key of
  `opencode.json` (`{"type": "local", "enabled": true, "command": ["sh",
  "-c", ...]}`), keeping your other keys. It writes no rules or hooks for
  OpenCode, which patch adds. `apm audit` reports the three rewritten
  agents as drift.

okf's MCP server runs okf's `okf_mcp.py` at the pinned okf-skills commit
with `uv run`, on the nearest `.okf/` folder above where it starts, so it
needs `uv` on PATH. A server of your own that runs `okf_mcp.py` under
another name stays, and `okf-bundle` is added beside it. When `apm.yml`
limits which packages may run hooks and MCP servers (an `executables:`
block, or the older `allowExecutables:`), APM writes them only for packages
it allows: `apm approve --pending` lists kmctl's package, and `apm approve`
allows it.

`apm uninstall NAME` (with `-g` at user scope) removes all of it, where
`NAME` is `HOST/OWNER/REPO/apm` from the `git:` URL of kmctl's entry, for
example `github.com/JasperHG90/kmctl/apm`. For OpenCode, run
`kmctl plugin patch --undo` first, or `apm uninstall` stops on the
rewritten agents (`Retained user-edited file`). At user scope it
leaves `okf-bundle` in the user `.claude.json`; remove it with
`claude mcp remove okf-bundle --scope user`.

### `kmctl doctor`

Check that kmctl's tools, its installed package for each harness and the
`kmctl init` files are in place. It prints one line per check on stdout,
`ok   ID: DETAIL` or `fail ID: WHAT IS WRONG; THE FIX`, where the fix is the
command to run (or, for trust, what to do in Antigravity).

It writes nothing and uses no network unless `--online`. It reads files,
and the one command it runs is
`uv tool run --offline --from apm-cli==0.33.0 apm --version`, which uses
uv's cache only. It never runs `claude`, `agy` or `opencode`: `claude plugin list` goes
online and writes `.claude.json`, so doctor reads `enabledPlugins` from the
settings files instead.

It finds the harnesses installed from what an install leaves: the
`targets:` in an `apm.yml` that names kmctl's package, the paths
`apm.lock.yaml` lists for that package and its sub-packages (`.claude/`,
`.opencode/`, or `.agents/` outside `.agents/skills/`, which serves both
Antigravity and OpenCode), the kmctl hook or an old kmctl plugin in
`.claude/settings.json`, `.agents/plugins/kmctl/` and
`.opencode/plugins/kmctl.js`. Any one is enough, so a deleted piece is
reported by name rather than hiding the harness. A harness that is not
installed gets no checks.

| Check | Harness | Passes when | Fix on failure |
|---|---|---|---|
| `kmctl.version` | all | Always; the detail is this kmctl's version, which the other checks compare against. | none |
| `dep.uv` | all | `uv` is on PATH. | install uv |
| `dep.git` | all | `git` is on PATH. | install git |
| `dep.apm` | all | `uv tool run --offline --from apm-cli==0.33.0 apm --version` exits 0. | `uvx --from apm-cli==0.33.0 apm --version`, which downloads it once |
| `dep.claude` | claude | `claude` is on PATH. | install Claude Code |
| `dep.agy` | antigravity | `agy` is on PATH. | install the Antigravity CLI |
| `dep.opencode` | opencode | `opencode` is on PATH. | install OpenCode |
| `init.okf` | all, project scope | `.okf/index.md` exists. | `kmctl init` |
| `init.docs` | all, project scope | `docs/README.md` exists. | `kmctl init` |
| `kmctl.harness` | all | A harness is installed; the detail names them. | `apm install --target claude (kmctl's package must be in apm.yml), then kmctl plugin patch` |
| `claude.scope` | claude | Passes, at project scope, when Claude Code is installed at user scope but not here; it says to run `kmctl doctor --scope user`. | none |
| `claude.lock`, `antigravity.lock`, `opencode.lock` | each | `apm.lock.yaml` names kmctl's package at `v<this version>`. | `apm install --target H (kmctl's package must be in apm.yml), then kmctl plugin patch` when the lock or the package is missing; `set kmctl's ref in apm.yml to vVERSION, run apm install --target H, then kmctl plugin patch` for another version |
| `claude.files`, `antigravity.files`, `opencode.files` | each | Every path the lock lists for kmctl's package for the harness (under `.claude/`; under `.agents/`; or under `.opencode/` and `.agents/skills/`) exists, and each file matches the sha256 the lock records. This covers the skills, the rules and, for `claude`, the agent. For `opencode` it skips the agents patch rewrites, which `opencode.agents` checks. | `apm install --target H (kmctl's package must be in apm.yml), then kmctl plugin patch` |
| `claude.okf-skills`, `antigravity.okf-skills`, `opencode.okf-skills` | each | The same for okf's skills (and, for `opencode`, without its rewritten agents). | `apm install --target H (kmctl's package must be in apm.yml), then kmctl plugin patch` |
| `claude.hook` | claude | `.claude/settings.json` (at user scope, the one in `$CLAUDE_CONFIG_DIR`) holds exactly the SessionStart hook kmctl's package ships, which APM writes. | when missing, `apm install --target claude (kmctl's package must be in apm.yml), then kmctl plugin patch`; when changed, `set kmctl's ref in apm.yml to vVERSION, run apm install --target claude, then kmctl plugin patch` |
| `claude.okf-mcp` | claude | `.mcp.json` (at user scope, `.claude.json` in `$CLAUDE_CONFIG_DIR`, by default `~/.claude.json`) declares `okf-bundle` with the command and args kmctl's package declares (keys APM adds, such as `type`, are not compared), or another server that runs `okf_mcp.py`. | the same as `claude.hook` |
| `claude.old-plugin` | claude | No settings file (`.claude/settings.json` or `.claude/settings.local.json`; at user scope, `settings.json` in `$CLAUDE_CONFIG_DIR`) enables `kmctl@kmctl` or `okf@scaccogatto`. | `kmctl plugin patch` when `kmctl@kmctl` is enabled (it removes okf too when okf came as its dependency); otherwise `claude plugin uninstall okf@scaccogatto --scope SCOPE`, the scope of the file that enables it |
| `antigravity.plugin` | antigravity | Every file under `.agents/plugins/kmctl/` is what this kmctl writes, `plugin.json` and the translated agents, with none missing or extra. Fails with `apm_modules/ is missing` when okf's agents cannot be read to compare. | `kmctl plugin patch`; for a missing `apm_modules/`, `apm install --target antigravity (kmctl's package must be in apm.yml), then kmctl plugin patch` |
| `antigravity.hook` | antigravity | `.agents/hooks.json` holds the SessionStart hook (`kmctl briefing --format antigravity`) and the okf Stop check that kmctl's package ships, which APM writes. | `apm install --target antigravity (kmctl's package must be in apm.yml), then kmctl plugin patch` |
| `antigravity.apm-hooks` | antigravity | `.agents/hooks.json` does not run `okf-stop-check.sh`. APM writes okf's Stop handler there with a path agy cannot find, so it fails at the end of every turn; every `apm install` puts it back. It also fails when the file is not a JSON object, which agy cannot load. | `kmctl plugin patch`; for a file that is not a JSON object, repair it by hand first |
| `antigravity.okf-mcp` | antigravity | `.agents/mcp_config.json` declares okf's MCP server `okf-bundle` with the command and args kmctl's package declares, which APM writes. | `apm install --target antigravity (kmctl's package must be in apm.yml), then kmctl plugin patch` |
| `antigravity.trust` | antigravity | Checked only when `agy` is on PATH: the repository is in `trustedWorkspaces` of `~/.gemini/antigravity-cli/settings.json`. Antigravity loads `.agents/` only from a trusted folder. | run `agy` in the folder and choose "Yes, I trust this folder" |
| `antigravity.okf-mcp-url` | antigravity | With `--online` only: okf's MCP script URL, which the MCP server runs with `uv run`, answers HTTP 200. | check the network, then run it again |
| `opencode.agents` | opencode | Each agent in `.opencode/agents/` is kmctl's translation into OpenCode's format. It fails after a bare `apm install`, which puts APM's Claude-format copies back; fails with `apm_modules/ is missing` when okf's agents cannot be read. | `kmctl plugin patch`; for a missing `apm_modules/`, `apm install --target opencode (kmctl's package must be in apm.yml), then kmctl plugin patch` |
| `opencode.rules` | opencode | `.opencode/rules/` holds kmctl's four rules as this kmctl writes them, and the `instructions` list of `opencode.json` holds `.opencode/rules/*.md`. | `kmctl plugin patch` |
| `opencode.okf-mcp` | opencode | `opencode.json` declares okf's MCP server `okf-bundle` as a local server running the command kmctl's package declares, which APM writes. | `apm install --target opencode (kmctl's package must be in apm.yml), then kmctl plugin patch` |
| `opencode.hook` | opencode | `.opencode/plugins/kmctl.js` is the briefing plugin this kmctl writes. | `kmctl plugin patch` |

`VERSION` is this kmctl's version. With `--scope user`, a fix runs
`apm install -g` and `kmctl plugin patch --scope user`, and the `init.`,
`antigravity.` and `opencode.` checks are left out: kmctl patches
Antigravity and OpenCode per repository only, and the init files belong to
a repository.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to check: an existing folder. | `.` |
| `--scope SCOPE` | `project` (the install in this repository) or `user` (the install `apm install -g` made: `~/.apm/` and `$CLAUDE_CONFIG_DIR`, by default `~/.claude`). | `project` |
| `--online` | Also check that okf's MCP script URL can be fetched. The only check that uses the network. | off |
| `--json` | Print one JSON object, `{"ok": bool, "checks": [{"id", "harness", "ok", "detail", "fix"}]}`. `harness` is `null` for a check that serves all harnesses; `fix` is `null` for a passed check. The ids are the ones in the table. | off |

Exit code: 0 when every check is ok, 1 when any fails, 2 for a usage
error such as a `--path` that is not a folder.

### Environment

| Variable | Used by | Meaning |
|---|---|---|
| `CLAUDE_CONFIG_DIR` | `kmctl plugin patch --scope user`, `kmctl doctor --scope user` | Claude Code's user folder, where the hook's `settings.json` and APM's user-scope skills, agent and rules go; by default `~/.claude`. |
