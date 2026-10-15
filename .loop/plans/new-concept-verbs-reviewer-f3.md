---
type: plan
title: 'Plan: new-concept-verbs-reviewer-f3'
description: Deferred hardening from new-concept-verbs, reviewer finding f3 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:48:37+00:00'
slug: new-concept-verbs-reviewer-f3
status: draft
epic: cli
depends_on: []
priority: null
---

# new-concept-verbs-reviewer-f3

Relayed from: new-concept-verbs, reviewer finding f3 in review round 1

## Intent

A --description holding a newline is written as is into the section index, splitting the entry across lines. at src/kmctl/concepts.py:140.

## Could invalidate this plan

- none
