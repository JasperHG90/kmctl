#!/bin/bash
# Which glob forms does agy 1.4.0 match for plugin rules, including a hidden .okf/ folder?
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad
cd $S/live/tempconv && git checkout -q -- . && git clean -qfd -e apm_modules
export PATH=$S/live/tools:$PATH GEMINI_API_KEY="$(bash -ic 'printf %s "$GEMINI_API_KEY"' 2>/dev/null)"; unset GOOGLE_API_KEY
R=.agents/plugins/kmctl/rules; mkdir -p $R docs/guide; echo "# Guide" > docs/guide/intro.md
w(){ printf -- '---\ntrigger: glob\nglobs: %s\n---\n\nThe secret word of this rule is %s.\n' "$1" "$2" > $R/zz-$2.md; }
w '"**/.okf/**"' OKFSTAR; w '".okf/**"' OKFBARE; w '"**/docs/**, **/README.md"' DOCSLIST; w '"docs/**"' DOCSBARE; w '"{**/docs/**,**/README.md}"' BRACES; w '"**/src/**"' SRCSTAR
ask(){ timeout 300 agy -p "Step 1: call view_file on $1. Step 2: make no other tool calls at all. Reply with only the secret words that appear in your rules or system instructions right now, comma separated, or NONE." --model gemini-3.8-flash-high --dangerously-skip-permissions --print-timeout 250s 2>&1 | tail -1; }
a=$(ask .okf/index.md); b=$(ask docs/guide/intro.md); c=$(ask README.md)
echo ".okf/index.md -> $a"; echo "docs/guide/intro.md -> $b"; echo "README.md -> $c"
git checkout -q -- . && git clean -qfd -e apm_modules
has(){ case ",$(echo "$1" | tr -d ' ')," in *",$2,"*) return 0;; esac; return 1; }
ok=1
has "$a" OKFSTAR || ok=0; has "$a" OKFBARE && ok=0
has "$b" DOCSLIST || ok=0; has "$b" DOCSBARE && ok=0; has "$b" BRACES && ok=0; has "$b" SRCSTAR && ok=0
has "$c" DOCSLIST || ok=0
[ $ok = 1 ]
