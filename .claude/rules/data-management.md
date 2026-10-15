---
paths: ["src/kmctl/**/*.py", ".loop/**"]
---

<constraint name="data-management">
The harness keeps state in stores, and each one is authoritative for exactly
one thing. Respect the ownership. Never invent another path.

- **Git** is ground truth for code and commits. Nothing else records what was
  committed.
- **The plan file** (`.loop/plans/<slug>.md`, front matter and prose) is the
  human-authored source of truth for a ticket's INTENT: `epic`, `depends_on`,
  `priority`, and the contract. The human owns these. The loop never rewrites
  them.
- **The eval contract** (`.loop/evals/<slug>/rows.json`) is the signed
  definition of done. The harness records the signer and a hash over each
  row's behavior, fails-when and command, and changing any of them needs a
  new sign-off (`.okf/decisions/0002-eval-rows-are-the-locked-contract.md`).
  The operator signs, or an agent under a standing grant on the record
  (`.loop/delegations/`, ADR 0012, ADR 0029). The eval's `README.md` is
  written by the harness from the rows (ADR 0027).
- **The models** in `src/loop_harness/stores/models.py` own the shape of
  every data object. `loopctl schema NAME` prints an object's JSON Schema from
  its model when it runs; no schema file is kept in `.loop/` (ADR 0038).
  Each carries a MAJOR.MINOR `schema_version` (ADR 0039,
  `.claude/rules/schema-versioning.md`).
- **The ledger** (`.loop/tickets/<slug>.json`, one JSON file per ticket
  with no body and no OKF fields, ADR 0034) is the machine-owned source of truth
  for LIFECYCLE state git cannot record: `stage`, `attempts`, cycle counts,
  `blocker`, `commit_sha`, `dropped`. The loop owns these. A hook refuses
  hand edits, and every write to a ticket file lands with an event in that
  ticket's lifecycle stream.
- **Stamps, verdicts and spikes** (`.loop/stamps/`, `.loop/verdicts/`,
  `.loop/spikes/`) are evidence. Stamps and spike runs (`run.json`, the
  output and the copied scripts) are harness-written; a spike's README
  carries the agent's question and outcome, written only through `loopctl
  plan spike` and `loopctl plan spike-note` (ADR 0026). A stamp is JSON
  data with no prose (ADR 0028). A verdict is the reviewer's text, submitted through `loopctl review verdict`
  and bound to the tree it reviewed; its label, findings and binds are the JSON
  record `<pass>-r<n>-<k>.json` beside the prose, and the placeholder is a
  record alone (ADR 0036).
- **The append-only logs** (cost ledger, findings ledger, gate-failure
  history, and each ticket's record of blocks and closes, all JSONL under
  `.loop/events/`, with `events/untracked/` for work outside a ticket) are
  machine-owned evidence. The harness appends, and `events.append` checks
  each record against its kind's model in `stores/event_models.py` first.
  Nothing rewrites an entry. A red gate's raw output sits beside its stream
  in `gate-output/`, named by hash, and the event points at it.

Which of prose, events or data each producer emits is
`.claude/rules/artifact-outputs.md`.

The ledger also holds a copy of the plan-owned intent fields, written at
`ticket register` and refreshed by `loopctl state reconcile`. The copy is a
cache, not a second source of truth, and nothing runs reconcile for you. So
every reader (`graph`, `epics`, `ticket next`, `ticket list`, the briefing,
`drive`, the dependency gate) reads intent from the plan through the one
parser (`current_intent` in `commands/common.py`), and a plan edit shows at
once. When a plan does not parse, a report warns and uses the copy, and the
dependency gate refuses. An archived ticket keeps its frozen copy. Reconcile
syncs plan to ledger for intent (the plan wins) and git to ledger for `stage`
(git wins), and prints each intent change it makes.

All of `.loop/` lives in the primary checkout. `loopctl` resolves it there
from any worktree, and a worktree never writes it (ADR 0010).
</constraint>

## The rule for a per-ticket field

Decide which store owns a new field, then follow that store's one path:

- A field the HUMAN authors (intent) is plan-owned. It is parsed and
  validated in one place (a bad value raises, never a silent drop), and
  loopctl reads it from the plan through that one parser; the ledger's copy
  is a cache. A skill reads the value from loopctl's output and never
  hand-parses the plan's front matter.
- A field the LOOP produces at runtime (lifecycle) is ledger-owned and never
  goes in the plan file.

v1 shipped four ledger fields that were never set across 113 tickets
(`review_rebinds`, `relay_block_nonfork`, `carried_over_finding`, `tags`). A
new field ships with the code that sets it and a replay case that reads it.

Config (`.loop/config.toml`) is the default layer under the plan-owned fields.
The plan overrides config, and config overrides nothing the plan declared.
