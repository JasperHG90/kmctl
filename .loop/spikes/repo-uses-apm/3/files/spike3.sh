#!/usr/bin/env bash
# Spike: does APM 0.33.0 install all 13 aim rules and 3 skills from
# jasperhg90/skills with paths: scoping equal to upstream applyTo, bodies equal
# to upstream, and skills byte for byte?
# Exit 0 only when, for every rule: (a) .claude/rules/<name>.md exists,
# (b) its paths: list equals upstream applyTo as a list (no applyTo -> no front
# matter), (c) its body equals the upstream body byte for byte; and (d) every
# skill folder equals upstream byte for byte.
# "Body" = text after the closing '---' of front matter (whole file if none),
# with leading blank lines removed on both sides (APM drops the blank line when
# it removes the whole front matter; spike 2).
# Also prints, per rule, a diff of paths: and body against kmctl's current
# aim-installed file (read only).
set -u
KM=/home/vscode/kmctl
W=$(mktemp -d)
export HOME="$W/home"; mkdir -p "$HOME"
git config --global user.email spike@example.invalid
git config --global user.name spike
PIN=f0813cd497dcc8575fabbea719f35f7aac96f81a
echo "== upstream main now: $(git ls-remote https://github.com/jasperhg90/skills refs/heads/main | cut -f1)"
echo "== pin: $PIN"

uv venv -q "$W/venv" && VIRTUAL_ENV="$W/venv" uv pip install -q apm-cli==0.33.0 pyyaml || exit 3
APM="$W/venv/bin/apm"; PY="$W/venv/bin/python"; "$APM" --version

git clone -q https://github.com/jasperhg90/skills "$W/src" && git -C "$W/src" checkout -q "$PIN" || exit 3

RULES="async-python dependency-choice httpx-for-http interface-audience plain-language pre-existing-issues prompts-may-code-must pydantic-boundaries python-docstrings python-testing python-type-hints uv-installer prek-code-quality"
SKILLS="agent-creator rule-creator generate-art"

mkdir "$W/proj"; cd "$W/proj"; git init -q
{
  echo "name: scratch"; echo "version: 0.1.0"; echo "targets: [claude]"
  echo "dependencies:"; echo "  apm:"
  for r in $RULES; do echo "    - jasperhg90/skills/rules/$r.instructions.md#$PIN"; done
  for s in $SKILLS; do echo "    - jasperhg90/skills/skills/tools/$s#$PIN"; done
} > apm.yml
"$APM" install > "$W/install.log" 2>&1; echo "== apm install exit: $?"
grep -E 'integrated|Installed|\[x\]' "$W/install.log"
echo "== files written (excluding .git, apm_modules):"
find . -path ./.git -prune -o -path ./apm_modules -prune -o -type f -print | sort
echo "== lock pins:"; grep -E 'resolved_commit' apm.lock.yaml | sort | uniq -c

cat > "$W/cmp.py" <<'EOF'
import sys, difflib, yaml
src, proj, km = sys.argv[1:4]
rules = sys.argv[4:]
def split(text):
    fm, body = None, text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        fm = yaml.safe_load(text[4:end]) or {}
        body = text[end + 5:]
    return fm, body.lstrip("\n")
def as_list(v):
    if v is None: return None
    if isinstance(v, list): return [str(x).strip() for x in v]
    return [p.strip() for p in str(v).split(",") if p.strip()]
fail = 0
for r in rules:
    up_fm, up_body = split(open(f"{src}/rules/{r}.instructions.md").read())
    want = as_list((up_fm or {}).get("applyTo"))
    try:
        got_text = open(f"{proj}/.claude/rules/{r}.md").read()
    except FileNotFoundError:
        print(f"[{r}] (a) FAIL missing"); fail = 1; continue
    got_fm, got_body = split(got_text)
    if want is None:
        b_ok = got_fm is None
    else:
        b_ok = got_fm is not None and set(got_fm) == {"paths"} and as_list(got_fm["paths"]) == want
    c_ok = got_body == up_body
    fail |= not (b_ok and c_ok)
    print(f"[{r}] (a) ok  (b) {'ok' if b_ok else 'FAIL'} upstream applyTo={want} installed fm={got_fm}  (c) {'ok' if c_ok else 'FAIL'}")
    # against kmctl today (read only)
    cur_fm, cur_body = split(open(f"{km}/.claude/rules/{r}.md").read())
    cur_paths = as_list((cur_fm or {}).get("paths"))
    new_paths = as_list((got_fm or {}).get("paths"))
    print(f"    vs kmctl today: paths {'same' if cur_paths == new_paths else 'CHANGES'}: {cur_paths} -> {new_paths}; "
          f"other keys dropped: {sorted(set(cur_fm or {}) - {'paths'})}; body {'same' if cur_body == got_body else 'CHANGES'}")
    if cur_body != got_body:
        for line in difflib.unified_diff(cur_body.splitlines(), got_body.splitlines(),
                                         f"kmctl/.claude/rules/{r}.md", f"apm/.claude/rules/{r}.md", lineterm="", n=1):
            print("      " + line)
sys.exit(fail)
EOF
echo "== rules"
"$PY" -I "$W/cmp.py" "$W/src" "$W/proj" "$KM" $RULES; ok=$?

echo "== skills"
for s in $SKILLS; do
  if diff -r "$W/src/skills/tools/$s" ".claude/skills/$s" >/dev/null; then echo "[$s] (d) ok byte-identical"
  else echo "[$s] (d) FAIL"; diff -r "$W/src/skills/tools/$s" ".claude/skills/$s" | head -20; ok=1; fi
  if diff -r "$KM/.claude/skills/$s" ".claude/skills/$s" >/dev/null; then echo "    vs kmctl today: same"
  else echo "    vs kmctl today: CHANGES"; diff -r "$KM/.claude/skills/$s" ".claude/skills/$s" | head -20; fi
done

echo "== RESULT: $([ $ok = 0 ] && echo 'risk does not hold' || echo 'risk holds')"
rm -rf "$W"
exit $ok
