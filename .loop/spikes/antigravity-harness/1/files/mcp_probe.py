"""Does `uv run <raw URL>` start okf's MCP server and answer over stdio?

Cases:
  A  cwd holds .okf/, no argument          (default ./.okf)
  B  cwd elsewhere, bundle dir as argument (`uv run <url> <bundle-dir>`)
  C  cwd elsewhere, no argument            (shows whether cwd matters)
Each case: initialize -> notifications/initialized -> tools/list ->
tools/call search_concepts("hello"). Exit 0 only when A and B both list the
three tools and find the test concept.
"""
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

URL = ("https://raw.githubusercontent.com/scaccogatto/okf-skills/"
       "a8b96420de90d102c43cda1693d01ec4f925f2ab/servers/okf_mcp.py")
WANT = {"search_concepts", "read_concept", "get_neighbors"}


def run_case(name, cwd, args, timeout):
    t0 = time.time()
    p = subprocess.Popen(["uv", "run", URL, *args], cwd=cwd,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l) for l in p.stdout], daemon=True).start()
    err = []
    threading.Thread(target=lambda: [err.append(l) for l in p.stderr], daemon=True).start()

    def send(msg):
        p.stdin.write(json.dumps(msg) + "\n")
        p.stdin.flush()

    def recv(want_id, t):
        end = time.time() + t
        while time.time() < end:
            try:
                line = q.get(timeout=max(0.1, end - time.time()))
            except queue.Empty:
                break
            try:
                m = json.loads(line)
            except ValueError:
                print(f"  [{name}] non-JSON stdout: {line.rstrip()!r}")
                continue
            if m.get("id") == want_id:
                return m
        return None

    res = {"case": name, "ok": False}
    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "spike", "version": "0"}}})
        init = recv(1, timeout)
        res["init_seconds"] = round(time.time() - t0, 1)
        if not init or "result" not in init:
            res["init"] = init
            return res
        r = init["result"]
        res["serverInfo"] = r.get("serverInfo")
        res["protocolVersion"] = r.get("protocolVersion")
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tl = recv(2, 20)
        tools = sorted(t["name"] for t in (tl or {}).get("result", {}).get("tools", []))
        res["tools"] = tools
        send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "search_concepts", "arguments": {"query": "hello"}}})
        call = recv(3, 20)
        cr = (call or {}).get("result", {})
        text = " ".join(c.get("text", "") for c in cr.get("content", []))
        res["search_isError"] = cr.get("isError")
        res["search_text"] = text[:300]
        res["ok"] = WANT <= set(tools) and not cr.get("isError") and "hello" in text
        return res
    finally:
        p.kill()
        p.wait()
        res["stderr_tail"] = "".join(err)[-400:]
        print(json.dumps(res, indent=2))


def main():
    print("uv:", subprocess.run(["uv", "--version"], capture_output=True,
                                text=True).stdout.strip())
    root = Path(tempfile.mkdtemp(prefix="okf-proj-"))
    other = Path(tempfile.mkdtemp(prefix="okf-elsewhere-"))
    (root / ".okf" / "concepts").mkdir(parents=True)
    (root / ".okf" / "index.md").write_text("# Index\n\n- [Hello](concepts/hello.md)\n")
    (root / ".okf" / "concepts" / "hello.md").write_text(
        "---\ntype: Concept\ntitle: Hello\ndescription: hello test concept\n---\nBody.\n")
    a = run_case("A cwd=project, no arg", root, [], 120)
    b = run_case("B cwd=elsewhere, arg=bundle", other, [str(root / ".okf")], 60)
    c = run_case("C cwd=elsewhere, no arg", other, [], 60)
    print(f"A ok={a['ok']} B ok={b['ok']} C ok={c['ok']}")
    sys.exit(0 if a["ok"] and b["ok"] else 1)


if __name__ == "__main__":
    main()
