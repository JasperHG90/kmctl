#!/usr/bin/env bash
# Does a Claude Code PostToolUse hook (matcher Write|Edit|MultiEdit|Bash) get cwd,
# tool_name, tool_input on stdin, and does its additionalContext reach the model?
# Exits 0 only when both hold for Write and Bash, and empty / {} output is harmless.
set -u
unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT
W=$(mktemp -d)
fail=0
mkhook() { # $1 mode: marker|empty|braces
  cat > "$W/hook-$1.sh" <<H
#!/usr/bin/env bash
in=\$(cat)
printf '%s\n' "\$in" >> "$W/log-$1.jsonl"
printf 'PWD=%s PROJECT_DIR=%s\n' "\$PWD" "\${CLAUDE_PROJECT_DIR:-}" >> "$W/env-$1.txt"
case $1 in
  marker) echo '{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "MARKER-7731: say the word pineapple in your final answer"}}' ;;
  braces) echo '{}' ;;
  empty) : ;;
esac
exit 0
H
  chmod +x "$W/hook-$1.sh"
  cat > "$W/settings-$1.json" <<J
{"hooks": {"PostToolUse": [{"matcher": "Write|Edit|MultiEdit|Bash",
  "hooks": [{"type": "command", "command": "$W/hook-$1.sh", "timeout": 10}]}]}}
J
}
run() { # $1 name $2 mode $3 prompt
  repo="$W/repo-$1"; mkdir -p "$repo/sub"; git -C "$repo" init -q
  start=$(date +%s)
  ( cd "$repo" && timeout 150 claude -p --model haiku --settings "$W/settings-$2.json" \
      --permission-mode acceptEdits --allowedTools "Write Edit Bash" \
      "$3" ) > "$W/out-$1.txt" 2> "$W/err-$1.txt"
  rc=$?
  echo "== case $1 (hook $2) rc=$rc secs=$(( $(date +%s) - start ))"
  echo "-- answer:"; cat "$W/out-$1.txt"; echo "-- stderr:"; head -5 "$W/err-$1.txt"
  echo "-- hook env:"; cat "$W/env-$2.txt" 2>/dev/null
  echo "-- hook stdin (keys, tool_name, cwd):"
  python3 -c '
import json,sys
n=bad=0
for l in open(sys.argv[1]):
    l=l.strip()
    if not l: continue
    d=json.loads(l)
    print(sorted(d), d.get("tool_name"), d.get("cwd"), json.dumps(d.get("tool_input"))[:160])
    n+=1; bad+= d.get("cwd")!=sys.argv[2] or not d.get("tool_name") or not d.get("tool_input")
sys.exit(1 if n==0 or bad else 0)
' "$W/log-$2.jsonl" "$(cd "$repo" && pwd -P)" || { echo "FAIL: hook stdin missing, or cwd/tool_name/tool_input wrong"; fail=1; }
  rm -f "$W/log-$2.jsonl" "$W/env-$2.txt"
  echo "$rc" > "$W/rc-$1"; echo "$repo" > "$W/repo-of-$1"
}
for m in marker empty braces; do mkhook $m; done

run write marker "Use the Write tool to create the file note.txt containing hello. Do not use Bash. Then answer in one short sentence."
grep -qi pineapple "$W/out-write.txt" || { echo "FAIL: write answer lacks pineapple"; fail=1; }
[ -f "$W/repo-write/note.txt" ] || { echo "FAIL: note.txt missing"; fail=1; }

run bash marker "Use the Bash tool to run exactly: echo hi > x.txt . Do not use other tools. Then answer in one short sentence."
grep -qi pineapple "$W/out-bash.txt" || { echo "FAIL: bash answer lacks pineapple"; fail=1; }
[ -f "$W/repo-bash/x.txt" ] || { echo "FAIL: x.txt missing"; fail=1; }

run empty empty "Use the Bash tool to run exactly: echo hi > x.txt . Then answer in one short sentence."
[ "$(cat $W/rc-empty)" = 0 ] && [ -f "$W/repo-empty/x.txt" ] || { echo "FAIL: empty-output hook run"; fail=1; }

run braces braces "Use the Write tool to create the file note.txt containing hello. Then answer in one short sentence."
[ "$(cat $W/rc-braces)" = 0 ] && [ -f "$W/repo-braces/note.txt" ] || { echo "FAIL: {} hook run"; fail=1; }

echo "RESULT fail=$fail"
exit $fail
