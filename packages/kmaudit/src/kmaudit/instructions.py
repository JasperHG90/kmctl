"""The extraction instructions the ``claims_todo`` MCP tool hands an agent, once, with the sections.

They live here, in the package, so the skill and the agent that drive the
verbs stay thin. The hash of ``GUIDANCE`` is part of every section's key, so
changing it hands every section out again; ``SUBMIT``, which only says how
answers reach kmaudit, is left out of the hash, so renaming the way in (a
command, an MCP tool) keeps every stored answer.
"""

import hashlib

#: What extraction depends on. Changing it hands every section out again: also
#: empty ``PREVIOUS_HASHES``, whose answers were made under other guidance, and
#: update the hash pinned in tests/test_claims_sections.py.
GUIDANCE = """
You read sections of a design document from a software repository and
decide, sentence by sentence, which claims each makes about that repository.

Why: an auditor checks each claim against the code and reports the ones that
no longer hold. A claim it cannot check wastes its time; a claim you miss is
drift nobody sees.

Go through every numbered sentence of a section in order and give each one a
verdict, including sentences that hold no claim. Do not stop early: an
answer that leaves a sentence without one is refused.

Kinds, by how a claim is checked. Each kind has examples of what it is, and
near misses that are another kind:

- point: look at one named thing in this repository (function, command,
  flag, config key, file, workflow, test).
  Is: "`audit init` writes audit.toml." "Retries stop after `MAX_RETRIES`."
  "The release workflow runs on every tag push" (the trigger is in that
  workflow file).
  Not: "Every command accepts --json" (structural: all commands). "The CLI is
  easy to use" (subjective). "GitHub keeps workflow logs for 90 days"
  (external).

- structural: check many files for a pattern ("every X does Y", "nothing
  imports Z", "only the CLI writes").
  Is: "Every workflow pins its actions to a commit." "Nothing outside cli.py
  imports typer." "Only the store writes to the database."
  Not: "The release workflow pins its actions" (point: one file). "The code
  is well organised" (subjective). "The system has three layers" (broad: no
  pattern to search for).

- broad: about this repository, but too sweeping for any one file to settle
  ("the tool covers every task a user needs", "the system has three
  layers").
  Is: "The CLI covers everything a user needs to keep docs current." "The
  design keeps configuration in one place."
  Not: "Configuration is read only from audit.toml" (structural: search for
  other reads). "The design is elegant" (subjective).

- subjective: a principle or value a person must judge; no file settles it.
  Is: "Plain language beats jargon." "Small changes are easier to review."
  Not: "Every docstring follows the numpy format" (structural: a value turned
  into a rule you can check). "Users find the CLI confusing" (external: about
  people, not the repository).

- external: about a tool, service or people outside this repository.
  Is: "uv resolves dependencies faster than pip." "GitHub runs scheduled
  workflows in UTC."
  Not: "CI pins uv to 0.5" (point: the version is in a file here). "The
  action runs on ubuntu-latest" (point: the workflow says so).

- none: no claim. Status, dates, authors; history ("came out of", "used
  to", "was"); measurements from a past run; the reasons for a choice; the
  alternatives a decision rejected; what an operator asked for; headings.
  Is: "Status: accepted." "We first tried Redis, which was too slow." "In
  the March run, recall was 93%." "Considered: a message queue." "The
  operator asked for a dry run."
  Not: "Since 0.4 the CLI reads audit.toml" (point: it still does; the date
  is history, the reading is a claim). "We chose SQLite because it needs no
  server" (point: the project uses SQLite; only the reason is none).

Give every claim a quantifier, by how many places in this repository settle
it:
- exists: one place proves it; find the function, file, flag, key or step
  that does it.
- all: every instance of something must comply ("every concept has a type",
  "each workflow pins its actions"); you must find every instance.
- none: no instance may exist anywhere ("never writes outside .okf/",
  "nothing imports the CLI", "only the CLI writes X"); you must search
  everywhere.
Judge the meaning, not the words: "the hook stays silent when the bundle is
clean" is exists, because one hook settles it.

Write how_to_check, then reason, before you choose the kind. If you cannot
name what to open or run in this repository, the kind is subjective,
external, broad or none. In reason, say in one short sentence why the
sentence is that kind: what in this repository settles it, or why nothing
does ("names the `audit init` command", "a value judgement; no file settles
it", "history: says what was tried before").

A sentence can hold several claims; list each one. Write each so it stands
alone: replace "it", "this", "the code", "both commits" and "the tool" with
the names they refer to, from this section or the earlier sections shown.
Keep what the sentence says, no more and no less:
- Keep its conditions: "If the child exits 0, it prints the line" is a claim
  that says "When the child exits 0, it prints the line", never "the child
  exits 0".
- Keep its tense: a sentence about the past is history (none); never restate
  it in the present.
- Keep its negation and its list's heading: an item under "Not built", "Out
  of scope" or "What it does not do" is a claim that it is not done, never
  that it is; an option under "Considered" or "Rejected" is none.
In refers_to, list the labels of the sentences a claim needs to be
understood: "s.n" for sentence n of earlier section s, "n" for this
section; leave it empty when the claim stands alone.

Earlier sections of the document are shown for context only: give no
verdicts for them. If the record has later corrections, they are shown for
context only: give no verdicts for them, and mark a sentence they overturn as
none.
""".strip()

SUBMIT = """
Answer each section with one JSON object, and pass a list of them to the
claims_submit tool as answers, with the namespace as folder:

{"section": "<id from todo>", "key": "<key from todo>", "sentences": [
  {"n": 1, "how_to_check": "...", "reason": "...", "kind": "point",
   "claims": [{"claim": "...", "quantifier": "exists", "refers_to": []}]},
  {"n": 2, "how_to_check": "", "reason": "history", "kind": "none",
   "claims": []}
]}
""".strip()

#: What ``claims_todo`` hands the agent: the guidance, then how to submit.
INSTRUCTIONS = f"{GUIDANCE}\n\n{SUBMIT}"
#: Hashes of earlier instructions whose stored answers still stand: the
#: guidance is the same and only the way answers are submitted changed.
#: ``a006057ae74b`` hashed the whole text when the audit was still part of kmctl.
PREVIOUS_HASHES: tuple[str, ...] = ("a006057ae74b",)


def instructions_hash() -> str:
    """A short hash of the current guidance, part of every section's key."""
    return hashlib.sha256(GUIDANCE.encode()).hexdigest()[:12]
