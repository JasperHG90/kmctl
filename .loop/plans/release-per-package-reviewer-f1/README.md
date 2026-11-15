---
type: plan
title: 'Plan: release-per-package-reviewer-f1'
description: Deferred hardening from release-per-package, reviewer finding f1 in review round 1.
tags:
- plan
- hardening
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T21:29:42+00:00'
slug: release-per-package-reviewer-f1
epic: monorepo-release
depends_on: []
priority: 2
schema_version: '2.0'
---

# release-per-package-reviewer-f1

Relayed from: release-per-package, reviewer finding f1 in review round 1

## Intent

The late-commit step takes the drafted commit as the first parent of the merge's second parent. If the release branch gets an "Update branch" merge from main and then a later commit (for example a notes edit), that parent is the update merge. Its history already holds the late commits, so they go unnamed and no warning is written. Reading the Drafted-From trailer from the release branch's own commits (git log FIRST..SECOND_PARENT) before falling back to the parent would cover this case. at .github/workflows/release-tag.yml:130.

## Problems

- P1: When the release branch takes an "Update branch" merge from main before a later commit, release-tag reads the update merge as the drafted commit and names none of the commits that landed after the notes were drafted.

## Goals

- G1: release-tag names every commit of the package that ships without a bullet in the reviewed notes.

## Outcomes

### O1: release-tag reads the Drafted-From trailer from the release branch's commits before falling back to the parent
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `.github/workflows/release-tag.yml`, `tests/scripts/test_workflows.py`
- checked by: a test that merges main into the release branch, adds a notes edit, merges the release and runs the step, which must name the late commit and the drafted commit; the existing merge, squash and no-trailer tests still pass
- seen by: operator

## Could invalidate this plan

- none

## Prior work

A fix was built and tested in release-per-package's fix round, then taken out when loopctl split this finding off. Its diff, against release-per-package's versions of the two files (the test hunk needs re-placing, because later tests were added to the end of test_workflows.py):

````diff
--- a/.github/workflows/release-tag.yml
+++ b/.github/workflows/release-tag.yml
@@ -110,9 +110,11 @@
             exit 1
           fi
       # A commit that reached main after the Release run drafted the notes
-      # ships in the tag with no bullet. Find the drafted commit (the parent of
-      # the merge's second parent, or a squash merge's Drafted-From trailer)
-      # and name this package's commits since it. The notes stay as reviewed.
+      # ships in the tag with no bullet. Find the drafted commit from the
+      # Drafted-From trailer (on the release branch's own commits for a merge,
+      # on the pushed commit for a squash), else from the parent of the
+      # merge's second parent, and name this package's commits since it. The
+      # notes stay as reviewed.
       - name: Name commits that landed after the notes were drafted
         if: ${{ steps.plan.outputs.verdict == 'raised' || steps.plan.outputs.verdict == 'resume' }}
         env:
@@ -122,11 +124,24 @@
           set -euo pipefail
           read -r -a PARENTS <<< "$(git rev-list --parents -n 1 "$GITHUB_SHA")"
           FIRST="${PARENTS[1]:-}"
+          # Print the first Drafted-From hash in stdin. awk reads all of it,
+          # so the writer never dies of SIGPIPE under pipefail.
+          drafted_from() {
+            awk '!d && match($0, /Drafted-From: *[0-9a-f]+/) {
+                d = substr($0, RSTART, RLENGTH); sub(/^Drafted-From: */, "", d)
+              }
+              END { if (length(d) >= 7 && length(d) <= 40) print d }'
+          }
           if [ "${#PARENTS[@]}" -eq 3 ]; then
-            DRAFTED="$(git rev-parse "${PARENTS[2]}^")"
+            # An "Update branch" merge on the release branch makes the second
+            # parent's parent a merge that already holds the late commits, so
+            # read the release commit's trailer first.
+            DRAFTED="$(git log --format=%B "$FIRST..${PARENTS[2]}" | drafted_from)"
+            if [ -z "$DRAFTED" ]; then
+              DRAFTED="$(git rev-parse "${PARENTS[2]}^")"
+            fi
           else
-            DRAFTED="$(git log -1 --format=%B "$GITHUB_SHA" \
-              | sed -n 's/^.*Drafted-From: *\([0-9a-f]\{7,40\}\).*$/\1/p' | head -n 1)"
+            DRAFTED="$(git log -1 --format=%B "$GITHUB_SHA" | drafted_from)"
           fi
           if [ -z "$FIRST" ] || [ -z "$DRAFTED" ] || ! git cat-file -e "$DRAFTED^{commit}" 2>/dev/null; then
             echo "::warning::Could not find the commit the $TAG notes were drafted from, so commits that landed after the draft are not named. Compare the notes with the history by hand."
--- a/tests/scripts/test_workflows.py
+++ b/tests/scripts/test_workflows.py
@@ -984,3 +984,28 @@
 
     assert res.returncode == 0, res.stdout + res.stderr
     assert "::warning::Could not find the commit" in res.stdout
+
+
+def test_release_tag_reads_the_trailer_past_an_update_branch_merge(
+    released: dict[str, Any], tmp_path: Path
+) -> None:
+    """A release branch that took an "Update branch" merge from main, then a later commit, still names the late commits.
+
+    The second parent's parent is then the update merge, whose history holds
+    the late commits, so the step must read the release commit's trailer.
+    """
+    repo: Path = released["repo"]
+    _land_late_commits(repo)
+    _git_out(repo, "switch", "-q", "release/kmaudit-v0.2.0")
+    _git_out(repo, "merge", "-q", "--no-ff", "-m", "Merge branch 'main'", "main")
+    _change(repo, "Edit notes", ".github/release-notes/kmaudit-v0.2.0.md")
+    _git_out(repo, "switch", "-q", "main")
+    _merge_release(repo, squash=False)
+
+    res, summary = _late(repo, tmp_path, "kmaudit")
+
+    assert res.returncode == 0, res.stdout + res.stderr
+    [warning] = [ln for ln in res.stdout.splitlines() if ln.startswith("::warning::")]
+    assert "Late kmaudit fix" in warning
+    assert released["drafted"] in warning
+    assert "Late kmaudit fix" in summary
````
