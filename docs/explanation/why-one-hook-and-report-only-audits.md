---
description: "Why kmctl's only hooks are the session briefing and the summary nudge, and why audits only report."
---

# Why two hooks and report-only audits

## The question

kmctl exists to keep a repository's knowledge true. So why does what it
installs do so little? Its own hooks print a briefing when a session starts
and, in Claude Code, a one-line nudge when a concept changes after the
summary; neither stops anything. Its audit reports what is wrong but fixes
nothing. (In Antigravity it also relays okf's opt-in Stop check, which is
okf's, not kmctl's; see below.)
This page explains why kmctl stops there.

## How it works

**The briefing.** When a Claude Code session starts, kmctl's own hook, which
APM installs from kmctl's package, runs
`kmctl briefing` and passes its output into the session. The briefing
says where each kind of knowledge lives (`docs/` for people who use the
project, `.okf/` for people and agents working on it), lists what is due for
review and which handoffs are live, lists the skills, and gives the one rule
for reading knowledge. The rules for writing knowledge reach the agent from
`.claude/rules/`, where APM installs them.
The hook always exits 0: if kmctl is missing or fails, it prints a one-line
note and the session goes on.

Because the hook prints whatever the CLI prints, upgrading kmctl updates the
briefing. The hook carries no copy of the briefing to drift out of date.

**The summary nudge.** In Claude Code, a second hook runs after every Write,
Edit, MultiEdit and Bash call (a PostToolUse hook). It runs
`kmctl summary nudge`, which asks git whether a concept in `.okf/` changed after
`.okf/summary.md`. When one did, the agent reads one line naming the changed
concepts and its two ways out: update the summary, or run `kmctl summary ack`
when it still holds. Changes to `log.md`, an index, a handoff or the summary
itself never count. It names each set of changes once, so the next tool call
on the same set is quiet, and it never writes `.okf/`. It exits 0 when
kmctl is missing or fails, as the briefing's hook does, but where that hook
prints how to install kmctl, the nudge prints only `{}`, so a tool call gets
no extra text.

**The audit.** A separate agent checks the knowledge. In a session, `/audit`
checks what is due: architecture pages against the code, decisions against
later decisions and the code, practices against the evidence they cite. That
auditor has only read and search tools. In CI, turned on as described in
[Install the plugin and the CI action](../how-to/install-the-plugin-and-the-ci-action.md),
an agent runs three audits: `.okf/` against the code, `docs/` against the
code, and `docs/` against `.okf/`. It can also run shell commands, so it can
use the scripts skills ship. Each audit's findings go to the job summary and
to that audit's own issue. Neither edits `docs/` or `.okf/`, and neither
marks a concept as verified.

**The free checks.** What a script can check, `kmctl check` checks on every
pull request: indexes agree with their folders, prototypes have a
`README.md`, links resolve. These cost nothing to run and fail the job when
they fail. Concepts that are due for review are reported, never failed.

## Why it is this way

**No hook can tell whether knowledge is still true.** Whether an architecture
page still matches the code is a judgment, not a rule a script can run. So
kmctl does the two things it can do well: it puts the right knowledge in front
of the agent at the start of every session, and it lets a separate agent
judge, on request.

**Why the briefing is injected, not linked.** A page that tells agents how to
manage knowledge is read only by an agent that already knows to look for it.
Native rule files work only in some harnesses, each with its own format. Every
harness that can run a command at session start can print the briefing
([ADR 0002](../../.okf/decisions/0002-briefing-and-rules-injected-by-the-cli.md)).
For Claude Code, kmctl's package also puts the knowledge rules in
`.claude/rules/` (APM installs it, [ADR 0014](../../.okf/decisions/0014-apm-is-the-only-install-route.md),
[ADR 0021](../../.okf/decisions/0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest.md))
and `kmctl init` writes a kmctl block into `CLAUDE.md`, because the briefing
alone left agents writing no architecture pages. The briefing now carries
only the one rule those files lack
([ADR 0011](../../.okf/decisions/0011-kmctl-init-writes-knowledge-rules-and-a-claude-md-block-for-claude-code.md)).

**Why there are only two hooks.** Three more hooks were considered and
rejected
([ADR 0004](../../.okf/decisions/0004-sessionstart-is-the-only-hook.md)):

- a nudge after each code edit, naming the pages that describe that file;
- a reminder when a session stops, if covered code changed;
- a gate that refuses a commit until the pages describing the changed code
  are verified.

The commit gate shows the cost best. A refactor changes code without making
any page wrong, so the gate would refuse often for nothing, and people learn
to work around a gate like that. kmctl adds a hook or a gate
only when a count shows it catches something.

The summary nudge is not the rejected code-edit nudge. It watches the bundle,
not the code, and the rule it applies is a fact git can check: a concept
changed after the summary did. One in six of this repository's Write, Edit,
MultiEdit and Bash calls touches `.okf/`, and the briefing reports a stale
summary only at the next session start. The operator asked for it "Not at
the end of a turn. Just when anything in .okf changes", so it is a PostToolUse
hook, not a Stop reminder
([ADR 0028](../../.okf/decisions/0028-two-hooks-the-session-briefing-and-the-summary-nudge.md)).
It runs the `kmctl` on PATH rather than the release the project pins, because
starting the pinned copy through uvx after every tool call would be too slow
for a hook.

One Stop hook does ship, for Antigravity only, and it is okf's, not kmctl's.
okf's package has an opt-in check that can send the agent back to work at
the end of a turn while a bundle's `.okf/index.md` sets `upkeep: enforced`.
APM's copy of it cannot run in Antigravity, so kmctl relays it there and
changes nothing about what it checks
([ADR 0018](../../.okf/decisions/0018-kmctl-runs-okf-s-stop-check-for-antigravity.md)).

**Why the audit only reports.** An agent that both judges the knowledge and
edits it can quietly make the knowledge agree with itself. Keeping the audit
read-only means every change still passes a person, or an agent the person
asked
([ADR 0005](../../.okf/decisions/0005-audits-report-only.md)). The rejected
alternative was letting the audit write `verified` stamps on concepts that
pass; that would make a model's opinion look like a person's check.

**Why the audit is opt-in in CI.** The checks mode costs nothing, so it runs
on every pull request. Audit mode sends the repository to a model with your
API key, so it runs only when you add it, and only by hand or on a schedule.
It refuses to run on a pull request, so code from a pull request or a fork
never reaches the key.

**The limits.** Nothing here forces knowledge to stay true. An agent can read
the briefing and still forget to update a decision; a pull request can pass
`kmctl check` with a stale architecture page; an audit can miss drift or
report drift that is not there. kmctl makes stale knowledge visible and
cheap to find. A person still decides what to fix.

For the commands themselves, see [Commands](../reference/commands.md).
