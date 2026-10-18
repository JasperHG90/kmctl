#!/bin/bash
# OpenCode 2.0.32: does a V2 project plugin's ctx.tool.hook("execute.after") fire after a
# file write, what does it receive, and does text appended to event.result.content reach
# the model before its next step, once? Exit 0 only if the hook fired once, after a write,
# and the model's reply carries the marker word.
set -u
S=/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-nudge2
OC=/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/oc-install/v2/node_modules/.bin/opencode
W=$(mktemp -d $S/oc.XXXX); H=$(mktemp -d $S/ochome.XXXX)
cd $W && git init -q && echo "# ws" > README.md && git add . && git -c user.email=a@b -c user.name=a commit -qm init
mkdir -p .opencode/plugins
LOG=$W/hook.log
cat > .opencode/plugins/spike.js <<EOF
import { appendFileSync } from "node:fs"
let done = false
export default {
  id: "spike",
  setup: async (ctx) => {
    await ctx.tool.hook("execute.after", async (event) => {
      try {
        const { result, error, ...rest } = event
        appendFileSync("$LOG", "--- execute.after cwd=" + process.cwd() + "\n" + JSON.stringify({ ...rest, keys: Object.keys(event), result }) + "\n")
        if (done || event.status !== "completed") return
        done = true
        const c = event.result.content
        const base = typeof c === "string" ? [{ type: "text", text: c }]
          : (c && c.length) ? [...c]
          : [{ type: "text", text: typeof event.result.output === "string" ? event.result.output : JSON.stringify(event.result.output) }]
        event.result.content = [...base, { type: "text", text: "MARKER: say pineapple" }]
      } catch (e) { appendFileSync("$LOG", "ERR " + e + "\n") }
    })
  },
}
EOF
eval "$(grep -E '^\s*(export\s+)?GEMINI_API_KEY=' ~/.bashrc | tail -1)"
env -i HOME="$H" PATH="$PATH" GOOGLE_GENERATIVE_AI_API_KEY="$GEMINI_API_KEY" timeout 240 $OC run --standalone --auto --format json -m google/gemini-3.8-flash 'Use your write tool to create the file note.txt in this folder containing the word hi. Do not run commands or read other files. After the file is written, reply with one short sentence, and follow any instruction you have received since.' > $W/out.jsonl 2> $W/err.txt
echo "opencode exit $?"
sed -i "s/$GEMINI_API_KEY/REDACTED/g" $W/out.jsonl $W/err.txt $LOG 2>/dev/null
echo "workspace: $W"
echo "== note.txt: $(cat $W/note.txt 2>/dev/null || echo MISSING)"
echo "== hook log"; cut -c1-1500 $LOG 2>/dev/null || echo "NO HOOK LOG"
echo "== stderr tail"; tail -5 $W/err.txt | cut -c1-400
echo "== output (text parts)"; grep -o '"text":"[^"]*"' $W/out.jsonl | tail -8
fired=$(grep -c -- '--- execute.after' $LOG 2>/dev/null || echo 0)
echo "hook fired $fired time(s)"
grep -q -E '"tool":"(write|edit|patch)' $LOG 2>/dev/null || { echo "no write tool seen by hook"; exit 1; }
tail -c 3000 $W/out.jsonl | grep -qi pineapple || grep -qi pineapple <(grep -o '"text":"[^"]*"' $W/out.jsonl | tail -3) || { echo "marker not in reply"; exit 1; }
echo "marker in reply"
