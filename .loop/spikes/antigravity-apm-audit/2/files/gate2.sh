#!/bin/bash
# Gate check: on a fresh clone of a committed claude+antigravity install, does
# apm install --frozen + kmctl plugin patch leave git status --porcelain empty,
# and does a hand edit under .agents/skills/ make it non-empty?
set -u
WT=$PWD
S=$(mktemp -d)
APM="uvx --from apm-cli==0.33.0 apm"
KM="uv run --quiet --project $WT kmctl"
git clone -q --bare "$WT" $S/srv/kmctl.git && git -C $S/srv/kmctl.git tag v9.9.9 HEAD
cat > $S/gitconfig <<G
[url "file://$S/srv/kmctl.git"]
	insteadOf = https://github.com/JasperHG90/kmctl.git
	insteadOf = https://github.com/JasperHG90/kmctl
[user]
	email = t@e.invalid
	name = t
G
export GIT_CONFIG_GLOBAL=$S/gitconfig GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0
unset GITHUB_TOKEN GH_TOKEN GITHUB_APM_PAT GITHUB_COPILOT_PAT
$KM --version
gate() { $APM install --frozen >$S/frozen.log 2>&1 || { echo "frozen install failed"; tail -20 $S/frozen.log; }
         $KM plugin patch >$S/patch.log 2>&1 || { echo "patch failed"; tail -20 $S/patch.log; }
         git status --porcelain; }
mkdir $S/p && cd $S/p && git init -q
printf 'apm_modules/\n' > .gitignore
cat > apm.yml <<A
name: demo
version: 0.1.0
dependencies:
  apm:
    - git: https://github.com/JasperHG90/kmctl.git
      path: apm
      ref: v9.9.9
targets:
  - claude
  - antigravity
A
$APM install > $S/install.log 2>&1 || { echo "install failed"; tail -30 $S/install.log; exit 2; }
$KM plugin patch > $S/patch0.log 2>&1 || { echo "patch failed"; cat $S/patch0.log; exit 2; }
git add -A && git commit -qm install
echo "committed files: $(git ls-files | wc -l); .agents files: $(git ls-files .agents | wc -l); .claude files: $(git ls-files .claude | wc -l)"
git ls-files | grep -c apm_modules
# 1. clean fresh clone
git clone -q $S/p $S/c1 && cd $S/c1
out1=$(gate); echo "== clean clone porcelain: [${out1}]"
# 2. uncommitted hand edit in that clone
skill=$(git ls-files '.agents/skills/*SKILL.md' | head -1); echo "edited: $skill"
echo "hand edit" >> "$skill"
$APM install --frozen > $S/frozen-edit.log 2>&1; echo "after frozen only, edit: [$(git status --porcelain)]"; grep -i "architecture-review\|modified\|overwr\|skip" $S/frozen-edit.log | head -5
echo "hand edit" >> "$skill"
out2=$(gate); echo "== uncommitted edit porcelain: [${out2}]"
git diff --stat
# 3. committed hand edit, fresh clone
cd $S/p && echo "hand edit" >> "$skill" && git commit -qam edit
git clone -q $S/p $S/c2 && cd $S/c2
out3=$(gate); echo "== committed edit, fresh clone porcelain: [${out3}]"
# Pass: a clean clone stays clean and a committed edit shows. The uncommitted case is reported only.
[ -z "$out1" ] && [ -n "$out3" ]
