"""MCP tool surface for mem20liez.

These tools are designed to be registered into the main mem20 MCP server
(or used standalone). They expose live lie/behavioural-signal sessions
to any MCP host.

All outputs remain probabilistic observations with explicit confidence.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import base64
import time
import uuid

from .pipeline import LieDetector
from .session import LiveLieSession
from .types import EarpieceCue

# In-memory session store for the MCP process lifetime.
# Production deployments should replace with a proper store or the main mem20 ledger.
_SESSIONS: Dict[str, LiveLieSession] = {}
_DETECTOR = LieDetector(enabled=True)


def _get_session(session_id: str) -> LiveLieSession:
    if session_id not in _SESSIONS:
        raise KeyError(f"unknown session_id: {session_id}")
    return _SESSIONS[session_id]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def lie_start_session(
    mode: str = "generic",
    consent: bool = False,
    subject_id: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    enable_earpiece: bool = True,
    capture_baseline: bool = False,
) -> dict:
    """Start a live behavioural-signal session.

    mode: interrogation | therapy | clinical | government | generic
    consent: must be true for high-stakes modes
    """
    if mode in ("interrogation", "government", "clinical") and not consent:
        return {
            "ok": False,
            "error": "consent=true is required for interrogation / government / clinical modes",
        }

    session = LiveLieSession(
        detector=_DETECTOR,
        mode=mode,  # type: ignore
        enable_earpiece=enable_earpiece,
    )
    # stash extra metadata
    session._meta = {  # type: ignore
        "subject_id": subject_id,
        "jurisdiction": jurisdiction,
        "consent": consent,
        "capture_baseline": capture_baseline,
    }
    _SESSIONS[session.session_id] = session

    return {
        "ok": True,
        "session_id": session.session_id,
        "mode": mode,
        "enable_earpiece": enable_earpiece,
        "started_at": session.started_at,
        "note": (
            "Feed audio with lie_feed_audio. "
            "Optionally set a calm baseline first with lie_set_baseline. "
            "Pull cues with lie_get_cues. Seal with lie_seal_session."
        ),
    }


def lie_set_baseline(
    session_id: str,
    audio_b64: str,
    sample_width: int = 2,
) -> dict:
    """Capture a neutral voice baseline for the subject."""
    session = _get_session(session_id)
    raw = base64.b64decode(audio_b64)
    # Run once to extract features, then store as baseline
    result = session.detector.voice.process_audio(raw, sample_width=sample_width)
    feats = (result.raw_features or result.value.get("features") or {})
    session.detector.set_baselines(voice=feats)
    return {
        "ok": True,
        "session_id": session_id,
        "baseline_features": feats,
        "confidence": result.confidence.model_dump(),
    }


def lie_feed_audio(
    session_id: str,
    chunk_b64: str,
    timestamp: Optional[float] = None,
    sample_width: int = 2,
) -> dict:
    """Push an audio chunk into the live session."""
    session = _get_session(session_id)
    raw = base64.b64decode(chunk_b64)
    results = session.feed_audio(raw, timestamp=timestamp)
    # also pass sample_width through to the voice detector on the next call if needed
    return {
        "ok": True,
        "session_id": session_id,
        "detections": [r.model_dump() for r in results],
        "pending_cues": len([c for c in session._cues if not c.acknowledged]),
    }


def lie_feed_transcript(
    session_id: str,
    text: str,
    timestamp: Optional[float] = None,
) -> dict:
    """Push a transcript segment (for manipulation / linguistic indicators)."""
    session = _get_session(session_id)
    results = session.feed_transcript(text, timestamp=timestamp)
    return {
        "ok": True,
        "session_id": session_id,
        "detections": [r.model_dump() for r in results],
    }


def lie_get_cues(
    session_id: str,
    since_id: Optional[str] = None,
    acknowledge: bool = False,
) -> dict:
    """Retrieve pending earpiece cues (TTS-ready strings)."""
    session = _get_session(session_id)
    cues = session.get_earpiece_cues(since_id=since_id)
    if acknowledge:
        for c in cues:
            session.acknowledge_cue(c.id)
    return {
        "ok": True,
        "session_id": session_id,
        "cues": [c.model_dump() for c in cues],
        "count": len(cues),
    }


def lie_acknowledge_cue(session_id: str, cue_id: str) -> dict:
    session = _get_session(session_id)
    session.acknowledge_cue(cue_id)
    return {"ok": True, "session_id": session_id, "cue_id": cue_id}


def lie_seal_session(
    session_id: str,
    annotations: Optional[dict] = None,
    officer_or_clinician_notes: Optional[str] = None,
) -> dict:
    """Seal the session into an immutable package ready for grounded memory."""
    session = _get_session(session_id)
    extra = annotations or {}
    if officer_or_clinician_notes:
        extra["professional_notes"] = officer_or_clinician_notes
    meta = getattr(session, "_meta", {})
    extra.update(meta)
    package = session.seal(annotations=extra)

    # Remove from live map (package is the durable artefact)
    _SESSIONS.pop(session_id, None)

    return {
        "ok": True,
        "package": package,
        "ready_for_grounded_memory": True,
        "disclaimer": package.get("disclaimer"),
    }


def lie_list_sessions() -> dict:
    return {
        "ok": True,
        "sessions": [
            {
                "session_id": s.session_id,
                "mode": s.mode,
                "started_at": s.started_at,
                "sealed": s.sealed,
                "detection_count": len(s._all_detections),
            }
            for s in _SESSIONS.values()
        ],
    }


# ---------------------------------------------------------------------------
# Schema helpers for MCP registration
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "lie_start_session",
        "description": "Start a live behavioural-signal (voice-stress / micro-expression / deception-indicator) session",
        "inputSchema": {
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
    },
    {
        "name": "lie_set_baseline",
        "description": "Capture a neutral voice baseline for later deviation scoring",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "audio_b64": {"type": "string", "description": "Base64-encoded PCM audio"},
                "sample_width": {"type": "integer", "default": 2},
            },
            "required": ["session_id", "audio_b64"],
        },
    },
    {
        "name": "lie_feed_audio",
        "description": "Push an audio chunk into the live session for voice-stress analysis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "chunk_b64": {"type": "string"},
                "timestamp": {"type": "number"},
                "sample_width": {"type": "integer", "default": 2},
            },
            "required": ["session_id", "chunk_b64"],
        },
    },
    {
        "name": "lie_feed_transcript",
        "description": "Push a transcript segment for linguistic / manipulation indicators",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "text": {"type": "string"},
                "timestamp": {"type": "number"},
            },
            "required": ["session_id", "text"],
        },
    },
    {
        "name": "lie_get_cues",
        "description": "Retrieve pending TTS-ready earpiece cues",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "since_id": {"type": "string"},
                "acknowledge": {"type": "boolean", "default": False},
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "lie_acknowledge_cue",
        "description": "Mark an earpiece cue as acknowledged",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "cue_id": {"type": "string"},
            },
            "required": ["session_id", "cue_id"],
        },
    },
    {
        "name": "lie_seal_session",
        "description": "Seal the live session into an immutable package for grounded memory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "annotations": {"type": "object"},
                "officer_or_clinician_notes": {"type": "string"},
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "lie_list_sessions",
        "description": "List active lie/behavioural-signal sessions",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

HANDLERS = {
    "lie_start_session": lie_start_session,
    "lie_set_baseline": lie_set_baseline,
    "lie_feed_audio": lie_feed_audio,
    "lie_feed_transcript": lie_feed_transcript,
    "lie_get_cues": lie_get_cues,
    "lie_acknowledge_cue": lie_acknowledge_cue,
    "lie_seal_session": lie_seal_session,
    "lie_list_sessions": lie_list_sessions,
}
