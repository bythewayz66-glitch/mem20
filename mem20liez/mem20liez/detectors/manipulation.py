"""Manipulation indicator detector — rule-based linguistic cues.

Detects conversational patterns commonly associated with steering,
evasion, or pressure. Never claims intent or deception. Confidence
is deliberately capped; this is an indicator layer only.
"""

from __future__ import annotations

from typing import Any, Optional, List
import re
import time

from ..types import DetectionResult, SignalType, Confidence

# Lightweight pattern sets — transparent and auditable.
_EVASION = [
    r"\b(i don't recall|i can't remember|to the best of my knowledge)\b",
    r"\b(that's a good question|interesting question)\b",
    r"\b(it depends|in a sense|sort of|kind of)\b",
]
_PRESSURE = [
    r"\b(you have to|you must|you need to|if you know what's good)\b",
    r"\b(everyone knows|everybody does|you wouldn't want)\b",
]
_STEERING = [
    r"\b(let's not focus on|moving on|that's not important)\b",
    r"\b(what matters is|the real issue is)\b",
]
_ABSOLUTES = [
    r"\b(always|never|everyone|no one|completely|totally)\b",
]


def _count_matches(patterns: List[str], text: str) -> List[str]:
    hits = []
    low = text.lower()
    for p in patterns:
        if re.search(p, low, re.IGNORECASE):
            hits.append(p)
    return hits


class ManipulationDetector:
    MODEL_ID = "mem20liez.manipulation"
    MODEL_VERSION = "0.2.0-rules"

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

        text = (transcript_segment or "").strip()
        if len(text) < 8:
            return DetectionResult(
                signal=SignalType.MANIPULATION,
                timestamp=ts,
                value={"status": "too_short", "indicators": []},
                confidence=Confidence(
                    score=0.0,
                    model_id=self.MODEL_ID,
                    model_version=self.MODEL_VERSION,
                    notes="transcript segment too short",
                ),
            )

        evasion = _count_matches(_EVASION, text)
        pressure = _count_matches(_PRESSURE, text)
        steering = _count_matches(_STEERING, text)
        absolutes = _count_matches(_ABSOLUTES, text)

        indicators = []
        if evasion:
            indicators.append({"kind": "evasion", "patterns": evasion})
        if pressure:
            indicators.append({"kind": "pressure", "patterns": pressure})
        if steering:
            indicators.append({"kind": "steering", "patterns": steering})
        if absolutes:
            indicators.append({"kind": "absolute_language", "patterns": absolutes})

        # Score: capped, transparent, never "this is manipulation"
        raw = 0.15 * len(evasion) + 0.25 * len(pressure) + 0.2 * len(steering) + 0.1 * len(absolutes)
        score = min(0.65, raw)  # hard cap — rule-based linguistic only

        interpretation = (
            "multiple_steering_indicators" if score >= 0.45 else
            "mild_linguistic_indicators" if score >= 0.2 else
            "no_significant_indicators"
        )

        return DetectionResult(
            signal=SignalType.MANIPULATION,
            timestamp=ts,
            value={
                "status": "ok",
                "indicators": indicators,
                "interpretation": interpretation,
                "note": "rule-based linguistic patterns only — not proof of intent",
            },
            confidence=Confidence(
                score=round(score, 3),
                model_id=self.MODEL_ID,
                model_version=self.MODEL_VERSION,
                notes=(
                    "transparent regex indicators; confidence capped at 0.65; "
                    "never a claim of manipulative intent"
                ),
            ),
            baseline_deviation=score,
            provenance={"engine": "rules-linguistic", "pattern_sets": 4},
        )
