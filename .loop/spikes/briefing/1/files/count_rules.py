"""Count words of the knowledge rules' constraints as a briefing would carry them.

Exits 0 when the constraints without WHY lines, plus a routing block (80 words)
and a state block (40 words), fit loopctl's 500-word briefing budget.
Words are counted as loopctl does: len(line.split()).
"""
import re, subprocess, sys
from pathlib import Path

RULES = ["/home/vscode/kmctl/.claude/rules/docs-layout.md",
         "/home/vscode/kmctl/.claude/rules/okf-bundle.md"]
BUDGET, ROUTING, STATE = 500, 80, 40
pat = re.compile(r'<constraint name="([^"]+)">\n(.*?)</constraint>', re.S)

def words(text): return sum(len(l.split()) for l in text.splitlines())

tot_with = tot_without = 0
for path in RULES:
    for name, body in pat.findall(Path(path).read_text()):
        # a WHY paragraph runs from "WHY:" to the first blank line
        why = re.match(r"WHY:.*?(\n\n|\Z)", body, re.S)
        rest = body[why.end():] if why else body
        w, wo = words(name) + words(body), words(name) + words(rest)
        tot_with += w; tot_without += wo
        print(f"{Path(path).name}:{name}: with_why={w} without_why={wo}")
whole = sum(words(Path(p).read_text()) for p in RULES)
print(f"constraints total: with_why={tot_with} without_why={tot_without}")
print(f"whole rule files: {whole}")
print(f"briefing with_why={tot_with+ROUTING+STATE} without_why={tot_without+ROUTING+STATE} budget={BUDGET}")
lb = subprocess.run(["loopctl", "briefing"], cwd="/home/vscode/kmctl", capture_output=True, text=True)
print(f"loopctl briefing words in kmctl: {words(lb.stdout)} (exit {lb.returncode})")
fits = tot_without + ROUTING + STATE <= BUDGET
print("fits without WHY:", fits, "| fits with WHY:", tot_with + ROUTING + STATE <= BUDGET)
sys.exit(0 if fits else 1)
