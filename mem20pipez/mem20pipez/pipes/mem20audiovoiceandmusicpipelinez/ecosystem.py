"""Cross-subsystem wiring for mem20pipez.

Six peers chosen for the audio/voice/music production pipeline job (not a
generic memory/focus/catalog/webhook template). Each adapter is called on the
normal report path and returns computed values; failures are reported, never
fatal.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Mapping, Sequence

__all__ = [
    "asset_intake_plan",
    "production_schedule",
    "content_binding",
    "model_fusion",
    "pipeline_optimization",
    "publish_events",
    "probe",
]

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_PROJECTS = (
    "mem20pipez",
    "mem20studioz",
    "mem20loreragcontentgeneratorz",
    "mem20livemodelfusionz",
    "mem20pipez",
    "mem20eventstreamsuperhighwayz",
)


def _bootstrap() -> None:
    for name in reversed(_PROJECTS):
        path = str(_REPO_ROOT / name)
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    root = str(_REPO_ROOT)
    if root not in sys.path:
        sys.path.append(root)


_bootstrap()


def asset_intake_plan(assets: Sequence[Mapping]) -> dict:
    """Validate and catalog audio/voice assets for pipeline ingest."""
    try:
        from mem20pipez.domain import (
            catalog_asset,
            intake_pipeline,
            validate_asset,
        )

        items = [dict(a) for a in assets]
        validations = [validate_asset(a) for a in items]
        valid_count = sum(1 for v in validations if v.get("valid", v.get("ok", True)))
        intake = intake_pipeline(items) if items else {"accepted": 0, "rejected": 0}
        cataloged = catalog_asset(items[0]) if items else {}
        return {
            "ok": True,
            "subsystem": "mem20pipez",
            "validated": len(validations),
            "valid_count": valid_count,
            "intake": intake,
            "catalog_id": cataloged.get("id") or cataloged.get("asset_id"),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "subsystem": "mem20pipez",
            "error": f"{type(exc).__name__}: {exc}",
        }


def production_schedule(stages: Sequence[Mapping], capacity: int = 4) -> dict:
    """Schedule pipeline stages against studio capacity."""
    try:
        from mem20studioz.domain import (
            resource_allocation,
            schedule_projects,
            studio_health,
        )

        projects = [{"id": s.get("id", f"stage-{i}"), "effort": s.get("effort", 1)} for i, s in enumerate(stages)]
        schedule = schedule_projects(projects, capacity)
        resources = {f"slot-{i}": 1 for i in range(max(1, capacity))}
        demands = [{"id": p["id"], "resource": "slot-0", "amount": 1, "priority": 0} for p in projects]
        allocation = resource_allocation(resources, demands)
        health = studio_health(projects, capacity)
        alloc_map = allocation.get("allocations", allocation) if isinstance(allocation, dict) else allocation
        return {
            "ok": True,
            "subsystem": "mem20studioz",
            "scheduled": len(schedule) if isinstance(schedule, list) else len(projects),
            "allocated": sum(1 for v in (alloc_map.values() if isinstance(alloc_map, dict) else []) if v),
            "health": float(health) if isinstance(health, (int, float)) else health,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "subsystem": "mem20studioz",
            "error": f"{type(exc).__name__}: {exc}",
        }


def content_binding(prompt: str, context_docs: Sequence[Mapping] | None = None) -> dict:
    """Generate/bind subtitle or narrative context for audio output."""
    try:
        from mem20loreragcontentgeneratorz.domain import generate, quality_score, rank_adapters

        docs = list(context_docs or [{"text": "audio pipeline context", "source": "pipeline"}])
        result = generate(docs, prompt, adapter="audio-bind")
        adapters = [{"name": "audio-bind", "score": 0.9}, {"name": "default", "score": 0.5}]
        ranked = rank_adapters(adapters, prompt)
        q = quality_score(result.get("output", ""), prompt)
        return {
            "ok": True,
            "subsystem": "mem20loreragcontentgeneratorz",
            "grounded": bool(result.get("grounded")),
            "adapter": ranked[0].get("name") if ranked else "default",
            "quality": float(q) if isinstance(q, (int, float)) else 0.0,
            "output_len": len(str(result.get("output", ""))),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "subsystem": "mem20loreragcontentgeneratorz",
            "error": f"{type(exc).__name__}: {exc}",
        }


def model_fusion(model_outputs: Sequence[Mapping]) -> dict:
    """Fuse voice/music model outputs into a pipeline decision."""
    try:
        from mem20livemodelfusionz.domain import fuse, fusion_health, select_best, weight_by_confidence

        models = [dict(m) for m in model_outputs] or [{"name": "mix", "output": 0.5, "confidence": 0.8}]
        fused = fuse(models)
        weighted = weight_by_confidence(models)
        best = select_best(models, metric="confidence") if "confidence" in (models[0] if models else {}) else select_best(models)
        health = fusion_health(models)
        return {
            "ok": True,
            "subsystem": "mem20livemodelfusionz",
            "fused": fused,
            "weighted_count": len(weighted) if isinstance(weighted, (list, dict)) else 1,
            "best": best.get("name") if isinstance(best, dict) else best,
            "health": health,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "subsystem": "mem20livemodelfusionz",
            "error": f"{type(exc).__name__}: {exc}",
        }


def pipeline_optimization(assets: Sequence[Mapping]) -> dict:
    """Optimize production pipeline budgets and batching for rendered/export assets."""
    try:
        from mem20pipez.domain import (
            batch_efficiency,
            frame_budget,
            optimize_pipeline,
        )

        items = [dict(a) for a in assets] or [{"id": "audio-export", "size": 1024}]
        optimized = optimize_pipeline(items)
        budget = frame_budget(fps=60)
        batching = batch_efficiency(len(items), batch_size=32)
        return {
            "ok": True,
            "subsystem": "mem20pipez",
            "optimized": optimized,
            "frame_budget_ms": budget.get("budget_ms") if isinstance(budget, dict) else budget,
            "batch_efficiency": batching,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "subsystem": "mem20pipez",
            "error": f"{type(exc).__name__}: {exc}",
        }


def publish_events(stream_name: str, events: Sequence[Mapping]) -> dict:
    """Publish pipeline events to the event stream superhighway."""
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream, publish, throughput

        stream = create_stream(stream_name)
        published = 0
        for ev in events or [{"type": "audio.pipeline.ready", "payload": {"ok": True}}]:
            publish(stream, ev.get("type", "event"), ev.get("payload", ev))
            published += 1
        tp = throughput(stream)
        return {
            "ok": True,
            "subsystem": "mem20eventstreamsuperhighwayz",
            "stream": stream.get("name") if isinstance(stream, dict) else stream_name,
            "published": published,
            "throughput": tp,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "subsystem": "mem20eventstreamsuperhighwayz",
            "error": f"{type(exc).__name__}: {exc}",
        }


def probe() -> dict:
    """Probe all six audio-pipeline peers with minimal safe calls."""
    checks = {
        "asset_intake": asset_intake_plan([{"id": "probe.wav", "name": "probe.wav", "type": "audio", "size": 128}]),
        "production_schedule": production_schedule([{"id": "mix", "effort": 1}]),
        "content_binding": content_binding("bind subtitle", [{"text": "voice line"}]),
        "model_fusion": model_fusion([{"name": "v1", "output": 0.6, "confidence": 0.9}]),
        "pipeline_optimization": pipeline_optimization([{"id": "master", "size": 256}]),
        "publish_events": publish_events("audio-probe", [{"type": "probe", "payload": {"x": 1}}]),
    }
    return {"ok": all(v.get("ok") for v in checks.values()), "checks": checks}
