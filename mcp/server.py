#!/usr/bin/env python3
"""MCP Server entry — loads full implementation from mem20liez/_server_impl.py."""
import os
import sys
import runpy

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_MCP = os.path.dirname(os.path.abspath(__file__))
if _MCP not in sys.path:
    sys.path.insert(0, _MCP)

_IMPL = os.path.join(_ROOT, "mem20liez", "_server_impl.py")
if not os.path.isfile(_IMPL):
    raise SystemExit(f"mem20 server implementation missing at {_IMPL}")

# Load implementation into this module's namespace
_globs = runpy.run_path(_IMPL, run_name="server")
for _k, _v in _globs.items():
    if not _k.startswith("__"):
        globals()[_k] = _v

_OrigServer = _globs["Mem20MCPServer"]
_orig_main = _globs["main"]


class Mem20MCPServer(_OrigServer):
    """Subclass that registers mem20liez tools after base setup."""

    def _setup_tools(self):
        super()._setup_tools()
        try:
            from tools.lie_tools import LieToolsMixin
            for name in dir(LieToolsMixin):
                if name.startswith("register_lie") or name.startswith("_lie_"):
                    setattr(self.__class__, name, getattr(LieToolsMixin, name))
            self.register_lie_tools()
        except Exception as e:
            import logging
            logging.getLogger("mem20").warning("lie tools not loaded: %s", e)

    async def _execute_tool(self, tool_name, arguments):
        if tool_name.startswith("lie_"):
            handler = getattr(self, f"_{tool_name}", None)
            if handler is not None:
                return await handler(arguments)
        return await super()._execute_tool(tool_name, arguments)


def main():
    import server as self_mod
    self_mod.Mem20MCPServer = Mem20MCPServer
    _orig_main()


if __name__ == "__main__":
    main()
