---
description: "Why the author of a pull request accepts each draft decision, their coding agent runs the command, and CI only blocks a draft at review."
stale_after: 2027-02-23
sources:
  - resource: "packages/kmctl/src/kmctl/accept.py"
  - resource: "packages/kmctl/src/kmctl/checks.py"
  - resource: "action/knowledge-ci.sh"
---

# Who decides a decision record

## The question

In a team that builds with coding agents, the agents write most decision
records. A record says "we chose this", so somebody has to have chosen it.
Before this change, nothing said who. `kmctl check` passed a draft, no verb
accepted one, and in one repository 29 of the 44 decision records that
merged pull requests added were still drafts when they merged.

kmctl answers with one rule: the author decides, their coding agent applies,
and CI enforces.

## How it works

Two parties act. The **author** of the pull request decides. Their **coding
agent**, in the author's local session, runs every kmctl command. CI only
checks.

| Step | Decides | Runs it | Where | How |
|---|---|---|---|---|
| Draft | Coding agent | Coding agent | Local | `kmctl new decision --draft` |
| List open drafts | | Coding agent | Local | `kmctl check --no-drafts` |
| Accept or drop | Author | Coding agent | Local | `kmctl decision accept NUMBER`, or delete the file |
| Mark ready | Author | Author | GitHub | Ready for review |
| Block drafts | | kmctl's action | CI | `kmctl check --no-drafts` |
| Review and merge | Reviewer | Reviewer | GitHub | Normal code review |

A record's status moves like this. Each box is a status; the coding agent
creates every draft.

```mermaid
flowchart TD
    D[Draft] -->|PR author accepts| S[Stable]
    D -->|author drops| X[Deleted]
    S -->|a later decision replaces it| R[Superseded]
```

One pull request, from start to merge. Boxes are actions, diamonds are
questions, and each names who acts. Every agent step ends with a push,
which runs CI again.

```mermaid
flowchart TD
    A[Coding agent drafts decisions] --> C{Author: keep each draft?}
    C -->|yes, agent runs kmctl decision accept| F[Author marks PR ready]
    C -->|no, agent deletes it| F
    F --> G{CI: drafts left?}
    G -->|yes| C
    G -->|no| L[Reviewer approves, PR merges]
```

The same pull request, read top to bottom by who talks to whom:

```mermaid
sequenceDiagram
    participant A as Author
    participant G as Coding agent
    participant CI
    participant R as Reviewer
    G->>A: open drafts, one summary each
    A->>G: accept or drop each
    G->>CI: kmctl decision accept, push
    A->>CI: mark PR ready
    CI->>CI: kmctl check --no-drafts
    R->>CI: approve and merge
```

## Why it is this way

**A person says yes, and the log says who.** `stable` has to mean somebody
chose it. So only a person accepts (ADR 0050): `kmctl decision accept`
refuses a `--by` that is not `human:<id>`, the knowledge rules tell the agent
to run it only on the author's explicit yes, and CI never runs it. The log
line names the person.

**The author, not the reviewer.** The author was there when the choice was
made and can explain it. A reviewer's approval covers the whole change, not
one record, so kmctl does not count it as accepting a decision.

**Blocked at review, not before.** A draft pull request is where a draft
belongs: the work is still moving. The action's default, `fail-when-ready`,
checks only once the pull request is ready for review. Set `drafts: fail` to
check on every run.

**Not verification.** Accepting answers "did we choose this?" once.
`kmctl verify` answers a different question: does a record still hold, as
the code changes? A person rereads it and confirms (ADR 0023). The two stay
separate verbs.
