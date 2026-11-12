# write-checks: skill-creator results

Made with the skill-creator skill (ADR 0007), together with the
`kmctl-check-writer` agent, on 2026-11-11 (ticket agent-audit-checks-skill).
In these runs the main session did the skill's steps (todo, batch, report)
itself, and the agent ran as a real subagent on `model: haiku` from
`apm/.apm/agents/kmctl-check-writer.md`, with Read and Bash only.

## Iteration 1

**Eval 2, claims the repository lacks** (run first). The repository was the
extract-claims eval's: 22 checkable claims, 19 of them from a copy of ADR
0005, which describes `action.yml`, `action/agent.py` and review skills the
fixture does not have. Two claims of `.okf/tool.md` already had a check
and a reason from the extract-claims smoke test, which the agent left
alone. For the other 20 it stored 12 checks (exact 11, proxy 1) and 8
reasons with no refusal; afterwards `kmctl audit checks todo` reported 22
checkable claims, 13 checks, 9 reasons and 0 to check, in 15 tool calls, 80k tokens and 83 s. It marked
12 checks as drift, each on a file the fixture lacks, rather than bending
them until they held. Its reply carried a few lines after the summary, so
the agent's last instruction now says nothing may follow it.

**Eval 1, code-backed claims.** Three claims stored with the fixture
helper: "The CLI writes out.txt.", "The CLI exits 1 when given more than
one argument." and "The store is SQLite." The agent stored 3 checks, all
exact, in 8 tool calls, 58k tokens and 36 s, and replied with the two
summary lines only. The two true claims hold with code steps
(`open("out.txt", "w").write("hi")` and `if len(sys.argv) > 2: $$$B`), each
noticing 2 of 6 changes. The SQLite claim was stored as drift: no tracked
file mentions SQLite. Afterwards `todo` reported 0 to check and `git status
--porcelain` was empty.

**Eval 3, no claims yet.** On a fresh fixture repository with no stored
claims, `kmctl audit checks todo` printed `0 checkable claims: 0 checks, 0
reasons, 0 to check`, so step 1 sends the user to `/extract-claims` before
any agent is dispatched. Only the CLI step ran; no agent was needed.

These runs played the main session's part by hand, so the plan's outcome in
a real Claude Code session (its transcript holds the summaries but no step)
is shown only through the agent's replies, not a `/write-checks` run.

**Baseline.** Not run: without the skill, a session that knows the verbs
does the same work in its own context, as the extract-claims baseline
showed for claims. The skill's point is the context it keeps out.

## Description

The first sentence is the briefing line and stays short: with this skill
and extract-claims, the worst-case briefing test
(`tests/test_briefing.py`) still passes. The trigger optimisation loop
(`run_loop`) did not run for this ticket.
