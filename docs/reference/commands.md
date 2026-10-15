# Commands

## Summary

Every `kmctl` command, subcommand and option in kmctl 0.1.0, taken from
`kmctl --help` and each command's `--help`. Every command takes `--help` (or
`-h`). Commands that read or write a repository take `--path` (default: the
current directory, which must be an existing folder). `--json` prints one
machine-readable result on stdout, for scripts; without it, output is meant
for people. Warnings and refusals go to stderr.

| Command | What it does |
|---|---|
| `kmctl init` | Create `docs/README.md` and a starter `.okf/` bundle, keeping any file that exists. |
| `kmctl check` | Check indexes agree with their folders, prototypes have a `README.md`, and links resolve. |
| `kmctl handoffs` | List the live handoffs in `.okf/handoffs/`, newest first. |
| `kmctl briefing` | Print the session briefing: where knowledge lives, what is due, and the rules. |
| `kmctl review` | Find knowledge that is due for review. Verbs: `due`. |
| `kmctl review due` | List concepts in `.okf/` due for review, with the reason for each. |
| `kmctl new` | Create a `.okf/` concept or a `docs/` page with its structure. Needs a repository set up by `kmctl init`. |
| `kmctl new decision` | Create a decision in `.okf/` with its front matter, skeleton, index entry and log line. |
| `kmctl new practice` | Create a practice in `.okf/`, the same way. |
| `kmctl new proposal` | Create a proposal in `.okf/`, the same way. |
| `kmctl new prototype` | Create a prototype in `.okf/`, the same way. |
| `kmctl new handoff` | Create a handoff in `.okf/`, the same way. |
| `kmctl new doc` | Create a `docs/` page in its Diataxis folder with a skeleton and its index entry. |
| `kmctl decision` | Change decision records in `.okf/decisions/`. Verbs: `supersede`. |
| `kmctl decision supersede` | Mark one decision superseded by another and link the two records both ways. |
| `kmctl plugin` | Install the Claude Code plugin that ships with this kmctl. Verbs: `install`, `update`, `status`. Needs the `claude` CLI on PATH. |
| `kmctl plugin install` | Install the kmctl plugin and its okf dependency through the `claude` CLI. |
| `kmctl plugin update` | Reinstall the plugin from this kmctl release, replacing an older one. |
| `kmctl plugin status` | Report the installed plugin's version against this kmctl, and what to fix. |

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

Create `docs/README.md` and a starter `.okf/` bundle (`index.md`, `log.md`,
`manifesto.md`). A file that already exists is never changed, so it is safe to
run again.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to set up: an existing folder. | `.` |
| `--json` | Print one JSON object with `created`, `skipped` and `warnings` lists. | off |

### `kmctl check`

Check that indexes agree with their folders, that each prototype has a
`README.md`, and that links resolve. A missing `docs/` or `.okf/` is reported
as skipped, not failed.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to check: an existing folder. | `.` |
| `--json` | Print a JSON list of findings (`check`, `file`, `line`, `message`, `level`). | off |

Exit codes: 0 when nothing fails, 1 when a check fails.

### `kmctl handoffs`

List the live handoffs in `.okf/handoffs/`, newest first. Handoffs past their
`stale_after` date are left out; `kmctl review due` lists them.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to read: an existing folder. | `.` |
| `--json` | Print a JSON list of handoffs (`id`, `path`, `title`, `description`, `date`), as `/continue` reads it. | off |

### `kmctl briefing`

Print the session briefing: where knowledge lives, what is due, and the rules
for writing knowledge. The plugin's SessionStart hook prints this. It reads and
never writes.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to brief on: an existing folder. | `.` |
| `--json` | Print one JSON object (`routing`, `state`, `rules`, `skills`). | off |

### `kmctl review due`

List the concepts in `.okf/` that are due for review, with the reason for
each. A source that resolves to no tracked file or folder is listed as a
notice, not a reason.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to read: an existing folder. | `.` |
| `--json` | Print one JSON object (`due`, `notices`, `expired_handoffs`, `history_skipped`). | off |

Exit code: always 0. Being due is a report, not a failure.

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
| `--json` | Print one JSON object (`id`, `path`, `created_section`). | off |
| `--key KEY` | Handoffs only: a session key, for example `$CLAUDE_CODE_SESSION_ID`. A handoff with the same key is updated in place instead of refused (ADR 0009). | none |

Exit code: 1 when kmctl refuses, with the reason on stderr.

### `kmctl new doc`

`kmctl new doc TYPE 'Title'`

Create a `docs/` page in its Diataxis folder with a heading skeleton, and add
its entry to `docs/README.md`. It refuses when `docs/README.md` is missing
(run `kmctl init` first) or the page already exists.

| Argument or option | Meaning | Default |
|---|---|---|
| `TYPE` | The Diataxis type: `tutorial` (a lesson), `how-to` (one task), `reference` (facts) or `explanation` (why). Required. | |
| `TITLE` | The page title; its kebab-case form names the file. Required. | |
| `--description TEXT` | An optional line for the index entry. | none |
| `--path DIR` | The repository to write in: an existing folder. | `.` |
| `--json` | Print one JSON object (`path`, `created_folder`). | off |

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

### `kmctl plugin install`

Install the kmctl plugin and its `okf` dependency through the `claude` CLI.
It adds the scaccogatto marketplace for the `okf` dependency when it is
missing. Running it again at the same version changes nothing.

| Option | Meaning | Default |
|---|---|---|
| `--scope SCOPE` | `project` (this repository) or `user` (every repository). | `project` |
| `--json` | Print the resulting status as one JSON object. | off |

Exit code: 1 when kmctl refuses, with the reason on stderr; for example when
an older plugin is installed, which `kmctl plugin update` replaces.

### `kmctl plugin update`

Reinstall the plugin from this kmctl release, replacing an older one. Run it
after upgrading kmctl: it restages the plugin and reinstalls it.

| Option | Meaning | Default |
|---|---|---|
| `--scope SCOPE` | `project` (this repository) or `user` (every repository). | `project` |
| `--json` | Print the resulting status as one JSON object. | off |

### `kmctl plugin status`

Report the installed plugin's version against this kmctl, and what to fix.
Each problem names the command that fixes it.

| Option | Meaning | Default |
|---|---|---|
| `--json` | Print one JSON object. | off |

Exit code: 0 whether or not there are problems.

### Environment

| Variable | Used by | Meaning |
|---|---|---|
| `XDG_DATA_HOME` | `kmctl plugin` | Where kmctl keeps the plugin it installs from: `$XDG_DATA_HOME/kmctl`, by default `~/.local/share/kmctl`. |
