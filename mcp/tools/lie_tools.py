"""mem20liez MCP tools — live behavioural-signal sessions.

Exposes voice-stress (real), micro-expression / emotion / manipulation /
deception indicators (scaffold) to any MCP host. On seal, the package is
written to grounded memory and optionally braid-journaled.
"""
from __future__ import annotations

import json
import os
import sys
import base64
from typing import Any, Dict, Optional

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

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Prefer the live mem20liez package from the monorepo
_LIEZ_ROOT = os.path.join(_REPO_ROOT, "mem20liez")
if _LIEZ_ROOT not in sys.path:
    sys.path.insert(0, _LIEZ_ROOT)

try:
    from mem20liez.mcp_tools import (
        lie_start_session as _start,
        lie_set_baseline as _baseline,
        lie_feed_audio as _feed_audio,
        lie_feed_transcript as _feed_transcript,
        lie_get_cues as _get_cues,
        lie_acknowledge_cue as _ack,
        lie_seal_session as _seal,
        lie_list_sessions as _list,
        _SESSIONS,
    )
    LIEZ_AVAILABLE = True
except Exception as e:
    LIEZ_AVAILABLE = False
    _LIEZ_IMPORT_ERROR = str(e)

# Grounded memory + braid (best-effort)
try:
    from memory import remember
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

try:
    from braid_bridge import commit as braid_commit
    BRAID_AVAILABLE = True
except ImportError:
    BRAID_AVAILABLE = False


