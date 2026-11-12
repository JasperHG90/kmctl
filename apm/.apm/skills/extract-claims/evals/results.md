# extract-claims: skill-creator results

Made with the skill-creator skill (ADR 0007), together with the
`kmctl-claims-extractor` agent, on 2026-11-11 (ticket agent-audit-claims-skill).
The repository was `tests/fixtures/audit_repo.py`'s fixture plus a copy of
`.okf/decisions/0005-audits-report-only.md`: 11 sections in 3 concepts.

In these runs the main session did the skill's steps (todo, batch, report)
itself, and the agent ran as a real subagent on `model: haiku` from
`apm/.apm/agents/kmctl-claims-extractor.md`, with Read and Bash only. So the plan's outcome in a real Claude Code session
(its transcript holds the summaries but no claim text) is shown only through
the agent's replies, not a `/extract-claims` run.

## Iteration 1

**Eval 1, first pass.** `kmctl audit claims todo` listed 3 files, 11
sections, which is one batch. The Haiku agent stored 11 of 11 sections with
no refusal, 25 claims (point 19, structural 4, subjective 1, external 1),
in 8 tool calls, 74k tokens and 69 s. Its reply was the two-line summary and
nothing else, so the main session saw no claim. Afterwards `todo` reported
0 to extract and `git status --porcelain` was empty. A read of the stored
claims found them standalone and in the present tense, with a usable
`how_to_check`. ADR 0005's history and its corrected sentences were kind
none, and only what the corrections still say became claims.

**Baseline, no skill** (Sonnet, the same prompt in words: "extract the
claims our .okf bundle makes"). It found `kmctl audit claims` on its own and
stored all 11 sections, 33 claims, in 58k tokens and 41 s. Two sections were
refused first (a subjective sentence with no claim) and fixed from the
refusal line. It worked, but every sentence, verdict and claim passed
through the session's own context. The skill's point is that they do not:
the main session keeps only the summary, and Haiku does the reading.

**Eval 2, after an edit.** One sentence was added to `.okf/tool.md`. `todo`
listed only `.okf/tool.md` (1 section, 1 changed) and kept the other 10.
The agent stored it in 4 tool calls, 46k tokens and 14 s, adding the new
claim "Every kmctl command accepts --json." as structural, quantifier all.

**Eval 3, nothing to do.** After eval 2, `todo` reported 11 up to date and
0 to extract, so step 1 stops the skill before any agent is dispatched.

## Description

The description's first sentence is the briefing line, so it stays short
(`kmctl briefing` lists every skill and I3 caps it at 500 tokens). The rest
names the triggers: extract, refresh or list the bundle's claims,
`/extract-claims`, and claims needed before writing checks. The trigger
optimisation loop (`run_loop`) did not run for this ticket.
