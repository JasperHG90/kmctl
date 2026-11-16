---
name: decision-gaps
description: Report the changes in git history that made an unrecorded decision. It writes nothing; the user decides which findings become records. Runs kmctl decision candidates and judges each change it lists. Use this whenever someone asks which decisions went unrecorded, what choices are missing from .okf/decisions/ or the ADRs, whether the decision log has fallen behind the code, or to scan history, merges, PRs or a release range for decisions, even if they do not say "decision record". Not for writing a record of a decision the user already names; that is kmctl new decision.
---

# decision-gaps

Changes often commit a project to one option over another without anyone
writing a decision record. A later contributor then finds the choice in the
code with no reason attached and either keeps it on faith or undoes it by
accident. This skill finds those changes and reports them. **It writes
nothing.** Which findings become records is the user's call: they turn one
into a record with `kmctl new decision`, or ask you to, for the findings
they pick.

The approach was measured on kmctl's own history
(`.okf/prototypes/decision-gaps/` in kmctl's repository): a judge looking at
every change found 25 of 30 hidden decisions, and about six in ten of its
other claims were real gaps. So treat each finding as a lead for the user
to confirm, not a verdict, and judge every change rather than only the ones
that look likely: the no-model score missed one decision in six.

## 1. List the candidates

```sh
kmctl decision candidates            # changes since the newest committed decision
kmctl decision candidates --since v0.13.0   # or since a point the user names
```

It prints one line per change (score, sha, kind, recorded, subject) and a
count. It splits history for you: one change per ticket merge, pull request
or plain commit, with sync merges read through and loop, release and
placeholder commits left out. Use `--since` when the user names a starting
point (a tag, a release, a date turned into a commit, a sha).

If the default range holds only a change or two (the newest record is
recent), say so, and say how many changes there are since the last release
tag (`git describe --tags --abbrev=0`) so the user can widen the range.

If the list is long, say how many changes there are before judging. Past
about forty, ask whether to go ahead or narrow the range with `--since`;
judging costs a few seconds and a little context per change, and the user
may only care about a recent stretch. When the user already said to go
ahead, or named the range, carry on.

## 2. Judge each change

Get the details with `kmctl decision candidates --json` (same `--since`).
Each object has `sha`, `parent`, `kind`, `subject`, `message`, `slug`,
`plan`, `files`, `recorded`, `signals` and `score`. Keep any files you write
along the way (the JSON, batch files) outside the repository, in a
temporary folder.

Judge in batches of about ten, and give every batch the same instructions:
[references/judging.md](references/judging.md), which says what to read for
each change, what counts as missing, covered or not a decision, and how to
answer. Each change was measured judged on its own with little around it; a
long session full of other changes blurs that, and judges given different
wording drift apart. In Claude Code, hand each batch to a subagent: the
path of `references/judging.md`, the batch's objects and the repository
path, nothing else. In a harness without subagents, read
`references/judging.md` once and work through the batches yourself, one
change at a time.

Collect every block. Where two changes carry the same choice (a commit and
the pull request that merged it), report it once and name both.

## 3. Report

Lead with the findings, then the counts. Keep each finding to what the user
needs to decide whether to record it:

```markdown
## Decisions with no record (N)

1. **<the choice, one sentence>**
   - Instead of: <the option turned down, if the change shows one>
   - Change: <short sha> <subject>
   - Why it counts: <one line: what a later contributor could question>

## Records with no change of their own (N)

- <short sha> <subject>: records <ADR number>; the choice was made elsewhere.

Judged <total> changes since <start>: <missing> missing, <covered> covered,
<none> not a decision.
```

Close by saying that nothing was written, and that the user can turn any
finding into a record with `kmctl new decision "<title>" --description
"<one sentence>"` or ask you to draft the ones they pick. Then stop: draft
or write a record only for findings the user picks, after they ask.

When nothing is missing, say so in one line with the counts.
