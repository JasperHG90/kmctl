"""Build throwaway two-tree repos and see which layout one root pytest run collects cleanly.

Root tree mirrors kmctl: tests/ with no __init__.py, tests/conftest.py,
tests/fixtures/audit_repo.py imported as `from fixtures.audit_repo import ...`,
pyproject pythonpath=["."], addopts as in kmctl. Second tree at
packages/kmaudit/tests/. Exits 0 only if layout E (the candidate that keeps
duplicate basenames and kmctl's imports untouched) passes with all 5 tests, in both no-arg and explicit-path runs.
"""
import subprocess, sys, tempfile, textwrap
from pathlib import Path

PYPROJECT = textwrap.dedent('''
    [tool.pytest.ini_options]
    addopts = ["--strict-markers", "-m", "not integration"]
    pythonpath = ["."]
    markers = ["integration: x"]
    {extra}
''')

def w(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(s))

def kmctl_tree(root: Path):
    w(root / "tests/conftest.py", "import pytest\n@pytest.fixture\ndef who(): return 'kmctl'\n")
    w(root / "tests/fixtures/audit_repo.py", "OWNER = 'kmctl'\ndef make_repo(): return 'kmctl'\n")
    for name in ("test_audit.py", "test_cli.py"):
        w(root / "tests" / name, """
            from fixtures.audit_repo import OWNER, make_repo
            def test_owner(who):
                assert OWNER == 'kmctl' and make_repo() == 'kmctl' and who == 'kmctl'
        """)

def kmaudit_tree(root: Path, fixtures_pkg: str, import_line: str, dup_names: bool, as_package: bool):
    t = root / "packages/kmaudit/tests"
    if as_package:
        w(t / "__init__.py", "")
        w(t / fixtures_pkg / "__init__.py", "")
    w(t / "conftest.py", "import pytest\n@pytest.fixture\ndef who(): return 'kmaudit'\n")
    w(t / fixtures_pkg / "audit_repo.py", "OWNER = 'kmaudit'\ndef make_repo(): return 'kmaudit'\n")
    names = ("test_audit.py", "test_cli.py") if dup_names else ("test_kmaudit_audit.py", "test_kmaudit_cli.py")
    for name in names:
        w(t / name, f"""
            {import_line}
            def test_owner(who):
                assert OWNER == 'kmaudit' and make_repo() == 'kmaudit' and who == 'kmaudit'
        """)
    # plus one kmaudit-only test file
    w(t / "test_only_kmaudit.py", f"""
        {import_line}
        def test_x(): assert OWNER == 'kmaudit'
    """)

CASES = {
    "A default mode, same `fixtures` name, duplicate test basenames": dict(
        fx="fixtures", imp="from fixtures.audit_repo import OWNER, make_repo", dup=True, pkg=False, extra=""),
    "B default mode, same `fixtures` name, unique test basenames": dict(
        fx="fixtures", imp="from fixtures.audit_repo import OWNER, make_repo", dup=False, pkg=False, extra=""),
    "C default mode, renamed `kmaudit_fixtures`, unique test basenames": dict(
        fx="kmaudit_fixtures", imp="from kmaudit_fixtures.audit_repo import OWNER, make_repo", dup=False, pkg=False, extra=""),
    "D default mode, renamed `kmaudit_fixtures`, duplicate test basenames": dict(
        fx="kmaudit_fixtures", imp="from kmaudit_fixtures.audit_repo import OWNER, make_repo", dup=True, pkg=False, extra=""),
    "E default mode, kmaudit tests/ is a package (__init__.py), relative fixtures import, duplicate basenames": dict(
        fx="fixtures", imp="from .fixtures.audit_repo import OWNER, make_repo", dup=True, pkg=True, extra=""),
    "F --import-mode=importlib, nothing else changed, duplicate basenames": dict(
        fx="kmaudit_fixtures", imp="from kmaudit_fixtures.audit_repo import OWNER, make_repo", dup=True, pkg=False,
        extra='# importlib\n'),
    "G --import-mode=importlib + pythonpath adds both tests dirs, renamed `kmaudit_fixtures`, duplicate basenames": dict(
        fx="kmaudit_fixtures", imp="from kmaudit_fixtures.audit_repo import OWNER, make_repo", dup=True, pkg=False,
        extra='# importlib+path\n'),
}

results = {}
for label, c in CASES.items():
    root = Path(tempfile.mkdtemp())
    extra = c["extra"]
    w(root / "pyproject.toml", PYPROJECT.format(extra="").replace('pythonpath = ["."]',
        'pythonpath = [".", "tests", "packages/kmaudit/tests"]' if "path" in extra else 'pythonpath = ["."]'))
    kmctl_tree(root)
    kmaudit_tree(root, c["fx"], c["imp"], c["dup"], c["pkg"])
    ok = True
    for paths in ([], ["tests", "packages/kmaudit/tests"]):
        args = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *paths]
        if extra.startswith("# importlib"):
            args.append("--import-mode=importlib")
        r = subprocess.run(args, cwd=root, capture_output=True, text=True)
        tail = [l for l in r.stdout.splitlines() if l.strip()][-4:]
        ok = ok and r.returncode == 0 and "5 passed" in r.stdout
        print(f"--- {label} | paths={paths or '(none, rootdir recursion)'} exit={r.returncode}")
    results[label] = ok
    print(f"=== clean={'yes' if ok else 'no'}")
    for l in tail:
        print("   ", l[:200])
    if not ok:
        for l in r.stdout.splitlines():
            if "Error" in l or "mismatch" in l or "assert" in l.lower():
                print("   >", l[:200]); 
        print()

import pytest
print("pytest", pytest.__version__)
sys.exit(0 if results[[k for k in CASES if k.startswith("E")][0]] else 1)
