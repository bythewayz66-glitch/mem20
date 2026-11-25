"""mem20pipez MCP tools — audio/voice/music pipeline surface.

Real domain operations and subsystem-specific peer probes (asset intake,
production studio, LoReRAG binding, model fusion, 2D/3D optimization, event
stream). Lazy/guarded imports.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

try:
    import mcp_types as mt
    MCP_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover
    MCP_SDK_AVAILABLE = False
    mt = None  # type: ignore[assignment]

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load():
    project = os.path.join(_REPO_ROOT, "mem20pipez")
    if project not in sys.path:
        sys.path.insert(0, project)
    import mem20pipez.domain as domain  # type: ignore[import-not-found]
    return domain


def _dumps(value: Any) -> str:
    return json.dumps(value, indent=2, default=str)


class AudioVoiceMusicPipelineToolsMixin:
    """Audio/Voice/Music Pipeline tools for the mem20 MCP server."""

    def register_audiovoiceandmusicpipelinez_tools(self):
        if not MCP_SDK_AVAILABLE:
            return
        self.tools["audiovoiceandmusicpipelinez_status"] = mt.Tool(
            name="audiovoiceandmusicpipelinez_status",
            title="Audio/Voice/Music Pipeline Status",
            description="Run core audio pipeline ops and return a real report with 6 subsystem-specific peer judgements.",
            inputSchema={"type": "object", "properties": {"prompt": {"type": "string"}, "bpm": {"type": "number"}}},
        )
        self.tools["audiovoiceandmusicpipelinez_doctor"] = mt.Tool(
            name="audiovoiceandmusicpipelinez_doctor",
            title="Audio/Voice/Music Pipeline Doctor",
            description="Probe 6 pipeline-specific peers (asset intake, production studio, LoReRAG binding, model fusion, 2D/3D optimization, event stream).",
            inputSchema={"type": "object", "properties": {}},
        )
        self.tools["audiovoiceandmusicpipelinez_mix"] = mt.Tool(
            name="audiovoiceandmusicpipelinez_mix",
            title="Audio Pipeline Mix Tracks",
            description="Mix tracks with gains.",
            inputSchema={"type": "object", "properties": {"tracks": {"type": "array", "items": {"type": "object"}}, "volumes": {"type": "array", "items": {"type": "number"}}}, "required": ["tracks"]},
        )
        self.tools["audiovoiceandmusicpipelinez_master"] = mt.Tool(
            name="audiovoiceandmusicpipelinez_master",
            title="Audio Pipeline Mastering Chain",
            description="Apply mastering stages (eq/compress/limit) to samples.",
            inputSchema={"type": "object", "properties": {"stages": {"type": "array", "items": {"type": "string"}}, "audio": {"type": "array", "items": {"type": "number"}}}, "required": ["stages", "audio"]},
        )

    async def _audiovoiceandmusicpipelinez_status(self, args: Dict[str, Any]) -> str:
        try:
            domain = _load()
            return _dumps(domain.pipeline_report(prompt=args.get("prompt", "bind audio"), bpm=args.get("bpm", 120)))
        except Exception as exc:  # noqa: BLE001
            return _dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"})

    async def _audiovoiceandmusicpipelinez_doctor(self, args: Dict[str, Any]) -> str:
        try:
            domain = _load()
            return _dumps(domain.probe())
        except Exception as exc:  # noqa: BLE001
            return _dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"})

    async def _audiovoiceandmusicpipelinez_mix(self, args: Dict[str, Any]) -> str:
        try:
            domain = _load()
            return _dumps(domain.mix_tracks(args.get("tracks", []), args.get("volumes")))
        except Exception as exc:  # noqa: BLE001
            return _dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"})

    async def _audiovoiceandmusicpipelinez_master(self, args: Dict[str, Any]) -> str:
        try:
            domain = _load()
            return _dumps(domain.mastering_chain(args.get("stages", []), args.get("audio", [])))
        except Exception as exc:  # noqa: BLE001
            return _dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
