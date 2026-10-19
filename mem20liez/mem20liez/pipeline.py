"""Top-level detector that runs all signal extractors."""

from __future__ import annotations

from typing import Any, Optional, List
import time

from .types import DetectionResult, SignalType
from .detectors import (
    MicroExpressionDetector,
    VoiceStressDetector,
    EmotionDetector,
    ManipulationDetector,
    DeceptionDetector,
)


class LieDetector:
    """Orchestrates all behavioural signal detectors."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.micro = MicroExpressionDetector(enabled=enabled)
        self.voice = VoiceStressDetector(enabled=enabled)
        self.emotion = EmotionDetector(enabled=enabled)
        self.manipulation = ManipulationDetector(enabled=enabled)
        self.deception = DeceptionDetector(enabled=enabled)
        self._history: List[DetectionResult] = []

    def set_baselines(self, *, face: Optional[dict] = None, voice: Optional[dict] = None) -> None:
        if face is not None:
            self.micro.set_baseline(face)
        if voice is not None:
            self.voice.set_baseline(voice)

    def process_audio(self, chunk: Any, timestamp: Optional[float] = None) -> List[DetectionResult]:
        ts = timestamp or time.time()
        results = []
        vs = self.voice.process_audio(chunk, timestamp=ts)
        results.append(vs)
        emo = self.emotion.process(audio_chunk=chunk, timestamp=ts)
        results.append(emo)
        self._history.extend(results)
        return results

    def process_video(self, frame: Any, timestamp: Optional[float] = None) -> List[DetectionResult]:
        ts = timestamp or time.time()
        results = []
        me = self.micro.process_frame(frame, timestamp=ts)
        results.append(me)
        emo = self.emotion.process(video_frame=frame, timestamp=ts)
        results.append(emo)
        self._history.extend(results)
        return results

    def process_transcript(self, text: str, timestamp: Optional[float] = None) -> List[DetectionResult]:
        ts = timestamp or time.time()
        man = self.manipulation.process(transcript_segment=text, timestamp=ts)
        self._history.append(man)
        return [man]

    def fuse_deception(self, recent: Optional[List[DetectionResult]] = None) -> DetectionResult:
        signals = recent if recent is not None else self._history[-12:]
        return self.deception.fuse(signals)

    def recent(self, n: int = 20) -> List[DetectionResult]:
        return self._history[-n:]
