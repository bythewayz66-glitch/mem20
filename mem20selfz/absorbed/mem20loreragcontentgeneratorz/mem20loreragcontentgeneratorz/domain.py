"""LoRA RAG content generator: retrieve + generate, grounded in memory_engine."""

from __future__ import annotations

import math
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def retrieve(docs, query, k=3):
    # simple keyword overlap (local corpus fallback)
    qwords = set(str(query).lower().split())
    scored = []
    for d in docs:
        dw = set(str(d.get("text", "")).lower().split())
        score = len(qwords & dw)
        scored.append((score, d))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [d for _, d in scored[:k]]


def retrieve_from_memory(query, *, store_path: str | Path, k: int = 3, topic: str | None = None) -> list[dict]:
    """Grounded retrieval via memory_engine."""
    cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
    eng = MemoryEngine(cfg)
    q = str(query)
    k = max(1, int(k))
    try:
        results = eng.recall(topic=topic or q, k=k)
    except TypeError:
        results = eng.recall(topic=q, k=k)
    out = []
    for r in (results or [])[:k]:
        if isinstance(r, dict):
            text = r.get("content") or r.get("text") or str(r)
            out.append({"text": text, "source": "memory_engine", "raw": r})
        else:
            text = getattr(r, "content", None) or getattr(r, "text", None) or str(r)
            out.append({"text": text, "source": "memory_engine"})
    if not out and topic is None:
        # fallback: broad recall and keyword filter
        try:
            broad = eng.recall(k=max(k, 20))
        except Exception:
            broad = []
        qwords = set(q.lower().split())
        for r in broad or []:
            text = r.get("content", "") if isinstance(r, dict) else (getattr(r, "content", None) or getattr(r, "text", None) or str(r))
            if qwords & set(str(text).lower().split()):
                out.append({"text": text, "source": "memory_engine"})
                if len(out) >= k:
                    break
    return out


def generate(context_docs, prompt, adapter="default"):
    ctx = " ".join(d.get("text", "") for d in (context_docs or []))
    grounded = any(d.get("source") == "memory_engine" for d in (context_docs or []))
    return {
        "prompt": prompt,
        "context": ctx[:500],
        "adapter": adapter,
        "grounded": grounded,
        "output": f"[{adapter}] {prompt} (ctx={len(ctx)} chars, grounded={grounded})",
    }


def rank_adapters(adapters, task):
    return sorted(adapters, key=lambda a: -a.get("score", 0))


def quality_score(output, reference):
    # token overlap
    ow = set(str(output).lower().split())
    rw = set(str(reference).lower().split())
    if not rw:
        return 0.0
    return round(len(ow & rw) / len(rw), 4)


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("lore-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "lore-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.index_health()
        ctx["engine_store"] = str(cfg.store_path)
        ctx["engine_status_checked"] = True
    return ctx
