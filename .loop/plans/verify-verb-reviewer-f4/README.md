---
type: plan
title: 'Plan: verify-verb-reviewer-f4'
description: Deferred hardening from verify-verb, reviewer finding f4 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T21:40:07+00:00'
slug: verify-verb-reviewer-f4
status: draft
epic: knowledge
depends_on: []
priority: null
---

# verify-verb-reviewer-f4

Relayed from: verify-verb, reviewer finding f4 in review round 1

## Intent

A trailing comment on the verified line ('verified:  # checks' over a block list, or 'verified: []  # none') makes _with_entry refuse, telling the person to rewrite it as a block list it already is. Strip a trailing ' #...' comment from rest before classifying it, or name the comment in the refusal. at src/kmctl/verify.py:66.

## Could invalidate this plan

- none
