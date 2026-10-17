#!/bin/bash
# Risk 4 (opencode-harness): with apm-cli 0.33.0 and targets: [opencode], does a
# first install (no .opencode/) write okf-bundle into opencode.json, is the entry
# a valid OpenCode local server, do pre-seeded instructions/theme keys survive a
# reinstall, and does the entry's command start okf's MCP server?
# Exit 0 only when all four hold.
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spikes/4
VENV=/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm/venv
APM=$VENV/bin/apm; PY=$VENV/bin/python
K=/home/vscode/kmctl
W=$(mktemp -d $S/run.XXXX)
export UV_CACHE_DIR=${UV_CACHE_DIR:-$HOME/.cache/uv} UV_PYTHON_INSTALL_DIR=${UV_PYTHON_INSTALL_DIR:-$HOME/.local/share/uv/python} HOME=$W/home; mkdir -p $HOME
echo "apm: $($APM --version 2>&1 | tail -1)"

# Package: kmctl's skills and agent plus the exact mcp entry from kmctl's apm/apm.yml.
P=$W/pkg; mkdir -p $P/.apm; cp -r $K/apm/.apm/skills $K/apm/.apm/agents $P/.apm/
$PY -I - "$K/apm/apm.yml" "$P/apm.yml" <<'PY'
import sys, yaml
src = yaml.safe_load(open(sys.argv[1]))
mcp = [m for m in src["dependencies"]["mcp"] if m["name"] == "okf-bundle"]
yaml.safe_dump({"name": "pkg", "version": "0.0.1", "dependencies": {"mcp": mcp}}, open(sys.argv[2], "w"))
PY

C=$W/c; mkdir -p $C && cd $C && git init -q
cp -r $K/.okf $C/.okf
printf "name: c\nversion: 0.0.1\ndependencies:\n  apm:\n    - $P\ntargets: [opencode]\n" > apm.yml

echo "== (a) first install, .opencode/ exists before: $([ -d .opencode ] && echo yes || echo no)"
$APM install > in1.txt 2>&1; echo "install rc=$?"
grep -iE "opencode|okf-bundle|error|warn|skip" in1.txt | head -15
echo ".opencode/ after: $(find .opencode -maxdepth 2 2>/dev/null | sort | tr '\n' ' ')"
echo "opencode.json exists: $([ -f opencode.json ] && echo yes || echo no)"
cp opencode.json oc1.json 2>/dev/null

echo "== second plain install (does opencode.json change?)"
$APM install > in2.txt 2>&1; echo "install rc=$?"
grep -iE "okf-bundle|opencode.json" in2.txt | head -5
cmp -s oc1.json opencode.json && echo "opencode.json unchanged by 2nd install" || echo "opencode.json CHANGED by 2nd install"

echo "== (c) pre-seed instructions + theme, reinstall"
$PY -I - <<'PY'
import json, os
d = json.load(open("opencode.json")) if os.path.exists("opencode.json") else {}
d["instructions"] = [".opencode/rules/*.md"]; d["theme"] = "x"
json.dump(d, open("opencode.json", "w"), indent=2)
PY
$APM install > in3.txt 2>&1; echo "install rc=$?"
grep -iE "okf-bundle|opencode.json" in3.txt | head -5
echo "--- opencode.json now:"; cat opencode.json; echo

echo "== (b)+(d) check entry and start it"
$PY -I - "$K/apm/apm.yml" <<'PY'
import json, sys, subprocess, select, time, yaml
want = [m for m in yaml.safe_load(open(sys.argv[1]))["dependencies"]["mcp"] if m["name"] == "okf-bundle"][0]
first = json.load(open("oc1.json")) if __import__("os").path.exists("oc1.json") else {}
a = "okf-bundle" in first.get("mcp", {})
print("(a) okf-bundle in opencode.json after FIRST install:", a)
d = json.load(open("opencode.json"))
c = d.get("instructions") == [".opencode/rules/*.md"] and d.get("theme") == "x"
print("(c) instructions and theme kept after reinstall:", c)
e = d.get("mcp", {}).get("okf-bundle")
print("entry:", json.dumps(e, indent=2))
allowed = {"type", "command", "cwd", "environment", "enabled", "timeout"}
b = bool(e) and e.get("type") == "local" and isinstance(e.get("command"), list) \
    and all(isinstance(x, str) for x in e["command"]) and isinstance(e.get("enabled", True), bool)
extra = sorted(set(e or {}) - allowed)
print("(b) valid McpLocalConfig (type local, command string array, enabled bool):", b,
      "| keys outside schema (ignored at runtime, rejected by the JSON schema):", extra)
print("command equals [sh] + apm.yml args:", bool(e) and e["command"] == [want["command"]] + want["args"])
ok_d = False
if e:
    p = subprocess.Popen(e["command"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "spike", "version": "0"}}}
    p.stdin.write(json.dumps(msg) + "\n"); p.stdin.flush()
    t0 = time.time(); line = ""
    while time.time() - t0 < 150:
        r, _, _ = select.select([p.stdout], [], [], 1)
        if r:
            line = p.stdout.readline(); break
        if p.poll() is not None: break
    print("initialize reply after %.1fs:" % (time.time() - t0), line.strip()[:400])
    try:
        ok_d = json.loads(line).get("result", {}).get("serverInfo") is not None
    except Exception:
        pass
    p.kill(); err = p.stderr.read()
    if not ok_d: print("server stderr:", err[-1500:])
print("(d) server answered initialize:", ok_d)
sys.exit(0 if (a and b and c and ok_d) else 1)
PY
