#!/usr/bin/env bash
# Spike: does copier render from a repo whose newest tag has copier.yml at the
# root with _subdirectory: starter, while older tags have no copier.yml?
set -u
W=$(mktemp -d)
export GIT_AUTHOR_NAME=spike GIT_AUTHOR_EMAIL=s@x GIT_COMMITTER_NAME=spike GIT_COMMITTER_EMAIL=s@x
COPIER="uvx copier@9.19.1"
echo "copier version: $($COPIER --version 2>&1)"

git clone -q /home/vscode/kmctl "$W/repo"
cd "$W/repo"
echo "tags: $(git tag | tr '\n' ' ')"
sed 's/^_subdirectory: template$/_subdirectory: starter/' /home/vscode/kmctl-starter/copier.yml > copier.yml
grep -n '^_subdirectory' copier.yml
cp -r /home/vscode/kmctl-starter/template starter
git add copier.yml starter
git commit -qm "add starter"
git tag v0.6.0
cd "$W"

ARGS=(--defaults --data project_name=demo --data codeowners=@octocat --data 'harnesses=[opencode]' --data kmctl_ref=v0.5.1)
fail=0

echo "=== (a) no --vcs-ref ==="
$COPIER copy "${ARGS[@]}" "$W/repo" out1 2>&1
echo "--- out1 files:"; (cd out1 && find . -type f | sort)
echo "--- out1/.copier-answers.yml:"; cat out1/.copier-answers.yml
echo "--- out1/apm.yml targets:"; sed -n '/^targets:/,$p' out1/apm.yml
grep -q '^_commit: v0.6.0$' out1/.copier-answers.yml || { echo "FAIL a: _commit is not v0.6.0"; fail=1; }
sed -n '/^targets:/,$p' out1/apm.yml | grep -q '^  - opencode$' || { echo "FAIL a: apm.yml targets lack opencode"; fail=1; }

echo "=== (c) no kmctl root files in output ==="
for f in src pyproject.toml action.yml tests copier.yml starter justfile.jinja; do
  [ -e "out1/$f" ] && { echo "FAIL c: out1/$f present"; fail=1; }
done
# README.md and justfile come from the template; check they are the rendered ones.
grep -q 'demo' out1/README.md || { echo "FAIL c: out1/README.md is not the template's"; fail=1; }

echo "=== (b) --vcs-ref HEAD with a dirty tree ==="
echo "DIRTY-MARKER" >> "$W/repo/starter/AGENTS.md.jinja"
echo "untracked" > "$W/repo/starter/UNTRACKED.txt"
$COPIER copy "${ARGS[@]}" --vcs-ref HEAD "$W/repo" out2 2>&1
echo "--- out2/.copier-answers.yml:"; cat out2/.copier-answers.yml
if grep -q DIRTY-MARKER out2/AGENTS.md; then echo "dirty-tree: modified file USED"; else echo "dirty-tree: modified file NOT used"; fi
if [ -e out2/UNTRACKED.txt ]; then echo "dirty-tree: untracked file USED"; else echo "dirty-tree: untracked file NOT used"; fi

echo "=== (b2) no --vcs-ref with same dirty tree ==="
$COPIER copy "${ARGS[@]}" "$W/repo" out3 2>&1
grep '^_commit' out3/.copier-answers.yml
grep -q DIRTY-MARKER out3/AGENTS.md && echo "no-ref dirty: USED" || echo "no-ref dirty: NOT used"

echo "result fail=$fail"
exit $fail
