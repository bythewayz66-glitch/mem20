#!/usr/bin/env python3
"""MCP Server for mem20.

Loads the full server implementation automatically:

1. Prefer mem20liez/_server_impl.py if present (optional vendored copy)
2. Else extract the last known-good server.py from git history and apply
   the LieToolsMixin patch in memory
3. Else clear error

A normal `git clone` (or shallow clone that includes commit 6a2bdaa) works
with zero manual recovery steps. Behavioural-signal tools register automatically.
"""
from __future__ import annotations

import os
import sys
import types
import subprocess
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_GOOD_COMMIT = "6a2bdaab2434611a2edee5d26b93bcc500edb87b"
_IMPL_PATH = os.path.join(_ROOT, "mem20liez", "_server_impl.py")

for p in (_ROOT, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)


def _read_vendored() -> str | None:
    if os.path.isfile(_IMPL_PATH) and os.path.getsize(_IMPL_PATH) > 10000:
        with open(_IMPL_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return None


def _read_from_git() -> str | None:
    """Extract known-good server.py from git object database."""
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{_GOOD_COMMIT}:mcp/server.py"],
            cwd=_ROOT,
            stderr=subprocess.DEVNULL,
        )
        text = raw.decode("utf-8")
        if "Mem20MCPServer" in text and len(text) > 10000:
            return text
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    # try from this file's repo root walking up
    try:
        raw = subprocess.check_output(
            ["git", "-C", _ROOT, "show", f"{_GOOD_COMMIT}:mcp/server.py"],
            stderr=subprocess.DEVNULL,
        )
        text = raw.decode("utf-8")
        if "Mem20MCPServer" in text and len(text) > 10000:
            return text
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    return None


def _apply_lie_patch(src: str) -> str:
    """Idempotently wire LieToolsMixin into the restored source."""
    if "LieToolsMixin" in src and "register_lie_tools" in src:
        return src  # already patched (e.g. vendored copy)

    old_import = "from tools.irc_tools import IRCToolsMixin\nfrom health import start_health_server"
    new_import = (
        "from tools.irc_tools import IRCToolsMixin\n"
        "from tools.lie_tools import LieToolsMixin\n"
        "from health import start_health_server"
    )
    if old_import in src:
        src = src.replace(old_import, new_import)

    old_bases = "BraidToolsMixin, IRCToolsMixin):"
    new_bases = "BraidToolsMixin, IRCToolsMixin, LieToolsMixin):"
    if old_bases in src:
        src = src.replace(old_bases, new_bases)

    old_reg = "        self.register_irc_tools()\n        self.register_job_tools()"
    new_reg = (
        "        self.register_irc_tools()\n"
        "        self.register_lie_tools()\n"
        "        self.register_job_tools()"
    )
    if old_reg in src:
        src = src.replace(old_reg, new_reg)

    marker = (
        '        """Execute a tool and return result as string."""\n'
        + (" " * 8)
        + "\n"
        + "        # IRC room tools"
    )
    dispatch = '''        """Execute a tool and return result as string."""

        # mem20liez behavioural-signal tools
        if tool_name == "lie_status":
            return await self._lie_status(arguments)
        elif tool_name == "lie_start_session":
            return await self._lie_start_session(arguments)
        elif tool_name == "lie_set_baseline":
            return await self._lie_set_baseline(arguments)
        elif tool_name == "lie_feed_audio":
            return await self._lie_feed_audio(arguments)
        elif tool_name == "lie_feed_transcript":
            return await self._lie_feed_transcript(arguments)
        elif tool_name == "lie_get_cues":
            return await self._lie_get_cues(arguments)
        elif tool_name == "lie_acknowledge_cue":
            return await self._lie_acknowledge_cue(arguments)
        elif tool_name == "lie_dual_acknowledge":
            return await self._lie_dual_acknowledge(arguments)
        elif tool_name == "lie_seal_session":
            return await self._lie_seal_session(arguments)
        elif tool_name == "lie_list_sessions":
            return await self._lie_list_sessions(arguments)

        # IRC room tools'''
    if marker in src and "lie_start_session" not in src.split("_execute_tool")[1][:2500]:
        src = src.replace(marker, dispatch)

    return src


def _bootstrap():
    """Load the restored server implementation, or raise ImportError.

    Every failure path here MUST surface as ImportError, never SystemExit.
    module-level SystemExit is not treated as an import failure by Python or
    pytest: it aborts the interpreter (and, under pytest, escalates to
    INTERNALERROR and kills collection for the whole session). Because this
    module is imported by several test files, an ImportError is contained to
    the importing module; SystemExit is not.
    """
    src = _read_vendored() or _read_from_git()
    if not src:
        raise ImportError(
            "mem20 MCP server implementation not found.\n"
            "Ensure this is a git checkout that contains commit "
            f"{_GOOD_COMMIT} (a normal clone does).\n"
            "Or place the full server at mem20liez/_server_impl.py."
        )
    src = _apply_lie_patch(src)

    mod = types.ModuleType("mem20_server_impl")
    mod.__file__ = os.path.join(_HERE, "<restored_server>")
    # Ensure mcp package dir imports resolve the same as a normal server.py
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    except SystemExit as exc:
        # The restored implementation calls sys.exit(1) on a missing optional
        # dependency. Translate that into a normal import failure so callers
        # (and pytest collection) see a diagnostic instead of a killed process.
        raise ImportError(
            "mem20 mcp bootstrap: restored server.py exited during exec "
            f"(code={exc.code!r}). The implementation could not be imported - "
            "usually a missing dependency; see requirements.txt."
        ) from exc
    return mod


_mod = _bootstrap()

# Re-export everything the rest of the tree expects
Mem20MCPServer = _mod.Mem20MCPServer
main = _mod.main
for _k, _v in _mod.__dict__.items():
    if not _k.startswith("_"):
        setattr(sys.modules[__name__], _k, _v)

if __name__ == "__main__":
    main()
