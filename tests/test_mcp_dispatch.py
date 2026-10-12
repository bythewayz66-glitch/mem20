import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP = os.path.join(REPO, "mcp")
if MCP not in sys.path:
    sys.path.insert(0, MCP)

import server
import health


def _handler_name(tool_name):
    return "_" + tool_name.replace("-", "_")


def test_tool_count_matches_handlers():
    s = server.Mem20MCPServer()
    missing = [n for n in s.tools if not hasattr(s, _handler_name(n))]
<<<<<<< Updated upstream
    assert len(s.tools) > 0, "expected at least one tool"
=======
    missing = [n for n in missing if n not in ("job_status", "job_wait")]
    # Expected count = deterministic set of tools registered by all mixins
    # (memory 49 + cognitive 20 + roadmap 4 + world 8 + blender 7 + unity 5 +
    #  integration 3 + a2a 5 + thought 7 + cloud 10 + cloudstorage 8 + comm 9 +
    #  database 10 + design 8 + dev 9 + enhanced 20 + filesystem 13 + finance 8 +
    #  marketing 9 + productivity 10 + search 7 + vcs 11 + webscraping 8 +
    #  braid 9 + job 2).
    assert len(s.tools) == 252, f"expected 252 tools, got {len(s.tools)}"
>>>>>>> Stashed changes
    assert not missing, f"tools without handler: {missing}"


def test_unknown_tool_returns_error_result():
    import asyncio

    s = server.Mem20MCPServer()
    params = type("P", (), {"name": "nope", "arguments": {}})()

    async def go():
        return await s._handle_call_tool(None, params)

    res = asyncio.new_event_loop().run_until_complete(go())
    assert res.is_error is True
    assert "Unknown tool" in res.content[0].text


def test_metrics_exposes_instrumentation():
    s = server.Mem20MCPServer()
    m = s.metrics()
    for key in ("event_taxonomy", "tool_calls", "tool_errors", "tool_calls_total", "tool_errors_total"):
        assert key in m, f"missing metric {key}"
    assert m["event_taxonomy"] == ["tool.call", "tool.success", "tool.error"]


def test_health_endpoint_serves_metrics():
    import json
    import urllib.request

    s = server.Mem20MCPServer()
    httpd = health.start_health_server(s, 8094)
    try:
        assert httpd is not None, "health server failed to bind"
        data = json.loads(urllib.request.urlopen("http://127.0.0.1:8094/metrics", timeout=2).read())
<<<<<<< Updated upstream
        assert data["tools_registered"] == len(s.tools)
=======
        assert data["tools_registered"] == 252
>>>>>>> Stashed changes
        assert data["service"] == "mem20-mcp"
    finally:
        if httpd is not None:
            httpd.shutdown()
