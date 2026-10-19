"""Real-time emotion detector (scaffold)."""

from __future__ import annotations

from typing import Any, Optional
import time

from ..types import DetectionResult, SignalType, Confidence


class EmotionDetector:
    MODEL_ID = "mem20liez.emotion"
    MODEL_VERSION = "0.1.0-scaffold"

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def process(
        self,
        audio_chunk: Any = None,
        video_frame: Any = None,
        timestamp: Optional[float] = None,
    ) -> DetectionResult:
        ts = timestamp or time.time()
        if not self.enabled:
            return DetectionResult(
                signal=SignalType.EMOTION,
                timestamp=ts,
                value={"status": "disabled"},
                confidence=Confidence(
                    score=0.0,
                    model_id=self.MODEL_ID,
                    model_version=self.MODEL_VERSION,
                    notes="detector disabled",
                ),
            )
        return DetectionResult(
            signal=SignalType.EMOTION,
            timestamp=ts,
            value={
                "status": "scaffold",
                "valence": None,
                "arousal": None,
                "categorical": None,
                "note": "real emotion engine not yet wired",
            },
            confidence=Confidence(
                score=0.0,
                model_id=self.MODEL_ID,
                model_version=self.MODEL_VERSION,
                notes="scaffold only — no real inference performed",
            ),
            provenance={"engine": "scaffold"},
        )
