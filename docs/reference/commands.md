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
| `kmctl init` | Create `docs/`, a starter `.okf/` bundle and a `CLAUDE.md` block; re-run to refresh the block. |
| `kmctl update` | Same as `kmctl init`. Run it after upgrading kmctl to refresh the `CLAUDE.md` block. |
| `kmctl check` | Check indexes agree with their folders, prototypes have a `README.md`, and links resolve. |
| `kmctl handoffs` | List the live handoffs in `.okf/handoffs/`, newest first. |
| `kmctl briefing` | Print the session briefing: where knowledge lives, what is due, and the skills. |
| `kmctl schema` | Print the JSON Schema of one document kind, or list the kinds there are. |
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
| `kmctl plugin` | Install kmctl's skills, audit agent, knowledge rules and session hook for an agent harness, through APM (Agent Package Manager). Verbs: `install`, `update`, `status`. Needs `uv` on PATH: kmctl runs APM with `uvx`. |
| `kmctl plugin install` | Install kmctl's APM package, its session hook and okf's MCP server for a harness. |
| `kmctl plugin update` | Reinstall kmctl's APM package at this kmctl's version; run it after upgrading kmctl. |
| `kmctl plugin status` | Report the installed kmctl package's version and the session hook, and what to fix. |

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

- `docs/README.md`, the docs index;
- a starter `.okf/` bundle: `index.md`, `log.md` and `manifesto.md`;
- a kmctl block between `<!-- kmctl:start -->` and `<!-- kmctl:end -->` in
  each `CLAUDE.md` and `AGENTS.md` that exists. The block lists where each
  kind of knowledge lives and gives the agent four duties: record each
  choice with `kmctl new decision`, name the code a concept describes with
  `--source` and give anything time-bound a `--stale-after`, keep
  `.okf/architecture/` matching the code, and run `kmctl check` before
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
from `kmctl plugin install`, and init never reads or writes `.claude/rules/`.

A file that already exists is kept, so it is safe to run again, with two
exceptions. The kmctl block is added to an existing `CLAUDE.md` or
`AGENTS.md`, or replaced when it is already there, and no other text in the
file changes. Writing the first decision into a kept bundle adds its entry to
the kept indexes and a line to the kept `log.md`. A second run changes
nothing.

A file counts as missing only when there is no directory entry for it, so a
dangling symlink counts as there. A `CLAUDE.md` or `AGENTS.md` symlink that is
dangling or points outside the repository is left alone, with a warning
naming the link and its target; init does not create or change its target.
When `AGENTS.md` is such a link and there is no `CLAUDE.md`, init writes no
`CLAUDE.md`: one with the block would hide the linked `AGENTS.md` from Claude
Code, and one importing it would load no block. Fix the link and run init
again. A symlink inside the repository is written through once.

