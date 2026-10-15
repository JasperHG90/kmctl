---
paths: ["src/kmctl/**/*.py", ".loop/**", "plugin/**", "tests/fixtures/**"]
---

# What each primitive emits

The harness has four kinds of producer, and each one emits one kind of
output. A concept in `.loop/` (markdown with OKF front matter) holds prose
that a person or an agent wrote. Front matter is metadata *about* that
prose: who wrote it, what it is for, and which ticket it belongs to. Data
that a program reads, such as rows, results and answers, is JSON or JSONL
beside the concept, never front matter and never a body. The decision is
`.okf/decisions/0028-concepts-hold-prose-checks-and-judgements-emit-data.md`.

| Primitive | What it is | Emits | Where |
|---|---|---|---|
| **Agent** (and the operator) | writes text a person reads: a plan, a verdict, a spike's question and outcome, a reflection | prose: an OKF concept with a written description and the sections its body schema names | `plans/<slug>.md`, `verdicts/<slug>/<pass>-r<n>-<k>.md`, `spikes/<slug>/<n>/README.md`, `reflections/<slug>.md`; loopctl splits a verdict's label, findings and binds into `verdicts/<slug>/<pass>-r<n>-<k>.json` beside it (ADR 0036) |
| **Operator** (or an agent drafting for one) | writes the rows a ticket is signed against | data: JSON checked against a schema | `evals/<slug>/rows.json`, beside the README loopctl writes from it (ADR 0027); a standing grant, which loopctl writes for the operator, is `delegations/g<n>.json` (ADR 0029) |
| **Judgement** | a model answers a fixed question (plan.split, review.hides-defect, ...) | events and data: one JSONL line per answer, the exact input and question as JSON files stored by hash | `events/<slug>/judgements.jsonl`, `judgement-inputs/`, `judgement-questions/` |
| **loopctl** (the lifecycle verbs) | records where each ticket stands: stage, rounds, blocker, sign-off | data: one JSON file per ticket, rewritten whole by each verb, and a lifecycle event per write | `tickets/<slug>.json` (ADR 0034), `events/<slug>/lifecycle.jsonl` |
| **Check** | a program runs and passes or fails: a gate, an eval row, a stamp, a spike's run | events and data: a JSON record of the result, a JSONL event per red result, and a red command's raw output as a `.txt` file the event points at | `stamps/<fingerprint>.json`, `events/<slug>/gates.jsonl`, `events/<slug>/gate-output/<sha>.txt` |

A folder holds a concept and its data side by side. An eval
(`evals/<slug>/`, ADR 0027) and a spike (`spikes/<slug>/<n>/`, ADR 0026) are
folders: the README is the concept and the JSON beside it is the data. A
verdict is a pair: `<pass>-r<n>-<k>.md` is the reviewer's text and
`<pass>-r<n>-<k>.json` its label, findings and binds, which loopctl reads to
decide a round. The reviewer still submits one document; loopctl checks it
and splits it on write. The fail-first placeholder is the record alone,
`<pass>-r<n>.json` with `placeholder: true` (ADR 0036).

<constraint name="checks-and-judgements-write-no-prose">
WHY: a stamp's body repeated its own front matter as headings and fenced
output, and 28 of them reached 10 KB each. Nobody read the body, and nothing
pruned it.

A check or a judgement never renders into a concept: no markdown body, no
generated paragraph, and no heading per result. It appends events and
writes JSON. A check keeps captured output only when a reader needs it,
which means red output, and keeps it as a raw `.txt` file that an event
names. A judgement's answer reaches a person through the verb's report and
ticket state fields, never as prose in a verdict or a plan.
</constraint>

<constraint name="data-is-not-front-matter">
WHY: an eval's rows were YAML in front matter above a body of template
instructions. So the file a reader opened was data, and its prose said
nothing (9 of 9 evals had the same generated description). ADR 0027 moved
the rows to `rows.json`.

A field that a program reads to decide something, and that a person does
not read as a summary, goes in a JSON file beside the concept. Front matter
keeps the OKF fields (`type`, `title`, `description`, `tags`, `generated`),
the slug, and the few keys that place the concept (a verdict's pass and
round), and a projection a
person reads to see a record (an eval README's `signoff` and `verified`,
ADR 0012). A new kind of output
names its store in this table before it ships.
</constraint>

<constraint name="prose-has-a-schema">
WHY: verdict bodies made up their headings round by round, and two of 16
plans kept the template's description after plan review.

Each prose concept's body has the sections its schema in
`src/loop_harness/checks/prose.py` names. The template is rendered from that
schema, and the verb that accepts the prose checks against the same schema:
`plan lint` and `review verdict`. ST-13 checks
the result. A section still holding its template text counts as unwritten.
Reflections and spike READMEs have no body schema yet; a new one is added
here and in `prose.py` together.
</constraint>

<constraint name="descriptions-are-written">
WHY: a spike's description was its shell command cut at 80 characters,
mid-token. That passed the validator, and an index showed it to every
reader.

A description is what an index shows a reader deciding whether to open a
concept. It is whole sentences, 20 to 400 characters, ends a
sentence, and is never the template's default. A harness may compose one
from fields ("reviewer verdict for round 2 of x: pass."). It never cuts one
from free text such as a command, an output or a body. A spike's
description is the `--about` question the agent wrote, kept whole, so a
short question passes. `description_problems` in `checks/prose.py` is the
check.
</constraint>
