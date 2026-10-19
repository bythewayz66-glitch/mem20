"""Basic smoke tests for mem20liez."""

from mem20liez import LieDetector, LiveLieSession, SignalType


def test_detector_instantiation():
    d = LieDetector()
    assert d is not None


def test_process_audio_returns_results():
    d = LieDetector()
    results = d.process_audio(b"\x00\x01" * 2000)
    assert len(results) >= 1


def test_process_video_returns_results():
    import numpy as np
    d = LieDetector()
    frame = np.full((80, 60), 0.5, dtype=np.float32)
    results = d.process_video(frame)
    assert len(results) >= 1
    assert any(r.signal == SignalType.MICRO_EXPRESSION for r in results)


def test_live_session_seal():
    session = LiveLieSession(mode="interrogation")
    session.feed_audio(b"\x00\x01" * 2000)
    package = session.seal()
    assert package["session_id"]
    assert package["mode"] == "interrogation"
    assert "disclaimer" in package
