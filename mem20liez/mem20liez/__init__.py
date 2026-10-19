\"\"\"mem20liez — real-time behavioural signal detection for mem20.\"\"\"

from .types import (
    DetectionResult,
    SignalType,
    Confidence,
    EarpieceCue,
)
from .pipeline import LieDetector
from .session import LiveLieSession

__version__ = "0.1.0"
__all__ = [
    "DetectionResult",
    "SignalType",
    "Confidence",
    "EarpieceCue",
    "LieDetector",
    "LiveLieSession",
]
