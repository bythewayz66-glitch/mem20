\"\"\"Micro-expression detector (scaffold).

Real implementation will use facial action unit (AU) analysis
on short temporal windows. Current version returns honest
\"not-yet-implemented\" results so the pipeline stays truthful.
\"\"\"

from __future__ import annotations

from typing import Any, Optional
import time

from ..types import DetectionResult, SignalType, Confidence


class MicroExpressionDetector:
    MODEL_ID = "mem20liez.micro_expression"
    MODEL_VERSION = "0.1.0-scaffold"

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._baseline: Optional[dict] = None

    def set_baseline(self, features: dict) -> None:
        \"\"\"Capture neutral baseline for later deviation scoring.\"\"\"
        self._baseline = features

    def process_frame(self, frame: Any, timestamp: Optional[float] = None) -> DetectionResult:
        \"\"\"Process a single video frame or short window.\"\"\"
        ts = timestamp or time.time()

        if not self.enabled:
            return DetectionResult(
                signal=SignalType.MICRO_EXPRESSION,
                timestamp=ts,
                value={"status": "disabled"},
                confidence=Confidence(
                    score=0.0,
                    model_id=self.MODEL_ID,
                    model_version=self.MODEL_VERSION,
                    notes="detector disabled",
                ),
            )

        # Scaffold: real AU extraction (OpenFace / MediaPipe / custom) goes here.
        # Until then we return an explicit low-confidence placeholder.
        return DetectionResult(
            signal=SignalType.MICRO_EXPRESSION,
            timestamp=ts,
            value={
                "status": "scaffold",
                "action_units": {},
                "note": "real micro-expression engine not yet wired",
            },
            confidence=Confidence(
                score=0.0,
                model_id=self.MODEL_ID,
                model_version=self.MODEL_VERSION,
                notes="scaffold only — no real inference performed",
            ),
            raw_features=None,
            provenance={"engine": "scaffold"},
        )
