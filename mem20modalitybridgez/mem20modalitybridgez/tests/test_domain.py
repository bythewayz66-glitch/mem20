import importlib
MOD="mem20modalitybridgez"
def _m(): return importlib.import_module(MOD+".domain")
def test_encode(): m=_m(); r=m.encode_text("hi there"); assert r["modality"]=="text"
def test_img(): m=_m(); r=m.to_image_desc({"alt":"pic","size":10}); assert r["modality"]=="image"
def test_audio(): m=_m(); r=m.to_audio_transcript({"transcript":"hi","duration":2}); assert r["modality"]=="audio"
def test_bridge(): m=_m(); r=m.bridge(m.encode_text("hi"),"image"); assert r["converted"] is True
def test_supported(): m=_m(); assert "text" in m.supported_modalities()
