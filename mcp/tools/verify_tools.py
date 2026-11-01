"""mem20verify tools for the mem20 MCP server.

Exposes the verification toolkit to agents so a claim can be checked instead of
believed. Every tool here runs a real check against the real tree or the live
system and reports what happened; none of them returns a canned verdict.

Tools:

* ``verify_drift``   -- registry claims vs the directories actually on disk
* ``verify_tests``   -- run each package's own suite and report real results
* ``verify_lint``    -- run the AST linters for known-shipped defect classes
* ``verify_wiring``  -- prove mem20verify's cross-subsystem edges
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

try:
    from mcp.server import Server
    from mcp.server.lowlevel.server import ServerRequestContext
    import mcp_types as mt
    MCP_SDK_AVAILABLE = True
    MCP_SDK_IMPORT_ERROR = None
except ImportError as _mcp_sdk_exc:  # pragma: no cover - only without the SDK
    # Never sys.exit() at import time: pytest imports this module during
    # collection and a SystemExit aborts the whole session instead of
    # reporting one collection error. Full note in mcp/server.py.
    MCP_SDK_AVAILABLE = False
    MCP_SDK_IMPORT_ERROR = _mcp_sdk_exc


def _verify():
    """Import mem20verify from the estate, wherever it lives."""
    try:
        import mem20verify  # noqa: F401
        from mem20verify import integrations
        from mem20verify import linters, testrun
        return integrations, linters, testrun
    except ImportError:
        pass
    root = Path(os.environ.get("MEM20_ROOT", "/opt/mem20"))
    candidate = root / "mem20verify"
    if (candidate / "mem20verify" / "__init__.py").is_file():
        sys.path.insert(0, str(candidate))
    from mem20verify import integrations
    from mem20verify import linters, testrun
    return integrations, linters, testrun


class VerifyToolsMixin:
    """Verification toolkit tools for mem20."""

    def register_verify_tools(self):
        """Register the mem20verify tools."""
        if not MCP_SDK_AVAILABLE:  # pragma: no cover
            return
        self.tools["verify_drift"] = mt.Tool(
            name="verify_drift",
            title="Verify Registry Drift",
            description=(
                "Compare what the tool registry claims exists with what is actually "
                "on disk. Reports subsystems listed but missing, and directories on "
                "disk that no one listed. Drift is reported in both directions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "root": {"type": "string", "description": "estate root override"},
                },
                "required": [],
            },
        )
        self.tools["verify_tests"] = mt.Tool(
            name="verify_tests",
            title="Verify Test Suites",
            description=(
                "Run each package's own test suite from its own root and report real "
                "pass/fail counts. A package whose suite cannot be run is reported as "
                "an error, never as a pass."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "packages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "package names to run (default: all discovered)",
                    },
                    "root": {"type": "string", "description": "estate root override"},
                },
                "required": [],
            },
        )
        self.tools["verify_lint"] = mt.Tool(
            name="verify_lint",
            title="Verify Lint",
            description=(
                "Run the AST linters that catch known-shipped defect classes "
                "(late-binding closures, import-time sys.exit, registry/dispatch "
                "mismatch) across the estate's source."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "root": {"type": "string", "description": "estate root override"},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": [],
            },
        )
        self.tools["verify_wiring"] = mt.Tool(
            name="verify_wiring",
            title="Verify Wiring",
            description=(
                "Prove mem20verify's cross-subsystem edges by calling each one: "
                "toolchest catalog, memory_engine pin_block, mem20kanbanz sha256, "
                "mem20ops declared_scripts, mem20corez CharMLP, mem20cliz "
                "build_envelope. Returns per-edge ok/result."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "root": {"type": "string", "description": "estate root override"},
                },
                "required": [],
            },
        )

    async def _verify_drift(self, arguments: Dict[str, Any]) -> str:
        integrations, _l, _t = _verify()
        root = arguments.get("root")
        drift = integrations.registry_drift(Path(root) if root else None)
        return json.dumps({"ok": True, **drift}, indent=2, default=str)

    async def _verify_tests(self, arguments: Dict[str, Any]) -> str:
        _i, _l, testrun = _verify()
        root = arguments.get("root") or str(Path(os.environ.get("MEM20_ROOT", "/opt/mem20")))
        wanted = arguments.get("packages") or testrun.discover_packages(root)
        results = []
        for name in wanted:
            try:
                result = testrun.run_package(name, root=root)
                results.append({
                    "package": name,
                    "passed": result.returncode == 0 and result.failed == 0
                              and result.errors == 0 and not result.timed_out,
                    "returncode": result.returncode,
                    "passed_count": result.passed,
                    "failed_count": result.failed,
                    "skipped": result.skipped,
                    "errors": result.errors,
                    "timed_out": result.timed_out,
                    "failed_ids": result.failed_ids[:10],
                    "error_text": (result.error_text or "")[-400:],
                })
            except Exception as exc:  # noqa: BLE001 - a real failure is a finding
                results.append({
                    "package": name,
                    "passed": False,
                    "error": f"{type(exc).__name__}: {exc}",
                })
        return json.dumps({
            "ok": all(r["passed"] for r in results),
            "total": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if not r["passed"]),
            "results": results,
        }, indent=2, default=str)

    async def _verify_lint(self, arguments: Dict[str, Any]) -> str:
        _i, linters, _t = _verify()
        import ast
        root = Path(arguments.get("root")
                    or os.environ.get("MEM20_ROOT", "/opt/mem20"))
        limit = int(arguments.get("limit") or 50)
        issues = []
        scanned = 0
        for path in sorted(root.rglob("*.py")):
            if ".venv" in path.parts or "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"),
                                 filename=str(path))
            except (OSError, SyntaxError, ValueError):
                continue
            scanned += 1
            for check_fn in linters.ALL_CHECKS:
                issues.extend(check_fn(str(path), tree))
            if len(issues) >= limit:
                break
        return json.dumps({
            "ok": not issues,
            "scanned": scanned,
            "findings": len(issues),
            "returned": min(limit, len(issues)),
            "issues": [i.as_dict() for i in issues[:limit]],
        }, indent=2, default=str)

    async def _verify_wiring(self, arguments: Dict[str, Any]) -> str:
        integrations, _l, _t = _verify()
        root = arguments.get("root")
        return json.dumps(integrations.wiring_report(Path(root) if root else None),
                          indent=2, default=str)
