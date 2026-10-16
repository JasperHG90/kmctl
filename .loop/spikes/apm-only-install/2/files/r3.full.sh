#!/usr/bin/env bash
# Risk 3: does `apm install -g URL --target claude` take a package with no git: parent,
# and land files under CLAUDE_CONFIG_DIR (skills, agents, rules)?
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
cd $W
echo "HOME=$HOME CLAUDE_CONFIG_DIR=$CLAUDE_CONFIG_DIR"
echo "== apm install -g $URL --target claude --allow-insecure"
apm install -g "$URL" --target claude --allow-insecure -v; rc=$?
echo "== apm exit $rc"
echo "== files under HOME (excluding caches):"
(cd $HOME && find . -type f -not -path './.cache/*' -not -path './.local/*' | sort)
for f in skills/audit/SKILL.md agents/x.md rules/okf-bundle.md; do echo "== \$CLAUDE_CONFIG_DIR/$f"; cat "$CLAUDE_CONFIG_DIR/$f" 2>/dev/null || echo MISSING; done
fail=0
[ $rc -eq 0 ] || fail=1
cmp -s $P/.apm/skills/audit/SKILL.md $CLAUDE_CONFIG_DIR/skills/audit/SKILL.md || { echo "skill not byte for byte"; fail=1; }
cmp -s $P/.apm/agents/x.md $CLAUDE_CONFIG_DIR/agents/x.md || { echo "agent not byte for byte"; fail=1; }
[ -f $CLAUDE_CONFIG_DIR/rules/okf-bundle.md ] || { echo "rule not under CLAUDE_CONFIG_DIR/rules"; fail=1; }
real_clean || fail=1
echo "== verdict fail=$fail"
exit $fail
