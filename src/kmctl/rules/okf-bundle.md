# The OKF bundle

<constraint name="start-at-the-index">
WHY: grepping a bundle finds words, not the concept that owns them.

Start at .okf/index.md and follow links. One concept is one file, named in
kebab-case for an entity, never a change. Prefer updating a concept to adding
a neighbour.
</constraint>

<constraint name="kmctl-writes-the-structure">
WHY: hand-written front matter and index lines drift from the format checks read.

Create concepts with kmctl new; it writes front matter, the index entry and
the log line, and you write the prose. After any hand edit to an index, run
kmctl check.
</constraint>

<constraint name="every-touched-concept-is-logged">
WHY: a log that misses changes reads as complete and is not.

A change that touches a concept appends a dated line to .okf/log.md naming
its id in backticks. Never rewrite an earlier line.
</constraint>

<constraint name="decisions-are-never-rewritten">
WHY: a rewritten decision hides the reasoning that was acted on.

Record a decision when it is made, with the alternative it rejected. Correct
it with an appended dated section; reverse it with a new record that
supersedes it.
</constraint>

<constraint name="trust-is-recorded">
WHY: an agent's summary read as checked fact spreads its mistakes.

An agent records itself in generated.by and leaves the concept unverified.
Only a person who checked the content adds a verified entry. Treat
unverified or stale concepts as leads, not facts.
</constraint>
