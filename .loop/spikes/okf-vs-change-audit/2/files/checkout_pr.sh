#!/usr/bin/env bash
# Mimic actions/checkout v7.0.1 (3d3c42e) on a pull_request event with
# fetch-depth: 0, persist-credentials: false, against a local bare "GitHub".
# From its source: src/ref-helper.ts getRefSpecForAllHistory and getCheckoutInfo,
# src/git-command-manager.ts fetch (--no-tags --prune --no-recurse-submodules).
set -u
fail=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fail=1; fi; }
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
export GIT_CONFIG_NOSYSTEM=1 HOME=$(mktemp -d)
git config --global init.defaultBranch main
root=$(mktemp -d)

scenario() {  # $1 name, $2 main-moves-before-merge (0/1), $3 main-moves-after-merge-ref (0/1)
  name=$1; d=$root/$name; mkdir -p $d
  git init -q --bare $d/remote.git
  git init -q $d/dev; cd $d/dev
  echo a > base.txt; echo s > shared.txt; git add .; git commit -qm init
  git switch -qc pr
  echo p > pr1.txt; mkdir -p .okf; echo p > .okf/pr2.md; echo s2 > shared.txt; git add .; git commit -qm pr
  git switch -q main
  if [ "$2" = 1 ]; then echo m > main_only.txt; git add .; git commit -qm main-moved; fi
  # GitHub's refs/pull/1/merge: a merge commit, parent 1 = base tip, parent 2 = PR head
  git switch -q --detach main; git merge -q --no-ff --no-edit pr; merge=$(git rev-parse HEAD)
  git switch -q main
  git push -q $d/remote.git main pr "$merge:refs/pull/1/merge"
  if [ "$3" = 1 ]; then echo late > late_main.txt; git add .; git commit -qm late; git push -q $d/remote.git main; fi
  # --- checkout action steps ---
  GITHUB_SHA=$merge; GITHUB_REF=refs/pull/1/merge; GITHUB_BASE_REF=main
  mkdir $d/ws; cd $d/ws; git init -q; git remote add origin $d/remote.git
  git -c protocol.version=2 fetch -q --no-tags --prune --no-recurse-submodules origin \
    '+refs/heads/*:refs/remotes/origin/*' '+refs/tags/*:refs/tags/*' "+$GITHUB_SHA:refs/remotes/pull/1/merge"
  git checkout -q --force refs/remotes/pull/1/merge
  # Prove no later step reaches the remote: break the URL.
  git remote set-url origin /nonexistent/remote.git
  echo "== $name: refs"; git for-each-ref --format='%(refname)'
  check "$name: HEAD is the merge commit" '[ "$(git rev-parse HEAD)" = "$GITHUB_SHA" ]'
  check "$name: (a) origin/main exists" 'git rev-parse --verify --quiet "origin/$GITHUB_BASE_REF^{commit}" >/dev/null'
  # knowledge-ci.sh fallback condition: fetch runs only when rev-parse fails
  base_ref="origin/$GITHUB_BASE_REF"; fetched=no
  git rev-parse --verify --quiet "$base_ref^{commit}" >/dev/null || { fetched=yes; git fetch --quiet origin "+refs/heads/$GITHUB_BASE_REF:refs/remotes/$base_ref" 2>/dev/null; }
  check "$name: knowledge-ci fallback fetch not needed" '[ $fetched = no ]'
  check "$name: (a) worktree add --detach origin/main, no remote" 'git worktree add -q --detach $d/basetree origin/$GITHUB_BASE_REF'
  echo "   base tree files: $(cd $d/basetree && git ls-files | tr '\n' ' ')"
  got=$(git diff --name-only origin/$GITHUB_BASE_REF...HEAD | sort | tr '\n' ' ')
  want=$(printf '.okf/pr2.md\npr1.txt\nshared.txt\n' | sort | tr '\n' ' ')
  echo "   diff origin/main...HEAD: $got"
  check "$name: (b) three-dot diff lists exactly the PR's files" '[ "$got" = "$want" ]'
}
scenario fresh 0 0
scenario main-moved 1 0
scenario main-moved-after-merge-ref 1 1
exit $fail
