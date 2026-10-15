# Why one hook and report-only audits

## The question

kmctl exists to keep a repository's knowledge true. So why does its plugin do
so little? It has one hook, which prints a briefing when a session starts and
never stops anything, and its audit reports what is wrong but fixes nothing.
This page explains why kmctl stops there.

## How it works

**The briefing.** When a Claude Code session starts, the plugin's only hook
runs `kmctl briefing` and passes its output into the session. The briefing
says where each kind of knowledge lives (`docs/` for people who use the
project, `.okf/` for people and agents working on it), lists what is due for
review and which handoffs are live, and gives the rules for writing knowledge.
The hook always exits 0: if kmctl is missing or fails, it prints a one-line
note and the session goes on.

Because the hook prints whatever the CLI prints, upgrading kmctl updates the
briefing. The plugin carries no copy of the rules to drift out of date.

**The audit.** A separate agent checks the knowledge that is due: architecture
pages against the code, decisions against later decisions and the code,
practices against the evidence they cite. You can ask for it in a session
(`/audit`), or turn it on in CI as described in
[Install the plugin and the CI action](../how-to/install-the-plugin-and-the-ci-action.md).
The auditor has only read and search tools. In CI it runs with the same
limit, and its findings go to the job summary and one "Knowledge audit" issue.
It never edits `docs/` or `.okf/`, and it never marks a concept as verified.

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

**Why there is only one hook.** Three more hooks were considered and rejected
([ADR 0004](../../.okf/decisions/0004-sessionstart-is-the-only-hook.md)):

- a nudge after each code edit, naming the pages that describe that file;
- a reminder when a session stops, if covered code changed;
- a gate that refuses a commit until the pages describing the changed code
  are verified.

The commit gate shows the cost best. A refactor changes code without making
any page wrong, so the gate would refuse often for nothing, and people learn
to work around a gate like that. kmctl adds a hook or a gate
only when a count shows it catches something.

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