class LieToolsMixin:
    """MCP tools for live behavioural-signal (liez) sessions."""

    def register_lie_tools(self):
        if not LIEZ_AVAILABLE:
            # Still register a status tool so the absence is visible
            self.tools["lie_status"] = mt.Tool(
                name="lie_status",
                title="Lie / Behavioural Signal Status",
                description="Report whether mem20liez is available",
                inputSchema={"type": "object", "properties": {}},
            )
            return

        self.tools["lie_status"] = mt.Tool(
            name="lie_status",
            title="Lie / Behavioural Signal Status",
            description="Report mem20liez availability and active sessions",
            inputSchema={"type": "object", "properties": {}},
        )
        self.tools["lie_start_session"] = mt.Tool(
            name="lie_start_session",
            title="Start Live Behavioural Session",
            description=(
                "Start a live behavioural-signal session. "
                "Modes: interrogation | therapy | clinical | government | generic. "
                "consent=true required for interrogation/government/clinical."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["interrogation", "therapy", "clinical", "government", "generic"],
                        "default": "generic",
                    },
                    "consent": {"type": "boolean", "default": False},
                    "subject_id": {"type": "string"},
                    "jurisdiction": {"type": "string"},
                    "enable_earpiece": {"type": "boolean", "default": True},
                    "capture_baseline": {"type": "boolean", "default": False},
                },
                "required": ["mode"],
            },
        )
        self.tools["lie_set_baseline"] = mt.Tool(
            name="lie_set_baseline",
            title="Set Voice Baseline",
            description="Capture a neutral voice baseline (base64 PCM) for deviation scoring",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "audio_b64": {"type": "string"},
                    "sample_width": {"type": "integer", "default": 2},
                },
                "required": ["session_id", "audio_b64"],
            },
        )
        self.tools["lie_feed_audio"] = mt.Tool(
            name="lie_feed_audio",
            title="Feed Audio Chunk",
            description="Push a base64 PCM audio chunk into the live session for voice-stress analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "chunk_b64": {"type": "string"},
                    "timestamp": {"type": "number"},
                    "sample_width": {"type": "integer", "default": 2},
                },
                "required": ["session_id", "chunk_b64"],
            },
        )
        self.tools["lie_feed_transcript"] = mt.Tool(
            name="lie_feed_transcript",
            title="Feed Transcript Segment",
            description="Push a transcript segment for linguistic / manipulation indicators",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "text": {"type": "string"},
                    "timestamp": {"type": "number"},
                },
                "required": ["session_id", "text"],
            },
        )
        self.tools["lie_get_cues"] = mt.Tool(
            name="lie_get_cues",
            title="Get Earpiece Cues",
            description="Retrieve pending TTS-ready earpiece cues",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "since_id": {"type": "string"},
                    "acknowledge": {"type": "boolean", "default": False},
                },
                "required": ["session_id"],
            },
        )
        self.tools["lie_acknowledge_cue"] = mt.Tool(
            name="lie_acknowledge_cue",
            title="Acknowledge Cue",
            description="Mark an earpiece cue as acknowledged by the primary operator",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "cue_id": {"type": "string"},
                },
                "required": ["session_id", "cue_id"],
            },
        )
        self.tools["lie_dual_acknowledge"] = mt.Tool(
            name="lie_dual_acknowledge",
            title="Dual-Control Acknowledge (Government)",
            description=(
                "Second-officer acknowledgement for high-priority cues in government mode. "
                "Required before certain high-priority cues are considered fully handled."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "cue_id": {"type": "string"},
                    "second_officer_id": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["session_id", "cue_id", "second_officer_id"],
            },
        )
        self.tools["lie_seal_session"] = mt.Tool(
            name="lie_seal_session",
            title="Seal Session to Grounded Memory",
            description=(
                "Seal the live session into an immutable package, write it to grounded "
                "memory, and optionally journal a braid event."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "annotations": {"type": "object"},
                    "officer_or_clinician_notes": {"type": "string"},
                    "write_grounded": {"type": "boolean", "default": True},
                    "braid_journal": {"type": "boolean", "default": True},
                },
                "required": ["session_id"],
            },
        )
        self.tools["lie_list_sessions"] = mt.Tool(
            name="lie_list_sessions",
            title="List Active Sessions",
            description="List active behavioural-signal sessions",
            inputSchema={"type": "object", "properties": {}},
        )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    async def _lie_status(self, args: Dict) -> str:
        if not LIEZ_AVAILABLE:
            return json.dumps({
                "ok": False,
                "available": False,
                "error": globals().get("_LIEZ_IMPORT_ERROR", "mem20liez not importable"),
            }, indent=2)
        listing = _list()
        return json.dumps({
            "ok": True,
            "available": True,
            "memory_available": MEMORY_AVAILABLE,
            "braid_available": BRAID_AVAILABLE,
            "sessions": listing.get("sessions", []),
        }, indent=2)

    async def _lie_start_session(self, args: Dict) -> str:
        if not LIEZ_AVAILABLE:
            return json.dumps({"ok": False, "error": "mem20liez unavailable"})
        result = _start(
            mode=args.get("mode", "generic"),
            consent=bool(args.get("consent", False)),
            subject_id=args.get("subject_id"),
            jurisdiction=args.get("jurisdiction"),
            enable_earpiece=bool(args.get("enable_earpiece", True)),
            capture_baseline=bool(args.get("capture_baseline", False)),
        )
        return json.dumps(result, indent=2)

    async def _lie_set_baseline(self, args: Dict) -> str:
        if not LIEZ_AVAILABLE:
            return json.dumps({"ok": False, "error": "mem20liez unavailable"})
        result = _baseline(
            session_id=args["session_id"],
            audio_b64=args["audio_b64"],
            sample_width=int(args.get("sample_width", 2)),
        )
        return json.dumps(result, indent=2, default=str)

    async def _lie_feed_audio(self, args: Dict) -> str:
        if not LIEZ_AVAILABLE:
            return json.dumps({"ok": False, "error": "mem20liez unavailable"})
        result = _feed_audio(
            session_id=args["session_id"],
            chunk_b64=args["chunk_b64"],
            timestamp=args.get("timestamp"),
            sample_width=int(args.get("sample_width", 2)),
        )
        return json.dumps(result, indent=2, default=str)

    async def _lie_feed_transcript(self, args: Dict) -> str:
        if not LIEZ_AVAILABLE:
            return json.dumps({"ok": False, "error": "mem20liez unavailable"})
        result = _feed_transcript(
            session_id=args["session_id"],
            text=args["text"],
            timestamp=args.get("timestamp"),
        )
        return json.dumps(result, indent=2, default=str)

    async def _lie_get_cues(self, args: Dict) -> str:
        if not LIEZ_AVAILABLE:
            return json.dumps({"ok": False, "error": "mem20liez unavailable"})
        result = _get_cues(
            session_id=args["session_id"],
            since_id=args.get("since_id"),
            acknowledge=bool(args.get("acknowledge", False)),
        )
        return json.dumps(result, indent=2, default=str)

    async def _lie_acknowledge_cue(self, args: Dict) -> str:
        if not LIEZ_AVAILABLE:
            return json.dumps({"ok": False, "error": "mem20liez unavailable"})
        result = _ack(session_id=args["session_id"], cue_id=args["cue_id"])
        return json.dumps(result, indent=2)

    async def _lie_dual_acknowledge(self, args: Dict) -> str:
        """Government dual-control: second officer must also acknowledge high-priority cues."""
        if not LIEZ_AVAILABLE:
            return json.dumps({"ok": False, "error": "mem20liez unavailable"})
        session_id = args["session_id"]
        cue_id = args["cue_id"]
        second = args["second_officer_id"]
        note = args.get("note", "")

        if session_id not in _SESSIONS:
            return json.dumps({"ok": False, "error": f"unknown session {session_id}"})
        session = _SESSIONS[session_id]
        if session.mode != "government":
            return json.dumps({
                "ok": False,
                "error": "dual_acknowledge is only valid in government mode",
            })

        # record dual ack on the cue if present
        found = False
        for c in session._cues:
            if c.id == cue_id:
                found = True
                # store dual-control metadata on the cue object
                if not hasattr(c, "dual_acks"):
                    c.dual_acks = []  # type: ignore
                c.dual_acks.append({  # type: ignore
                    "second_officer_id": second,
                    "note": note,
                    "ts": __import__("time").time(),
                })
                c.acknowledged = True
                break
        if not found:
            return json.dumps({"ok": False, "error": f"cue {cue_id} not found"})

        return json.dumps({
            "ok": True,
            "session_id": session_id,
            "cue_id": cue_id,
            "second_officer_id": second,
            "dual_control": True,
        }, indent=2)

    async def _lie_seal_session(self, args: Dict) -> str:
        if not LIEZ_AVAILABLE:
            return json.dumps({"ok": False, "error": "mem20liez unavailable"})

        write_grounded = bool(args.get("write_grounded", True))
        do_braid = bool(args.get("braid_journal", True))

        result = _seal(
            session_id=args["session_id"],
            annotations=args.get("annotations"),
            officer_or_clinician_notes=args.get("officer_or_clinician_notes"),
        )
        if not result.get("ok"):
            return json.dumps(result, indent=2)

        package = result["package"]
        memory_receipt = None
        braid_receipt = None

        # --- Grounded memory write ---
        if write_grounded and MEMORY_AVAILABLE:
            try:
                content = (
                    f"[mem20liez sealed session]\n"
                    f"mode={package.get('mode')} session_id={package.get('session_id')}\n"
                    f"detections={len(package.get('detections', []))} "
                    f"cues={len(package.get('cues', []))}\n"
                    f"disclaimer={package.get('disclaimer', '')}\n"
                    f"annotations={json.dumps(package.get('annotations', {}), default=str)[:2000]}"
                )
                tags = [
                    "mem20liez",
                    "behavioural_signal",
                    f"mode:{package.get('mode')}",
                    "sealed",
                ]
                meta = package.get("meta") or package.get("annotations") or {}
                if meta.get("jurisdiction"):
                    tags.append(f"jurisdiction:{meta['jurisdiction']}")
                if meta.get("subject_id"):
                    tags.append(f"subject:{meta['subject_id']}")

                # remember() expects grounded origin; we keep the payload factual
                memory_receipt = remember(
                    content,
                    tags=tags,
                    metadata={
                        "source": "mem20liez",
                        "session_id": package.get("session_id"),
                        "mode": package.get("mode"),
                        "package_summary": {
                            "detection_count": len(package.get("detections", [])),
                            "cue_count": len(package.get("cues", [])),
                            "started_at": package.get("started_at"),
                            "sealed_at": package.get("sealed_at"),
                        },
                        "full_package": package,  # full audit trail
                    },
                )
            except Exception as e:
                memory_receipt = {"error": str(e)}

        # --- Braid journal ---
        if do_braid and BRAID_AVAILABLE:
            try:
                braid_receipt = braid_commit(
                    op="liez.session.sealed",
                    target=package.get("session_id", "unknown"),
                    payload={
                        "mode": package.get("mode"),
                        "detection_count": len(package.get("detections", [])),
                        "cue_count": len(package.get("cues", [])),
                        "disclaimer": package.get("disclaimer"),
                        "meta": package.get("meta") or package.get("annotations"),
                    },
                    cap="agent:write:*",
                )
            except Exception as e:
                braid_receipt = {"error": str(e)}

        result["memory_receipt"] = memory_receipt
        result["braid_receipt"] = braid_receipt
        result["grounded_written"] = memory_receipt is not None and "error" not in (memory_receipt or {})
        result["braid_journaled"] = braid_receipt is not None and "error" not in (braid_receipt or {})
        return json.dumps(result, indent=2, default=str)

    async def _lie_list_sessions(self, args: Dict) -> str:
        if not LIEZ_AVAILABLE:
            return json.dumps({"ok": False, "error": "mem20liez unavailable"})
        return json.dumps(_list(), indent=2)
