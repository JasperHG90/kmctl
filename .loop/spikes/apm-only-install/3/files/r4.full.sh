#!/usr/bin/env bash
# Risk 4: project install over a .claude/rules/okf-bundle.md and .claude/skills/audit/ that APM
# did not write. Pass (exit 0) only if apm exits 0 and both are replaced with package content.
# Shared setup: build a small APM package, serve it over smart HTTP. Sourced by r3.sh / r4.sh.
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
echo "== apm install $URL --target claude --allow-insecure"
apm install "$URL" --target claude --allow-insecure -v; rc=$?
echo "== apm exit $rc"
echo "== git status"; git status --short --untracked-files=all
echo "== rule:"; cat .claude/rules/okf-bundle.md
echo "== skill:"; cat .claude/skills/audit/SKILL.md
echo "== skill dir:"; ls -la .claude/skills/audit
fail=0
[ $rc -eq 0 ] || { echo "apm failed"; fail=1; }
grep -q 'PACKAGE RULE BODY' .claude/rules/okf-bundle.md || { echo "rule NOT overwritten"; fail=1; }
cmp -s $P/.apm/skills/audit/SKILL.md .claude/skills/audit/SKILL.md || { echo "skill NOT overwritten"; fail=1; }
real_clean || fail=1
echo "== verdict fail=$fail"
exit $fail
