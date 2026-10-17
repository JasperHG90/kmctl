"""Static check of OpenCode's agent loader (sst/opencode 9d97a5b) for kmctl's translated agents.

Reads source files only; runs nothing from the clone. Usage: python -I THIS SRC_ROOT
Exit 0 when a front matter of description + mode: subagent + tools mapping (name->bool),
with no name key, decodes and loads (the risk does not hold); 1 otherwise.
"""
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
loader = "packages/core/src/config/plugin/agent.ts"
native = "packages/schema/src/config/agent.ts"
v1 = "packages/core/src/v1/config/agent.ts"
migrate = "packages/core/src/v1/config/migrate.ts"
perm_v1 = "packages/core/src/v1/config/permission.ts"
must, notes = [], []


def find(rel, pattern):
    for n, line in enumerate((root / rel).read_text().splitlines(), 1):
        if re.search(pattern, line):
            return f"{rel}:{n}: {line.strip()}"
    return None


def check(label, rel, pattern, required=True):
    hit = find(rel, pattern)
    (must if required else notes).append((label, hit))


check("folder: agent/ and agents/ both globbed", loader, r'\{agent,agents\}/\*\*/\*\.md')
check("name comes from file path", loader, r'replace\(/\^\(agent\|agents\|mode\|modes\)')
check("any non-native key -> legacy V1 decode", loader, r'some\(\(key\) => !agentKeys\.has\(key\)\)')
check("decode failure drops the agent silently", loader, r'if \(!agent\) return')
check("native keys", native, r'permissions: Permission\.Ruleset')
check("V1 tools = mapping name->bool, deprecated", v1, r'tools: Schema\.optional\(ConfigPermissionV1\.Entries\(Schema\.Boolean\)\)')
check("tools deprecated note", v1, r'@deprecated Use .permission. field')
check("V1 schema keeps unknown keys (StructWithRest)", v1, r'StructWithRest')
check("V1 'name' is a known key", v1, r'KNOWN_KEYS = new Set\(\["name"')
check("unknown keys -> options", v1, r'if \(!KNOWN_KEYS\.has\(key\)\) options\[key\] = value')
check("tools true/false -> allow/deny", v1, r'const action = enabled \? "allow" : "deny"')
check("V1 permission accepts action string or object", perm_v1, r'Schema\.Union\(\[Action, Schema\.ObjectKeyword\]\)')
check("options -> request.body (sent to provider)", migrate, r'request: Object\.keys\(body\)\.length \? \{ body \}')
check("model needs provider/model else dropped", migrate, r'/\^\[\^/#\]\+\\/\[\^#\]\+\$/')
check("bash->shell, task->subagent, write/patch->edit", migrate, r'if \(action === "bash"\) return "shell"')
check("V1 color = hex or theme literal only", v1, r'Schema\.Literals\(\["primary", "secondary"', required=False)
check("no rule matched -> ask", "packages/core/src/permission.ts", r'effect: "ask"', required=False)
check("permission rules: last match wins", "packages/core/src/permission.ts", r'findLast', required=False)

tools = {}
for f in sorted((root / "packages/core/src/tool/plugin").glob("*.ts")):
    m = re.search(r'^export const name = "([a-z_]+)"', f.read_text(), re.M)
    if m:
        tools[m.group(1)] = f"{f.relative_to(root)}"
print("built-in tool names:", ", ".join(sorted(tools)))
claude_map = {"Read": "read", "Grep": "grep", "Glob": "glob", "Write": "write", "Edit": "edit", "Bash": "shell"}
for c, o in claude_map.items():
    must.append((f"tool {c} -> {o} exists", tools.get(o)))
notes.append(("tool 'list' exists", tools.get("list")))
notes.append(("tool 'bash' exists (else via normalizeAction->shell)", tools.get("bash")))

for label, hit in must:
    print(("OK   " if hit else "FAIL ") + label + ("  | " + hit if hit else ""))
for label, hit in notes:
    print("NOTE " + label + ": " + (hit or "absent"))
sys.exit(0 if all(h for _, h in must) else 1)
