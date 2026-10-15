---
type: verdict
title: 'Verdict: prototype-check plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of prototype-check: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:12:37+00:00'
slug: prototype-check
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan is small and its approach works: a presence check for README.md per prototype folder, added to the kmctl check command that knowledge-check builds. Its one open risk is scope: "every folder under" reads as recursive, which would flag every real prototype with subfolders. Once the plan says direct children only and adds a nested-folder fixture, it can go ahead.

## Checked

- The plan's risk list is "none"; there is no spike or operator acceptance to weigh.
- The repo: src/kmctl has only __init__.py, so kmctl check does not exist yet; the plan rightly depends on knowledge-check, whose plan says later checks (links, prototypes) add to that command.
- The manifesto names prototypes/ as an .okf/ section, and the new-concept-verbs plan writes a prototype as a folder with README.md, so the two plans agree on the shape.
- The okf validator (plugin okf 0.10.1, skills/validate/scripts/okf_validate.py) treats every non-reserved .md file as a concept and checks its front matter, but never checks that a folder has a README.md. So this check does not repeat the validator, as knowledge-check requires.

## Findings

- p1: the contract does not say whether nested folders count. Read recursively, the check fails on real prototypes with code subfolders, and the planned flat fixtures would not show it.

## Notes

The eval has no rows yet. The front matter checks on README.md belong to the okf validator, so this check should only test that the file exists.
