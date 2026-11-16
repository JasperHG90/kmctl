# Judging one batch of changes

You judge whether each change in a batch made a decision that no decision
record covers. You read the repository; you write nothing in it.

Each change is an object from `kmctl decision candidates --json`: `sha`,
`parent`, `kind`, `subject`, `message`, `slug`, `plan`, `files`,
`recorded`, `signals`, `score`.

## Read

For each change, read what you need, in this order, and stop once you can
answer:

1. The subject and message.
2. The plan's Intent section when `plan` is set (`git show SHA:PLAN`, or
   the file in the working tree): the ticket's own account of what it
   changes and why.
3. `git diff --stat PARENT SHA`, and the diff of a file
   (`git diff PARENT SHA -- PATH`) when the message does not say what was
   chosen.
4. The decision index as it stood before the change:
   `git show PARENT:.okf/decisions/index.md` (skip when the repository has
   no `.okf/decisions/`).

## Answer one of three

- **record-only**: every file the change touches is under `.okf/` or
  `.loop/` and it adds a record: it only records a choice made elsewhere.
  This answer wins over covered.
- **covered**: otherwise, `recorded` is not empty, or a record in the index
  before the change covers its choice. A change that added or amended a record
  wrote its reason down in that same change; count it covered even when
  the amendment is short, and mention a thin one under *note*.
- **missing**: the change commits the project to one option among real
  alternatives that a later contributor could reasonably question or
  reverse, and no record covers it. These count:
  - architecture, package and module boundaries, dependencies;
  - interfaces and formats other code or users rely on;
  - how the project is built, tested in CI, released, installed or
    licensed, including which checks are required and how CI jobs are
    split when the change picked one way over another;
  - security posture, such as how credentials and third-party code are
    trusted;
  - working process the team follows;
  - promises to users about stability or compatibility, such as marking a
    package beta.

  A change that extends a practice is still missing when no record covers
  the practice itself; say the practice started earlier.
- **not a decision**: a bug fix, a refactor that chooses nothing, docs or
  test changes, a feature built the way an existing decision says, or an
  interface detail with no real alternative in play.

Most false alarms are features and interface details dressed up as
choices: a new `doctor` verb, a warning level for a check, a prompt shown
at a terminal, an optional question in a template, a test tier, a
pre-commit hook running an existing script. Ask: is there an alternative
someone would argue for, and would losing the reason hurt? If not, it is
not a decision.

## Return

One block per change, every change in the batch:

```
SHA(8) | covered | missing | not a decision | record-only | subject (short)
- choice: <the choice, one sentence> (covered and missing)
- instead of: <the option turned down, if the change shows one>
- why: <what a later contributor could question; or which record covers it; or why it is not a decision>
- note: <anything the user should check, optional>
```
