#!/bin/sh
# Can a loop/adr-0057-pr-audit worktree branch cut from main carry PR 71's
# branch through loopctl's git backstop, so a push back fast-forwards it,
# and can ticket done close without ticket land? Exits 0 only if all hold.
set -u
fail=0
ok()  { echo "OK   $*"; }
bad() { echo "FAIL $*"; fail=1; }
PR=refs/remotes/origin/adr/audit-pull-requests
common=$(git rev-parse --path-format=absolute --git-common-dir)
git rev-parse -q --verify "$PR" >/dev/null || { echo "FAIL $PR not fetched"; exit 2; }
MAIN=$(git rev-parse main); PRH=$(git rev-parse "$PR")
echo "main=$MAIN pr71=$PRH"
echo "main..pr71: $(git rev-list --count main..$PRH)  pr71..main: $(git rev-list --count $PRH..main)"
git merge-base --is-ancestor main "$PRH" && echo "INFO pr71 already contains main" || echo "INFO pr71 does not contain main: a merge is needed, not a fast-forward"

# Q2: main + pr71 merge cleanly, and the merge fast-forwards pr71.
tree=$(git merge-tree --write-tree main "$PRH") && ok "main and pr71 merge with no conflict" || bad "merge-tree reports conflicts: $tree"
m=$(git commit-tree "$tree" -p main -p "$PRH" -m probe)
git merge-base --is-ancestor "$PRH" "$m" && ok "a merge commit on loop/SLUG contains pr71 head, so pushing it is a fast-forward" || bad "not a fast-forward"

# Backstop: pr71 brings no .loop/ path (what _merge_refusal judges for a non-ticket ref).
base=$(git merge-base main "$PRH")
loopp=$(git diff --name-only "$base" "$PRH" -- .loop/)
[ -z "$loopp" ] && ok "pr71 changes no .loop/ path since merge-base" || bad "pr71 changes .loop/: $loopp"

# Q1: in a throwaway clone with the real backstop hooks, branch loop/SLUG from
# main and run git merge --no-commit of pr71; the hooks must let it through.
d=$(mktemp -d)
git clone -q --no-local "$common" "$d/c" || { echo "FAIL clone"; exit 2; }
git -C "$d/c" fetch -q "$common" "$PR:$PR"
for h in reference-transaction pre-merge-commit commit-msg pre-commit; do cp "$common/hooks/$h" "$d/c/.git/hooks/$h"; done
git -C "$d/c" checkout -q main 2>/dev/null || git -C "$d/c" checkout -q -b main origin/main
git -C "$d/c" reset -q --hard "$MAIN"
( cd "$d/c" && git checkout -q -b loop/adr-0057-pr-audit main ) && ok "hooks allow creating loop/adr-0057-pr-audit from main" || bad "branch creation refused"
( cd "$d/c" && git merge --no-ff --no-commit "$PR" ) >"$d/merge.out" 2>&1; rc=$?
cat "$d/merge.out"
[ $rc -eq 0 ] && [ -f "$d/c/.git/MERGE_HEAD" ] && ok "backstop hooks allow git merge --no-commit of pr71 into loop/SLUG (MERGE_HEAD set)" || bad "merge refused rc=$rc"
# The commit gate re-judges MERGE_HEAD at commit time with the same _merge_refusal.
PY=$(dirname "$(readlink -f "$(command -v loopctl)")")/python
( cd "$d/c" && "$PY" -c '
from pathlib import Path
from loop_harness.hooks.entries import _merge_refusal
r=_merge_refusal(Path.cwd(), ["MERGE_HEAD"], "HEAD"); print("commit-time _merge_refusal:", r); raise SystemExit(r is not None)' ) && ok "commit gate would not refuse the merge for loop state" || bad "commit gate refuses the merge"

# Q1/Q3 from loopctl's source: worktree start point, and what plain done needs.
SP=$("$PY" -c 'import loop_harness,os;print(os.path.dirname(loop_harness.__file__))')
grep -n '"worktree", "add", "-b", branch, str(path), start' "$SP/commands/lifecycle.py" >/dev/null && grep -n 'ctx.integration_branch if git.rev_exists(ctx.integration_branch' "$SP/commands/lifecycle.py" >/dev/null && ok "advance building cuts loop/SLUG from integration_branch (main), or reuses an existing loop/SLUG" || bad "worktree start point not as expected"
grep -n 'for r in (f"loop/{slug}", ctx.integration_branch)' "$SP/commands/common.py" >/dev/null && ok "plain done finds the Loop-Ticket commit on loop/SLUG or main; it need not be on main" || bad "trailer_commit lookup changed"
sed -n '/^def _done_on_evidence/,/^def done_outside/p' "$SP/commands/lifecycle.py" | grep -nE 'land|is-ancestor|merge-base' && bad "done references land/ancestry" || ok "done never calls land and checks no ancestry against main"
rm -rf "$d"
exit $fail
