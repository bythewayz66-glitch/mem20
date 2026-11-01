"""Measure the live MCP surface of mem20 — runtime registry, not a text grep.

Constructs the real Mem20MCPServer and reads the registry that `tools/list`
actually serves, then instantiates each register_*_tools group separately to
prove the groups partition the registry with no overlap and no remainder.

Run this from OUTSIDE the repo root. `mcp/` is the server package directory, so
putting the repo root on sys.path[0] shadows the MCP SDK import; the SDK is
imported first, then `mcp/` is inserted ahead of the repo root.

Usage:
    python3 scripts/surface_measure.py
    MEM20_REPO=/path/to/mem20 python3 scripts/surface_measure.py

Expected at v3.1.0: RUNTIME_TOOLS 270 / REGISTRAR_METHODS 28 / PARTITION_CLEAN True.
"""
import json
import os
import sys

REPO = os.environ.get("MEM20_REPO") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

import mcp  # noqa: E402,F401  SDK first, so mcp/ cannot shadow it
import mcp_types  # noqa: E402,F401

sys.path.insert(0, os.path.join(REPO, "mcp"))
sys.path.insert(0, REPO)
import server as S  # noqa: E402

srv = S.Mem20MCPServer()
runtime = sorted(srv.tools)
print("RUNTIME_TOOLS", len(runtime))

regs = sorted(
    n
    for n in dir(S.Mem20MCPServer)
    if n.startswith("register_")
    and n.endswith("_tools")
    and callable(getattr(S.Mem20MCPServer, n))
)
print("REGISTRAR_METHODS", len(regs))

groups = {}
for g in regs:
    probe = S.Mem20MCPServer.__new__(S.Mem20MCPServer)
    probe.tools = {}
    for attr in ("_jobs", "_tool_calls", "_tool_errors"):
        setattr(probe, attr, {})
    probe._job_timeout = 1800.0
    probe._start_time = 0.0
    probe._request_count = 0
    probe._request_errors = 0
    probe._event_taxonomy = []
    probe._audit_cache = None
    probe._audit_cache_ts = 0.0
    getattr(probe, g)()
    groups[g] = sorted(probe.tools)

flat = [t for v in groups.values() for t in v]
print("SUM_OF_GROUPS", len(flat), "UNION", len(set(flat)))
print("PARTITION_CLEAN", len(flat) == len(set(flat)) == len(runtime))
print("---PER-GROUP---")
for g in regs:
    label = g.replace("register_", "").replace("_tools", "")
    print("%-38s %3d" % (label, len(groups[g])))
print("---JSON---")
print(
    json.dumps(
        {g.replace("register_", "").replace("_tools", ""): len(groups[g]) for g in regs},
        sort_keys=True,
    )
)
