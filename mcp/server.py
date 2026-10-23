#!/usr/bin/env python3
"""MCP Server for mem20.

Loads the full server implementation automatically, in this order:

1. Prefer the vendored copy: ``mem20liez/_server_impl.py``, or the committed
   gzip+base64 form ``mem20liez/_server_impl.py.gz.b64`` (the one that ships in
   the repo). Either way a ``git clone --depth 1`` checkout works with no
   history and no network.
2. Else recover the last known-good ``mcp/server.py`` from the git object
   database (needs the object to be present locally).
3. Else, if this is a shallow clone, fetch just the needed commit
   (``git fetch --depth=1 origin <sha>``) and retry step 2. Disable with
   ``MEM20_MCP_AUTO_FETCH=0``.
4. Else scan history for the newest ``mcp/server.py`` blob that looks like the
   full implementation, and use it.
5. Else fail with a diagnostic that names the detected condition and the exact
   remediation.

The LieToolsMixin patch is applied in memory when the recovered source is
unpatched; a vendored copy is already patched and is used verbatim.

History is therefore an optimisation, never a hard requirement.
"""
from __future__ import annotations

import os
import sys
import types
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_GOOD_COMMIT = os.environ.get(
    "MEM20_GOOD_COMMIT", "6a2bdaab2434611a2edee5d26b93bcc500edb87b"
)
_IMPL_PATH = os.path.join(_ROOT, "mem20liez", "_server_impl.py")
_IMPL_GZ_PATH = os.path.join(_ROOT, "mem20liez", "_server_impl.py.gz.b64")
_MIN_IMPL_BYTES = 10000
_IMPL_MARKER = "Mem20MCPServer"

for p in (_ROOT, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)


def _git(*args: str, timeout: int = 120) -> str | None:
    """Run a git command at the repo root; return stdout, or None on failure."""
    try:
        raw = subprocess.check_output(
            ["git", *args],
            cwd=_ROOT,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        OSError,
    ):
        return None
    return raw.decode("utf-8", "replace")


def _looks_like_impl(text: str | None) -> bool:
    return bool(text) and _IMPL_MARKER in text and len(text) > _MIN_IMPL_BYTES


