"""Multimodal task capture: capture tasks from text/voice/image/video."""
import time, uuid


def capture(text=None, voice=None, image=None, video=None, source="manual"):
    task = {"id": str(uuid.uuid4())[:8], "source": source, "created": time.time()}
    if text:
        task["text"] = text
    if voice:
        task["voice_transcript"] = voice
    if image:
        task["image_ref"] = image
    if video:
        task["video_ref"] = video
    task["modalities"] = [m for m in ("text","voice","image","video") if locals().get(m if m!="voice" else "voice") and (text if m=="text" else voice if m=="voice" else image if m=="image" else video)]
    return task


def merge_captures(captures):
    merged = {"id": "merged", "modalities": [], "parts": []}
    for c in captures:
        merged["parts"].append(c)
        for m in c.get("modalities", []):
            if m not in merged["modalities"]:
                merged["modalities"].append(m)
    return merged


def extract_action_items(task):
    text = task.get("text") or task.get("voice_transcript") or ""
    items = [s.strip() for s in text.split(".") if s.strip()]
    return [{"action": it} for it in items]


def capture_health(tasks):
    return {"total": len(tasks), "modalities": len(set(m for t in tasks for m in t.get("modalities", [])))}
