# write-docs: skill-creator results

Made with the skill-creator skill (ADR 0007). The four prompts in
`evals.json` are one request of each Diataxis type, run against a copy of this
repository set up with `kmctl init`, with the skill and without it.

## Iteration 1

Scripted checks (the `expectations` in `evals.json`, run by `grade.py` here:
page in the right type folder, listed in docs/README.md, `kmctl check` passes,
no page outside a type folder): 4/4 with the skill and
4/4 without, so those checks do not tell the two apart here. This repository's
`kmctl --help` and rules already lead an agent to `kmctl new doc`.

Read by hand, the pages written with the skill kept closer to their type: the
how-to was 370 words against 590, the explanation carried a Limits section and
links to its decisions, and the baseline tutorial pasted whole files, with
their headings, into the page. Both tutorial runs guessed a wrong install URL.

## Iteration 2

Change: step 4 now says to run the page's commands in a scratch copy and never
to guess a fact the repository does not hold (install URL, package name,
version), writing a TODO instead. Rerun of the tutorial prompt: the agent took
the install command from plugin/hooks/hooks.json and left a TODO where the
repository has no source.
