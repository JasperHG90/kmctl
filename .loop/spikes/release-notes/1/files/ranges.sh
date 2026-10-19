#!/usr/bin/env bash
# Exit 0 when every release range from v0.2.0..v0.3.0 on has a useful
# first-parent entry, and every `loop: land SLUG` in a range has a matching
# `Merge loop/SLUG` in the same range.
set -u
tags=$(git tag -l 'v*' --sort=v:refname)
prev=""
fail=0
noise='^(loop: |release: |Merge pull request |Merge remote-tracking branch|Merge main into|Merge branch .main.)'
for t in $tags; do
  if [ -z "$prev" ]; then range="$t"; label="root..$t"; else range="$prev..$t"; label="$range"; fi
  subjects=$(git log --first-parent --format=%s $range)
  kept=$(printf '%s\n' "$subjects" | grep -Ev "$noise" | grep -v '^$')
  merges=$(printf '%s\n' "$kept" | grep -c '^Merge loop/' || true)
  other=$(printf '%s\n' "$kept" | grep -v '^Merge loop/' | grep -vc '^$' || true)
  echo "== $label: Merge loop/ $merges, other $other"
  printf '%s\n' "$kept" | grep -v '^Merge loop/' | grep -v '^$' | sed 's/^/   other: /'
  merged=$(printf '%s\n' "$kept" | sed -n 's/^Merge loop\/\([^:]*\):.*/\1/p' | sort -u)
  landed=$(printf '%s\n' "$subjects" | sed -n 's/^loop: land \(.*\)$/\1/p' | sort -u)
  for s in $landed; do
    if ! printf '%s\n' "$merged" | grep -qx "$s"; then
      echo "   LANDED WITHOUT MERGE: $s"
      [ -n "$prev" ] && fail=1
    fi
  done
  if [ -n "$prev" ] && [ $((merges + other)) -eq 0 ]; then echo "   EMPTY RANGE"; fail=1; fi
  prev=$t
done
exit $fail
