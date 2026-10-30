"""Real-time emotion detector (classical feature-based).

Estimates valence/arousal from acoustic and facial features using
transparent heuristics. Never claims a labelled emotion with certainty;
outputs are coarse indicators with bounded confidence. Not a clinical
or diagnostic tool.
"""

from __future__ import annotations

from typing import Any, Optional
import time

from ..types import DetectionResult, SignalType, Confidence

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from .voice_stress import _bytes_to_float32, _rms, _zcr, _estimate_pitch, _energy_variance, _burst_rate
    HAS_VOICE_HELPERS = True
except Exception:
    HAS_VOICE_HELPERS = False

try:
    from .micro_expression import _to_gray, _central_crop, _region_means
    HAS_FACE_HELPERS = True
except Exception:
    HAS_FACE_HELPERS = False


def _audio_features(chunk: Any, sample_rate: int = 16000) -> Optional[dict]:
    if not HAS_NUMPY or chunk is None:
        return None
    if isinstance(chunk, (bytes, bytearray)):
        if not HAS_VOICE_HELPERS:
            return None
        x = _bytes_to_float32(bytes(chunk), sample_width=2)
    elif isinstance(chunk, np.ndarray):
        x = chunk.astype(np.float32)
        if x.ndim > 1:
            x = x.mean(axis=-1)
    else:
        try:
            x = np.asarray(chunk, dtype=np.float32).ravel()
        except Exception:
            return None
    if x.size < 160:
        return None
    if HAS_VOICE_HELPERS:
        feats = {
            "rms": _rms(x),
            "zcr": _zcr(x),
            "pitch_hz": _estimate_pitch(x, sample_rate),
            "energy_var": _energy_variance(x),
            "burst_rate": _burst_rate(x, sample_rate),
            "n_samples": int(x.size),
        }
    else:
        feats = {
            "rms": float(np.sqrt(np.mean(x * x))) if x.size else 0.0,
            "zcr": 0.0,
            "pitch_hz": 0.0,
            "energy_var": 0.0,
            "burst_rate": 0.0,
            "n_samples": int(x.size),
        }
    return feats


def _face_features(frame: Any) -> Optional[dict]:
    if not HAS_NUMPY or frame is None:
        return None
    if HAS_FACE_HELPERS:
        gray = _to_gray(frame)
    else:
        if isinstance(frame, np.ndarray):
            arr = frame.astype(np.float32)
            if arr.ndim == 3:
                arr = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
            if arr.max() > 1.5:
                arr = arr / 255.0
            gray = arr
        else:
            return None
    if gray is None or gray.size < 100:
        return None
    if HAS_FACE_HELPERS:
        face = _central_crop(gray)
        regions = _region_means(face)
    else:
        face = gray
        regions = {"global": float(np.mean(face))}
    motion = float(np.std(face)) if face.size else 0.0
    brightness = float(np.mean(face)) if face.size else 0.0
    return {
        "regions": regions,
        "motion": motion,
        "brightness": brightness,
        "face_size": int(face.size),
    }


def _arousal_from_audio(f: dict) -> float:
    rms = min(1.0, f.get("rms", 0.0) * 4.0)
    pitch = min(1.0, (f.get("pitch_hz", 0.0) / 300.0)) if f.get("pitch_hz", 0) > 0 else 0.3
    burst = min(1.0, f.get("burst_rate", 0.0) / 6.0)
    ev = min(1.0, f.get("energy_var", 0.0) * 20.0)
    return float(min(1.0, max(0.0, 0.35 * rms + 0.25 * pitch + 0.2 * burst + 0.2 * ev)))


def _valence_from_audio(f: dict) -> float:
    zcr = f.get("zcr", 0.0)
    pitch = f.get("pitch_hz", 0.0)
    val = 0.0
    if pitch > 120:
        val += 0.15
    if zcr < 0.1:
        val += 0.1
    if f.get("energy_var", 0.0) > 0.02:
        val -= 0.05
    return float(max(-1.0, min(1.0, val)))