Output lists each file as `created`, `updated` (its kmctl block, or the first
decision's index entry and log line) or `kept`, and ends with the next steps:
`kmctl plugin install --harness claude` for the skills and the knowledge
rules, fill the purpose and invariants in the manifesto (its values are the
operator's), add an architecture page once there is code, and record each
choice with `kmctl new decision`.

| Option | Meaning | Default |
|---|---|---|
| `--path DIR` | The repository to set up: an existing folder. | `.` |
| `--json` | Print one JSON object with `created`, `skipped`, `updated` and `warnings` lists. | off |

### `kmctl update`

The same command as `kmctl init`, with the same options and output. Run it
after upgrading kmctl: it replaces the kmctl block with this release's block,
and keeps every other file. `kmctl plugin update` refreshes the skills and
the knowledge rules.

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

Print the session briefing: where knowledge lives, what is due, and the
package's skills, in under 500 tokens. The rules for writing knowledge are not
in it: `kmctl plugin install` puts them in `.claude/rules/`, and the briefing
adds only the one they lack. The SessionStart hook `kmctl plugin install`
writes prints this: Claude Code's runs `kmctl briefing`, Antigravity's runs
`kmctl briefing --format antigravity`. It reads and never writes.

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
| `--json` | Print one JSON object (`routing`, `state`, `rules`, `skills`). Not with `--format antigravity`. | off |
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
| `KIND` | The kind whose schema to print: `decision`, `practice`, `proposal`, `prototype`, `handoff` (what `kmctl new` writes); `manifesto`, `index`, `section-index`, `log` (the bundle files `kmctl init` writes); `architecture` (a diagram page, which no verb writes); `tutorial`, `how-to`, `reference`, `explanation`, `docs-index` (`docs/` pages and their index). | none: list the kinds |
| `--json` | With no kind, print the list as one JSON object of kind to where it lives and what it is for. A kind's schema is JSON either way. | off |

The body is in `x-kmctl-sections`: a list of the `##` sections in order,
`{"pattern": REGEX}` when every heading has one form (the log's dated
sections), `{"last": "Depicts"}` for an architecture page's free sections
that end with Depicts, or `null` for no fixed sections. When sections may
follow the fixed list, `x-kmctl-then` gives their `{"pattern": REGEX}`: a
decision may end with any number of `Correction, YYYY-MM-DD` sections, which
`kmctl decision supersede` appends. A kind with no front
matter (the `docs/` pages, the indexes below the root, the log) allows no
properties, and the root index allows only `okf_version`. Dates such as
`generated.at` are a date or a UTC timestamp.

Exit code: 1 for an unknown kind, with the list of kinds on stderr.

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
| `--stale-after WHEN` | When `kmctl review due` lists the concept as due, written as `stale_after`. A duration from now: `30d` days, `12w` weeks, `6m` calendar months, `1y` calendar years (a month end past the new month's last day moves back to it). Or a date: `2027-01-15`, read as its midnight UTC, or a timestamp such as `2027-01-15T08:00:00Z`. It must be in the future, so `0d` and today's date are refused. | `14d` for a handoff, none for the rest |
| `--source PATH` | Not for handoffs: a file or folder the concept describes, written to `sources` as `- resource: PATH`. Repeat it for more; they are written in the order given. It must exist on disk, found the way `kmctl review due` finds sources: from the concept's folder, then `.okf/`, then the repository root, with a leading `/` meaning `.okf/` and `.md` added when needed. Git is not needed, so a file you have not added yet is fine. Once someone verifies the concept, `kmctl review due` lists it when a commit changes a source. | none |

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

Install kmctl's APM package (the skills, the audit agent and the four
knowledge rules, with the okf skills they use), its session hook and okf's
MCP server for a harness: `claude` (Claude Code), `antigravity` or both.
Steps 5 to 7 are for `claude`; step 8 is for `antigravity`. It runs, in
order:

1. Refuses before changing anything when `uvx` is not on PATH, when
   `apm.yml`, `.claude/settings.json` or `.mcp.json` does not parse, or when
   `antigravity` is asked for with `--scope user`.
2. Runs `apm uninstall` on an `apm.yml` entry that names
   `JasperHG90/Knowledge-management/apm` another way than kmctl writes it, so
   the old package's hook goes with it.
3. Writes the entry `{git: SOURCE, path: apm, ref: vVERSION}`, where
   `VERSION` is this kmctl's, and the harnesses as `targets:` into `apm.yml`
   (`~/.apm/apm.yml` with `--scope user`). Other entries and comments are
   kept; a missing file is created.
4. Runs `uvx --from apm-cli==0.33.0 apm install --target HARNESSES` (with
   `-g` at user scope). For `claude`, APM writes the skills to
   `.claude/skills/`, the agent to `.claude/agents/` and the rules, with
   their `paths:`, to `.claude/rules/`. For `antigravity`, it writes the
   skills to `.agents/skills/` and the rules to `.agents/rules/`.
5. Once APM has succeeded, removes the old claude plugin `kmctl@kmctl`
   installed for this repository (or, with `--scope user`, for the user):
   `claude plugin uninstall`, then `claude plugin prune`, which also removes
   an okf plugin only kmctl needed, then
   `claude plugin marketplace remove kmctl`, each at the plugin's scope.
   When the `claude` CLI is not on PATH it skips this and says so.
6. Merges one SessionStart hook that runs `kmctl briefing` into
   `.claude/settings.json` (at user scope, the `settings.json` in
   `$CLAUDE_CONFIG_DIR`, by default `~/.claude/`). It finds its own entry by
   that command and replaces it in place; every other key and hook stays.
   The hook prints how to install kmctl and exits 0 when kmctl is missing or
   fails.
7. Declares okf's MCP server as `okf-bundle` in `.mcp.json` (at user scope,
   with `claude mcp add-json --scope user`). It runs okf's `okf_mcp.py` at
   the pinned okf-skills commit with `uv run`, on the nearest `.okf/` folder
   above where it starts. When there is already a server that runs
   `okf_mcp.py` under another name, kmctl adds none, removes its own, and
   says which it kept. Claude Code asks you to approve a project `.mcp.json`
   server once.
8. Replaces the folder `.agents/plugins/kmctl/`, which kmctl alone owns,
   with what this kmctl writes: `plugin.json`; `hooks.json` with one named
   hook, `kmctl-briefing`, whose one SessionStart handler runs
   `kmctl briefing --format antigravity` and prints `{}` and exits 0 when
   kmctl is missing or fails; `agents/kmctl-auditor.md` and okf's
   `agents/bundle-weaver.md` and `agents/event-analyzer.md`, translated
   from Claude Code's format (okf's are read from
   `apm_modules/scaccogatto/okf-skills/agents/`); and `mcp_config.json`
   declaring okf's MCP server as `bundle`, the same `uv run` launcher as
   step 7, which also looks above the plugin folder. Antigravity loads the
   folder only once you trust the repository folder, and the MCP server
   needs `uv` on PATH.

