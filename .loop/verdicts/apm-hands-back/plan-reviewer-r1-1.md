---
type: verdict
title: 'Verdict: apm-hands-back plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of apm-hands-back: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T12:56:53+00:00'
slug: apm-hands-back
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The three listed risks are settled by spikes whose evidence answers them:
sub-packages split by harness, agy loading the workspace hook and MCP files,
and APM's behaviour over a kmctl-written install. Source reading turned up
one gap that could break the plan. Install still supports `--scope user`
for Claude Code, and the plan drops kmctl's own hook and MCP writing without
saying, or showing, that `apm install -g` delivers them there (p1). That
needs a spike and a sentence in the plan, not a rethink. Verdict: fail.

## Checked

- Spike 1 (script, stdout, run.json): one `{git, path: apm, ref}` entry
  pulled `./claude` and `./antigravity` sub-packages. Each harness got only
  its own rule and hook. The agy rule came out as
  `globs: "**/docs/**, **/.okf/**"`, okf-bundle reached `.mcp.json` and
  `.agents/mcp_config.json`, and uninstall removed the rules, skills and
  hooks. This answers risk 1.
- Spike 2: agy 1.4.0 ran a workspace `.agents/hooks.json` hook named `apm`
  and a workspace `okf-bundle` server, with no plugin folder. It used the
  launcher with PLUGIN_ROOT unset, so the start folder was $PWD, the same
  as the plan's plain launcher. `kmctl briefing --format antigravity` reads
  the repository from the hook's stdin `workspacePaths`, so the folder the
  hook runs in does not matter. This answers risk 2.
- Spike 3: APM kept the Claude guard, the agy briefing and the agy Stop
  wrapper (`cd ..`) byte for byte. It left two SessionStart groups, and it
  skipped an existing okf-bundle while still recording it in the lock. This
  answers risk 3, and the plan's migration steps follow from it.
- APM 0.33.0 source:
  - `install/target_filter.py`: package `targets:` only narrow. A
    claude-only consumer gets a "do not overlap ... skipping" warning for
    `./antigravity`, not an error, and kmctl's SKIP_LINE check does not
    match that line.
  - `mcp_integrator_install._resolve_target_runtimes`: an explicit
    `--target` bypasses runtime discovery, so MCP is written even when
    `.claude/` or `.agents/` is missing.
  - `_install_self_defined_deps`: drift is detected only against the lock's
    stored config, never the file. That confirms an older okf pin already in
    `.mcp.json` stays until kmctl removes it, as the plan says.
  - `exec_gate.check_executable_approval`: hooks and MCP are allowed by
    default unless the consumer's apm.yml has an `allowExecutables` block.
- kmctl code: `antigravity.drop_apm_okf_stop` matches any command holding
  `okf-stop-check.sh`, which kmctl's own wrapper also contains. The plan
  already narrows it to the exact command. The user-scope paths are
  `plugin.install_mcp`, `settings_path` and `_preflight`, which refuses
  antigravity at user scope.

## Findings

- p1: the plan does not cover user scope. kmctl stops writing the hook and
  MCP server at every scope, but only project-scope delivery by APM has been
  shown. Settle it with the spike named in the finding, then state the
  user-scope behaviour and its migration in the plan.

## Notes

- Agy rules now come from the workspace `.agents/rules/`, not the plugin
  folder. The live glob evidence (spike:antigravity-rules/3) used
  plugin-folder rules. ADR 0016 records agy parsing (and refusing) APM's
  `.agents/rules/` files, so agy does read that folder. A `**/x/**` glob
  matches both relative and absolute paths, so I do not count this as a
  risk. The end-to-end check will catch it if it is wrong.
- A consumer whose apm.yml has an `allowExecutables` block gets no kmctl
  hook or server from APM, where today kmctl writes them anyway. Doctor
  would report it. Worth a line in the new ADR.
- Spike 1 did not check that `apm uninstall` removes okf-bundle from both
  MCP files, which the success criterion needs. Because APM records a
  skipped, pre-existing okf-bundle as its own (spike 3), uninstall may also
  remove a server the user wrote.
- The eval has no rows yet.
