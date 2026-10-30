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
