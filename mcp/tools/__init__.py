"""mem20 MCP tool mixins.

Importing this package installs the RM-239 large-asset release-audit tool onto
the version-control mixin, so ``Mem20MCPServer`` picks it up through the
``register_versioncontrol_tools()`` call it already makes. The installer is
idempotent and never raises: a missing optional dependency leaves the rest of
the MCP surface untouched.
"""

try:
    from tools.rm239_tools import install as _install_rm239

    _install_rm239()
except Exception:  # never let an optional subsystem break the server import
    pass
