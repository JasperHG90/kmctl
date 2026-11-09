---
type: plan
title: 'Plan: verify-verb'
description: "A kmctl verify verb writes a person's verified entry into a concept or docs page, and the briefing, the audit skill and the okf-bundle rule tell an agent how a concept leaves kmctl review due."
tags:
- plan
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T21:18:58+00:00'
slug: verify-verb
epic: knowledge
depends_on: []
priority: null
---

# verify-verb

Relayed from: operator, 2026-10-17, from an Antigravity session: an audit found a due concept holds, but neither the agent nor the briefing knew how to clear it from `kmctl review due`; "Yeah but the agent doesn't know about that?" and "And that kmctl command maybe?"

## Intent

`kmctl review due` lists a concept with no `verified` entry (`src/kmctl/review_due.py`), and nothing tells an agent how one gets cleared. ADR 0005 keeps audits report only; a person, or an agent the person asks, acts on findings. No verb writes the entry, so today it is a hand edit of YAML whose shape only the rule describes.

- New verb `kmctl verify ID --by human:<id>`, in `src/kmctl/__init__.py`, with its logic in `new:src/kmctl/verify.py`. `ID` is what `kmctl review due` prints: a concept id under `.okf/` (`decisions/0001-...`, `manifesto`) or a docs page id (`docs/how-to/...`). It appends `{by, at: now}` to the front matter's `verified` list (creating the list when absent; a single mapping becomes a one-item list), with `at` a full UTC timestamp in the form `kmctl new` writes `generated.at`, not a bare date: `review_due` reads a bare date as midnight UTC, so a source committed earlier the same day would keep the id due (round 1 plan review). A `verified` entry never clears `stale_after passed`, so the verb takes `--stale-after` in the forms `kmctl new` accepts (`stale_after_time` in `src/kmctl/concepts.py`) and writes that field too; when the file's `stale_after` has already passed it refuses without `--stale-after`, naming the flag, so no run leaves the id due (round 1 plan review). It leaves every other line of the file as it was, and appends a line to `.okf/log.md` for a concept. It refuses, naming the fix, when `--by` does not start with `human:` (only a person verifies), when `--stale-after` is missing for a passed `stale_after` or is not in the future, when the id matches no file, when the file is a handoff (handoffs are never verified), or when the front matter cannot be read. `--json` prints the id, path, by and at; the text output ends with a `Next: kmctl review due` line.
- The verb's help and the okf-bundle rule (`apm/claude/.apm/instructions/okf-bundle.instructions.md`, regenerated for Antigravity) say an agent runs it only after the named person has read the concept and confirmed it, never on an audit verdict alone. The audit skill (`apm/.apm/skills/audit/SKILL.md`) ends by saying how a concept leaves the list and names the verb. The uncommitted rule and skill edits in the primary checkout are the start of this; their changed body hash is the failing `tests/test_apm_package.py` test, updated here.
- The briefing stays as it is: it already points at `kmctl review due`, and it has no room (spike:verify-verb/1). Instead `kmctl review due`'s text output, when it lists anything due, ends with a `Next:` line naming `kmctl verify ID --by human:<id>` for a concept a person has checked, and `--stale-after` for one listed as `stale_after passed`, and its help epilog says the same. The `--json` shape does not change.
- A new ADR records that a person's check is written by `kmctl verify` and that an agent may run it only on that person's confirmation; it does not change ADR 0005 or I2, which forbid an audit stamping. `docs/reference/commands.md` and the architecture overview's Depicts list gain the verb.

Measured: 0 verbs write a `verified` entry; neither the briefing nor `kmctl review due` names a way to clear the 24 concepts due in this repository, all 24 for `unverified`, so the new `Next:` line would have shown on every run here.

Done when tests show `kmctl verify` writes the entry so that `kmctl review due` no longer lists that id, for an unverified concept, a docs page whose source changed earlier the same day, and a concept past its `stale_after` given `--stale-after`, keeps the rest of the file byte for byte, appends to an existing `verified` list, and refuses each case above with a one-line fix on stderr and exit 1; `kmctl review due` names `kmctl verify` when something is due and not when nothing is; the audit skill and both okf-bundle rules name the verb; and the gates pass.

## Could invalidate this plan

- The hint only helps if an agent reaches `kmctl review due` from the briefing. Naming the verb in the briefing itself does not fit: spike:verify-verb/1 put the worst-case briefing test at 494 of 500 tokens, and the shortest hint takes it to 505. So the plan rests on the briefing's state line naming `kmctl review due` whenever something is due, which spike:verify-verb/2 checks against this repository's 24 due concepts.