def _arousal_from_face(f: dict) -> float:
    motion = min(1.0, f.get("motion", 0.0) * 12.0)
    regions = f.get("regions", {})
    vals = [v for v in regions.values() if isinstance(v, (int, float))]
    spread = (max(vals) - min(vals)) if len(vals) > 1 else 0.0
    return float(min(1.0, max(0.0, 0.5 * motion + 0.5 * min(1.0, spread * 4.0))))


def _valence_from_face(f: dict) -> float:
    regions = f.get("regions", {})
    mouth = regions.get("mouth", 0.5)
    brow = regions.get("brow_center", 0.5)
    global_i = regions.get("global", 0.5)
    val = (mouth - brow) * 2.0 + (global_i - 0.5)
    return float(max(-1.0, min(1.0, val)))


def _categorical(valence: float, arousal: float) -> str:
    if arousal >= 0.5:
        return "excited/activated" if valence >= 0 else "tense/anxious"
    return "calm/positive" if valence >= 0 else "low/sad"


class EmotionDetector:
    MODEL_ID = "mem20liez.emotion"
    MODEL_VERSION = "0.2.0-classical"

    def __init__(self, enabled: bool = True, sample_rate: int = 16000):
        self.enabled = enabled
        self.sample_rate = sample_rate

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

        audio_f = _audio_features(audio_chunk, self.sample_rate) if audio_chunk is not None else None
        face_f = _face_features(video_frame) if video_frame is not None else None

        if audio_f is None and face_f is None:
            return DetectionResult(
                signal=SignalType.EMOTION,
                timestamp=ts,
                value={"status": "no_input", "valence": None, "arousal": None, "categorical": None},
                confidence=Confidence(
                    score=0.0,
                    model_id=self.MODEL_ID,
                    model_version=self.MODEL_VERSION,
                    notes="no audio or video input provided",
                ),
                provenance={"engine": "none"},
            )

        valences = []
        arousals = []
        sources = []
        if audio_f is not None:
            valences.append(_valence_from_audio(audio_f))
            arousals.append(_arousal_from_audio(audio_f))
            sources.append("audio")
        if face_f is not None:
            valences.append(_valence_from_face(face_f))
            arousals.append(_arousal_from_face(face_f))
            sources.append("video")

        valence = float(sum(valences) / len(valences))
        arousal = float(sum(arousals) / len(arousals))
        categorical = _categorical(valence, arousal)

        conf = 0.30
        if audio_f is not None:
            conf += 0.20
            if audio_f.get("rms", 0) > 0.01:
                conf += 0.10
            if audio_f.get("pitch_hz", 0) > 50:
                conf += 0.05
        if face_f is not None:
            conf += 0.20
            if face_f.get("face_size", 0) > 5000:
                conf += 0.10
        if len(sources) == 2:
            conf += 0.05
        conf = min(0.75, conf)

        value = {
            "status": "ok",
            "valence": round(valence, 3),
            "arousal": round(arousal, 3),
            "categorical": categorical,
            "modalities": sources,
            "note": "classical feature-based estimate — indicator only, not a diagnosis",
        }
        if audio_f is not None:
            value["audio_features"] = {
                "rms": round(audio_f.get("rms", 0.0), 4),
                "pitch_hz": round(audio_f.get("pitch_hz", 0.0), 2),
                "zcr": round(audio_f.get("zcr", 0.0), 4),
            }
        if face_f is not None:
            value["face_motion"] = round(face_f.get("motion", 0.0), 4)

        return DetectionResult(
            signal=SignalType.EMOTION,
            timestamp=ts,
            value=value,
            confidence=Confidence(
                score=round(conf, 3),
                model_id=self.MODEL_ID,
                model_version=self.MODEL_VERSION,
                notes=(
                    "classical acoustic + facial feature heuristics; "
                    "coarse valence/arousal indicator, not an emotion diagnosis"
                ),
            ),
            raw_features={"audio": audio_f, "face": face_f},
            provenance={"engine": "classical-heuristic", "modalities": sources},
        )
