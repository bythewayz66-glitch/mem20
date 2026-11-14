"""Tenant-scoped, serialized access to mem20 stores via mem20api.

All memory-store operations go through mem20api.open_store / MemoryStore. The
underlying engine binds store paths via module-global state, so every operation
is serialized with a single process-wide lock and store bindings are never
shared across concurrent requests.
"""

from __future__ import annotations

import asyncio
import threading
from copy import deepcopy
from typing import Any, Callable, Dict, Iterable, List, Optional

from .config import UserAccount

_STORE_LOCK = threading.RLock()


class StoreAccessError(RuntimeError):
    """A store operation failed in a way that should be reported to the caller."""


def _sanitize(obj: Any) -> Any:
    """Redact internal server filesystem paths from customer-visible payloads."""
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if k in ("path", "store") and isinstance(v, str) and (v.startswith("/") or v.startswith("~") or ":\\" in v):
                continue
            if k == "indexes" and isinstance(v, dict):
                out[k] = {ik: _sanitize(iv) for ik, iv in v.items()}
            elif k == "health" and isinstance(v, dict):
                out[k] = _sanitize(v)
            else:
                out[k] = _sanitize(v)
        return out
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    return obj


def _with_store_locked(store_path: str, fn: Callable[[Any], Any]) -> Any:
    try:
        from mem20api import EngineNotFound, StoreError, open_store
    except Exception as e:  # pragma: no cover - environment dependent
        raise StoreAccessError(
            "mem20api is not available (ensure mem20api is installed or on PYTHONPATH): "
            f"{e}"
        ) from e
    with _STORE_LOCK:
        try:
            with open_store(store_path) as store:
                return fn(store)
        except (EngineNotFound, StoreError) as e:
            raise StoreAccessError(str(e)) from e


async def run_store(store_path: str, fn: Callable[[Any], Any]) -> Any:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _with_store_locked(store_path, fn))


async def get_stats(account: UserAccount) -> dict:
    def op(store):
        return _sanitize(deepcopy(store.stats()))
    return await run_store(account.resolved_store_path, op)


async def get_health(account: UserAccount) -> dict:
    def op(store):
        return _sanitize(deepcopy(store.health()))
    return await run_store(account.resolved_store_path, op)


async def get_ledger(account: UserAccount, limit: int = 50) -> List[dict]:
    limit = max(1, min(int(limit), 500))

    def op(store):
        recs = store.ledger(k=limit)
        # most recent last from engine; present newest first for UI
        return list(reversed(deepcopy(recs)))

    return await run_store(account.resolved_store_path, op)


async def browse_memories(account: UserAccount, limit: int = 50) -> List[dict]:
    """Recent grounded/remembered memories (newest first)."""
    limit = max(1, min(int(limit), 500))

    def op(store):
        # recall without topic returns recent records in engine; request enough to filter
        recs = store.recall(k=max(limit * 3, limit), include_simulated=False) or []
        out = []
        for r in recs:
            if not isinstance(r, dict):
                continue
            action = r.get("action")
            if action in (None, "remember"):
                out.append(deepcopy(r))
            if len(out) >= limit:
                break
        # recall may not be strictly newest-first in all modes; sort by ts desc when available
        out.sort(key=lambda x: str(x.get("ts") or ""), reverse=True)
        return out[:limit]

    return await run_store(account.resolved_store_path, op)


async def recall_memories(
    account: UserAccount,
    topic: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
    k: int = 10,
) -> List[dict]:
    k = max(1, min(int(k), 100))
    tags_list = list(tags or [])

    def op(store):
        return deepcopy(store.recall(topic=topic or None, tags=tags_list, k=k))

    return await run_store(account.resolved_store_path, op)


async def query_memories(
    account: UserAccount,
    query: str,
    mode: str = "hybrid",
    k: int = 10,
    topic: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
) -> dict:
    mode = (mode or "hybrid").lower()
    if mode not in ("semantic", "hybrid", "graph"):
        raise StoreAccessError("mode must be one of: semantic, hybrid, graph")
    tags_list = list(tags or [])

    def op(store):
        if mode == "semantic":
            res = deepcopy(store.semantic(query, k=max(1, min(int(k), 50)), topic=topic, tags=tags_list))
            res = _sanitize(res)
            return {"mode": "semantic", **res}
        if mode == "hybrid":
            res = deepcopy(store.hybrid(query, k=max(1, min(int(k), 50)), topic=topic, tags=tags_list))
            res = _sanitize(res)
            return {"mode": "hybrid", **res}
        # graph: k interpreted as hops
        hops = max(1, min(int(k), 6))
        res = deepcopy(store.graph(query, hops=hops))
        res = _sanitize(res)
        if "hits" not in res:
            # normalize: graph returns entities/facts; expose as hits-like facts list for UI convenience
            facts = res.get("facts") or []
            res["hits"] = facts if isinstance(facts, list) else []
        return {"mode": "graph", **res}

    return await run_store(account.resolved_store_path, op)


async def get_entities(account: UserAccount, limit: int = 50) -> List[dict]:
    limit = max(1, min(int(limit), 500))

    def op(store):
        return deepcopy(store.entities(limit=limit))

    return await run_store(account.resolved_store_path, op)
