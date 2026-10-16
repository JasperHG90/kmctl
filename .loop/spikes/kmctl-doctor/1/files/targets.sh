#!/usr/bin/env bash
# Does APM 0.33.0 record --target claude,antigravity in the consumer's apm.yml
# or apm.lock.yaml, and does the lock list deployed .agents/ paths with sha256?
# Exit 0 when, in both scenarios, the targets are recoverable (apm.yml targets:
# or lock lists both .claude/ and .agents/ deployed paths). Exit 1 otherwise.
set -u
export UV_CACHE_DIR="${UV_CACHE_DIR:-$(uv cache dir)}"
W=$(mktemp -d)
export HOME="$W/home"; mkdir -p "$HOME"
git config --global user.email s@x; git config --global user.name s
git config --global init.defaultBranch main

# tiny local package
P="$W/pkg"; mkdir -p "$P/.apm/skills/demo" "$P/.apm/instructions"
cat > "$P/apm.yml" <<'EOF'
name: demo-pkg
version: 0.1.0
EOF
cat > "$P/.apm/skills/demo/SKILL.md" <<'EOF'
---
name: demo
description: Demo skill for a spike.
---
Say hello.
EOF
cat > "$P/.apm/instructions/demo.instructions.md" <<'EOF'
---
applyTo: "**/*.py"
---
Use four spaces.
EOF

APM=(uvx --from apm-cli==0.33.0 apm)
ok=0

run_case() {
  local name=$1 pre=$2
  local C="$W/$name"; mkdir -p "$C"; cd "$C" || exit 2
  git init -q .
  if [ "$pre" = yes ]; then
    printf 'name: consumer\nversion: 0.0.1\n' > apm.yml
  fi
  echo "===== CASE $name (pre-existing apm.yml: $pre) ====="
  "${APM[@]}" install ../pkg --target claude,antigravity 2>&1 | tail -40
  echo "--- exit ${PIPESTATUS[0]}"
  echo "--- files (excluding .git)"
  find . -path ./.git -prune -o -type f -print | sort
  echo "--- apm.yml"; cat apm.yml 2>&1
  echo "--- apm.lock.yaml"; cat apm.lock.yaml 2>&1
  local yml_t=no lock_t=no lock_claude=no lock_agents=no
  grep -qE '^\s*targets?:' apm.yml 2>/dev/null && yml_t=yes
  grep -qiE 'target' apm.lock.yaml 2>/dev/null && lock_t=yes
  grep -q '\.claude/' apm.lock.yaml 2>/dev/null && lock_claude=yes
  grep -q '\.agents/' apm.lock.yaml 2>/dev/null && lock_agents=yes
  echo "SUMMARY $name: apm.yml targets=$yml_t lock mentions target=$lock_t lock .claude/=$lock_claude lock .agents/=$lock_agents"
  if [ "$yml_t" = yes ] || { [ "$lock_claude" = yes ] && [ "$lock_agents" = yes ]; }; then
    echo "RECOVERABLE $name: yes"
  else
    echo "RECOVERABLE $name: no"; ok=1
  fi
}

run_case fresh no
run_case existing yes
exit $ok
