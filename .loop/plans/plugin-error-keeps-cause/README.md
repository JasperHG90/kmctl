---
type: plan
title: 'Plan: plugin-error-keeps-cause'
description: "When a claude plugin command fails, kmctl's error names the line that says why (a git fatal or error line, such as Could not resolve host) instead of only claude's last stderr line, so an offline install no longer reads as an access-rights problem."
slug: plugin-error-keeps-cause
epic: plugin
depends_on: [network-tests-retry]
priority: 6
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261015
  at: '2026-10-15T19:23:11+00:00'
---

# plugin-error-keeps-cause

Relayed from: network-tests-retry's build, which found that in a full GitHub outage claude 2.1.300 tries HTTPS, falls back to SSH, and ends its stderr with SSH's "Please make sure you have the correct access rights / and the repository exists"; `_require` in `src/kmctl/plugin.py` keeps only that last line.

## Intent

`_require` turns a failed `claude plugin ...` call into a `PluginError` holding claude's last stderr line. When the last line is the cause, that is enough. When claude retries over SSH, the line that names the cause (git's `fatal: unable to access '...': Could not resolve host: github.com`) comes earlier, and the operator sees an access-rights message for what is a network outage. The integration tier's retry (network-tests-retry) also misses that path, since it looks for git's network wording in the report.

- `_require` keeps, in the order claude printed them, every stderr line that starts with git's `fatal:` or `error:`, and claude's last line if it is not one of them, joined with "; ", capped at a few hundred characters. With no such lines it keeps the last line, as now.
- The message still ends with "run it by hand to see why, then kmctl plugin install again", and still names the command that failed.
- The marketplace-mismatch check (`_MISMATCH`) still matches, since it reads claude's full output, not the message.

Measured: in the SSH-fallback path, 0 of 1 kmctl messages name the network cause today (network-tests-retry's build); in the HTTPS-only path, 1 of 1 do (spike:network-tests-retry/1).

Done when a test with a stub claude whose stderr is HTTPS's `fatal: ... Could not resolve host`, then SSH's two access-rights lines, gives a PluginError naming "Could not resolve host" and the SSH line; one whose stderr has a single last line gives that line as now; a long stderr is cut to the cap; the integration tier's retry then fires on the SSH-fallback path (a test with a stub claude in the integration tier); and the other plugin tests pass.

## Could invalidate this plan

- none
