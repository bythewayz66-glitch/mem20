"""mem20liez — real-time behavioural signal detection for mem20."""

from .types import (
    DetectionResult,
    SignalType,
    Confidence,
    EarpieceCue,
)
from .pipeline import LieDetector
from .session import LiveLieSession
from .gates import GateError, DISCLAIMER, PROHIBITED_USES

__version__ = "0.3.0"
__all__ = [
    "DetectionResult",
    "SignalType",
    "Confidence",
    "EarpieceCue",
    "LieDetector",
    "LiveLieSession",
    "GateError",
    "DISCLAIMER",
    "PROHIBITED_USES",
]

try:
    from .live import LiveCapture, EarpieceTTS, run_live_session
    __all__ += ["LiveCapture", "EarpieceTTS", "run_live_session"]
except Exception:
    pass
