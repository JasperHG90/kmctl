"""Serve bare git repos under ROOT over smart HTTP on 127.0.0.1:PORT via git http-backend.

Usage: python3 -I githttp.py ROOT PORT
"""

import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT, PORT = sys.argv[1], int(sys.argv[2])


class Handler(BaseHTTPRequestHandler):
    def _run(self) -> None:
        path, _, query = self.path.partition("?")
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        env = dict(
            os.environ,
            GIT_PROJECT_ROOT=ROOT,
            GIT_HTTP_EXPORT_ALL="1",
            PATH_INFO=path,
            QUERY_STRING=query,
            REQUEST_METHOD=self.command,
            CONTENT_TYPE=self.headers.get("Content-Type", ""),
            CONTENT_LENGTH=str(length),
            HTTP_CONTENT_ENCODING=self.headers.get("Content-Encoding", ""),
            GIT_PROTOCOL=self.headers.get("Git-Protocol", ""),
            REMOTE_ADDR="127.0.0.1",
        )
        out = subprocess.run(["git", "http-backend"], input=body, env=env, capture_output=True).stdout
        head, _, rest = out.partition(b"\r\n\r\n")
        status = 200
        headers = []
        for line in head.decode().split("\r\n"):
            key, _, value = line.partition(":")
            if key.lower() == "status":
                status = int(value.strip().split()[0])
            elif key:
                headers.append((key, value.strip()))
        self.send_response(status)
        for key, value in headers:
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(rest)))
        self.end_headers()
        self.wfile.write(rest)

    do_GET = _run
    do_POST = _run

    def log_message(self, *args: object) -> None:
        pass


ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