def _read_vendored() -> str | None:
    """Vendored implementation: raw ``_server_impl.py`` first, then the
    committed gzip+base64 copy (``_server_impl.py.gz.b64``).

    The compressed form is what ships in the repo — it is ~3x smaller than the
    raw source, so it survives tooling that mangles very large single-file
    commits. ``regen_server_impl.py`` writes the raw file when git history is
    available; both are accepted here.
    """
    if os.path.isfile(_IMPL_PATH) and os.path.getsize(_IMPL_PATH) > _MIN_IMPL_BYTES:
        try:
            with open(_IMPL_PATH, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError:
            text = None
        if _looks_like_impl(text):
            return text

    payload = _read_vendored_compressed()
    if _looks_like_impl(payload):
        return payload
    return None


def _read_vendored_compressed() -> str | None:
    if not os.path.isfile(_IMPL_GZ_PATH):
        return None
    try:
        import base64
        import gzip

        with open(_IMPL_GZ_PATH, "rb") as f:
            raw = base64.b64decode(f.read())
        return gzip.decompress(raw).decode("utf-8")
    except (OSError, ValueError, EOFError, ImportError):
        return None


def _is_shallow() -> bool:
    out = _git("rev-parse", "--is-shallow-repository")
    if out is not None:
        return out.strip() == "true"
    # Older git (<2.15) has no --is-shallow-repository.
    return bool(_git("rev-parse", "--git-dir")) and os.path.isfile(
        os.path.join(_ROOT, ".git", "shallow")
    )


def _read_from_git(sha: str = _GOOD_COMMIT) -> str | None:
    """Extract known-good server.py from the local git object database."""
    text = _git("show", f"{sha}:mcp/server.py")
    if _looks_like_impl(text):
        return text
    return None


def _fetch_commit(sha: str = _GOOD_COMMIT) -> bool:
    """Fetch a single commit into a shallow clone. True if it became readable.

    Only fetches history depth for that one commit, so the clone stays small.
    Does not rewrite working-tree files.
    """
    if os.environ.get("MEM20_MCP_AUTO_FETCH", "1").lower() in {"0", "false", "no"}:
        return False
    if not os.path.isdir(os.path.join(_ROOT, ".git")):
        return False
    for args in (
        ("fetch", "--depth=1", "origin", sha),
        ("fetch", "origin", sha),
    ):
        if _git(*args) is None:
            continue
        if _looks_like_impl(_git("show", f"{sha}:mcp/server.py")):
            return True
    return False


def _scan_history() -> str | None:
    """Newest committed mcp/server.py blob that looks like the full server."""
    log = _git("log", "--all", "--format=%H", "--", "mcp/server.py")
    if not log:
        return None
    for sha in log.split():
        text = _read_from_git(sha)
        if text:
            return text
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
        "        \n"
        "        # IRC room tools"
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


def _diagnose() -> str:
    """Build an actionable failure message for the conditions we can detect."""
    lines = ["mem20 MCP server implementation not found.", ""]
    has_git = os.path.isdir(os.path.join(_ROOT, ".git"))

    if not has_git:
        lines += [
            "Cause: this is not a git checkout (no .git directory found at",
            f"  {_ROOT}).",
            "  History recovery is unavailable, and the vendored copy is",
            f"  missing from {_IMPL_PATH}",
            f"  and {_IMPL_GZ_PATH}.",
        ]
    elif _is_shallow():
        lines += [
            "Cause: this is a SHALLOW clone and the vendored copy is missing,",
            f"  so commit {_GOOD_COMMIT} is not present locally.",
            "  A shallow clone normally works because the implementation is",
            "  vendored in the repo; if that file was deleted, run:",
            "",
            f"    git fetch --depth=1 origin {_GOOD_COMMIT}",
            "",
            "  or deepen the clone:  git fetch --unshallow",
        ]
    else:
        lines += [
            "Cause: full history is present but the implementation blob could",
            f"  not be read from commit {_GOOD_COMMIT}, and the vendored copy",
            f"  is missing from {_IMPL_PATH}",
            f"  and {_IMPL_GZ_PATH}.",
            "",
            "  The commit may have been rewritten or garbage collected. Fetch it:",
            "",
            f"    git fetch origin {_GOOD_COMMIT}",
        ]

    lines += [
        "",
        "Fixes, cheapest first:",
        f"  1. Restore the vendored implementation at {_IMPL_PATH}",
        f"     or {_IMPL_GZ_PATH}",
        "     (regenerate with: python mem20liez/regen_server_impl.py)",
        "  2. Make git history available (see the commands above)",
        "  3. Point at a specific commit: export MEM20_GOOD_COMMIT=<sha>",
    ]
    return "\n".join(lines)


def _load_impl_source() -> str:
    src = _read_vendored()
    if src:
        return src

    src = _read_from_git()
    if src:
        return src

    # Shallow clone (or a rewritten commit): try to pull just that object.
    if _fetch_commit():
        src = _read_from_git()
        if src:
            return src

    src = _scan_history()
    if src:
        return src

    raise SystemExit(_diagnose())


def _bootstrap():
    src = _apply_lie_patch(_load_impl_source())

    mod = types.ModuleType("mem20_server_impl")
    mod.__file__ = os.path.join(_HERE, "<restored_server>")
    # Ensure mcp package dir imports resolve the same as a normal server.py
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


_mod = _bootstrap()

# Re-export everything the rest of the tree expects
Mem20MCPServer = _mod.Mem20MCPServer
main = _mod.main
for _k, _v in _mod.__dict__.items():
    if not _k.startswith("_"):
        globals()[_k] = _v

if __name__ == "__main__":
    main()
