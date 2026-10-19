"""Side-load mem20liez tools into Mem20MCPServer after construction.

Import this from mcp_server.py or call apply(server) after Mem20MCPServer().
"""
from __future__ import annotations

def apply(server) -> None:
    try:
        from tools.lie_tools import LieToolsMixin
    except Exception as e:
        print(f"[lie_bootstrap] lie_tools unavailable: {e}")
        return

    for name in dir(LieToolsMixin):
        if name.startswith("register_") or name.startswith("_lie_"):
            setattr(server, name, getattr(LieToolsMixin, name).__get__(server, type(server)))

    if hasattr(server, "register_lie_tools"):
        server.register_lie_tools()

    original = server._execute_tool

    async def _execute_with_lie(tool_name, arguments):
        if tool_name.startswith("lie_"):
            handler = getattr(server, f"_{tool_name}", None)
            if handler:
                return await handler(arguments)
        return await original(tool_name, arguments)

    server._execute_tool = _execute_with_lie
    print("[lie_bootstrap] mem20liez tools registered")
