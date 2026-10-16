#!/usr/bin/env bash
# Risk 2 (dev items): does a consumer that installs the kmctl package get the
# repository's own dev rules from the root apm.yml, and is there a way to keep
# them out? The dev dependency is the real one the repo would use:
#   jasperhg90/skills/rules/plain-language.instructions.md#f0813cd
# Cases (each a git repo served over local HTTP, a clean consumer):
#   R1 root apm.yml dependencies.apm: [rule], consumer installs the repo root
#   R2 root apm.yml devDependencies.apm: [rule], consumer installs the repo
#      root; and `apm install` in the source repo itself
#   R3 root apm.yml dependencies.apm: [rule], consumer installs path: plugin
#      (a) plugin/ has no apm.yml  (b) plugin/apm.yml with no deps
#   V  apm.yml with no version: field, as a package (plugin/apm.yml) and as
#      the consumer's own manifest
# Exit 0 only when some route keeps the rule out of the consumer while the
# kmctl skills still reach it: R2 (devDependencies) or R3 (subfolder package).
PORT=8772
. /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/common.sh
RULE="jasperhg90/skills/rules/plain-language.instructions.md#f0813cd"
has_rule()  { [ -f "$W/c-$1/.claude/rules/plain-language.md" ]; }
has_skill() { [ -f "$W/c-$1/.claude/skills/audit/SKILL.md" ]; }
report() { echo "   rule in consumer: $(has_rule "$1" && echo YES || echo no); kmctl skills in consumer: $(has_skill "$1" && echo YES || echo no)"; files "$1" | sed 's/^/     /'; }
root_yml() {  # root_yml NAME SECTION: root apm.yml with RULE under SECTION.apm
  printf 'name: kmctl-dev\nversion: 0.1.0\ntargets: [claude]\n%s:\n  apm:\n    - %s\n' "$2" "$RULE" > "$W/$1/apm.yml"
}

echo "== R1: root dependencies.apm, consumer installs root"
new_src r1; root_yml r1 dependencies; publish r1
consumer r1 "    - git: $GIT/r1.git" "      allow_insecure: true"; report r1

echo "== R2: root devDependencies.apm, consumer installs root"
new_src r2; root_yml r2 devDependencies; publish r2
consumer r2 "    - git: $GIT/r2.git" "      allow_insecure: true"; report r2
R2=1; [ "$CEXIT" = 0 ] && ! has_rule r2 && has_skill r2 && R2=0
echo "-- R2 source repo itself: apm install"
( cd "$W/r2" && "$APM" install > "$W/r2-self.log" 2>&1 ); echo "   exit $?; rule installed in source repo: $([ -f "$W/r2/.claude/rules/plain-language.md" ] && echo YES || echo no)"
grep -n -A3 'devDependencies' "$W/r2/apm.lock.yaml" 2>/dev/null | head -5; grep -n 'dev' "$W/r2/apm.lock.yaml" 2>/dev/null | head -5

echo "== R3a: root dependencies.apm, consumer installs path: plugin (no plugin/apm.yml)"
new_src r3a; root_yml r3a dependencies; publish r3a
consumer r3a "    - git: $GIT/r3a.git" "      path: plugin" "      allow_insecure: true"; report r3a
R3a=1; [ "$CEXIT" = 0 ] && ! has_rule r3a && has_skill r3a && R3a=0

echo "== R3b: root dependencies.apm, consumer installs path: plugin (plugin/apm.yml, no deps)"
new_src r3b; root_yml r3b dependencies; printf 'name: kmctl\nversion: 0.1.0\n' > "$W/r3b/plugin/apm.yml"; publish r3b
consumer r3b "    - git: $GIT/r3b.git" "      path: plugin" "      allow_insecure: true"; report r3b
R3b=1; [ "$CEXIT" = 0 ] && ! has_rule r3b && has_skill r3b && R3b=0

echo "== V1: plugin/apm.yml with no version: field"
new_src v1; printf 'name: kmctl\n' > "$W/v1/plugin/apm.yml"; publish v1
consumer v1 "    - git: $GIT/v1.git" "      path: plugin" "      allow_insecure: true"
echo "   kmctl skills in consumer: $(has_skill v1 && echo YES || echo no)"
echo "== V2: consumer apm.yml with no version: field"
rm -rf "$W/c-v2"; mkdir "$W/c-v2"; ( cd "$W/c-v2" && git init -q )
printf 'name: c-v2\ntargets: [claude]\ndependencies:\n  apm:\n    - git: %s/b.git\n      path: plugin\n      allow_insecure: true\n' "$GIT" > "$W/c-v2/apm.yml"
new_src b; publish b
( cd "$W/c-v2" && "$APM" install --allow-insecure > "$W/c-v2.log" 2>&1 ); echo "   exit $?"; grep -E '\[x\]' "$W/c-v2.log" | head -3

echo "== RESULT: R2(devDependencies)=$R2 R3a=$R3a R3b=$R3b (0 = rule kept out, skills in)"
[ $R2 = 0 ] || [ $R3a = 0 ] || [ $R3b = 0 ]
