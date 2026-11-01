"""mem20_mcp — thin real loader for the canonical mem20 MCP server.

The canonical, *running* mem20 MCP server lives at /opt/mem20/mcp (proven by the
live process table, ``mcp-server.service`` and opencode.jsonc). Every module in
this package is a read-only forwarder to that tree — see :mod:`mem20_mcp._forward`.
This package therefore boots the identical real tool set instead of stale drift,
and both ``import mem20_mcp.server`` and the top-level ``tools.*`` imports used by
the canonical server resolve to one shared implementation.

Resolution is **lazy**. ``canonical_root()`` still raises ``ImportError`` when the
canonical tree is missing — that refusal is the whole point of the package — but
it is no longer raised at *import* time. Resolving eagerly made the package
unimportable anywhere the canonical tree is absent, which is every bare clone:
the test suite could not be collected and the loader audit could not run, so the
one tool that detects drift was itself unusable off the production box. Importing
the package now always succeeds; touching the canonical tree still fails loudly.
"""

from ._forward import canonical_root as canonical_root

__all__ = ["__canonical_root__", "canonical_root"]


def __getattr__(name: str):
    """Resolve ``__canonical_root__`` on first access, not at import time."""
    if name == "__canonical_root__":
        return canonical_root()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
