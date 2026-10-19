#!/usr/bin/env python3
"""MCP Server entry — loads full implementation and wires mem20liez."""
import os
import sys
import runpy
import pathlib

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MCP = os.path.dirname(os.path.abspath(__file__))
for p in (_ROOT, _MCP):
    if p not in sys.path:
        sys.path.insert(0, p)

_IMPL = os.path.join(_ROOT, "mem20liez", "_server_impl.py")
_GOOD_COMMIT = "6a2bdaab2434611a2edee5d26b93bcc500edb87b"


def _ensure_impl() -> str:
    if os.path.isfile(_IMPL) and os.path.getsize(_IMPL) > 10000:
        return _IMPL
    # Try common recovery locations
    for candidate in (
        os.path.join(_MCP, "_server_impl.py"),
        os.path.join(_ROOT, "mcp", "_server_impl.py"),
    ):
        if os.path.isfile(candidate) and os.path.getsize(candidate) > 10000:
            return candidate
    # Attempt download of last known-good server.py from git history
    try:
        import urllib.request
        url = f"https://raw.githubusercontent.com/bythewayz66-glitch/mem20/{_GOOD_COMMIT}/mcp/server.py"
        dest = pathlib.Path(_IMPL)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=45) as r:
            data = r.read()
        if len(data) > 10000 and b"Mem20MCPServer" in data:
            dest.write_bytes(data)
            return str(dest)
    except Exception as e:
        print(f"[server] recovery download failed: {e}", file=sys.stderr)
    raise SystemExit(
        "mcp server implementation missing.\n"
        "Recover with:\n"
        f"  git show {_GOOD_COMMIT}:mcp/server.py > mem20liez/_server_impl.py\n"
        "Then restart the MCP server."
    )


_impl_path = _ensure_impl()
_globs = runpy.run_path(_impl_path, run_name="server")
for _k, _v in _globs.items():
    if not _k.startswith("__"):
        globals()[_k] = _v

_OrigServer = _globs["Mem20MCPServer"]
_orig_main = _globs["main"]


class Mem20MCPServer(_OrigServer):
    """Registers mem20liez tools after the base tool set."""

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
