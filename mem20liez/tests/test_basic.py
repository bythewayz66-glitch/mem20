\"\"\"Basic smoke tests for mem20liez scaffold.\"\"\"

from mem20liez import LieDetector, LiveLieSession, SignalType


def test_detector_instantiation():
    d = LieDetector()
    assert d is not None


def test_process_audio_returns_results():
    d = LieDetector()
    results = d.process_audio(b"fake-audio-chunk")
    assert len(results) >= 1
    assert all(r.signal in (SignalType.VOICE_STRESS, SignalType.EMOTION) for r in results)


def test_process_video_returns_results():
    d = LieDetector()
    results = d.process_video(None)  # scaffold accepts anything
    assert len(results) >= 1


def test_live_session_seal():
    session = LiveLieSession(mode="interrogation")
    session.feed_audio(b"chunk1")
    session.feed_video(None)
    package = session.seal()
    assert package["session_id"]
    assert package["mode"] == "interrogation"
    assert "disclaimer" in package
    assert len(package["detections"]) > 0


def test_cues_are_generated_only_on_sufficient_confidence():
    # With current scaffold confidence is 0.0, so no cues should appear.
    session = LiveLieSession(mode="interrogation")
    session.feed_audio(b"chunk")
    cues = session.get_earpiece_cues()
    assert cues == []
