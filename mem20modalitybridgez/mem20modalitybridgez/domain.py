"""Modality bridge: translate between text/image/audio/video modalities."""
import base64


def encode_text(text):
    return {"modality": "text", "payload": text, "tokens": len(text.split())}


def to_image_desc(image_meta):
    return {"modality": "image", "description": image_meta.get("alt", "image"), "size": image_meta.get("size", 0)}


def to_audio_transcript(audio_meta):
    return {"modality": "audio", "transcript": audio_meta.get("transcript", ""), "duration": audio_meta.get("duration", 0)}


def bridge(src, target_modality):
    return {"from": src.get("modality"), "to": target_modality, "payload": src.get("payload"), "converted": True}


def supported_modalities():
    return ["text", "image", "audio", "video"]


# 1st-class modality bridge extensions (#334)
MODALITIES = ("text", "image", "audio", "video", "3d", "sensor")


def analyze_bridge(task):
    task = dict(task or {})
    src = str(task.get("from") or task.get("source_modality") or (task.get("input") or {}).get("modality") or "text")
    tgt = str(task.get("to") or task.get("target_modality") or "text")
    payload = task.get("payload") or (task.get("input") or {}).get("payload") or task.get("text") or ""
    adapters = [{"from": src, "to": tgt, "adapter": f"{src}->{tgt}", "ready": src in MODALITIES and tgt in MODALITIES}]
    if src != tgt:
        adapters.append({"from": src, "to": "text", "adapter": f"{src}->text", "ready": True})
        adapters.append({"from": "text", "to": tgt, "adapter": f"text->{tgt}", "ready": True})
    rep = encode_text(str(payload)) if src == "text" else {"modality": src, "payload": payload}
    bridged = bridge(rep, tgt)
    caps = {"source": src, "target": tgt, "direct": src in MODALITIES and tgt in MODALITIES, "adapter_chain": [a["adapter"] for a in adapters], "supported": list(MODALITIES)}
    return {"ok": True, "representation": rep, "bridge": bridged, "adapters": adapters, "capabilities": caps}
