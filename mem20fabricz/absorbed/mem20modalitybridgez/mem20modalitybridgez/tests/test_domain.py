import importlib
MOD="mem20modalitybridgez"
def _m(): return importlib.import_module(MOD+".domain")
def test_encode(): m=_m(); r=m.encode_text("hi there"); assert r["modality"]=="text"
def test_img(): m=_m(); r=m.to_image_desc({"alt":"pic","size":10}); assert r["modality"]=="image"
def test_audio(): m=_m(); r=m.to_audio_transcript({"transcript":"hi","duration":2}); assert r["modality"]=="audio"
def test_bridge(): m=_m(); r=m.bridge(m.encode_text("hi"),"image"); assert r["converted"] is True
def test_supported(): m=_m(); assert "text" in m.supported_modalities()

from mem20modalitybridgez import ecosystem


def _assert_signal(sig):
    assert isinstance(sig, dict) and "subsystem" in sig and "ok" in sig
    if not sig["ok"]:
        assert "error" in sig


def test_analyze_bridge():
    m = _m()
    r = m.analyze_bridge({"from": "text", "to": "image", "payload": "a cat"})
    assert r["ok"] and r["bridge"]["to"] == "image"
    assert r["capabilities"]["source"] == "text"
    assert len(r["adapters"]) >= 1


def test_ecosystem():
    ctx = {"from": "text", "to": "image", "payload": "probe"}
    _assert_signal(ecosystem.sensory_ingest_signal(ctx))
    _assert_signal(ecosystem.specialist_forge_signal(ctx))
    _assert_signal(ecosystem.predictive_recall_signal(ctx))
    _assert_signal(ecosystem.output_compile_signal(ctx))
    _assert_signal(ecosystem.compression_signal(ctx))
    _assert_signal(ecosystem.episodic_signal(ctx))
    r = ecosystem.modality_signals(ctx)
    assert set(r["checks"].keys()) == {"sensory_ingest", "specialist_forge", "predictive_recall", "output_compile", "compression", "episodic"}
    for v in r["checks"].values():
        _assert_signal(v)
