#!/usr/bin/env python3
"""MCP handshake verifier: initialize + tools/list, assert the tool count."""
import json, os, subprocess, sys

EXPECTED = int(os.environ.get("MEM20_EXPECTED_TOOLS", "270"))
ROOT = os.path.dirname(os.path.abspath(__file__))

p = subprocess.Popen(
    [sys.executable, os.path.join(ROOT, "launcher.py")],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    cwd=ROOT, text=True, bufsize=1,
    env={**os.environ, "PYTHONUNBUFFERED": "1"},
)

def send(obj):
    p.stdin.write(json.dumps(obj) + "\n"); p.stdin.flush()

def recv():
    while True:
        line = p.stdout.readline()
        if not line:
            raise SystemExit("EOF from server; stderr:\n" + p.stderr.read()[:2000])
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)

send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
    "protocolVersion":"2025-06-18","capabilities":{},
    "clientInfo":{"name":"verify","version":"1"}}})
init = recv()
print("INIT:", json.dumps(init.get("result", {}), sort_keys=True)[:300])
send({"jsonrpc":"2.0","method":"notifications/initialized"})
send({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
tools = recv()["result"]["tools"]
names = [t["name"] for t in tools]
print("TOOL_COUNT:", len(names))
print("FIRST_8:", names[:8])
lie = sorted(n for n in names if n.startswith("lie_"))
print("LIE_TOOLS:", len(lie), lie)
p.terminate(); p.wait(timeout=5)
print("STDERR:", p.stderr.read()[:300])
ok = len(names) == EXPECTED and len(lie) == 10
print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
