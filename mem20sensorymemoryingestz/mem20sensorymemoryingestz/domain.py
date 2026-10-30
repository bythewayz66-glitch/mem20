"""Sensory memory ingest: ingest sensory streams into memory."""
import time, hashlib


def ingest(stream, data, modality="text"):
    entry = {"id": hashlib.md5(f"{modality}{time.time()}".encode()).hexdigest()[:8], "modality": modality, "data": data, "ts": time.time()}
    stream.setdefault("entries", []).append(entry)
    return entry


def filter_by_modality(stream, modality):
    return [e for e in stream.get("entries", []) if e.get("modality") == modality]


def recent(stream, n=5):
    return sorted(stream.get("entries", []), key=lambda e: -e["ts"])[:n]


def ingest_health(stream):
    mods = set(e.get("modality") for e in stream.get("entries", []))
    return {"entries": len(stream.get("entries", [])), "modalities": len(mods)}
