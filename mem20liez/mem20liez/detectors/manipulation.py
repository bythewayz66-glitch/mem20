"""Manipulation indicator detector (scaffold)."""

from __future__ import annotations

from typing import Any, Optional
import time

from ..types import DetectionResult, SignalType, Confidence


class ManipulationDetector:
    MODEL_ID = "mem20liez.manipulation"
    MODEL_VERSION = "0.1.0-scaffold"

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def process(
        self,
        transcript_segment: str = "",
        behavioural_context: Optional[dict] = None,
        timestamp: Optional[float] = None,
    ) -> DetectionResult:
        ts = timestamp or time.time()
        if not self.enabled:
            return DetectionResult(
                signal=SignalType.MANIPULATION,
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
            signal=SignalType.MANIPULATION,
            timestamp=ts,
            value={
                "status": "scaffold",
                "indicators": [],
                "note": "real manipulation engine not yet wired",
            },
            confidence=Confidence(
                score=0.0,
                model_id=self.MODEL_ID,
                model_version=self.MODEL_VERSION,
                notes="scaffold only — no real inference performed",
            ),
            provenance={"engine": "scaffold"},
        )
