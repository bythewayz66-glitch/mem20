"""Bridge between the gateway tool registry and the self-healing subsystem.

``gateway/gateway_tools.py`` is the estate's tool catalog (``get_gateway_tools()``
is what the MCP server and Hermes agents read). Its functions are plain, importable
callables with no repository plumbing of their own, so the three RM-217 entries it
declares live here: this module owns only the *construction* of a controller and
keeps that concern out of the registry file, which stays a thin description.

Why a separate module rather than calling the subsystem directly from
``gateway_tools.py``:
  * ``gateway_tools.py`` is imported in environments that do not have the
    subsystem on ``sys.path``; keeping the import here means a broken integration
    degrades to a clear error from the tool call instead of an ImportError at
    registry import time.
  * the controller is cached per state directory, so repeated tool calls in one
    process share a warm fleet instead of rebuilding it every time.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = ["controller_for", "sys_path_entries"]

_CACHE: Dict[str, Any] = {}


def sys_path_entries() -> List[str]:
    """Project roots the subsystem needs on ``sys.path`` (idempotent)."""
    repo_root = Path(__file__).resolve().parents[1]
    candidates = [
        repo_root / "memory_engine",
        repo_root / "mcp",
        repo_root / "gateway",
        repo_root / "toolchest" / "src",
        repo_root / "mem20selfhealingruntimecivilizationz",
    ]
    added = []
    for path in candidates:
        text = str(path)
        if path.exists() and text not in sys.path:
            sys.path.insert(0, text)
            added.append(text)
    return added


def controller_for(state_dir: Optional[str] = None, catalogue_limit: int = 12):
    """Build (or reuse) a FleetController over the real on-disk catalogue.

    Raises ``RuntimeError`` with the underlying reason when the subsystem cannot
    be imported — a tool call should fail loudly, not return a plausible-looking
    payload it did not compute.
    """
    sys_path_entries()
    try:
        from mem20selfhealingruntimecivilizationz.controller import (  # type: ignore
            ControllerConfig,
            FleetController,
        )
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "mem20selfhealingruntimecivilizationz could not be imported "
            f"({type(exc).__name__}: {exc}); the RM-217 tools need the mem20 "
            "checkout on sys.path"
        ) from exc

    repo_root = Path(__file__).resolve().parents[1]
    target = Path(
        state_dir
        or os.environ.get("MEM20_SELFHEALING_STATE", "")
        or repo_root / "state" / "selfhealing"
    )
    key = str(Path(target).resolve())
    if key not in _CACHE:
        controller = FleetController(
            config=ControllerConfig(),
            state_dir=Path(target),
            repo_root=repo_root,
        )
        controller.load_fleet_from_catalogue(limit=catalogue_limit)
        _CACHE[key] = controller
    return _CACHE[key]
