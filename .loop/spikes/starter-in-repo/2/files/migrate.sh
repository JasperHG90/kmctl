#!/usr/bin/env bash
# Spike: can a project made from kmctl-starter v0.3.0 (_commit: v0.3.0) be
# moved onto a template that lives in kmctl's repo under starter/?
# Exits 0 only when some command moves it, keeping answers, and a later
# `copier update` applies a newer template change.
set -u
STARTER=/home/vscode/kmctl-starter
KMCTL=/home/vscode/kmctl
W=$(mktemp -d)
cd "$W"
echo "workdir: $W"
uvx copier --version
fail=0
check() { if eval "$2"; then echo "PASS: $1"; else echo "FAIL: $1"; fail=1; fi; }
run() { echo "+ $*"; "$@"; rc=$?; echo "  -> exit $rc"; return $rc; }

echo "== 1. project from kmctl-starter v0.3.0"
git clone -q "$STARTER" starter-clone
run uvx copier copy --defaults --data project_name=demo --data codeowners=@octocat \
  --vcs-ref v0.3.0 "$W/starter-clone" proj || exit 2
cd proj
git init -q && git add -A && git commit -qm init
echo "LOCAL USER EDIT" >> README.md
git commit -qam "user edit"
cat .copier-answers.yml
cd "$W"

echo "== 2. fake new template in a kmctl clone"
git clone -q "$KMCTL" newrepo
cd newrepo
git tag | tr '\n' ' '; echo
sed 's/^_subdirectory: template$/_subdirectory: starter/' "$STARTER/copier.yml" > copier.yml
grep -n '^_subdirectory' copier.yml
cp -r "$STARTER/template" starter
echo '# MARKER-V060 template change' >> starter/justfile.jinja
git add -A && git commit -qm "starter in repo" && git tag v0.6.0
cd "$W"

echo "== 3. move _src_path and try update"
cd proj
sed -i "s|^_src_path: .*|_src_path: $W/newrepo|" .copier-answers.yml
git commit -qam "move src path"
cat .copier-answers.yml
run uvx copier update --defaults --skip-answered
update_rc=$?
echo "git status after update:"; git status --short
echo "README.md after update (conflict markers?):"; grep -n -E "^(<<<<<<<|=======|>>>>>>>)|LOCAL USER EDIT" README.md
echo "justfile marker after update:"; grep -c MARKER-V060 justfile
echo "_commit after update:"; grep '^_commit' .copier-answers.yml
# reset whatever update did, to test recopy from a clean state
git reset -q --hard && git clean -qfd

echo "== 4. recopy"
run uvx copier recopy --defaults --skip-answered --overwrite
recopy_rc=$?
cat .copier-answers.yml
git status --short
check "recopy exit 0" "[ $recopy_rc -eq 0 ]"
check "answers kept (project_name demo)" "grep -q '^project_name: demo' .copier-answers.yml"
check "answers kept (codeowners @octocat)" "grep -q '^codeowners: .@octocat' .copier-answers.yml"
check "_commit is v0.6.0" "grep -q '^_commit: v0.6.0' .copier-answers.yml"
check "_src_path is new repo" "grep -q '^_src_path: $W/newrepo' .copier-answers.yml"
check "template change present" "grep -q MARKER-V060 justfile"
check "no stray kmctl files rendered" "[ ! -e pyproject.toml ] && [ ! -d src ] && [ ! -d starter ]"
if grep -q "LOCAL USER EDIT" README.md; then echo "README user edit: KEPT by recopy"; else echo "README user edit: OVERWRITTEN by recopy"; fi
git diff --stat
git add -A && git commit -qm "recopy onto new template"

echo "== 5. later release v0.6.1, then copier update"
# re-apply a user edit after recopy so update's merge can be judged
grep -q "LOCAL USER EDIT" README.md || { echo "LOCAL USER EDIT" >> README.md; git commit -qam "user edit again"; }
cd "$W/newrepo"
echo '# MARKER-V061 later change' >> starter/justfile.jinja
git commit -qam "later change" && git tag v0.6.1
cd "$W/proj"
run uvx copier update --defaults --skip-answered
upd2_rc=$?
git status --short
check "second update exit 0" "[ $upd2_rc -eq 0 ]"
check "_commit is v0.6.1" "grep -q '^_commit: v0.6.1' .copier-answers.yml"
check "v0.6.1 change applied" "grep -q MARKER-V061 justfile"
check "answers still kept" "grep -q '^project_name: demo' .copier-answers.yml"
check "user README edit kept by update" "grep -q 'LOCAL USER EDIT' README.md"
check "no conflict files" "! ls -R | grep -q '\.rej$'"
echo "summary: first update rc=$update_rc recopy rc=$recopy_rc second update rc=$upd2_rc"
exit $fail
