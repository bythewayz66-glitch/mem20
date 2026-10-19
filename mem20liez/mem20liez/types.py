\"\"\"Shared types for mem20liez.\"\"\"

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
import time


class SignalType(str, Enum):
    MICRO_EXPRESSION = "micro_expression"
    VOICE_STRESS = "voice_stress"
    EMOTION = "emotion"
    MANIPULATION = "manipulation"
    DECEPTION = "deception"


class Confidence(BaseModel):
    \"\"\"Explicit confidence envelope — never omit.\"\"\"
    score: float = Field(..., ge=0.0, le=1.0)
    model_id: str
    model_version: str
    notes: Optional[str] = None


class DetectionResult(BaseModel):
    \"\"\"One atomic detection event.\"\"\"
    signal: SignalType
    timestamp: float = Field(default_factory=time.time)
    value: Any                          # detector-specific payload
    confidence: Confidence
    baseline_deviation: Optional[float] = None
    raw_features: Optional[dict] = None
    provenance: dict = Field(default_factory=dict)

    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        return self.confidence.score >= threshold


class EarpieceCue(BaseModel):
    \"\"\"Short, speakable cue for the professional's earpiece.\"\"\"
    id: str
    text: str                           # TTS-ready, concise
    priority: int = 1                   # 1=info, 2=notable, 3=urgent
    related_signals: list[SignalType] = Field(default_factory=list)
    confidence: float
    timestamp: float = Field(default_factory=time.time)
    acknowledged: bool = False
