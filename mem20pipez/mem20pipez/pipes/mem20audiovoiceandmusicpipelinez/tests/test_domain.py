import importlib
import tempfile

MOD = "mem20pipez"


def _m():
    return importlib.import_module(MOD + ".domain")


def _eco():
    return importlib.import_module(MOD + ".ecosystem")


def test_mix():
    m = _m()
    r = m.mix_tracks([{"id": "a", "samples": [1, 2]}])
    assert "tracks" in r and r["master_gain"] == 1.0


def test_normalize():
    m = _m()
    r = m.normalize([0.5, 1.0], -3)
    assert len(r) == 2 and max(abs(x) for x in r) > 0


def test_sync():
    m = _m()
    r = m.sync_to_beat(10, 120)
    assert r["beats"] > 0 and r["interval_s"] > 0


def test_export():
    m = _m()
    r = m.export_format([1, 2], "wav")
    assert r["format"] == "wav" and r["sample_rate"] == 44100


def test_master():
    m = _m()
    r = m.mastering_chain(["limit"], [1.5, -1.5])
    assert all(abs(x) <= 0.99 for x in r)


def test_ecosystem_asset_intake_real_values():
    eco = _eco()
    r = eco.asset_intake_plan([{"id": "vox.wav", "name": "vox.wav", "type": "audio", "size": 512}])
    assert r["ok"] is True
    assert r["subsystem"] == "mem20pipez"
    assert r["validated"] == 1
    assert "intake" in r


def test_ecosystem_production_schedule_real_values():
    eco = _eco()
    r = eco.production_schedule([{"id": "mix", "effort": 1}, {"id": "master", "effort": 1}], capacity=2)
    assert r["ok"] is True
    assert r["subsystem"] == "mem20aiproductionstudiooperatingsystemz"
    assert r["scheduled"] >= 1
    assert "health" in r


def test_ecosystem_content_binding_real_values():
    eco = _eco()
    r = eco.content_binding("subtitle bind", [{"text": "voice"}])
    assert r["ok"] is True
    assert r["subsystem"] == "mem20loreragcontentgeneratorz"
    assert r["output_len"] > 0
    assert "quality" in r


def test_ecosystem_model_fusion_real_values():
    eco = _eco()
    r = eco.model_fusion([{"name": "a", "output": 0.7, "confidence": 0.9}, {"name": "b", "output": 0.6, "confidence": 0.8}])
    assert r["ok"] is True
    assert r["subsystem"] == "mem20livemodelfusionz"
    assert "fused" in r and "health" in r


def test_ecosystem_pipeline_optimization_real_values():
    eco = _eco()
    r = eco.pipeline_optimization([{"id": "master", "size": 256}])
    assert r["ok"] is True
    assert r["subsystem"] == "mem20pipez"
    assert "frame_budget_ms" in r or "optimized" in r


def test_ecosystem_publish_events_real_values():
    eco = _eco()
    r = eco.publish_events("avmp-test", [{"type": "ready", "payload": {"ok": True}}])
    assert r["ok"] is True
    assert r["subsystem"] == "mem20eventstreamsuperhighwayz"
    assert r["published"] == 1


def test_pipeline_report_and_probe_real_integrations():
    m = _m()
    report = m.pipeline_report(tracks=[{"id": "vox", "samples": [0.1, 0.2]}], samples=[0.5, 1.0], prompt="bind")
    assert report["export"]["format"] == "wav"
    peers = report["peers"]
    assert len(peers) == 6
    assert peers["asset_intake"]["ok"] is True
    assert peers["production_schedule"]["ok"] is True
    assert peers["content_binding"]["ok"] is True
    assert peers["model_fusion"]["ok"] is True
    assert peers["pipeline_optimization"]["ok"] is True
    assert peers["publish_events"]["ok"] is True
    probe = m.probe()
    assert probe["ok"] is True
    assert len(probe["checks"]) == 6


def test_estate_context_compat_real_report():
    m = _m()
    ctx = m.estate_context()
    assert ctx["engine_status_checked"] is True
    assert ctx["peer_count"] == 6
