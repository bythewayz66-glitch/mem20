"""mem20 MCP tool mixins.

Importing this package installs the wave-1 subsystem tools onto the
version-control mixin, so ``Mem20MCPServer`` picks them up through the
``register_versioncontrol_tools()`` call it already makes:

  RM-239  vcs_asset_release_audit          large-asset release audit
  RM-052  graph_execute_reversible_plan    reversible plan execution

Each installer is idempotent and never raises: a missing optional dependency
leaves the rest of the MCP surface untouched.
"""

try:
    from tools.rm239_tools import install as _install_rm239

    _install_rm239()
except Exception:  # never let an optional subsystem break the server import
    pass

try:
    from tools.rm052_tools import install as _install_rm052

    _install_rm052()
except Exception:  # never let an optional subsystem break the server import
    pass
