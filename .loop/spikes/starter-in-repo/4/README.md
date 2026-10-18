---
type: spike
title: Spike starter-in-repo/4
description: do uv and APM 0.33.0 follow a git url.insteadOf rewrite of https://github.com/JasperHG90/kmctl to a local http:// git server?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T09:58:21+00:00'
slug: starter-in-repo
n: 4
outcome_written: true
---

# Spike starter-in-repo/4

do uv and APM 0.33.0 follow a git url.insteadOf rewrite of https://github.com/JasperHG90/kmctl to a local http:// git server?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike2/spike-http.sh
```

## Outcome

With a scratch HOME and GIT_CONFIG_GLOBAL holding `url."http://127.0.0.1:PORT/o/kmctl.git".insteadOf` for both `https://github.com/JasperHG90/kmctl.git` and `https://github.com/JasperHG90/kmctl`, uv follows the rewrite: `uv tool install --force git+https://github.com/JasperHG90/kmctl@v0.5.1` and `uvx --from` it both built the served copy (marker file present; the server logged 6 info/refs and 15 upload-pack requests).
APM 0.33.0 refuses it before any request: "HTTPS Git remote must not rewrite to insecure HTTP" (exit 1). Its code (apm_cli/utils/git_env.py, validate_resolved_git_url_rewrite) hard-codes this with no env var or config to allow it, and also refuses any rewrite to a different network host, so a local http or https server cannot work for APM.
Does not settle risk 2 by itself; spike:starter-in-repo/5 shows a file:// rewrite does.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-http.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike2/spike-http.sh`, which the command used
