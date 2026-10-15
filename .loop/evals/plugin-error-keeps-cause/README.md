---
type: eval
title: 'Eval: plugin-error-keeps-cause'
description: 'Definition of done for plugin-error-keeps-cause: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261015
  at: '2026-10-15T19:23:13+00:00'
slug: plugin-error-keeps-cause
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 0db444128d81f03a694708024599b37a7b78e061481b484f856b815b5486819d
  at: '2026-10-15T19:23:13+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: A failed claude plugin command's PluginError names every git fatal: or error: line from claude's stderr, in order, plus claude's last line, joined with '; '.
  Fails when: with a stub claude printing HTTPS's 'fatal: unable to access ...: Could not resolve host: github.com' then SSH's access-rights lines, the message lacks 'Could not resolve host' or the SSH line, or puts them out of order
- r2: With no git fatal: or error: lines, the message keeps claude's last line as now; a long stderr is cut to the cap; the message still names the command and ends with the fix line.
  Fails when: a single-line failure's message differs from today's, a long stderr makes a message over the cap, or the command or the 'run it by hand' fix is missing
- r3: The integration tier's retry fires on the SSH-fallback path.
  Fails when: an integration-marked test whose install fails twice with the SSH-fallback stderr and then passes is reported as failed
- r4: The other tests still pass.
  Fails when: uv run pytest or uv run pytest -m integration fails
