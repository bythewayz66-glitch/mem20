"""Cross-module wiring for the mem20wasmz component lab.

Criterion 6 of the 4.0 renovation is an architecture rule: a subsystem must be
wired into at least five other mem20 modules and the imported function must be
**called** on a tested path. This module is that path for ``mem20wasmz``.

The lab's job is to run language-neutral components with explicit interfaces and
strong isolation. Two things follow from that, and they shape this module:

* a component result is only quotable if it is **canonically serialised and
  stably hashed** — otherwise two runs of the same component produce different
  bytes and nothing downstream can compare them;
* a component result must never be *asserted*. ``moonshot`` already enforces
  that a number is reported only if it was measured; the wiring below keeps the
  same discipline by returning real values from real calls.

Wired subsystems:

===========================  ==========================================
module                       function called
===========================  ==========================================
``mem20core.core``           ``canonical`` / ``stable_hash``
``memory_engine.memory``     ``status``
``toolchest.catalog``        ``discover_mcp_tools``
``mem20verify.linters``      ``identical_branches``
``mem20ops.memchecks``       ``identity_check``
``gateway.hermes_gateway``   ``load_names``
===========================  ==========================================
"""
from __future__ import annotations

import ast
import os
import sys
import tempfile
from typing import Any, Dict, List

# mem20wasmz/mem20wasmz/wiring.py -> mem20wasmz/mem20wasmz -> mem20wasmz -> <repo>
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

# Source-layout packages that are importable only with an explicit path entry.
_SOURCE_PATHS = (
    REPO_ROOT,
    os.path.join(REPO_ROOT, "mem20core"),
    os.path.join(REPO_ROOT, "toolchest", "src"),
    os.path.join(REPO_ROOT, "mem20verify"),
    os.path.join(REPO_ROOT, "mem20ops", "src"),
)


def ensure_paths() -> str:
    """Put every source-layout package root on ``sys.path``. Returns the root."""
    for path in _SOURCE_PATHS:
        if path not in sys.path:
            sys.path.insert(0, path)
    return REPO_ROOT


ensure_paths()

import mem20core.core as mem20core_core
import memory_engine.memory as memory_engine_memory
import toolchest.catalog as toolchest_catalog
import mem20verify.linters as mem20verify_linters
import mem20ops.memchecks as mem20ops_memchecks
import gateway.hermes_gateway as gateway_hermes


def canonical_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Canonical form + stable hash of a component result.

    ``mem20core.core.canonical`` sorts keys and strips incidental whitespace, so
    the same component result hashes identically no matter what order the lab
    built the dict in. That is what makes a run comparable across hosts.
    """
    return {
        "canonical": mem20core_core.canonical(result),
        "stable_hash": mem20core_core.stable_hash(result),
    }


def memory_status_line() -> str:
    """First line of ``memory_engine.memory.status()`` — the grounded store state."""
    report = memory_engine_memory.status()
    return report.splitlines()[0] if report else ""


def tool_surface() -> Dict[str, Any]:
    """The live MCP tool surface as discovered by ``toolchest.catalog``."""
    payload = toolchest_catalog.discover_mcp_tools()
    entries = payload.get("entries") or []
    return {
        "ok": bool(payload.get("ok")),
        "count": len(entries),
        "runtime_count": payload.get("runtime_count"),
    }


def lint_source(source: str, filename: str = "<mem20wasmz-wiring>") -> List[Dict[str, Any]]:
    """Run mem20verify's identical-branch linter over a source string."""
    tree = ast.parse(source, filename=filename)
    issues = mem20verify_linters.identical_branches(filename, tree)
    return [{"line": i.line, "message": i.message} for i in issues]


def store_identity(store_path: str | None = None) -> Dict[str, Any]:
    """mem20ops identity probe against a scratch store."""
    path = store_path or tempfile.mkdtemp(prefix="mem20wasmz-wiring-")
    return mem20ops_memchecks.identity_check(path)


def gateway_agents() -> Dict[str, Any]:
    """Registered gateway agents (empty dict when the fleet registry is empty)."""
    return gateway_hermes.load_names()


def describe_run(result: Dict[str, Any]) -> Dict[str, Any]:
    """Describe a component run using every wired subsystem.

    This is the single entry point the CLI and the MCP tool call. It takes a
    real run result and returns a description that is reproducible: the same
    result always yields the same ``stable_hash``.

    The result is *described*, never rewritten — the lab records what a
    component produced, it does not adjust it.
    """
    # The runtime's real result shape is
    # {job_id, roadmap_id, title, mode, decision, result, cache_hit, explanation}.
    # Only fields that actually exist are described — a missing key stays None
    # rather than being invented.
    decision = result.get("decision") or {}
    described = {
        "job_id": result.get("job_id"),
        "roadmap_id": result.get("roadmap_id"),
        "mode": result.get("mode"),
        "confidence": decision.get("confidence"),
        "cache_hit": bool(result.get("cache_hit", False)),
        "output": result.get("result"),
    }
    canon = canonical_result(described)
    return {
        "run": described,
        "canonical": canon["canonical"],
        "stable_hash": canon["stable_hash"],
        "memory_status": memory_status_line(),
        "tool_surface": tool_surface(),
        "store_identity": store_identity(),
        "gateway_agents": gateway_agents(),
        "wired_modules": [
            "mem20core",
            "memory_engine",
            "toolchest",
            "mem20verify",
            "mem20ops",
            "gateway",
        ],
    }


def self_check() -> Dict[str, Any]:
    """Prove every wired call works, returning the real value each produced."""
    here = os.path.abspath(__file__)
    with open(here, "r", encoding="utf-8") as handle:
        source = handle.read()
    return {
        "mem20core": canonical_result({"probe": 1})["stable_hash"],
        "memory_engine": memory_status_line(),
        "toolchest": tool_surface(),
        "mem20verify": lint_source(source, here),
        "mem20ops": store_identity(),
        "gateway": gateway_agents(),
    }
