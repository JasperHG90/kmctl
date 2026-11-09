---
type: plan
title: 'Plan: scaffold-init'
description: "kmctl init sets up docs/ and .okf/ in a repository, without touching anything that already exists."
slug: scaffold-init
epic: cli
depends_on: []
priority: 4
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:20+00:00'
---

# scaffold-init

Relayed from: none

## Intent

`kmctl init` creates, in the target repository, docs/README.md and an .okf/ bundle (`index.md` with `okf_version`, `log.md`, a `manifesto.md` stub) and prints what it created. Diataxis folders and `.okf/` sections are created by the verbs that add their first page, not here, so no empty folders. It never overwrites a file, and running it twice changes nothing the second time.

Done when tests show a first run creates the files, a second run changes nothing, and the result passes the okf validator.

The okf validator in tests is a pinned, test-only copy of `okf_validate.py` from okf-skills 0.10.1 (MIT), kept with its licence under tests/vendor/ and run in strict mode with pyyaml as a dev dependency. The first ticket that needs it adds it. It checks conformance only; the plugin still gets OKF authoring from the okf dependency (ADR 0003).

## Could invalidate this plan

- none
