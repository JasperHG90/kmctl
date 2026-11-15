---
type: note
title: "Audit agent config requirements"
description: "What the audit agent's TOML config file should support: providers per agent, extra skips, telemetry."
tags: [prototype]
generated:
  by: human:jasperginn
  at: 2026-11-05
---

Configuration file should be TOML, and should:

- Take multiple providers, and be configurable per agent which provider/model is being used (also type I or II)
- Should have extend_skip or something to skip folders next to e.g. .git folder
- Should also have extend_skip or something for certain file types that should always be ignored (e.g. *.pyc)
- Should support telemetry by default.
