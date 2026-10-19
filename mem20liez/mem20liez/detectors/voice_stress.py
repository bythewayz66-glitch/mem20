"""Real-time voice stress detector.

Pure-numpy implementation of classic acoustic features commonly used
as voice-stress indicators:

- RMS energy
- Zero-crossing rate
- Simple pitch estimate (autocorrelation)
- Short-term energy variance
- Speaking-rate proxy (energy bursts)

All scores are relative to an optional personal baseline.
Confidence is derived from signal quality and baseline presence.
Never claims deception — only reports stress indicators.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple
import time
import struct
import math

from ..types import DetectionResult, SignalType, Confidence

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore


def _bytes_to_float32(chunk: bytes, sample_width: int = 2) -> "np.ndarray":
    """Convert raw PCM bytes to float32 mono in [-1, 1]."""
    if sample_width == 2:
        n = len(chunk) // 2
        if n == 0:
            return np.zeros(0, dtype=np.float32)
        samples = struct.unpack(f"<{n}h", chunk[: n * 2])
        arr = np.array(samples, dtype=np.float32) / 32768.0
        return arr
    # fallback: treat as raw float32
    n = len(chunk) // 4
    if n == 0:
        return np.zeros(0, dtype=np.float32)
    return np.frombuffer(chunk[: n * 4], dtype=np.float32).copy()


def _rms(x: "np.ndarray") -> float:
    if x.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(x * x)))


def _zcr(x: "np.ndarray") -> float:
    if x.size < 2:
        return 0.0
    signs = np.sign(x)
    signs[signs == 0] = 1
    return float(np.mean(np.abs(np.diff(signs)) > 0))


def _estimate_pitch(x: "np.ndarray", sr: int = 16000, fmin: float = 80.0, fmax: float = 400.0) -> float:
    """Very simple autocorrelation pitch estimate. Returns 0 if unreliable."""
    if x.size < sr // 20:  # need at least ~50 ms
        return 0.0
    # window
    w = x[: min(len(x), sr // 4)]
    w = w - np.mean(w)
    if np.max(np.abs(w)) < 1e-4:
        return 0.0
    corr = np.correlate(w, w, mode="full")
    corr = corr[len(corr) // 2 :]
    # search range
    min_lag = int(sr / fmax)
    max_lag = int(sr / fmin)
    if max_lag >= len(corr):
        max_lag = len(corr) - 1
    if min_lag >= max_lag:
        return 0.0
    segment = corr[min_lag:max_lag]
    if segment.size == 0:
        return 0.0
    peak = int(np.argmax(segment)) + min_lag
    if corr[peak] < 0.3 * corr[0]:
        return 0.0
    return float(sr / peak)


def _energy_variance(x: "np.ndarray", frame: int = 256) -> float:
    if x.size < frame * 2:
        return 0.0
    frames = []
    for i in range(0, len(x) - frame, frame // 2):
        frames.append(_rms(x[i : i + frame]))
    if len(frames) < 2:
        return 0.0
    return float(np.var(frames))


def _burst_rate(x: "np.ndarray", sr: int = 16000, thresh: float = 0.02) -> float:
    """Rough speaking-rate proxy: energy bursts per second."""
    if x.size < sr // 10:
        return 0.0
    frame = max(64, sr // 50)
    energies = [_rms(x[i : i + frame]) for i in range(0, len(x) - frame, frame)]
    if not energies:
        return 0.0
    above = sum(1 for e in energies if e > thresh)
    duration = len(x) / sr
    return float(above / max(duration, 0.01))


class VoiceStressDetector:
    MODEL_ID = "mem20liez.voice_stress"
    MODEL_VERSION = "0.2.0-numpy"

    def __init__(self, enabled: bool = True, sample_rate: int = 16000):
        self.enabled = enabled
        self.sample_rate = sample_rate
        self._baseline: Optional[dict] = None

    def set_baseline(self, audio_features: dict) -> None:
        """Store neutral baseline features for later deviation scoring."""
        self._baseline = dict(audio_features)

    def _extract(self, x: "np.ndarray") -> dict:
        return {
            "rms": _rms(x),
            "zcr": _zcr(x),
            "pitch_hz": _estimate_pitch(x, self.sample_rate),
            "energy_var": _energy_variance(x),
            "burst_rate": _burst_rate(x, self.sample_rate),
            "n_samples": int(x.size),
            "duration_s": float(x.size / self.sample_rate) if self.sample_rate else 0.0,
        }

    def _deviation_score(self, features: dict) -> Tuple[float, dict]:
        """Return (0-1 stress-like deviation, detail dict)."""
        if not self._baseline:
            return 0.0, {"reason": "no baseline"}

        detail = {}
        scores = []

        # Higher RMS / energy variance relative to baseline → possible stress
        for key, weight in [("rms", 0.25), ("energy_var", 0.25), ("zcr", 0.15), ("burst_rate", 0.15)]:
            b = self._baseline.get(key)
            v = features.get(key)
            if b is None or v is None or b == 0:
                continue
            ratio = v / (b + 1e-8)
            # stress often increases these; clamp contribution
            contrib = min(1.0, max(0.0, (ratio - 1.0) * 1.5))
            scores.append(contrib * weight)
            detail[key] = {"baseline": b, "current": v, "ratio": ratio, "contrib": contrib}

        # Pitch: both large upward or downward shifts can be informative
        bp = self._baseline.get("pitch_hz") or 0.0
        cp = features.get("pitch_hz") or 0.0
        if bp > 50 and cp > 50:
            pitch_ratio = abs(cp - bp) / bp
            pitch_contrib = min(1.0, pitch_ratio * 2.0) * 0.2
            scores.append(pitch_contrib)
            detail["pitch_hz"] = {"baseline": bp, "current": cp, "contrib": pitch_contrib}

        if not scores:
            return 0.0, detail
        return float(min(1.0, sum(scores))), detail

    def process_audio(
        self,
        chunk: bytes | Any,
        timestamp: Optional[float] = None,
        sample_width: int = 2,
    ) -> DetectionResult:
        ts = timestamp or time.time()

        if not self.enabled:
            return DetectionResult(
                signal=SignalType.VOICE_STRESS,
                timestamp=ts,
                value={"status": "disabled"},
                confidence=Confidence(
                    score=0.0,
                    model_id=self.MODEL_ID,
                    model_version=self.MODEL_VERSION,
                    notes="detector disabled",
                ),
            )

        if not HAS_NUMPY:
            return DetectionResult(
                signal=SignalType.VOICE_STRESS,
                timestamp=ts,
                value={"status": "numpy_missing"},
                confidence=Confidence(
                    score=0.0,
                    model_id=self.MODEL_ID,
                    model_version=self.MODEL_VERSION,
                    notes="numpy not installed — voice stress requires numpy",
                ),
                provenance={"engine": "numpy-required"},
            )

        # Accept already-numpy arrays or raw PCM bytes
        if isinstance(chunk, np.ndarray):
            x = chunk.astype(np.float32)
            if x.ndim > 1:
                x = x.mean(axis=-1)
        elif isinstance(chunk, (bytes, bytearray)):
            x = _bytes_to_float32(bytes(chunk), sample_width=sample_width)
        else:
            # last-resort: try to coerce
            try:
                x = np.asarray(chunk, dtype=np.float32).ravel()
            except Exception:
                return DetectionResult(
                    signal=SignalType.VOICE_STRESS,
                    timestamp=ts,
                    value={"status": "bad_input", "type": str(type(chunk))},
                    confidence=Confidence(
                        score=0.0,
                        model_id=self.MODEL_ID,
                        model_version=self.MODEL_VERSION,
                        notes="could not convert input to float audio",
                    ),
                )

        if x.size < 160:  # < 10 ms @ 16 kHz
            return DetectionResult(
                signal=SignalType.VOICE_STRESS,
                timestamp=ts,
                value={"status": "too_short", "n_samples": int(x.size)},
                confidence=Confidence(
                    score=0.0,
                    model_id=self.MODEL_ID,
                    model_version=self.MODEL_VERSION,
                    notes="audio chunk too short for reliable features",
                ),
            )

        features = self._extract(x)
        deviation, detail = self._deviation_score(features)

        # Confidence: higher when we have a baseline and enough signal energy
        conf = 0.35
        if self._baseline:
            conf += 0.35
        if features["rms"] > 0.01:
            conf += 0.15
        if features["pitch_hz"] > 50:
            conf += 0.15
        conf = min(0.95, conf)

        value = {
            "status": "ok",
            "features": features,
            "baseline_deviation": deviation,
            "deviation_detail": detail,
            "has_baseline": self._baseline is not None,
            "interpretation": (
                "elevated_stress_indicator" if deviation >= 0.45 else
                "mild_deviation" if deviation >= 0.25 else
                "near_baseline"
            ),
        }

        return DetectionResult(
            signal=SignalType.VOICE_STRESS,
            timestamp=ts,
            value=value,
            confidence=Confidence(
                score=round(conf, 3),
                model_id=self.MODEL_ID,
                model_version=self.MODEL_VERSION,
                notes=(
                    "classic acoustic features + optional baseline deviation; "
                    "not a deception claim"
                ),
            ),
            baseline_deviation=deviation,
            raw_features=features,
            provenance={
                "engine": "numpy-classic",
                "sample_rate": self.sample_rate,
            },
        )
