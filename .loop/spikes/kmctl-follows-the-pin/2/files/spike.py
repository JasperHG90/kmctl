"""Spike: does a detached refresh started by a session hook block the hook or die with it?

Modes:
  parent CACHE SLEEP  -- stand-in for `kmctl briefing`: print, spawn detached child, exit
  child CACHE SLEEP   -- sleep, then write CACHE
  (no args)           -- run checks a, b, c, d
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ME = os.path.abspath(__file__)


def parent(cache, sleep):
    print("briefing line", flush=True)
    subprocess.Popen(
        [sys.executable, ME, "child", cache, sleep],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def child(cache, sleep):
    time.sleep(float(sleep))
    Path(cache).write_text("filled\n")


def wait_for(path, limit):
    end = time.monotonic() + limit
    while time.monotonic() < end:
        if path.exists():
            return True
        time.sleep(0.1)
    return path.exists()


def main():
    tmp = Path(tempfile.mkdtemp())
    ok = True
    results = {}

    # a) + b): subprocess.run with capture_output (pipe read to EOF)
    cache = tmp / "a_run.txt"
    t0 = time.monotonic()
    r = subprocess.run([sys.executable, ME, "parent", str(cache), "3"], capture_output=True, text=True)
    dt = time.monotonic() - t0
    early = cache.exists()
    filled = wait_for(cache, 6)
    t_fill = time.monotonic() - t0
    results["a_run"] = dict(return_s=round(dt, 3), stdout=r.stdout.strip(), cache_before_return=early, cache_filled=filled, fill_s=round(t_fill, 2))
    ok &= dt < 1 and r.stdout.strip() == "briefing line" and not early and filled

    # a) + b): shell $(...) capture
    cache = tmp / "a_shell.txt"
    t0 = time.monotonic()
    r = subprocess.run(["bash", "-c", f'out=$({sys.executable} {ME} parent {cache} 3); echo "got:$out"'], capture_output=True, text=True)
    dt = time.monotonic() - t0
    early = cache.exists()
    filled = wait_for(cache, 6)
    t_fill = time.monotonic() - t0
    results["a_shell"] = dict(return_s=round(dt, 3), stdout=r.stdout.strip(), cache_before_return=early, cache_filled=filled, fill_s=round(t_fill, 2))
    ok &= dt < 1 and r.stdout.strip() == "got:briefing line" and not early and filled

    # c): caller puts the parent in its own process group, then kills the group after it exits
    cache = tmp / "c_killpg.txt"
    t0 = time.monotonic()
    p = subprocess.Popen([sys.executable, ME, "parent", str(cache), "3"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    pgid = os.getpgid(p.pid)
    out, _ = p.communicate()
    dt = time.monotonic() - t0
    try:
        os.killpg(pgid, signal.SIGKILL)
        killed = "sent"
    except ProcessLookupError:
        killed = "group already empty"
    filled = wait_for(cache, 6)
    t_fill = time.monotonic() - t0
    results["c_killpg"] = dict(return_s=round(dt, 3), killpg=killed, cache_filled=filled, fill_s=round(t_fill, 2))
    ok &= dt < 1 and filled

    # d): real Claude Code SessionStart hook, if claude is on PATH and logged in
    claude = shutil.which("claude")
    if claude:
        cache = tmp / "d_claude.txt"
        hook = f"{sys.executable} {ME} parent {cache} 25"
        settings = {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": hook}]}]}}
        t0 = time.monotonic()
        try:
            r = subprocess.run(
                [claude, "-p", "--model", "haiku", "--settings", json.dumps(settings), "Reply with the single word ok."],
                capture_output=True, text=True, timeout=60, cwd=tmp, stdin=subprocess.DEVNULL,
            )
            dt = time.monotonic() - t0
            early = cache.exists()
            ran = r.returncode == 0
            filled = wait_for(cache, 40) if ran else False
            results["d_claude"] = dict(exit=r.returncode, return_s=round(dt, 2), stdout=r.stdout.strip()[:200], stderr=r.stderr.strip()[:300], cache_before_return=early, cache_filled=filled, fill_s=round(time.monotonic() - t0, 2))
            if ran:
                ok &= dt < 25 and not early and filled
            else:
                results["d_claude"]["note"] = "claude -p failed; d not counted"
        except subprocess.TimeoutExpired:
            results["d_claude"] = dict(note="claude -p timed out at 60 s")
            ok = False
    else:
        results["d_claude"] = dict(note="claude not on PATH; a/b/c model it")

    print(json.dumps(results, indent=2))
    print("RISK DOES NOT HOLD" if ok else "RISK HOLDS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "parent":
        parent(*sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == "child":
        child(*sys.argv[2:])
    else:
        main()
