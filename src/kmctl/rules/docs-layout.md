# docs/ and .okf/

<constraint name="audience-picks-the-folder">
WHY: a spike or a handoff in docs/ reads as current instructions to a user.

docs/ is for people who use the project; .okf/ is for people and agents
working on it. A decision, proposal, prototype, audit or handoff goes in
.okf/, even when it reads like a guide.
</constraint>

<constraint name="docs-sorted-by-reader-intent">
WHY: a page filed under the wrong heading is read by the wrong person.

Each docs/ page has one Diataxis type: tutorials/ (a lesson that works in
one sitting), how-to/ (one task, one way), reference/ (facts, no
instructions), explanation/ (why it is shaped this way). Two intents in one
page means two pages.
</constraint>

<constraint name="docs-describe-what-exists">
WHY: a page about a command that does not exist yet is a hallucination.

A docs/ page lands in the same change as the behaviour it describes. Until
then the design lives in .okf/.
</constraint>

<constraint name="prototypes-hold-their-scripts">
WHY: a number is only evidence if someone can re-run it.

A prototype is one folder in .okf/prototypes/ with its README.md, every
script behind a number in it, and the raw results. Never run analysis inline
or from a scratch folder.
</constraint>
