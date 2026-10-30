"""MCP tool surface for mem20liez.

Hard gates: consent, dual-control, prohibited uses, training acknowledgement,
and contamination firewall on seal. All outputs remain probabilistic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import base64
import time

from .pipeline import LieDetector
from .session import LiveLieSession
from .gates import GateError, DISCLAIMER, PROHIBITED_USES

_SESSIONS: Dict[str, LiveLieSession] = {}
_DETECTOR = LieDetector(enabled=True)

# In-process training acknowledgements (operator_id -> version)
_TRAINING_ACK: Dict[str, str] = {}
TRAINING_VERSION = "2026-10-30"


def _get_session(session_id: str) -> LiveLieSession:
    if session_id not in _SESSIONS:
        raise KeyError(f"unknown session_id: {session_id}")
    return _SESSIONS[session_id]


def _gate_error(exc: GateError) -> dict:
    return exc.as_dict()


def lie_acknowledge_training(
    operator_id: str,
    version: str = TRAINING_VERSION,
) -> dict:
    """Record that an operator has completed mem20liez user training."""
    if not operator_id or not operator_id.strip():
        return {"ok": False, "error": "operator_id is required"}
    _TRAINING_ACK[operator_id.strip()] = version
    return {
        "ok": True,
        "operator_id": operator_id.strip(),
        "training_version": version,
        "note": "Training acknowledgement recorded for this process. "
                "See docs/use-cases/TRAINING-MEM20LIEZ.md.",
    }


def lie_start_session(
    mode: str = "generic",
    consent: bool = False,
    consent_attested_by: Optional[str] = None,
    subject_id: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    operator_id: Optional[str] = None,
    intended_uses: Optional[List[str]] = None,
    enable_earpiece: bool = True,
    capture_baseline: bool = False,
) -> dict:
    """Start a live behavioural-signal session under hard gates."""
    try:
        training_ok = bool(
            operator_id and operator_id.strip() in _TRAINING_ACK
        )
        training_ver = _TRAINING_ACK.get(operator_id.strip()) if operator_id else None

        session = LiveLieSession(
            detector=_DETECTOR,
            mode=mode,  # type: ignore
            enable_earpiece=enable_earpiece,
            consent=consent,
            consent_attested_by=consent_attested_by,
            subject_id=subject_id,
            jurisdiction=jurisdiction,
            operator_id=operator_id,
            intended_uses=intended_uses,
            training_acknowledged=training_ok,
            training_version=training_ver,
        )
    except GateError as e:
        return _gate_error(e)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    session._meta["capture_baseline"] = capture_baseline  # type: ignore
    _SESSIONS[session.session_id] = session

    return {
        "ok": True,
        "session_id": session.session_id,
        "mode": mode,
        "consent": consent,
        "enable_earpiece": enable_earpiece,
        "started_at": session.started_at,
        "gates": {
            "consent_required": session.gates.requires_consent(),
            "dual_control_required": session.gates.requires_dual_control(),
            "training_acknowledged": session.gates.training_acknowledged,
            "prohibited_uses": sorted(PROHIBITED_USES),
        },
        "disclaimer": DISCLAIMER,
        "note": (
            "Feed audio with lie_feed_audio. "
            "Optionally set a calm baseline first with lie_set_baseline. "
            "Pull cues with lie_get_cues. "
            "Government high-priority cues need lie_dual_acknowledge. "
            "Seal with lie_seal_session."
        ),
    }


def lie_set_baseline(
    session_id: str,
    audio_b64: str,
    sample_width: int = 2,
) -> dict:
    try:
        session = _get_session(session_id)
        raw = base64.b64decode(audio_b64)
        result = session.detector.voice.process_audio(raw, sample_width=sample_width)
        feats = (result.raw_features or result.value.get("features") or {})
        session.detector.set_baselines(voice=feats)
        return {
            "ok": True,
            "session_id": session_id,
            "baseline_features": feats,
            "confidence": result.confidence.model_dump(),
        }
    except GateError as e:
        return _gate_error(e)
    except KeyError as e:
        return {"ok": False, "error": str(e)}


def lie_feed_audio(
    session_id: str,
    chunk_b64: str,
    timestamp: Optional[float] = None,
    sample_width: int = 2,
) -> dict:
    try:
        session = _get_session(session_id)
        raw = base64.b64decode(chunk_b64)
        results = session.feed_audio(raw, timestamp=timestamp)
        return {
            "ok": True,
            "session_id": session_id,
            "detections": [r.model_dump() for r in results],
            "pending_cues": len([c for c in session._cues if not c.acknowledged]),
        }
    except GateError as e:
        return _gate_error(e)
    except KeyError as e:
        return {"ok": False, "error": str(e)}


def lie_feed_transcript(
    session_id: str,
    text: str,
    timestamp: Optional[float] = None,
) -> dict:
    try:
        session = _get_session(session_id)
        results = session.feed_transcript(text, timestamp=timestamp)
        return {
            "ok": True,
            "session_id": session_id,
            "detections": [r.model_dump() for r in results],
        }
    except GateError as e:
        return _gate_error(e)
    except KeyError as e:
        return {"ok": False, "error": str(e)}


def lie_get_cues(
    session_id: str,
    since_id: Optional[str] = None,
    acknowledge: bool = False,
) -> dict:
    try:
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
            "high_priority_ids": session.high_priority_cue_ids(),
        }
    except KeyError as e:
        return {"ok": False, "error": str(e)}


def lie_acknowledge_cue(session_id: str, cue_id: str) -> dict:
    try:
        session = _get_session(session_id)
        session.acknowledge_cue(cue_id)
        return {"ok": True, "session_id": session_id, "cue_id": cue_id}
    except KeyError as e:
        return {"ok": False, "error": str(e)}


def lie_dual_acknowledge(
    session_id: str,
    cue_id: str,
    first_officer_id: str,
    second_officer_id: str,
    notes: str = "",
) -> dict:
    """Government dual-control: two distinct officers acknowledge a high-priority cue."""
    try:
        session = _get_session(session_id)
        rec = session.dual_acknowledge(
            cue_id=cue_id,
            first_officer_id=first_officer_id,
            second_officer_id=second_officer_id,
            notes=notes,
        )
        return {
            "ok": True,
            "session_id": session_id,
            "cue_id": cue_id,
            "first_officer_id": rec.first_officer_id,
            "second_officer_id": rec.second_officer_id,
            "acknowledged_at": rec.acknowledged_at,
            "dual_control_count": session.gates.dual_control_count(),
        }
    except GateError as e:
        return _gate_error(e)
    except KeyError as e:
        return {"ok": False, "error": str(e)}


def lie_seal_session(
    session_id: str,
    annotations: Optional[dict] = None,
    officer_or_clinician_notes: Optional[str] = None,
) -> dict:
    """Seal under consent, dual-control, prohibited-use, and contamination gates."""
    try:
        session = _get_session(session_id)
        extra = dict(annotations or {})
        if officer_or_clinician_notes:
            extra["professional_notes"] = officer_or_clinician_notes
        package = session.seal(annotations=extra)
        _SESSIONS.pop(session_id, None)
        return {
            "ok": True,
            "package": package,
            "ready_for_grounded_memory": True,
            "disclaimer": package.get("disclaimer"),
            "firewall": package.get("firewall"),
        }
    except GateError as e:
        return _gate_error(e)
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}
    except KeyError as e:
        return {"ok": False, "error": str(e)}


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
                "consent": s.gates.consent,
                "dual_control_count": s.gates.dual_control_count(),
                "training_acknowledged": s.gates.training_acknowledged,
            }
            for s in _SESSIONS.values()
        ],
    }


def lie_prohibited_uses() -> dict:
    """Return the formal prohibited-uses list (for training and UI)."""
    return {
        "ok": True,
        "prohibited_uses": sorted(PROHIBITED_USES),
        "disclaimer": DISCLAIMER,
        "training_version": TRAINING_VERSION,
    }


TOOL_SCHEMAS = [
    {
        "name": "lie_acknowledge_training",
        "description": "Record that an operator completed mem20liez user training (required for high-stakes modes)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "operator_id": {"type": "string"},
                "version": {"type": "string", "default": TRAINING_VERSION},
            },
            "required": ["operator_id"],
        },
    },
    {
        "name": "lie_start_session",
        "description": "Start a live behavioural-signal session under consent / dual-control / prohibited-use gates",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["interrogation", "therapy", "clinical", "government", "generic"],
                    "default": "generic",
                },
                "consent": {"type": "boolean", "default": False},
                "consent_attested_by": {"type": "string"},
                "subject_id": {"type": "string"},
                "jurisdiction": {"type": "string"},
                "operator_id": {"type": "string"},
                "intended_uses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Declared uses; any prohibited use is refused",
                },
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
                "audio_b64": {"type": "string"},
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
        "description": "Mark an earpiece cue as acknowledged by the primary operator",
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
        "name": "lie_dual_acknowledge",
        "description": "Government dual-control: two distinct officers acknowledge a high-priority cue",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "cue_id": {"type": "string"},
                "first_officer_id": {"type": "string"},
                "second_officer_id": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["session_id", "cue_id", "first_officer_id", "second_officer_id"],
        },
    },
    {
        "name": "lie_seal_session",
        "description": "Seal the session under consent, dual-control, prohibited-use, and contamination gates",
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
    {
        "name": "lie_prohibited_uses",
        "description": "Return the formal prohibited-uses list and disclaimer",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

HANDLERS = {
    "lie_acknowledge_training": lie_acknowledge_training,
    "lie_start_session": lie_start_session,
    "lie_set_baseline": lie_set_baseline,
    "lie_feed_audio": lie_feed_audio,
    "lie_feed_transcript": lie_feed_transcript,
    "lie_get_cues": lie_get_cues,
    "lie_acknowledge_cue": lie_acknowledge_cue,
    "lie_dual_acknowledge": lie_dual_acknowledge,
    "lie_seal_session": lie_seal_session,
    "lie_list_sessions": lie_list_sessions,
    "lie_prohibited_uses": lie_prohibited_uses,
}
