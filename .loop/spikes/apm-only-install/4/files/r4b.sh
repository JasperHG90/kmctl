#!/usr/bin/env bash
# Risk 4 (changed plan): kmctl detects APM's skip line and offers --force.
# Exit 0 only if: (a) plain install exits 0 with a greppable skip marker and the skipped path can be found;
# (b) --force replaces SKILL.md with package bytes; (c) the hand rule is overwritten without --force.
set -u
REAL=/home/vscode/.claude
W=$(mktemp -d)
export UV_CACHE_DIR=$(uv cache dir)
export HOME=$W/home CLAUDE_CONFIG_DIR=$W/home/.claude
mkdir -p $HOME
P=$W/pkg
mkdir -p $P/.apm/skills/audit $P/.apm/agents $P/.apm/instructions
printf 'name: pkg\nversion: 0.1.0\n' > $P/apm.yml
printf -- '---\nname: audit\ndescription: package audit skill\n---\n\nPACKAGE AUDIT BODY\n' > $P/.apm/skills/audit/SKILL.md
printf -- '---\nname: x\ndescription: package agent\n---\n\nPACKAGE AGENT BODY\n' > $P/.apm/agents/x.md
printf -- '---\napplyTo: "docs/**,.okf/**"\n---\n\nPACKAGE RULE BODY\n' > $P/.apm/instructions/okf-bundle.instructions.md
git -C $P init -q -b main && git -C $P add -A && git -C $P -c user.name=s -c user.email=s@s commit -qm pkg
mkdir -p $W/srv/o && git clone -q --bare $P $W/srv/o/pkg.git && git -C $W/srv/o/pkg.git update-server-info
PORT=$(python3 -I -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
python3 -I /home/vscode/kmctl/tests/fixtures/githttp.py $W/srv $PORT >$W/srv.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null; rm -rf $W' EXIT
sleep 1
URL=http://127.0.0.1:$PORT/o/pkg.git
apm() { uvx -q --from apm-cli==0.33.0 apm "$@"; }
# Guard: APM must not touch the real Claude config dir.
real_clean() {
  local bad=0
  for d in $REAL/agents $REAL/rules $REAL/skills/audit; do
    [ -e $d ] && { echo "LEAK: $d exists in the real Claude dir"; bad=1; }
  done
  return $bad
}
real_clean || { echo "real Claude dir not clean before run"; exit 2; }
R=$W/repo; mkdir -p $R/.claude/rules $R/.claude/skills/audit
git -C $R init -q -b main
printf -- '---\npaths:\n  - "docs/**"\n---\n\nOLD HAND RULE\n' > $R/.claude/rules/okf-bundle.md
printf -- '---\nname: audit\ndescription: hand-made\n---\n\nOLD HAND SKILL\n' > $R/.claude/skills/audit/SKILL.md
echo extra > $R/.claude/skills/audit/notes.txt
git -C $R add -A && git -C $R -c user.name=s -c user.email=s@s commit -qm old
cd $R
MARK='skipped -- local files exist'
fail=0
echo "== [a1] apm install (no -v, no --force)"
apm install "$URL" --target claude --allow-insecure >$W/a1.out 2>&1; rc1=$?
cat $W/a1.out; echo "== exit $rc1"
[ $rc1 -eq 0 ] || { echo "FAIL a: install exited $rc1"; fail=1; }
echo "== skip marker lines (plain):"; grep -n 'skipped' $W/a1.out
grep -qF "$MARK" $W/a1.out || { echo "FAIL a: marker '$MARK' missing from plain output"; fail=1; }
echo "== [c] rule after plain install:"; cat .claude/rules/okf-bundle.md
grep -q 'PACKAGE RULE BODY' .claude/rules/okf-bundle.md || { echo "FAIL c: rule NOT overwritten"; fail=1; }
cmp -s $P/.apm/skills/audit/SKILL.md .claude/skills/audit/SKILL.md && { echo "NOTE: skill already replaced without --force"; }
echo "== apm.lock.yaml after plain install:"; cat apm.lock.yaml
echo "== [a2] apm install -v (no --force), re-run"
apm install --target claude --allow-insecure -v >$W/a2.out 2>&1; rc2=$?
cat $W/a2.out; echo "== exit $rc2"
grep -qF "$MARK" $W/a2.out && echo "RECORD: marker present on re-run" || echo "RECORD: marker absent on re-run"
named=0
for f in $W/a1.out $W/a2.out; do
  if grep -q 'skills/audit' $f; then echo "RECORD: skipped path named in $(basename $f):"; grep -n 'skills/audit' $f; named=1; fi
done
if [ $named -eq 0 ]; then
  echo "RECORD: skipped path not named in plain or -v output"
  if grep -q 'skills/audit' apm.lock.yaml; then echo "RECORD: lockfile lists skills/audit"; else echo "RECORD: lockfile does not list skills/audit"; fi
  echo "FAIL a: skipped path cannot be found from APM output"; fail=1
fi
echo "== [b] apm install --force"
apm install --target claude --allow-insecure --force >$W/b.out 2>&1; rc3=$?
cat $W/b.out; echo "== exit $rc3"
[ $rc3 -eq 0 ] || { echo "FAIL b: --force install exited $rc3"; fail=1; }
cmp -s $P/.apm/skills/audit/SKILL.md .claude/skills/audit/SKILL.md && echo "RECORD: SKILL.md now matches package bytes" || { echo "FAIL b: SKILL.md not replaced by --force"; cat .claude/skills/audit/SKILL.md; fail=1; }
[ -e .claude/skills/audit/notes.txt ] && echo "RECORD: notes.txt survives --force" || echo "RECORD: notes.txt removed by --force"
echo "== skill dir:"; ls -la .claude/skills/audit
echo "== git status"; git status --short --untracked-files=all
real_clean || fail=1
echo "== verdict fail=$fail"
exit $fail
