#!/usr/bin/env bash
# Does prek 0.5.5 install and run a language: python hook from a local path
# repo pinned to a commit of this checkout? Exits 0 only if both the plain
# hook and an args: [--version] hook run kmctl.
set -euo pipefail
SRC="$PWD"
W=$(mktemp -d)
export PREK_HOME="$W/prek-home"   # cold prek cache: no reused hook envs
export GIT_AUTHOR_NAME=s GIT_COMMITTER_NAME=s GIT_AUTHOR_EMAIL=s@x GIT_COMMITTER_EMAIL=s@x
git clone -q "$SRC" "$W/kmctl"
cd "$W/kmctl"
cat > .pre-commit-hooks.yaml <<'Y'
- id: kmctl-check
  name: kmctl check
  entry: kmctl check
  language: python
  pass_filenames: false
  always_run: true
Y
git add .pre-commit-hooks.yaml
git commit -qm "spike: hook manifest"
REV=$(git rev-parse HEAD)
echo "hook repo $W/kmctl at $REV"

mkdir "$W/consumer" && cd "$W/consumer" && git init -q
echo "# consumer" > README.md
cat > .pre-commit-config.yaml <<Y
repos:
  - repo: $W/kmctl
    rev: $REV
    hooks:
      - id: kmctl-check
Y
git add -A && git commit -qm init

echo "== run 1: plain hook (cold PREK_HOME) =="
t0=$(date +%s)
uvx prek@0.5.5 run kmctl-check --all-files -v
t1=$(date +%s); echo "run 1 seconds: $((t1-t0))"

echo "== run 2: plain hook again (warm) =="
uvx prek@0.5.5 run kmctl-check --all-files -v
t2=$(date +%s); echo "run 2 seconds: $((t2-t1))"

echo "== run 3: entry kmctl, args: [--version] =="
cat > .pre-commit-config.yaml <<Y
repos:
  - repo: $W/kmctl
    rev: $REV
    hooks:
      - id: kmctl-check
        entry: kmctl
        args: [--version]
Y
git commit -qam args
out=$(uvx prek@0.5.5 run kmctl-check --all-files -v 2>&1); echo "$out"
t3=$(date +%s); echo "run 3 seconds: $((t3-t2))"
echo "$out" | grep -q "kmctl 0\." || { echo "FAIL: --version output not seen"; exit 1; }

echo "== run 4: args: [--json] appended to entry kmctl check =="
cat > .pre-commit-config.yaml <<Y
repos:
  - repo: $W/kmctl
    rev: $REV
    hooks:
      - id: kmctl-check
        args: [--json]
Y
git commit -qam args2
uvx prek@0.5.5 run kmctl-check --all-files -v
echo "ALL OK"
