\"\"\"Turn detection results into short TTS-ready earpiece cues.\"\"\"

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
            if r.confidence.score < 0.55:
                continue  # too weak to bother the professional

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
        # Scaffold language — deliberately cautious.
        if r.signal == SignalType.VOICE_STRESS:
            return "Voice stress indicator elevated."
        if r.signal == SignalType.MICRO_EXPRESSION:
            return "Possible micro-expression detected."
        if r.signal == SignalType.EMOTION:
            return "Emotional shift noted."
        if r.signal == SignalType.MANIPULATION:
            return "Possible conversational steering."
        if r.signal == SignalType.DECEPTION:
            return "Deception indicator present — treat as hypothesis only."
        return ""

    def _priority(self, r: DetectionResult) -> int:
        if r.signal == SignalType.DECEPTION and r.confidence.score >= 0.75:
            return 3
        if r.confidence.score >= 0.7:
            return 2
        return 1
