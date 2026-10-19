"""Tests for classical micro-expression detector."""

import numpy as np
from mem20liez.detectors.micro_expression import MicroExpressionDetector
from mem20liez.types import SignalType


def _frame(val=0.5, h=120, w=100):
    return np.full((h, w), val, dtype=np.float32)


def test_micro_runs():
    d = MicroExpressionDetector()
    r = d.process_frame(_frame(0.4))
    assert r.signal == SignalType.MICRO_EXPRESSION
    assert r.value["status"] == "ok"
    assert "regions" in r.value


def test_motion_increases_score():
    d = MicroExpressionDetector()
    d.process_frame(_frame(0.3))  # establish prev
    r2 = d.process_frame(_frame(0.8))  # big change
    assert r2.value["motion_energy"] > 0.0


def test_baseline_path():
    d = MicroExpressionDetector()
    r0 = d.process_frame(_frame(0.5))
    d.set_baseline(r0.raw_features or r0.value)
    r1 = d.process_frame(_frame(0.5))
    assert r1.value["has_baseline"] is True
