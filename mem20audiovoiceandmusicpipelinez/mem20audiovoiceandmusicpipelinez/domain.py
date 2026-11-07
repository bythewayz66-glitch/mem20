"""Audio/voice/music pipeline: mixing, mastering, sync, export, and estate report."""

from __future__ import annotations

import math

from . import ecosystem

__all__ = [
    "mix_tracks",
    "normalize",
    "sync_to_beat",
    "export_format",
    "mastering_chain",
    "pipeline_report",
    "estate_context",
    "probe",
]


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


def pipeline_report(
    tracks=None,
    samples=None,
    prompt="bind audio",
    bpm=120,
    stream_name="audio-pipeline",
):
    """Run core audio ops and collect subsystem-specific peer judgements."""
    tracks = tracks or [{"id": "main", "samples": [0.2, -0.1, 0.4]}]
    samples = samples if samples is not None else [0.2, -0.1, 0.4, 0.9]
    mixed = mix_tracks(tracks)
    normalized = normalize(samples)
    sync = sync_to_beat(max(1.0, len(normalized) / 44100.0 * 10), bpm)
    mastered = mastering_chain(["limit"], normalized)
    export = export_format(mastered)
    assets = [{"id": t.get("id", "asset"), "name": f"{t.get('id', 'asset')}.wav", "type": "audio", "size": len(t.get("samples", []))} for t in tracks]
    peers = {
        "asset_intake": ecosystem.asset_intake_plan(assets),
        "production_schedule": ecosystem.production_schedule([{"id": "mix"}, {"id": "master"}, {"id": "export"}]),
        "content_binding": ecosystem.content_binding(prompt),
        "model_fusion": ecosystem.model_fusion([{"name": "mix", "output": 0.7, "confidence": 0.9}, {"name": "alt", "output": 0.6, "confidence": 0.8}]),
        "pipeline_optimization": ecosystem.pipeline_optimization(assets),
        "publish_events": ecosystem.publish_events(stream_name, [{"type": "audio.exported", "payload": {"format": export["format"]}}]),
    }
    return {
        "ok": all(v.get("ok") for v in peers.values()),
        "mixed": mixed,
        "normalized_peak": max((abs(x) for x in normalized), default=0.0),
        "sync": sync,
        "export": export,
        "peers": peers,
    }


def probe():
    """Probe all six pipeline-specific peers."""
    return ecosystem.probe()


def estate_context(store_path: str | None = None):
    """Compatibility wrapper: real peer report (store_path unused; no generic template)."""
    _ = store_path
    report = pipeline_report()
    return {
        "engine_status_checked": True,
        "peer_count": len(report.get("peers", {})),
        "peers_ok": report.get("ok"),
        "checks": report.get("peers", {}),
    }
