# handoff: skill-creator results

Made with the skill-creator skill (ADR 0007). The two prompts in `evals.json`
ran against a scratch repository set up with `kmctl init`, with the skill and
without it. Workspace: iteration-1, graded by reading each run against the
`expectations`.

| Run | Created with kmctl new handoff | --key only when set | Sections name the real work | kmctl check | Tool calls, seconds |
|---|---|---|---|---|---|
| new session, with skill | yes | yes | yes, and says what the session never named instead of guessing | pass | 7, 41 s |
| new session, baseline | yes (found it in --help) | yes | yes; filled the sections with a Python edit | pass | 7, 51 s |
| same session, with skill | updated in place | yes | yes | pass | 7, 41 s |
| same session, baseline | updated in place | yes | yes, but re-ran the update and then deleted a log line by hand | pass | 6, 46 s |

The baseline's repeat run exposed a kmctl gap: a second keyed update wrote a
duplicate log line. kmctl now adds no line identical to the last one
(`tests/test_handoff_key.py::test_repeated_update_logs_once`).
