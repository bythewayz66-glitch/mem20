"""Live session wrapper that ties detectors to the AV memory pipeline."""

from __future__ import annotations

from typing import Any, Optional, List, Literal
import time
import uuid

from .pipeline import LieDetector
from .types import DetectionResult, EarpieceCue, SignalType
from .cues import CueGenerator

SessionMode = Literal["interrogation", "therapy", "clinical", "government", "generic"]


class LiveLieSession:
    """One live professional session with continuous detection + cueing."""

    def __init__(
        self,
        detector: Optional[LieDetector] = None,
        mode: SessionMode = "generic",
        enable_earpiece: bool = True,
    ):
        self.session_id = str(uuid.uuid4())
        self.mode = mode
        self.detector = detector or LieDetector()
        self.cue_gen = CueGenerator(mode=mode)
        self.enable_earpiece = enable_earpiece

        self._cues: List[EarpieceCue] = []
        self._all_detections: List[DetectionResult] = []
        self.started_at = time.time()
        self.sealed = False
        self._meta: dict = {}

    def feed_audio(self, chunk: Any, timestamp: Optional[float] = None) -> List[DetectionResult]:
        results = self.detector.process_audio(chunk, timestamp=timestamp)
        self._all_detections.extend(results)
        self._maybe_generate_cues(results)
        return results

    def feed_video(self, frame: Any, timestamp: Optional[float] = None) -> List[DetectionResult]:
        results = self.detector.process_video(frame, timestamp=timestamp)
        self._all_detections.extend(results)
        self._maybe_generate_cues(results)
        return results

    def feed_transcript(self, text: str, timestamp: Optional[float] = None) -> List[DetectionResult]:
        results = self.detector.process_transcript(text, timestamp=timestamp)
        self._all_detections.extend(results)
        self._maybe_generate_cues(results)
        return results

    def _maybe_generate_cues(self, new_results: List[DetectionResult]) -> None:
        if not self.enable_earpiece:
            return
        new_cues = self.cue_gen.from_detections(new_results, mode=self.mode)
        self._cues.extend(new_cues)

    def get_earpiece_cues(self, since_id: Optional[str] = None) -> List[EarpieceCue]:
        if since_id is None:
            return [c for c in self._cues if not c.acknowledged]
        out = []
        seen = False
        for c in self._cues:
            if c.id == since_id:
                seen = True
                continue
            if seen and not c.acknowledged:
                out.append(c)
        return out

    def acknowledge_cue(self, cue_id: str) -> None:
        for c in self._cues:
            if c.id == cue_id:
                c.acknowledged = True
                break

    def seal(self, annotations: Optional[dict] = None) -> dict:
        """Produce the package that will be written to grounded memory."""
        if self.sealed:
            raise RuntimeError("session already sealed")

        self.sealed = True
        package = {
            "session_id": self.session_id,
            "mode": self.mode,
            "started_at": self.started_at,
            "sealed_at": time.time(),
            "detections": [d.model_dump() for d in self._all_detections],
            "cues": [c.model_dump() for c in self._cues],
            "annotations": annotations or {},
            "meta": self._meta,
            "disclaimer": (
                "All behavioural signals are probabilistic observations only. "
                "They do not constitute definitive proof of deception, emotion, "
                "or intent. Model versions and confidence scores are recorded "
                "for audit."
            ),
        }
        return package
