---
type: decision
title: "ADR 0046: kmctl works from code toward knowledge and kmaudit from knowledge toward code"
description: "A feature goes in the package whose direction it shares: kmctl starts from the code and the decisions and keeps docs/ and .okf/ current, kmaudit starts from docs/ and .okf/ and checks them against the code."
tags: [decision]
generated:
  by: process:kmctl/0.13.0
  at: 2026-11-16T11:37:44Z
status: stable
sources:
  - resource: "packages/kmctl/"
  - resource: "packages/kmaudit/"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0046: kmctl works from code toward knowledge and kmaudit from knowledge toward code

## Context

The repository holds two packages since
[ADR 0043](0043-the-audit-is-its-own-library-kmaudit-served-over-mcp.md)
split the audit out as kmaudit and
[ADR 0044](0044-kmctl-and-kmaudit-are-both-workspace-packages.md) made
both workspace packages. Nothing said which one a new feature belongs in.
The question came up on 2026-11-16 for a skill that scans git history for
decisions nobody recorded: it reads commits and decisions, and could be
argued into either package, since both deal with knowledge. The operator
settled it: "kmctl starts from code & decisions -> docs & okf, kmaudit
starts from docs & okf -> code."

## Decision

A feature goes in the package whose direction it shares.

- **kmctl starts from the code and the decisions** and works toward
  `docs/` and `.okf/`: it keeps knowledge current as the code changes. The
  briefing, `kmctl review due`, `kmctl new`, the knowledge rules
  and the `/audit` agent's review of decisions, practices and
  architecture pages all begin from what changed in the code or the
  decision log and end in knowledge.
- **kmaudit starts from `docs/` and `.okf/`** and works toward the code:
  it lists what a folder of docs claims and checks each claim against the
  code, rerunning the checks with no model.

When a feature reads both, the side it starts from decides: the history
scan starts from commits and ends in a decision record, so it is kmctl's.

Rejected: deciding per feature by what is handiest to build, or by which
package already has a similar helper. That reargues each placement and
lets the packages blur, and kmaudit's promise of running on any folder of
docs without kmctl depends on keeping it to one direction.

## Consequences

- Placing a feature is a one-line question: what does it start from?
- If the history scan for missing decisions is built, it goes in kmctl;
  whether to build it waits on measuring it on this repository's history.
- A feature that only works in kmaudit's direction but needs kmctl's
  bundle layout goes in kmaudit and reads that layout as plain files, so
  kmaudit still runs without kmctl.

## Correction, 2026-11-27

One feature sits outside the rule above. The CI agent that rereads, on a
pull request, the pages whose `sources` it changed
([ADR 0060](0060-the-ci-agent-only-rereads-the-pages-a-pull-request-changed.md))
works from `docs/` and `.okf/` toward the code, kmaudit's direction, but it
ships in kmctl's GitHub Action (`action/agent.py` and `action/prompt.md`),
outside both packages. The action is how a repository runs kmctl in CI, and
kmaudit has no action of its own.
[ADR 0057](0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md)'s
2026-11-26 Correction records this placement. If the shipped audit moves
into kmaudit, it moves with it.
