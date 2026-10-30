"""Deception indicator fusion (classical, multi-signal).

Combines voice-stress deviation, micro-expression spikes, manipulation
indicators, and emotion arousal into a single probabilistic indicator.
Requires multiple converging signals before the score rises; a single
indicator never produces a high score. Never claims deception definitively.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence
import time

from ..types import DetectionResult, SignalType, Confidence


def _extract_contributions(signals: Sequence[DetectionResult]) -> dict:
    """Pull numeric indicator strengths from a list of detection results."""
    voice_dev = 0.0
    voice_conf = 0.0
    micro_score = 0.0
    micro_conf = 0.0
    manip_score = 0.0
    manip_conf = 0.0
    emotion_arousal = 0.0
    emotion_conf = 0.0
    n_voice = 0
    n_micro = 0
    n_manip = 0
    n_emotion = 0

    for s in signals:
        if s is None:
            continue
        val = s.value if isinstance(s.value, dict) else {}
        conf = s.confidence.score if s.confidence else 0.0
        if s.signal == SignalType.VOICE_STRESS:
            if val.get("status") == "ok":
                voice_dev = max(voice_dev, float(val.get("baseline_deviation", 0.0) or 0.0))
                voice_conf = max(voice_conf, conf)
                n_voice += 1
        elif s.signal == SignalType.MICRO_EXPRESSION:
            if val.get("status") == "ok":
                micro_score = max(micro_score, float(val.get("micro_score", 0.0) or 0.0))
                micro_conf = max(micro_conf, conf)
                n_micro += 1
        elif s.signal == SignalType.MANIPULATION:
            if val.get("status") == "ok":
                manip_score = max(manip_score, float(val.get("baseline_deviation", 0.0) or 0.0))
                manip_conf = max(manip_conf, conf)
                n_manip += 1
        elif s.signal == SignalType.EMOTION:
            if val.get("status") == "ok":
                arousal = val.get("arousal")
                if isinstance(arousal, (int, float)):
                    emotion_arousal = max(emotion_arousal, float(arousal))
                    emotion_conf = max(emotion_conf, conf)
                    n_emotion += 1

    return {
        "voice_deviation": voice_dev,
        "voice_confidence": voice_conf,
        "n_voice": n_voice,
        "micro_score": micro_score,
        "micro_confidence": micro_conf,
        "n_micro": n_micro,
        "manipulation_score": manip_score,
        "manipulation_confidence": manip_conf,
        "n_manipulation": n_manip,
        "emotion_arousal": emotion_arousal,
        "emotion_confidence": emotion_conf,
        "n_emotion": n_emotion,
    }


class DeceptionDetector:
    MODEL_ID = "mem20liez.deception"
    MODEL_VERSION = "0.2.0-fusion"

    # Hard cap: never present as certainty.
    MAX_SCORE = 0.75
    MAX_CONFIDENCE = 0.70

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

        signals = list(signals or [])
        contrib = _extract_contributions(signals)

        # Convergence: count how many distinct indicator families are elevated.
        elevated = 0
        if contrib["voice_deviation"] >= 0.35 and contrib["n_voice"] > 0:
            elevated += 1
        if contrib["micro_score"] >= 0.40 and contrib["n_micro"] > 0:
            elevated += 1
        if contrib["manipulation_score"] >= 0.30 and contrib["n_manipulation"] > 0:
            elevated += 1
        if contrib["emotion_arousal"] >= 0.60 and contrib["n_emotion"] > 0:
            elevated += 1

        # Weighted base score — single indicator contributes little.
        base = (
            0.30 * contrib["voice_deviation"]
            + 0.25 * contrib["micro_score"]
            + 0.25 * contrib["manipulation_score"]
            + 0.20 * contrib["emotion_arousal"]
        )

        # Convergence bonus: requires >=2 elevated families to matter.
        convergence_bonus = 0.0
        if elevated >= 2:
            convergence_bonus = 0.10 * (elevated - 1)
        if elevated >= 3:
            convergence_bonus += 0.05

        score = min(self.MAX_SCORE, base + convergence_bonus)

        # If only one family elevated, dampen — single indicator is not evidence.
        if elevated <= 1:
            score = min(score, 0.35)

        # Interpretation
        if elevated >= 3:
            interpretation = "multiple_converging_indicators"
        elif elevated == 2:
            interpretation = "two_converging_indicators"
        elif elevated == 1:
            interpretation = "single_indicator_only"
        else:
            interpretation = "no_converging_indicators"

        # Confidence: depends on number of distinct signals and their quality.
        distinct = sum(1 for k in ("n_voice", "n_micro", "n_manipulation", "n_emotion") if contrib[k] > 0)
        conf = 0.20
        if distinct >= 2:
            conf += 0.15
        if distinct >= 3:
            conf += 0.15
        if elevated >= 2:
            conf += 0.10
        # Quality weighting
        q = 0.0
        if contrib["n_voice"]:
            q += contrib["voice_confidence"]
        if contrib["n_micro"]:
            q += contrib["micro_confidence"]
        if contrib["n_manipulation"]:
            q += contrib["manipulation_confidence"]
        if contrib["n_emotion"]:
            q += contrib["emotion_confidence"]
        if distinct > 0:
            conf += 0.10 * (q / distinct)
        conf = min(self.MAX_CONFIDENCE, conf)

        # If no signals at all, zero out.
        if not signals:
            score = 0.0
            conf = 0.0
            interpretation = "no_input"

        value = {
            "status": "ok",
            "fused_score": round(score, 3),
            "converging_families": elevated,
            "interpretation": interpretation,
            "contributing": {
                "voice_stress": round(contrib["voice_deviation"], 3),
                "micro_expression": round(contrib["micro_score"], 3),
                "manipulation": round(contrib["manipulation_score"], 3),
                "emotion_arousal": round(contrib["emotion_arousal"], 3),
            },
            "input_count": len(signals),
            "distinct_signal_families": distinct,
            "note": (
                "probabilistic fusion of behavioural indicators; "
                "not proof of deception; requires human judgement"
            ),
        }

        return DetectionResult(
            signal=SignalType.DECEPTION,
            timestamp=ts,
            value=value,
            confidence=Confidence(
                score=round(conf, 3),
                model_id=self.MODEL_ID,
                model_version=self.MODEL_VERSION,
                notes=(
                    "multi-signal fusion; single indicator cannot raise score; "
                    "hard-capped; never a definitive deception claim"
                ),
            ),
            baseline_deviation=score,
            raw_features=contrib,
            provenance={
                "engine": "classical-fusion",
                "input_count": len(signals),
                "converging_families": elevated,
            },
        )
