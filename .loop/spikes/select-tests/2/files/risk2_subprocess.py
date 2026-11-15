"""select-tests risk 2: do tests that run kmctl as a separate process show up in the map?

Usage: python risk2_subprocess.py MAP_JSON PROCS_JSON

Reads the per-test coverage map recorded at BASE (every Python process measured,
tagged with the test that started it via COV_TEST_ID) and the per-process data
summary. A test "drives kmctl as a process" when its function, or a helper or
fixture in its file it calls, launches kmctl: a ["kmctl", ...] or which("kmctl")
command, a `python -c "from kmctl import main"` shim, or uvx prek. Run
from the repository at BASE.

Prints, for those tests: how many have no src/ line in the map, how many
started a subprocess coverage measured, and which ran a kmctl copy outside src/.
Exits 0 when every default-suite test that runs kmctl in another process has
src/ lines in the map and at least one measured subprocess, 1 otherwise. Tests
that only build a wheel are listed apart: they run no kmctl code.
"""
import ast, json, re, sys
from collections import defaultdict
from pathlib import Path

raw = json.loads(Path(sys.argv[1]).read_text())
procs = json.loads(Path(sys.argv[2]).read_text())
tests = raw["tests"]
src_lines, outside_lines = defaultdict(int), defaultdict(int)
for f, per in raw["lines"].items():
    for ids in per.values():
        for t in ids:
            if f.startswith("src/"):
                src_lines[t] += 1
            elif f.startswith("/"):
                outside_lines[t] += 1
outside_files = sorted(f for f in raw["lines"] if f.startswith("/"))
# Tests that started at least one measured subprocess, and whether it ran tree src.
sub_tests, sub_src = defaultdict(int), defaultdict(int)
for name, p in procs.items():
    if len(p["contexts"]) == 1 and p["contexts"][0]:
        sub_tests[p["contexts"][0]] += 1
        sub_src[p["contexts"][0]] += p["in_tree"] > 0

# Runs kmctl in another process: by name on PATH, a found path, or a python -c shim.
RUNS = re.compile(r'which\(\s*"kmctl"|\[\s*"kmctl"|\[kmctl,|_kmctl_bin\(|\bMAIN\b|'
                  r'from kmctl import main|"-m",\s*"kmctl"|\["uvx",\s*"prek')
# Builds a wheel or sdist of kmctl (runs no kmctl code itself).
BUILDS = re.compile(r'"uv",\s*"build"')

def launchers(path, MARK):
    """Names of functions in `path` that launch kmctl, directly or through another."""
    text = path.read_text()
    tree = ast.parse(text)
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)}
    direct = {name for name, n in funcs.items() if MARK.search(ast.get_source_segment(text, n) or "")}
    calls = {name: {c.func.id for c in ast.walk(n) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
                   | {a.arg for a in n.args.args} for name, n in funcs.items()}
    out = set(direct)
    while True:
        more = {name for name, used in calls.items() if used & out} - out
        if not more:
            return out
        out |= more

by_file = defaultdict(list)
for t in tests:
    by_file[t.split("::", 1)[0]].append(t)

def scan(mark):
    found = []
    conf = launchers(Path("tests/conftest.py"), mark)
    for f, ids in sorted(by_file.items()):
        names = launchers(Path(f), mark) | conf
        found += [t for t in ids if t.split("::")[-1].split("[", 1)[0] in names]
    return found

drives = scan(RUNS)
builds = scan(BUILDS)

no_src = [t for t in drives if not src_lines.get(t)]
unmeasured = [t for t in drives if not sub_tests.get(t)]
print(f"map: {len(tests)} default-suite tests; kmctl files measured outside src/: {len(outside_files)}")
for f in outside_files[:5]:
    print("   ", f)
print(f"tests with lines in a kmctl copy outside src/: {sum(1 for t in tests if outside_lines[t])}")
started = {t for t, n in sub_tests.items() if n}
print(f"tests that started a Python subprocess running measured kmctl code: {len(started)} "
      f"({sum(1 for t in started if sub_src[t])} of them ran this tree's src/ in it), "
      f"{sum(sub_tests.values())} processes")
print(f"\ntests that drive kmctl as a process (static scan): {len(drives)} in "
      f"{len({t.split('::')[0] for t in drives})} files")
print(f"  with no src/ line in the map: {len(no_src)}")
print(f"  with no measured subprocess: {len(unmeasured)}")
print("\nper test: src lines | measured subprocesses (with src) | test")
for t in drives:
    print(f"  {src_lines[t]:6d} | {sub_tests[t]:3d} ({sub_src[t]:3d}) | {t}")
print(f"\ntests that build a kmctl wheel or sdist (run no kmctl code): {len(builds)}")
for t in builds:
    print(f"  {src_lines[t]:6d} | {sub_tests[t]:3d} ({sub_src[t]:3d}) | {t}")
sys.exit(0 if not no_src and not unmeasured else 1)
