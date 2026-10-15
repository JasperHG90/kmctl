"""Fake OpenAI-compatible endpoint for the Hermes spike.

Usage: fake_llm.py PORTFILE LOGFILE TARGET_PATH

Round 1 (no tool results in the conversation yet): reply with tool calls that
try to write TARGET_PATH (write_file, patch, terminal, execute_code) and one
read_file of a fixture, whatever the offered tools are.
Round 2: reply with a final answer holding a fenced json findings block.
Every request (method, path, headers of interest, body) is appended to LOGFILE
as one JSON line.
"""

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTFILE, LOGFILE, TARGET = sys.argv[1], sys.argv[2], sys.argv[3]
MODEL = "fake-model"
import os
CTX = int(os.environ.get("FAKE_CTX", "131072"))
FINAL = (
    "Audit done.\n\n```json\n"
    '{"findings": [{"id": "F1", "status": "drifted", "path": "README.md"}]}\n'
    "```"
)


def log(entry):
    with open(LOGFILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def tool_calls():
    calls = [
        ("write_file", {"path": TARGET, "content": "PWNED by write_file\n"}),
        ("patch", {"path": TARGET, "old_string": "x", "new_string": "y"}),
        ("terminal", {"command": f"echo PWNED-by-terminal > {TARGET}"}),
        ("execute_code", {"code": f"open({TARGET!r},'w').write('PWNED-by-code')"}),
        ("read_file", {"path": "fixture.txt"}),
        ("kmctl_read_file", {"path": "fixture.txt"}),
        ("kmctl_search_files", {"pattern": "hello", "target": "content", "path": "."}),
        ("search_files", {"pattern": "hello", "path": "."}),
    ]
    return [
        {
            "id": f"call_{i}",
            "type": "function",
            "function": {"name": n, "arguments": json.dumps(a)},
        }
        for i, (n, a) in enumerate(calls)
    ]


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        log({"method": "GET", "path": self.path})
        if os.environ.get("FAKE_NOMODELS"):
            self._json(404, {"error": {"message": "not found"}})
            return
        if self.path.rstrip("/").endswith("/models"):
            self._json(200, {"object": "list", "data": [{
                "id": MODEL, "object": "model", "owned_by": "fake",
                "context_length": CTX, "max_model_len": CTX,
                "context_window": CTX,
            }]})
        elif "/models/" in self.path:
            self._json(200, {"id": MODEL, "object": "model",
                             "context_length": CTX, "max_model_len": CTX})
        else:
            self._json(404, {"error": {"message": "not found"}})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n)
        try:
            body = json.loads(raw)
        except Exception:
            body = {"_raw": raw.decode("utf-8", "replace")}
        log({"method": "POST", "path": self.path,
             "auth": self.headers.get("Authorization"), "body": body})
        if not self.path.endswith("/chat/completions") or (
                os.environ.get("FAKE_NOMODELS") and "/api/" in self.path):
            self._json(404, {"error": {"message": "not found"}})
            return
        msgs = body.get("messages") or []
        has_tool_results = any(m.get("role") == "tool" for m in msgs)
        if not body.get("tools"):
            # side calls (titles, summaries): plain short answer
            msg = {"role": "assistant", "content": "ok"}
            finish = "stop"
        elif has_tool_results:
            msg = {"role": "assistant", "content": FINAL}
            finish = "stop"
        else:
            msg = {"role": "assistant", "content": None, "tool_calls": tool_calls()}
            finish = "tool_calls"
        usage = {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
        cid, now = "chatcmpl-1", int(time.time())
        if not body.get("stream"):
            self._json(200, {"id": cid, "object": "chat.completion", "created": now,
                             "model": MODEL, "usage": usage, "choices": [
                                 {"index": 0, "message": msg, "finish_reason": finish}]})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()

        def chunk(delta, fin=None, extra=None):
            c = {"id": cid, "object": "chat.completion.chunk", "created": now,
                 "model": MODEL,
                 "choices": [{"index": 0, "delta": delta, "finish_reason": fin}]}
            if extra:
                c.update(extra)
            self.wfile.write(f"data: {json.dumps(c)}\n\n".encode())

        chunk({"role": "assistant"})
        if msg.get("tool_calls"):
            for i, tc in enumerate(msg["tool_calls"]):
                chunk({"tool_calls": [{"index": i, **tc}]})
        else:
            chunk({"content": msg["content"]})
        chunk({}, finish)
        c = {"id": cid, "object": "chat.completion.chunk", "created": now,
             "model": MODEL, "choices": [], "usage": usage}
        self.wfile.write(f"data: {json.dumps(c)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
with open(PORTFILE, "w") as f:
    f.write(str(srv.server_address[1]))
srv.serve_forever()
