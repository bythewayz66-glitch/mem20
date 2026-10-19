\"\"\"Deception indicator fusion (scaffold).

Combines micro-expression, voice-stress, emotion and manipulation
signals together with baseline deviation. Never claims certainty.
\"\"\"

from __future__ import annotations

from typing import Any, Optional, Sequence
import time

from ..types import DetectionResult, SignalType, Confidence


class DeceptionDetector:
    MODEL_ID = "mem20liez.deception"
    MODEL_VERSION = "0.1.0-scaffold"

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def fuse(
        self,
        signals: Sequence[DetectionResult],
        timestamp: Optional[float] = None,
    ) -> DetectionResult:
        ts = timestamp or time.time()

        if not self.enabled:
            return DetectionResult(
                signal=SignalType.DECEPTION,
                timestamp=ts,
                value={"status": "disabled"},
                confidence=Confidence(
                    score=0.0,
                    model_id=self.MODEL_ID,
                    model_version=self.MODEL_VERSION,
                    notes="detector disabled",
                ),
            )

        # Scaffold: real fusion logic (weighted, calibrated, baseline-aware)
        # will live here. For now we stay explicitly non-claiming.
        return DetectionResult(
            signal=SignalType.DECEPTION,
            timestamp=ts,
            value={
                "status": "scaffold",
                "fused_score": None,
                "contributing_signals": [s.signal.value for s in signals],
                "note": "real deception fusion not yet wired — no claim is made",
            },
            confidence=Confidence(
                score=0.0,
                model_id=self.MODEL_ID,
                model_version=self.MODEL_VERSION,
                notes="scaffold only — deception detection is probabilistic and currently inactive",
            ),
            provenance={"engine": "scaffold", "input_count": len(signals)},
        )
