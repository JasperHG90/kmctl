# extract-claims: skill-creator results

These runs used the commands while they were still a kmctl group; they are
`kmaudit` now (ADR 0043), and the names below use the new one.

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

**Eval 1, first pass.** `kmaudit claims todo` listed 3 files, 11
sections, which is one batch. The Haiku agent stored 11 of 11 sections with
no refusal, 25 claims (point 19, structural 4, subjective 1, external 1),
in 8 tool calls, 74k tokens and 69 s. Its reply was the two-line summary and
nothing else, so the main session saw no claim. Afterwards `todo` reported
0 to extract and `git status --porcelain` was empty. A read of the stored
claims found them standalone and in the present tense, with a usable
`how_to_check`. ADR 0005's history and its corrected sentences were kind
none, and only what the corrections still say became claims.

**Baseline, no skill** (Sonnet, the same prompt in words: "extract the
claims our .okf bundle makes"). It found `kmaudit claims` on its own and
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

## Moved to kmaudit's package and its MCP tools (ticket kmaudit-skills-mcp)

The skill moved to kmaudit's APM package, its agent became
`kmaudit-*` with Read, Grep, Glob and the kmaudit MCP tools only, and
both now call those tools instead of the CLI. `evals.json` names the tools
in each expectation and adds eval 4, the same work in a harness with no
agent (Antigravity, OpenCode). The runs above used the CLI and are kept as
the record of the flow's results then.

The evals were not rerun for this change. A run needs a session where the
kmaudit MCP server is configured and `mcp__kmaudit__*` allowed: the
building session had no such server, and starting one meant a nested
`claude` session, which the build left out (the loop's guards refuse one,
as the plan's spike found). The `tests/test_skills.py`
checks (every tool named exists in the server, no kmaudit shell command is
named) and `packages/kmaudit/tests/test_apm_package.py`'s check of the
agents' tools hold, and the APM integration test in
`packages/kmaudit/tests/test_apm_package.py` installs the agents and
server. Rerun these evals in such a session before tuning the description.

**End-to-end runs through MCP, 2026-11-15.** Three runs of the eval-1
shape, made from the parent session with a plain script (Claude Code
2.1.325, `claude -p "/extract-claims" --model sonnet`), since the loop's
guards refuse a nested session inside a recorded spike. The project was
kmaudit's test fixture repository
(`packages/kmaudit/tests/fixtures/audit_repo.py`, 2 concepts, 4 sections),
with this skill in `.claude/skills/`, `kmaudit-claims-extractor` in
`.claude/agents/`, the kmaudit server from this tree in `.mcp.json`, and
`--allowedTools` naming the three claims tools, Read, Grep, Glob and Agent.
The script passes only when the agent was dispatched, it called
`claims_submit`, nothing called Bash, claims are stored and fewer sections
are pending than before.

- Runs 1 and 2: the agent stored all 4 sections through `claims_submit`
  with no shell (3 point and 1 subjective claim, 0 pending after). Run 1's
  pass/fail line was wrong (the script misread `claims_list`'s JSON); run 2
  failed it honestly: the main session ran one `ls` to see which folders
  exist before choosing `.okf`.
- The skill then gained one sentence: with no folder named, call
  `claims_todo` on the repository root's `.okf` straight away.
- Run 3: passed. One dispatch, two `claims_submit` calls inside the agent,
  no Bash anywhere, 4 claims stored, 0 pending.

write-checks and the no-agent eval were not run.
