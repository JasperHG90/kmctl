# continue: skill-creator results

Made with the skill-creator skill (ADR 0007). The three prompts in `evals.json`
ran against scratch repositories. Iteration 1 used one with four live handoffs
(empty sections) and one expired, and one with none. Iteration 2 used four live
handoffs with their sections filled in. The runs had no AskUserQuestion, so the
skill's text fallback is what ran.

## Iteration 1

| Run | Listed through kmctl handoffs --json | Expired one left out | Acted before the user chose | Tool calls, seconds |
|---|---|---|---|---|
| four handoffs, with skill | yes | yes | no; listed and stopped | 4, 22 s |
| four handoffs, baseline | yes, after reading every handoff file and git | yes | read all four files before any choice | 6, 35 s |
| none, with skill | yes | n/a | no; said none and suggested /handoff | 4, 19 s |
| none, baseline | yes, after ls, git, find, briefing and review due | n/a | no; offered three options | 6, 36 s |

In iteration 1 the pick run listed all four handoffs as text, which fails
expectation 2 (three plus `more`): the fallback for no AskUserQuestion did not
keep the limit, and no run reached step 3.

## Iteration 2

Change: the text fallback offers the same three plus `more`, and a message that
already names the handoffs skips the question. The handoffs in the fixture had
real content this time.

| Run | Expectations | Tool calls, seconds |
|---|---|---|
| `/continue` (four handoffs) | 3/3: listed through kmctl, three newest plus `more`, read nothing and stopped | 4, 20 s |
| `/continue the parser refactor and the CI action ones` | 3/3: read only those two, one brief with where each stands, how they connect and next steps, ended with the question | not recorded |

The pick through AskUserQuestion itself was not exercised: the eval runner has
no AskUserQuestion, so the text fallback is what ran.
