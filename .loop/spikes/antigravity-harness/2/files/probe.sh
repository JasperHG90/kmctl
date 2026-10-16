#!/usr/bin/env bash
# Does agy 1.4.0 discover a plugin placed in a workspace's .agents/plugins/<name>/?
# Offline only: `agy agents` lists agents from discovered customizations,
# including agents shipped inside plugins. Exits 0 when the plugin's agent
# is listed from a trusted workspace (repo root and a subfolder).
set -u
AGY=${AGY:-$HOME/.local/bin/agy}
T=$(mktemp -d); R=$T/repo; export HOME=$T/home; mkdir -p "$HOME"
P=$R/.agents/plugins/kmctl
mkdir -p "$P/agents" "$R/sub"; git -C "$R" init -q
echo '{"name":"kmctl"}' > "$P/plugin.json"
echo '{"kmctl-briefing":{"SessionStart":[{"type":"command","command":"echo {}","timeout":10}]}}' > "$P/hooks.json"
printf -- '---\nname: kmctl-probe\ndescription: probe agent\ntools: [view_file, grep_search]\n---\nYou probe.\n' > "$P/agents/kmctl-probe.md"

echo "== agy $("$AGY" --version 2>/dev/null | head -1)"
echo "== validate"; "$AGY" plugin validate --strict --json "$P"
echo "== plugin list (installed plugins only?)"; (cd "$R" && timeout 30 "$AGY" plugin list --json)
echo "== agents, workspace untrusted"; U=$(cd "$R" && timeout 30 "$AGY" agents); echo "${U:-<none>}"
mkdir -p "$HOME/.gemini/antigravity-cli"
echo "{\"trustedWorkspaces\": [\"$R\"]}" > "$HOME/.gemini/antigravity-cli/settings.json"
echo "== agents, workspace trusted, cwd=repo root"; A=$(cd "$R" && timeout 30 "$AGY" agents); echo "${A:-<none>}"
echo "== agents, workspace trusted, cwd=repo/sub"; B=$(cd "$R/sub" && timeout 30 "$AGY" agents); echo "${B:-<none>}"
echo "== no user-level plugins exist:"; ls "$HOME/.gemini/config/plugins" 2>&1
grep -qx kmctl-probe <<<"$A" && grep -qx kmctl-probe <<<"$B"