When APM reports that it left in place files it did not write, the install
stops before step 5, names the skill folders and exits 1; run it again with
`--force` to replace them. Running it again at the same version changes
nothing. Output: a `note:` line for each old install removed or step
skipped, then the status line as `kmctl plugin status` prints it, then a
`Next:` line.

| Option | Meaning | Default |
|---|---|---|
| `--harness LIST` | The agent harnesses to install for, as a comma list. Accepted: `claude`, `antigravity`. | `claude` |
| `--scope SCOPE` | `project` (this repository: `apm.yml`, `.claude/`, `.mcp.json` and `.agents/` here) or `user` (every repository: `~/.apm/apm.yml` and Claude Code's folder, `$CLAUDE_CONFIG_DIR` or `~/.claude`). `antigravity` is `project` only. | `project` |
| `--source GIT_URL` | The git URL of the repository holding the kmctl package, its `apm/` folder at the tag `vVERSION`. Set it for a fork, a local git server or an unreleased tree; an `http://` URL is allowed as insecure. | `https://github.com/JasperHG90/Knowledge-management.git` |
| `--force` | Let APM replace skill folders it did not write. It replaces each folder whole, deleting any file you added there. | off |
| `--json` | Print the resulting status and a `notes` list as one JSON object. | off |

Exit code: 1 when kmctl refuses, with the reason and the fix on stderr; for
example an unknown harness, an `apm.yml` or `settings.json` that does not
parse, a failed APM run (with APM's cause), or skipped files.

### `kmctl plugin update`

The same steps and options as `kmctl plugin install`. Run it after upgrading
kmctl: it moves the `apm.yml` entry to the new version's tag and reinstalls.

### `kmctl plugin status`

Report the ref `apm.lock.yaml` records for the kmctl package against this
kmctl's version, and for `claude` whether `.claude/settings.json` holds the
hook this kmctl writes. For `antigravity` it compares every file under
`.agents/plugins/kmctl/` with what this kmctl writes and reports each
missing, extra or different one, or that `apm_modules/` is missing. Each
problem names the command that fixes it: a missing package or hook, and any
problem with the Antigravity folder, names
`kmctl plugin install --harness HARNESS`, an older package names
`kmctl plugin update --harness HARNESS`, and a changed Claude hook names
`kmctl plugin update`. It reads files only.

| Option | Meaning | Default |
|---|---|---|
| `--harness LIST` | The harnesses to check, as a comma list: `claude`, `antigravity`. | `claude` |
| `--scope SCOPE` | `project` (this repository) or `user` (`~/.apm/` and Claude Code's folder). | `project` |
| `--json` | Print one JSON object: `cli_version`, `scope`, `package_ref`, `hook` (every checked harness's hook is the one this kmctl writes), `problems`. | off |

Exit code: 0 whether or not there are problems; 1 for a harness it does not know.

### Environment

| Variable | Used by | Meaning |
|---|---|---|
| `CLAUDE_CONFIG_DIR` | `kmctl plugin --scope user` | Claude Code's user folder, where the hook's `settings.json` and APM's user-scope skills, agent and rules go; by default `~/.claude`. |
