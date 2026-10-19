"""Micro-expression detector (real classical pipeline).

Uses only numpy + optional PIL. No OpenCV / MediaPipe required.

Approach
--------
1. Convert frame to grayscale float.
2. Maintain a short temporal buffer.
3. Compute frame-to-frame absolute difference (motion energy).
4. Partition the face-ish upper/mid/lower thirds into regions that
   roughly correspond to common action-unit zones (brows, eyes, nose,
   mouth). Without a face detector we treat the central portrait crop
   as the face; callers can pass an explicit bbox.
5. Score short-lived intensity spikes in those regions as micro-expression
   candidates. Baseline-relative scoring when a neutral baseline is set.

This is deliberately classical and honest: it reports motion energy and
region spikes with confidence, never "AU12 detected with certainty".
"""

from __future__ import annotations

from typing import Any, Optional, Tuple, List
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


def _to_gray(frame: Any) -> Optional["np.ndarray"]:
    """Accept numpy HxW, HxWxC, PIL Image, or raw bytes (fail soft)."""
    if not HAS_NUMPY:
        return None
    if frame is None:
        return None
    if HAS_PIL and isinstance(frame, Image.Image):
        arr = np.asarray(frame.convert("L"), dtype=np.float32)
        return arr / 255.0
    if isinstance(frame, np.ndarray):
        arr = frame.astype(np.float32)
        if arr.ndim == 3:
            # RGB or BGR → gray
            if arr.shape[2] >= 3:
                arr = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
            else:
                arr = arr[:, :, 0]
        if arr.max() > 1.5:
            arr = arr / 255.0
        return arr
    # unsupported
    return None


def _central_crop(gray: "np.ndarray", frac: float = 0.7) -> "np.ndarray":
    h, w = gray.shape
    ch, cw = int(h * frac), int(w * frac)
    y0 = (h - ch) // 2
    x0 = (w - cw) // 2
    return gray[y0 : y0 + ch, x0 : x0 + cw]


def _region_means(face: "np.ndarray") -> dict:
    """Split face crop into AU-ish bands and return mean intensity per band."""
    h, w = face.shape
    # vertical thirds
    t1, t2 = h // 3, 2 * h // 3
    # horizontal thirds for left/right
    l1, l2 = w // 3, 2 * w // 3

    def m(y0, y1, x0, x1):
        patch = face[y0:y1, x0:x1]
        return float(np.mean(patch)) if patch.size else 0.0

    return {
        "brow_left": m(0, t1, 0, l1),
        "brow_center": m(0, t1, l1, l2),
        "brow_right": m(0, t1, l2, w),
        "eye_left": m(t1, t2, 0, l1),
        "eye_right": m(t1, t2, l2, w),
        "nose": m(t1, t2, l1, l2),
        "mouth": m(t2, h, l1, l2),
        "mouth_left": m(t2, h, 0, l1),
        "mouth_right": m(t2, h, l2, w),
        "global": float(np.mean(face)),
    }


class MicroExpressionDetector:
    MODEL_ID = "mem20liez.micro_expression"
    MODEL_VERSION = "0.2.0-numpy-pil"

    def __init__(self, enabled: bool = True, buffer_size: int = 5):
        self.enabled = enabled
        self.buffer_size = buffer_size
        self._prev: Optional["np.ndarray"] = None
        self._baseline_regions: Optional[dict] = None
        self._spike_history: List[float] = []

    def set_baseline(self, features: dict) -> None:
        """Store neutral region means (from a calm frame)."""
        if "regions" in features:
            self._baseline_regions = dict(features["regions"])
        else:
            self._baseline_regions = dict(features)

    def process_frame(self, frame: Any, timestamp: Optional[float] = None) -> DetectionResult:
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

        if not HAS_NUMPY:
            return DetectionResult(
                signal=SignalType.MICRO_EXPRESSION,
                timestamp=ts,
                value={"status": "numpy_missing"},
                confidence=Confidence(
                    score=0.0,
                    model_id=self.MODEL_ID,
                    model_version=self.MODEL_VERSION,
                    notes="numpy required",
                ),
            )

        gray = _to_gray(frame)
        if gray is None or gray.size < 100:
            return DetectionResult(
                signal=SignalType.MICRO_EXPRESSION,
                timestamp=ts,
                value={"status": "bad_frame", "note": "could not convert to grayscale"},
                confidence=Confidence(
                    score=0.0,
                    model_id=self.MODEL_ID,
                    model_version=self.MODEL_VERSION,
                    notes="unsupported or empty frame",
                ),
            )

        face = _central_crop(gray)
        regions = _region_means(face)

        motion_energy = 0.0
        if self._prev is not None and self._prev.shape == face.shape:
            diff = np.abs(face - self._prev)
            motion_energy = float(np.mean(diff))
        self._prev = face.copy()

        # Baseline deviation per region
        region_dev = {}
        max_dev = 0.0
        if self._baseline_regions:
            for k, v in regions.items():
                b = self._baseline_regions.get(k)
                if b is None:
                    continue
                d = abs(v - b)
                region_dev[k] = d
                if d > max_dev:
                    max_dev = d

        # Spike score: short-lived high motion relative to recent history
        self._spike_history.append(motion_energy)
        if len(self._spike_history) > 30:
            self._spike_history = self._spike_history[-30:]
        recent_mean = float(np.mean(self._spike_history[:-1])) if len(self._spike_history) > 1 else 0.0
        spike = 0.0
        if recent_mean > 1e-6:
            spike = min(1.0, max(0.0, (motion_energy - recent_mean) / (recent_mean + 1e-4)))
        elif motion_energy > 0.02:
            spike = min(1.0, motion_energy * 10)

        # Combined micro-expression likelihood (heuristic)
        micro_score = 0.0
        micro_score += 0.45 * spike
        micro_score += 0.35 * min(1.0, max_dev * 8)  # intensity shift vs baseline
        micro_score += 0.20 * min(1.0, motion_energy * 15)
        micro_score = float(min(1.0, micro_score))

        conf = 0.40
        if self._baseline_regions:
            conf += 0.25
        if motion_energy > 0.005:
            conf += 0.15
        if face.size > 5000:
            conf += 0.10
        conf = min(0.90, conf)

        interpretation = (
            "micro_expression_candidate" if micro_score >= 0.45 else
            "mild_facial_motion" if micro_score >= 0.25 else
            "near_baseline"
        )

        value = {
            "status": "ok",
            "motion_energy": round(motion_energy, 5),
            "spike": round(spike, 4),
            "micro_score": round(micro_score, 4),
            "regions": {k: round(v, 4) for k, v in regions.items()},
            "region_deviation": {k: round(v, 4) for k, v in region_dev.items()},
            "max_region_deviation": round(max_dev, 4),
            "has_baseline": self._baseline_regions is not None,
            "interpretation": interpretation,
            "engine": "numpy-pil-classical",
        }

        return DetectionResult(
            signal=SignalType.MICRO_EXPRESSION,
            timestamp=ts,
            value=value,
            confidence=Confidence(
                score=round(conf, 3),
                model_id=self.MODEL_ID,
                model_version=self.MODEL_VERSION,
                notes=(
                    "classical frame-diff + regional intensity; "
                    "not a labelled AU classifier; treat as observation only"
                ),
            ),
            baseline_deviation=micro_score,
            raw_features={"regions": regions, "motion_energy": motion_energy},
            provenance={"engine": "numpy-pil-classical", "has_pil": HAS_PIL},
        )
