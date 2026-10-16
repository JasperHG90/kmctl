#!/usr/bin/env bash
# Does a workspace plugin's SessionStart hook fire and its MCP server start
# under agy 1.4.0, and with which cwd / PLUGIN_ROOT? Builds a scratch repo
# with .agents/plugins/probe/, trusts it in a scratch HOME, runs agy commands
# that load the workspace, then shows what the hook and MCP scripts logged.
# Exits 0 only when both hook.log and mcp.log appear.
set -u
AGY=${AGY:-/home/vscode/.local/bin/agy}
REAL_HOME=$HOME
T=$(mktemp -d); R=$T/repo; O=$T/out; export HOME=$T/home
mkdir -p "$HOME/.gemini/antigravity-cli" "$O" "$R/.agents/plugins/probe"; git -C "$R" init -q
P=$R/.agents/plugins/probe

cat > "$T/hook.sh" <<H
#!/usr/bin/env bash
{ echo "== hook fired \$(date +%T) argv: \$*"; echo "pwd: \$(pwd)"
  echo "-- env (selected)"; env | grep -E '^(PLUGIN|ANTIGRAV|GEMINI|AGY|CLAUDE|PWD|WORKSPACE|EXTENSION)' | grep -viE 'key|token|secret'
  echo "-- env var names"; env | cut -d= -f1 | sort | tr '\n' ' '; echo
  echo "-- stdin"; timeout 3 cat; echo; } >> "$O/hook.log" 2>&1
echo '{}'
H
cat > "$T/mcp.sh" <<M
#!/usr/bin/env bash
{ echo "== mcp started \$(date +%T)"; echo "pwd: \$(pwd)"
  i=0; for a in "\$@"; do i=\$((i+1)); echo "arg\$i: [\$a]"; done
  echo "-- env (selected)"; env | grep -E '^(PLUGIN|ANTIGRAV|GEMINI|AGY|CLAUDE|PWD|WORKSPACE|EXTENSION)' | grep -viE 'key|token|secret'
  echo "-- env var names"; env | cut -d= -f1 | sort | tr '\n' ' '; echo; } >> "$O/mcp.log" 2>&1
sleep 5
M
chmod +x "$T/hook.sh" "$T/mcp.sh"
echo '{"name":"probe"}' > "$P/plugin.json"
echo "{\"probe\": {\"SessionStart\": [{\"type\":\"command\",\"command\":\"$T/hook.sh\",\"timeout\":10}]}}" > "$P/hooks.json"
echo "{\"mcpServers\": {\"probe\": {\"command\": \"$T/mcp.sh\", \"args\": [\"\$PLUGIN_ROOT\", \"\${PLUGIN_ROOT}\"]}}}" > "$P/mcp_config.json"
echo "{\"trustedWorkspaces\": [\"$R\"]}" > "$HOME/.gemini/antigravity-cli/settings.json"
echo "== scratch: $T"; echo "== agy $("$AGY" --version 2>/dev/null | head -1)"
echo "== validate"; "$AGY" plugin validate --strict --json "$P" 2>&1

run_all() {
  cd "$R"
  echo "== agents"; timeout 30 "$AGY" agents 2>&1 | head -20
  echo "== mcp list"; timeout 30 "$AGY" mcp list 2>&1 | head -20
  echo "== plugin list"; timeout 30 "$AGY" plugin list 2>&1 | head -20
  echo "== -p hi"; timeout 60 "$AGY" --log-file "$O/agy-$1.log" -p hi 2>&1 | head -30; echo "exit ${PIPESTATUS[0]}"
  sleep 6
  echo "== agy log tail ($1)"; grep -iE 'plugin|hook|mcp|probe|eligib|auth' "$O/agy-$1.log" 2>/dev/null | head -40
}
echo "########## phase A: no auth"; run_all A
if [ ! -s "$O/hook.log" ] || [ ! -s "$O/mcp.log" ]; then
  echo "########## phase B: copy of real ~/.gemini auth (real dir untouched)"
  for f in antigravity-oauth-token installation_id jetski_state.pbtxt; do
    cp "$REAL_HOME/.gemini/antigravity-cli/$f" "$HOME/.gemini/antigravity-cli/" 2>/dev/null
  done
  ls "$HOME/.gemini/antigravity-cli"
  run_all B
fi
echo "########## hook.log"; cat "$O/hook.log" 2>/dev/null || echo "<absent>"
echo "########## mcp.log"; cat "$O/mcp.log" 2>/dev/null || echo "<absent>"
rm -f "$HOME/.gemini/antigravity-cli/antigravity-oauth-token"   # drop copied auth
[ -s "$O/hook.log" ] && [ -s "$O/mcp.log" ]
