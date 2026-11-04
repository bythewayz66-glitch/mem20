#!/usr/bin/env python3
"""Tiny HTTP fixture for the Godot health/ready test.

Serves the same shape as mem20's health endpoint, so the test exercises a real
HTTPRequest against a real socket instead of asserting a hardcoded return.
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - http.server API
        if self.path not in ("/health", "/ready"):
            self.send_error(404)
            return
        payload = {
            "service": "mem20",
            "status": "ok",
            "ready": self.path == "/ready",
            "path": self.path,
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:  # keep the test output clean
        return


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write("usage: health_fixture.py <port>\n")
        return 2
    server = ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
