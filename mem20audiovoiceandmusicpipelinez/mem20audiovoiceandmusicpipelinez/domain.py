"""Audio/voice/music pipeline: mixing, mastering, sync, export."""

from __future__ import annotations

import math
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def mix_tracks(tracks, volumes=None):
    volumes = volumes or [1.0] * len(tracks)
    out = []
    for t, v in zip(tracks, volumes):
        out.append({"id": t.get("id"), "gain": v, "samples": t.get("samples", [])})
    return {"tracks": out, "master_gain": 1.0}


def normalize(samples, target_db=-3.0):
    if not samples:
        return samples
    peak = max(abs(s) for s in samples) or 1.0
    target = 10 ** (target_db / 20.0)
    gain = target / peak
    return [round(s * gain, 6) for s in samples]


def sync_to_beat(audio_len_s, bpm, offset=0.0):
    beat_interval = 60.0 / bpm
    beats = int((audio_len_s - offset) / beat_interval)
    return {
        "beats": beats,
        "interval_s": round(beat_interval, 4),
        "remainder": round((audio_len_s - offset) % beat_interval, 4),
    }


def export_format(samples, fmt="wav", sample_rate=44100):
    return {
        "format": fmt,
        "sample_rate": sample_rate,
        "channels": 2,
        "duration_s": round(len(samples) / sample_rate, 3),
        "size_bytes": len(samples) * 2,
    }


def mastering_chain(stages, audio):
    out = audio
    for s in stages:
        if s == "eq":
            out = [round(x * 1.05, 6) for x in out]
        elif s == "compress":
            out = [round(x * 0.9 if abs(x) > 0.5 else x, 6) for x in out]
        elif s == "limit":
            out = [max(-0.99, min(0.99, x)) for x in out]
    return out


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("avmp-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "avmp-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
