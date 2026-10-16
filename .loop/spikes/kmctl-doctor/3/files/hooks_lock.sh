#!/usr/bin/env bash
# p2: after apm install of pinned okf-skills (ships a Stop hook) with targets
# claude+antigravity, and a kmctl-style SessionStart merge into
# .claude/settings.json, does apm.lock.yaml list hook/settings files, and do
# all listed sha256 still match disk? Exit 0 iff every listed hash matches
# after the merge.
set -u
export UV_CACHE_DIR="${UV_CACHE_DIR:-$(uv cache dir)}"
W=$(mktemp -d)
export HOME="$W/home" CLAUDE_CONFIG_DIR="$W/home/.claude"; mkdir -p "$CLAUDE_CONFIG_DIR"
git config --global user.email s@x; git config --global user.name s
git config --global init.defaultBranch main
C="$W/consumer"; mkdir -p "$C"; cd "$C" || exit 2
git init -q .
cat > apm.yml <<'Y'
name: consumer
version: 0.0.1
targets:
  - claude
  - antigravity
dependencies:
  apm:
    - scaccogatto/okf-skills#a8b96420de90d102c43cda1693d01ec4f925f2ab
Y
echo "===== apm install"
uvx --from apm-cli==0.33.0 apm install 2>&1 | tail -40
echo "--- exit ${PIPESTATUS[0]}"
echo "--- files (excluding .git, apm_modules)"
find . \( -path ./.git -o -path ./apm_modules \) -prune -o -type f -print | sort
for f in .claude/settings.json .agents/hooks.json; do echo "--- $f"; cat "$f" 2>&1; done
echo "--- apm.lock.yaml"; cat apm.lock.yaml
echo "===== merge SessionStart into .claude/settings.json"
python3 -I - <<'PY'
import json, pathlib
p = pathlib.Path(".claude/settings.json")
d = json.loads(p.read_text()) if p.exists() else {}
d.setdefault("hooks", {}).setdefault("SessionStart", []).append(
    {"hooks": [{"type": "command", "command": "kmctl briefing"}]})
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(d, indent=2) + "\n")
print(p.read_text())
PY
echo "===== check hashes"
python3 -I - <<'PY'
import hashlib, pathlib, re, sys
lock = pathlib.Path("apm.lock.yaml").read_text()
pairs = {}
for block in re.findall(r"^  deployed_file_hashes:\n((?:    \S.*\n)+)", lock, re.M):
    pairs.update(re.findall(r"^    (\S+): sha256:([0-9a-f]{64})$", block, re.M))
deployed = set(re.findall(r"^\s+- (\.(?:claude|agents)/\S+)\s*$", lock, re.M))
hookish = sorted(x for x in deployed | set(pairs)
                 if "hook" in x.lower() or x.endswith("settings.json"))
print("listed paths:", len(deployed), "hashed paths:", len(pairs))
print("hook/settings paths listed in lock:", hookish or "none")
bad = 0
for path, want in sorted(pairs.items()):
    f = pathlib.Path(path)
    got = hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else "MISSING"
    ok = got == want
    bad += not ok
    print("OK  " if ok else "BAD ", path)
print("mismatches:", bad)
sys.exit(1 if bad or not pairs else 0)
PY
rc=$?
for p in /home/vscode/.claude/agents /home/vscode/.claude/rules /home/vscode/.claude/skills/audit; do
  [ -e "$p" ] && { echo "REAL HOME TOUCHED: $p"; rc=3; }
done
echo "--- final exit $rc"; exit $rc
