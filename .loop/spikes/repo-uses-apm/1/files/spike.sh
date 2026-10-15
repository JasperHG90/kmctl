#!/usr/bin/env bash
# Spike: does APM install a rule from jasperhg90/skills to .claude/rules/ with
# its front matter intact, and a skill to .claude/skills/?
# Exit 0 only when: both rules land in .claude/rules/ byte for byte with the
# source, and the skill lands in .claude/skills/ byte for byte.
set -u
W=$(mktemp -d)
export HOME="$W/home"; mkdir -p "$HOME"
git config --global user.email spike@example.invalid
git config --global user.name spike
PIN=f0813cd497dcc8575fabbea719f35f7aac96f81a   # skills HEAD: "make the rules installable with apm"

uv venv -q "$W/venv" && VIRTUAL_ENV="$W/venv" uv pip install -q apm-cli || exit 3
APM="$W/venv/bin/apm"; "$APM" --version

git clone -q https://github.com/jasperhg90/skills "$W/src" && git -C "$W/src" checkout -q "$PIN" || exit 3
echo "== source rules/ (first 3):"; ls "$W/src/rules" | head -3

mkdir "$W/proj"; cd "$W/proj"; git init -q
cat > apm.yml <<EOF
name: scratch
version: 0.1.0
targets: [claude]
dependencies:
  apm:
    - jasperhg90/skills/rules/python-testing.instructions.md#$PIN
    - jasperhg90/skills/rules/plain-language.instructions.md#$PIN
    - jasperhg90/skills/skills/tools/generate-art#$PIN
EOF
"$APM" install 2>&1 | grep -E '\[\+\]|\[x\]|\[\*\]|integrated'
echo "== files written (excluding .git, apm_modules):"
find . -path ./.git -prune -o -path ./apm_modules -prune -o -type f -print | sort
echo "== AGENTS.md/CLAUDE.md after install:"; ls AGENTS.md CLAUDE.md 2>&1
echo "== lock pins:"; grep -E 'resolved_commit|resolved_ref' apm.lock.yaml | sort | uniq -c

ok=0
for r in python-testing plain-language; do
  echo "== rule $r: front matter source vs installed"
  if [ ! -f ".claude/rules/$r.md" ]; then echo "MISSING .claude/rules/$r.md"; ok=1; continue; fi
  diff "$W/src/rules/$r.instructions.md" ".claude/rules/$r.md" | head -12 && echo "byte-identical" || ok=1
done
echo "== skill generate-art vs source:"
diff -r "$W/src/skills/tools/generate-art" .claude/skills/generate-art && echo "byte-identical" || ok=1

echo "== plain .md rule path (the form aim installs) accepted?"
sed -i "s#python-testing.instructions.md#python-testing.md#" apm.yml
"$APM" install 2>&1 | grep -E 'Invalid|must end' | head -3
git checkout -q -- . 2>/dev/null; git clean -qfd 2>/dev/null

echo "== RESULT: $([ $ok = 0 ] && echo 'risk does not hold' || echo 'risk holds: content not byte-identical or missing')"
rm -rf "$W"
exit $ok
