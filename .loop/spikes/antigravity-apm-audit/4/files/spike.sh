#!/usr/bin/env bash
# Risk 2 of antigravity-apm-audit: can kmctl's package (apm/apm.yml) or the
# consumer's apm.yml make `apm audit --ci` (APM 0.33.0) pass config-consistency
# and drift for a claude+antigravity install followed by kmctl plugin patch?
# Each variant installs a copy of this checkout's apm/ (served from a file://
# bare repo via git insteadOf), runs kmctl plugin patch, then apm audit --ci.
# Exit 0 only when no variant clears either check (the risk does not hold);
# a variant only clears drift if okf's own Stop handler is still out of
# .agents/hooks.json and okf's skills and stop script are still under .agents/.
set -u
KM=$(pwd); S=$(mktemp -d); UVC=$(uv cache dir); RH=$HOME
unset GITHUB_TOKEN GH_TOKEN GITHUB_APM_PAT GITHUB_COPILOT_PAT ADO_APM_PAT
export HOME=$S/home XDG_DATA_HOME=$S/home/.local/share XDG_CONFIG_HOME=$S/home/.config \
  UV_CACHE_DIR=$UVC GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0 CLAUDE_CONFIG_DIR=$S/home/.claude
mkdir -p $CLAUDE_CONFIG_DIR
APM="uvx --from apm-cli==0.33.0 apm"
OKF='scaccogatto/okf-skills#a8b96420de90d102c43cda1693d01ec4f925f2ab'
BUNDLE='    - {name: bundle, registry: false, transport: stdio, command: uv, args: [run, "${CLAUDE_PLUGIN_ROOT}/servers/okf_mcp.py"]}'
cleared=""
run() { # $1 name, $2 python edit of package apm.yml (var t), $3 consumer apm.yml extra, $4 install flags
  local n=$1 W=$S/$1; echo "== $n"
  mkdir -p $W/work && git -C $KM archive HEAD | tar -x -C $W/work  # whole checkout: kmctl plugin patch builds kmctl from the locked commit
  [ -n "$2" ] && python3 -c "p='$W/work/apm/apm.yml';t=open(p).read();$2;open(p,'w').write(t)"
  git -C $W/work init -q -b main && git -C $W/work add -A && git -C $W/work -c user.email=t@e -c user.name=t commit -qm t
  git clone -q --bare $W/work $W/kmctl.git
  # A fresh HOME per variant: APM caches git checkouts by URL and ref.
  export GIT_CONFIG_GLOBAL=$W/gitconfig HOME=$W/home XDG_DATA_HOME=$W/home/.local/share XDG_CONFIG_HOME=$W/home/.config CLAUDE_CONFIG_DIR=$W/home/.claude
  mkdir -p $CLAUDE_CONFIG_DIR
  export APM_CACHE_DIR=$W/apmcache
  git config --global url.file://$W/kmctl.git.insteadOf https://github.com/JasperHG90/kmctl.git
  git config --global --add url.file://$W/kmctl.git.insteadOf https://github.com/JasperHG90/kmctl
  local C=$W/c; mkdir -p $C/.agents $C/.claude; git -C $C init -q
  printf 'name: c\nversion: 0.0.1\ntargets: [claude, antigravity]\ndependencies:\n  apm:\n    - {git: https://github.com/JasperHG90/kmctl.git, path: apm, ref: main}\n%s' "$3" > $C/apm.yml
  (cd $C && $APM install $4 > install.txt 2>&1) || { echo "  install failed:"; tail -5 $C/install.txt; return; }
  local sha=$(git -C $W/work rev-parse HEAD)
  grep -q "resolved_commit: $sha" $C/apm.lock.yaml || { echo "  lock does not hold the served commit $sha; stopping"; exit 3; }
  (cd $C && env -u APM_CACHE_DIR HOME=$RH uv run -q --project $KM kmctl plugin patch > patch.txt 2>&1) || { echo "  patch failed"; tail -3 $C/patch.txt; }
  (cd $C && $APM audit --ci --no-policy --no-fail-fast -f json -o audit.json > audit.txt 2>&1); echo "  audit rc=$?"
  OKF_STOP=$(cd $KM && env -u GIT_CONFIG_GLOBAL HOME=$RH uv run -q python -c 'from kmctl.antigravity import APM_OKF_STOP;print(APM_OKF_STOP)') \
  python3 - $C <<'PY' > $W/verdict
import json,sys,pathlib
c=pathlib.Path(sys.argv[1]); d=json.load(open(c/"audit.json")); r={x["name"]:x for x in d["checks"]}
hooks=(c/".agents/hooks.json").read_text() if (c/".agents/hooks.json").exists() else ""
import os
okf_stop_in = json.dumps(os.environ["OKF_STOP"]) in hooks
okf_skills = (c/".agents/skills/okf/SKILL.md").exists()
script = (c/".agents/hooks/okf-skills/hooks/okf-stop-check.sh").exists()
def kinds(f):
    s=json.load(open(c/f)).get("mcpServers",{}) if (c/f).exists() else {}
    return {k:("kmctl launcher" if "okf_mcp.py \\\"$d/.okf" in json.dumps(v) or "$d/.okf" in json.dumps(v) else "okf's own (CLAUDE_PLUGIN_ROOT)" if "CLAUDE_PLUGIN_ROOT" in json.dumps(v) else "other") for k,v in s.items()}
servers = {"agy": kinds(".agents/mcp_config.json"), "claude": kinds(".mcp.json")}
for k in ("config-consistency","drift"):
    x=r.get(k,{}); print(f"  {k}: {'pass' if x.get('passed') else 'FAIL'} {'; '.join(x.get('details') or [])[:200]}")
print(f"  okf Stop handler in .agents/hooks.json: {okf_stop_in}; okf skills in .agents: {okf_skills}; okf-stop-check.sh in .agents: {script}; agy servers: {servers}")
cc = r.get("config-consistency",{}).get("passed")
dr = r.get("drift",{}).get("passed") and not okf_stop_in and okf_skills and script
print("CLEARS", ("cc " if cc else "") + ("drift" if dr else ""))
PY
  cat $W/verdict | sed '/^CLEARS/d'; c=$(sed -n 's/^CLEARS *//p' $W/verdict); [ -n "$c" ] && cleared="$cleared $n($c)"
}
run base "" "" ""
run trust-transitive-mcp "" "" "--trust-transitive-mcp"
run rename-okf-bundle-to-bundle "t=t.replace('- name: okf-bundle','- name: bundle')" "" ""
run consumer-declares-bundle "" "  mcp:
$BUNDLE
" ""
run drop-okf-bundle-consumer-declares "t=t[:t.index('  mcp:')]" "  mcp:
$BUNDLE
" ""
run okf-skills-claude-only "t=t.replace('    - $OKF','    - {git: https://github.com/scaccogatto/okf-skills.git, ref: a8b96420de90d102c43cda1693d01ec4f925f2ab, targets: [claude]}')" "" ""
run okf-skills-skill-subset "t=t.replace('    - $OKF','    - {git: https://github.com/scaccogatto/okf-skills.git, ref: a8b96420de90d102c43cda1693d01ec4f925f2ab, skills: [backfill, okf, validate, visualize]}')" "" ""
echo "variants that clear a check:${cleared:- none}"
[ -z "$cleared" ]
