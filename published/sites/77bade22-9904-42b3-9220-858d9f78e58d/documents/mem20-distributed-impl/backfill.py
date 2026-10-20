#!/usr/bin/env python3
"""
mem20 distributed sync — Phase 2 backfill
=========================================

Turns a mem20 database that already has data into a node of the replicated
system: one synthetic ``upsert`` event per legacy row, per node, taken from a
``sqlite3 .backup`` snapshot (**never** ``cp`` — a live WAL database copied with
``cp`` can be torn).

Why a snapshot: the backfill reads the legacy tables while the live database may
still be serving mem20. Reading a consistent point-in-time copy means the
synthetic events describe exactly the state that existed when the snapshot was
taken, and the snapshot doubles as the rollback artefact for gate G-3.

Determinism (this is what makes G-3 reachable): every synthetic event gets an
HLC derived from the row's own ``created_at`` (ties broken by ``origin``, then by
the origin's monotonic ``seq``). Two nodes backfilling their own rows therefore
produce event sets that, once exchanged, project to a byte-identical state.

History handling: mem20's ``persist_node()`` writes BOTH ``tot_nodes`` and
``cognitive_substrate_history`` in one logical write, so the sync layer models
that as ONE ``tot_node`` event and the projection derives the history row from
it. The backfill follows the same rule — it emits ``memories`` + ``tot_nodes``
events, and emits an explicit ``history`` event only for a legacy history row
whose ``node_id`` has no ``tot_nodes`` row (an orphan), so nothing is lost and
nothing is double-counted.

Usage:
    python3 backfill.py --db <live.db> --node sidney [--snapshot-dir DIR]
    python3 backfill.py --db <live.db> --node sidney --snapshot-only
    python3 backfill.py --db <live.db> --node sidney --verify

Deps: Python 3.11+ stdlib only.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mem20_sync import (  # noqa: E402
    Mem20Sync, memory_key, history_key, node_key,
)

BACKFILL_MARKER = "backfill_done"


# ---------------------------------------------------------------------------
# Snapshot — sqlite3 .backup, never cp
# ---------------------------------------------------------------------------

def snapshot(db_path: str, snap_path: str) -> str:
    """Consistent point-in-time copy via SQLite's online backup API.

    Equivalent to ``sqlite3 <db> ".backup <snap>"`` but without shelling out.
    Safe against a live writer (unlike ``cp`` of a WAL database).
    """
    os.makedirs(os.path.dirname(os.path.abspath(snap_path)), exist_ok=True)
    src = sqlite3.connect(db_path)
    try:
        dst = sqlite3.connect(snap_path)
        try:
            with dst:
                src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    return snap_path


# ---------------------------------------------------------------------------
# created_at -> HLC millis (deterministic, UTC)
# ---------------------------------------------------------------------------

def _created_at_to_ms(value: Any) -> int:
    """Parse mem20's ``CURRENT_TIMESTAMP`` (``YYYY-MM-DD HH:MM:SS``, UTC) to ms.

    Unparseable / NULL timestamps map to 0 so the ordering falls back to
    ``(origin, seq)`` — still deterministic.
    """
    if not value:
        return 0
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            dt = _dt.datetime.strptime(text, fmt).replace(tzinfo=_dt.timezone.utc)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    return 0


def _hlc_for(ms: int, origin: str, counter: int = 0) -> str:
    return f"{ms:013d}-{counter:04d}-{origin}"


# ---------------------------------------------------------------------------
# Backfill
# ---------------------------------------------------------------------------

def _read_legacy(snap_path: str) -> Dict[str, List[Dict[str, Any]]]:
    conn = sqlite3.connect(snap_path)
    conn.row_factory = sqlite3.Row
    try:
        def rows(sql: str) -> List[Dict[str, Any]]:
            try:
                return [dict(r) for r in conn.execute(sql)]
            except sqlite3.OperationalError:
                return []
        return {
            "memories": rows("SELECT * FROM memories ORDER BY id"),
            "tot_nodes": rows("SELECT * FROM tot_nodes ORDER BY node_id"),
            "history": rows("SELECT * FROM cognitive_substrate_history ORDER BY id"),
        }
    finally:
        conn.close()


def backfill(live_db: str, node_id: str, snap_path: Optional[str] = None,
             snapshot_dir: Optional[str] = None) -> Dict[str, Any]:
    """Backfill one synthetic upsert per legacy row, from a .backup snapshot.

    Idempotent: guarded by a ``backfill_done`` marker in ``replication_state``.
    Returns a summary dict (counts + snapshot path + state hash).
    """
    live_db = os.path.abspath(live_db)
    if snap_path is None:
        snap_dir = snapshot_dir or os.path.join(os.path.dirname(live_db), "snapshots")
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snap_path = os.path.join(snap_dir, f"{os.path.basename(live_db)}.{node_id}.{stamp}.bak")
    snapshot(live_db, snap_path)

    legacy = _read_legacy(snap_path)

    node = Mem20Sync(live_db, node_id=node_id)
    if node._get_state(BACKFILL_MARKER) == "1":
        node.close()
        return {"skipped": True, "reason": "backfill already done",
                "snapshot": snap_path, "node_id": node_id}

    emitted = {"memory": 0, "tot_node": 0, "history": 0}

    # 1) memories -> content-addressed key
    for r in legacy["memories"]:
        hlc = _hlc_for(_created_at_to_ms(r.get("created_at")), node_id)
        node._emit("memory", memory_key(r["session_id"], r.get("topic") or "",
                                        r["content"]), "upsert", {
            "session_id": r["session_id"], "topic": r.get("topic") or "",
            "content": r["content"], "tags": r.get("tags") or "",
            "trust": r.get("trust", 0.5),
        }, hlc=hlc)
        node.hlc.observe(hlc)
        emitted["memory"] += 1

    # 2) tot_nodes -> node_id unchanged (already a stable TEXT PK).
    #    The projection derives the matching history row from this event.
    tot_node_ids = set()
    for r in legacy["tot_nodes"]:
        tot_node_ids.add(r["node_id"])
        score = r.get("heuristic_score_delta", 0.0) or 0.0
        hlc = _hlc_for(_created_at_to_ms(r.get("created_at")), node_id)
        node._emit("tot_node", node_key(r["node_id"]), "upsert", {
            "session_id": r["session_id"],
            "parent_node_id": r.get("parent_node_id"),
            "branch_index": r.get("branch_index", 0),
            "depth": r.get("depth", 0),
            "prompt_context": r.get("prompt_context") or "",
            "cleaned_output": r.get("cleaned_output") or "",
            "substrate_payload": r.get("substrate_payload") or "{}",
            "heuristic_score_delta": score,
            "status": r.get("status") or "pending",
            # mem20 derives history.is_pruned from the score, not the status
            "is_pruned": 1 if score <= -100 else 0,
        }, hlc=hlc)
        node.hlc.observe(hlc)
        emitted["tot_node"] += 1

    # 3) orphan history rows only (no matching tot_nodes row) -> explicit event
    for r in legacy["history"]:
        if r["node_id"] in tot_node_ids:
            continue
        hlc = _hlc_for(_created_at_to_ms(r.get("created_at")), node_id)
        seq = node._next_seq + 1
        node._emit("history", history_key(node_id, seq), "upsert", {
            "node_id": r["node_id"], "session_id": r["session_id"],
            "substrate_payload": r.get("substrate_payload") or "{}",
            "heuristic_score_delta": r.get("heuristic_score_delta", 0.0),
            "is_pruned": r.get("is_pruned", 0),
        }, hlc=hlc)
        node.hlc.observe(hlc)
        emitted["history"] += 1

    node.set_state(BACKFILL_MARKER, "1")
    node.set_state("backfill_snapshot", snap_path)
    proj = node.project()
    result = {
        "skipped": False, "node_id": node_id, "snapshot": snap_path,
        "legacy_rows": {k: len(v) for k, v in legacy.items()},
        "emitted": emitted, "projected": proj,
        "ledger_events": node.ledger_size(),
        "state_hash": node.state_hash(),
    }
    node.close()
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="mem20 Phase-2 backfill (from a .backup snapshot)")
    ap.add_argument("--db", required=True, help="live mem20 SQLite database")
    ap.add_argument("--node", required=True, help="this node's id (e.g. sidney, server2)")
    ap.add_argument("--snapshot-dir", default=None, help="where to write the .backup snapshot")
    ap.add_argument("--snapshot-only", action="store_true", help="take the snapshot and exit")
    ap.add_argument("--verify", action="store_true", help="print the current state hash and exit")
    args = ap.parse_args(argv)

    if args.snapshot_only:
        snap_dir = args.snapshot_dir or os.path.join(os.path.dirname(os.path.abspath(args.db)), "snapshots")
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snap = os.path.join(snap_dir, f"{os.path.basename(args.db)}.{args.node}.{stamp}.bak")
        snapshot(args.db, snap)
        print(json.dumps({"snapshot": snap, "ok": os.path.exists(snap)}, indent=2))
        return 0

    if args.verify:
        node = Mem20Sync(args.db, node_id=args.node)
        node.project()
        print(json.dumps({"node_id": node.node_id, "state_hash": node.state_hash(),
                          "ledger_events": node.ledger_size(),
                          "vector_clock": node.vector_clock()}, indent=2))
        node.close()
        return 0

    out = backfill(args.db, args.node, snapshot_dir=args.snapshot_dir)
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
