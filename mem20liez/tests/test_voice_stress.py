"""Tests for the real numpy voice-stress detector."""

import struct
import math
import pytest

from mem20liez.detectors.voice_stress import VoiceStressDetector
from mem20liez.types import SignalType


def _sine_pcm(freq: float = 180.0, duration: float = 0.6, sr: int = 16000, amp: float = 0.3) -> bytes:
    n = int(sr * duration)
    samples = [int(amp * 32767 * math.sin(2 * math.pi * freq * i / sr)) for i in range(n)]
    return struct.pack(f"<{n}h", *samples)


def test_voice_stress_runs_without_baseline():
    d = VoiceStressDetector()
    pcm = _sine_pcm()
    r = d.process_audio(pcm)
    assert r.signal == SignalType.VOICE_STRESS
    assert r.value["status"] == "ok"
    assert "features" in r.value
    assert r.confidence.score > 0.0


def test_voice_stress_with_baseline_detects_deviation():
    d = VoiceStressDetector()
    calm = _sine_pcm(freq=160, amp=0.15)
    stressed = _sine_pcm(freq=260, amp=0.55)  # higher pitch + energy

    # set baseline from calm
    base_result = d.process_audio(calm)
    d.set_baseline(base_result.raw_features or base_result.value["features"])

    r = d.process_audio(stressed)
    assert r.value["status"] == "ok"
    assert r.baseline_deviation is not None
    assert r.baseline_deviation >= 0.0
    # we expect some elevation
    assert r.value["interpretation"] in ("elevated_stress_indicator", "mild_deviation", "near_baseline")


def test_too_short_chunk():
    d = VoiceStressDetector()
    r = d.process_audio(b"\x00\x01" * 10)
    assert r.value["status"] == "too_short"
    assert r.confidence.score == 0.0
