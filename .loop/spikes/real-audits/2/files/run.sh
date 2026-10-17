#!/usr/bin/env bash
# Live run of the citation-validator prototype on /home/vscode/kmctl with Gemini Flash.
# Exits 0 only when the run finished with a report inside the request cap.
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-real-audits
cd /home/vscode/kmctl
rm -rf "$S/out"
AUDIT_API_KEY="$(bash -ic 'printf %s "$GEMINI_API_KEY"' 2>/dev/null)" \
  env -u GH_TOKEN -u GITHUB_TOKEN uv run --script "$S/agent.py" run \
  --model gemini-3.8-flash \
  --base-url https://generativelanguage.googleapis.com/v1beta/openai/ \
  --api-key-env AUDIT_API_KEY --repo /home/vscode/kmctl --timeout 20m --out "$S/out"
code=$?
echo "--- report.md"; cat "$S/out/report.md" 2>/dev/null
exit $code
