"""Turn detection results into short TTS-ready earpiece cues."""

from __future__ import annotations

from typing import List
import uuid
import time

from .types import DetectionResult, EarpieceCue, SignalType


class CueGenerator:
    def __init__(self, mode: str = "generic"):
        self.mode = mode

    def from_detections(self, results: List[DetectionResult], mode: str | None = None) -> List[EarpieceCue]:
        mode = mode or self.mode
        cues: List[EarpieceCue] = []

        for r in results:
            # Gate: require usable confidence; micro can fire a bit lower when status=ok
            min_conf = 0.40 if r.signal == SignalType.MICRO_EXPRESSION else 0.45
            if r.confidence.score < min_conf:
                continue

            text = self._render(r, mode)
            if not text:
                continue

            cues.append(
                EarpieceCue(
                    id=str(uuid.uuid4()),
                    text=text,
                    priority=self._priority(r),
                    related_signals=[r.signal],
                    confidence=r.confidence.score,
                    timestamp=r.timestamp or time.time(),
                )
            )
        return cues

    def _render(self, r: DetectionResult, mode: str) -> str:
        if r.signal == SignalType.VOICE_STRESS:
            val = r.value or {}
            if val.get("status") != "ok":
                return ""
            interp = val.get("interpretation", "")
            dev = val.get("baseline_deviation")
            if interp == "elevated_stress_indicator":
                if mode in ("interrogation", "government"):
                    return f"Voice stress elevated (deviation {dev:.2f}). Consider slowing pace."
                if mode == "clinical":
                    return f"Patient voice stress elevated (deviation {dev:.2f})."
                if mode == "therapy":
                    return f"Voice stress rise noted (deviation {dev:.2f})."
                return f"Voice stress indicator elevated (deviation {dev:.2f})."
            if interp == "mild_deviation":
                return "Mild voice stress deviation."
            return ""

        if r.signal == SignalType.MICRO_EXPRESSION:
            val = r.value or {}
            if val.get("status") != "ok":
                return ""
            interp = val.get("interpretation", "")
            score = val.get("micro_score")
            if interp == "micro_expression_candidate":
                if mode in ("interrogation", "government"):
                    return f"Facial micro-motion candidate (score {score:.2f})."
                return f"Micro-expression candidate (score {score:.2f})."
            if interp == "mild_facial_motion":
                return "Mild facial motion noted."
            return ""

        if r.signal == SignalType.EMOTION:
            return "Emotional shift noted."
        if r.signal == SignalType.MANIPULATION:
            return "Possible conversational steering."
        if r.signal == SignalType.DECEPTION:
            return "Deception indicator present — treat as hypothesis only."
        return ""

    def _priority(self, r: DetectionResult) -> int:
        if r.signal == SignalType.VOICE_STRESS and (r.baseline_deviation or 0) >= 0.55:
            return 3
        if r.signal == SignalType.MICRO_EXPRESSION and (r.baseline_deviation or 0) >= 0.55:
            return 3
        if r.signal == SignalType.DECEPTION and r.confidence.score >= 0.75:
            return 3
        if r.confidence.score >= 0.7:
            return 2
        return 1
