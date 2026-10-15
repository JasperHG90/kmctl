---
name: interface-audience
description: Design every interface for a named audience — human, script, agent, or calling code — because the same information needs a different shape for each. Read before designing a CLI, an API, a library's public surface, an agent tool, or an error message.
---

<constraint name="name-the-audience">
Before designing anything another party consumes — a CLI, an HTTP or library
API, an agent tool, a config format, an error message — name who consumes it.
If more than one audience does, name them all. An interface built without that
answer defaults to serving whoever the author was imagining, and everyone else
works around it.
</constraint>

Audiences differ in what they can do with what you give them, so the same
information needs a different shape for each:

| Audience | Can do | Needs |
|---|---|---|
| A human, live | Read prose, notice colour, answer a prompt, guess | Discoverability, readable formatting, forgiving errors that say what to do next |
| A script or CI job | Parse, branch on exit codes | Stable output shapes, stable exit codes, no prompts, no colour |
| An agent | All of the above, plus read the docs at runtime | Self-describing help, machine-readable errors, no path that requires a human |
| Calling code | Import and call | Typed signatures, real exceptions, no I/O or `sys.exit` buried in the logic |

The recurring failure is a single surface that silently assumes one of these.
Progress bars written to stdout break the pipe. A prompt with no `--yes` hangs
CI. An error that says "invalid configuration" without naming the key leaves a
human guessing and gives an agent nothing to act on. Logic reachable only
through a command body cannot be called by anything else.

<constraint name="human-default-machine-escape">
Serve multiple audiences from one surface rather than forking the tool: a
human-friendly default plus a machine-readable escape hatch. A formatted table
by default and `--json` on request; a rendered error plus a stable error code.
Two audiences, one code path, one set of behaviour to keep correct.
</constraint>

Help text is the interface an agent reads before it acts, which makes
completeness a functional requirement rather than a courtesy. Everything a
caller needs — what a parameter means, what values it accepts, where it can come
from — belongs in the interface itself, not in a README they may never see.

Say what the audience needs to know in the terms they use, per the
plain-language rule. Serving an audience well and writing plainly are the same
skill applied at two scales.

<example name="asking-the-question">
Adding `--verbose` to a data-export command: who runs it? A human debugging a
failed export — so the extra detail goes to stderr, keeping the exported data on
stdout clean for the script that consumes it. One question, and the design
decides itself.
</example>
