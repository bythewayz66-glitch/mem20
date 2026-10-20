#!/usr/bin/env python3
"""
mem20 distributed sync — acceptance suite
=========================================

Runs the design's gates against the real implementation:

  G-2  the reference scenario passes 8/8 on two temp DBs
  G-3  backfill yields a byte-identical ``state_hash()`` on both nodes
       (HARD GATE — snapshots are not archived before this passes)

plus the build-handoff invariants:

  * each wrapped write path emits **exactly one** event
  * stable keys are ``mem:<sha256[:16]>`` / ``hist:<node>:<seq>`` / ``node_id``
  * ``ingest`` is idempotent (re-applying the same events changes nothing)
  * a tombstone is honoured and does not resurrect
  * a prune (status transition) propagates
  * the losing side of a conflict is retained in the audit ledger

Run:  python3 acceptance_suite.py
Exit: 0 = all gates pass, 1 = a gate failed.
Deps: Python 3.11+ stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mem20_sync import (  # noqa: E402
    Mem20Sync, memory_key, history_key, node_key, MEM20_SCHEMA,
)
import backfill as bf  # noqa: E402

RESULTS: List[Tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((label, bool(ok), detail))


# ---------------------------------------------------------------------------
# G-2 — the reference scenario, ported onto the real module
# ---------------------------------------------------------------------------

def scenario_g2(workdir: str) -> Dict[str, Any]:
    A = Mem20Sync(os.path.join(workdir, "a.db"), node_id="sidney", clock_ms=1_700_000_000_000)
    B = Mem20Sync(os.path.join(workdir, "b.db"), node_id="server2", clock_ms=1_700_000_000_500)

    # shared pre-history
    base = "mem:project:conventions"
    A.persist_memory_keyed(base, "All timestamps are UTC ISO-8601.", topic="conventions", trust=0.9)
    B.sync_with(A)
    A.project(); B.project()
    baseline_ok = A.state_hash() == B.state_hash()

    # PARTITION — both keep working offline
    A.persist_memory_keyed("mem:sidney:laptop", "Sidney runs on the home NAS.", topic="infra")
    A.persist_memory_keyed("mem:sidney:backup", "Nightly Litestream -> S3 bucket b1.", topic="infra")
    A.persist_node("tot:deploy-1", "session-a", status="active",
                   substrate={"foundations": {"premise_validation": "deps pinned"}},
                   score_delta=10.0, cleaned_output="pin versions")
    A.prune_failed_approach("tot:deploy-1")

    B.persist_memory_keyed("mem:server2:gpu", "Server 2 has an RTX 4090 for local models.", topic="infra")
    B.persist_memory_keyed("mem:sidney:backup", "Nightly Litestream -> S3 bucket b2 (B's view).",
                           topic="infra", trust=0.6)   # CONFLICT
    B.persist_memory_keyed("mem:server2:scratch", "temp note", topic="scratch")
    B.delete_memory_keyed("mem:server2:scratch", reason="superseded")   # tombstone

    A.project(); B.project()
    pre_diverged = A.state_hash() != B.state_hash()

    transfer = A.sync_with(B)
    A.project(); B.project()
    post_a, post_b = A.state_hash(), B.state_hash()

    a_mem = {r["entity_key"]: r for r in A.dump("proj_memories")}
    b_mem = {r["entity_key"]: r for r in B.dump("proj_memories")}
    winner_a = a_mem.get("mem:sidney:backup", {})
    winner_b = b_mem.get("mem:sidney:backup", {})

    out = {
        "baseline_ok": baseline_ok,
        "pre_sync_diverged": pre_diverged,
        "transfer": transfer,
        "converged": post_a == post_b,
        "convergence_hash": post_a,
        "P2_no_loss": ("mem:sidney:laptop" in a_mem and "mem:sidney:laptop" in b_mem
                       and "mem:server2:gpu" in a_mem and "mem:server2:gpu" in b_mem),
        "P3_conflict_converges": (winner_a.get("content") == winner_b.get("content")
                                  and winner_a.get("origin") == winner_b.get("origin")),
        "conflict_winner_origin": winner_a.get("origin"),
        "P5_audit_trail_present": bool(winner_a.get("superseded")),
        "tombstone_honored": "mem:server2:scratch" not in a_mem,
        "prune_propagated": any(r["status"] == "pruned" for r in A.dump("proj_tot_nodes")),
        "ledger_events": {"sidney": A.ledger_size(), "server2": B.ledger_size()},
    }
    A.close(); B.close()
    return out


# ---------------------------------------------------------------------------
# G-3 — backfill from a .backup snapshot, then converge
# ---------------------------------------------------------------------------

def _seed_legacy(db_path: str, rows: Dict[str, List[tuple]]) -> None:
    """Create a mem20 v1.0.1 database with pre-existing legacy rows."""
    conn = sqlite3.connect(db_path)
    conn.executescript(MEM20_SCHEMA)
    for r in rows.get("memories", []):
        conn.execute("INSERT INTO memories(session_id,topic,content,tags,trust,created_at) "
                     "VALUES(?,?,?,?,?,?)", r)
    for r in rows.get("tot_nodes", []):
        conn.execute("INSERT INTO tot_nodes(node_id,session_id,parent_node_id,branch_index,"
                     "depth,prompt_context,raw_llm_output,cleaned_output,substrate_payload,"
                     "heuristic_score_delta,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", r)
    for r in rows.get("history", []):
        conn.execute("INSERT INTO cognitive_substrate_history(node_id,session_id,"
                     "substrate_payload,heuristic_score_delta,is_pruned,created_at) "
                     "VALUES(?,?,?,?,?,?)", r)
    conn.commit()
    conn.close()


def scenario_g3(workdir: str) -> Dict[str, Any]:
    a_db = os.path.join(workdir, "sidney.db")
    b_db = os.path.join(workdir, "server2.db")

    # Sidney's pre-existing data
    _seed_legacy(a_db, {
        "memories": [
            ("default", "infra", "Sidney runs on the home NAS.", "infra", 0.8, "2026-09-01 10:00:00"),
            ("default", "conventions", "All timestamps are UTC ISO-8601.", "conv", 0.9, "2026-09-01 10:05:00"),
        ],
        "tot_nodes": [
            ("tot-a1", "sess-a", None, 0, 0, "ctx", "raw", "clean",
             json.dumps({"foundations": {"premise_validation": "ok"}}), 5.0, "active", "2026-09-02 11:00:00"),
        ],
        "history": [
            ("tot-a1", "sess-a", json.dumps({"foundations": {"premise_validation": "ok"}}), 5.0, 0, "2026-09-02 11:00:00"),
        ],
    })
    # Server 2's pre-existing data (different rows, overlapping content on one)
    _seed_legacy(b_db, {
        "memories": [
            ("default", "infra", "Server 2 has an RTX 4090 for local models.", "infra", 0.7, "2026-09-03 09:00:00"),
            ("default", "conventions", "All timestamps are UTC ISO-8601.", "conv", 0.9, "2026-09-01 10:05:00"),
        ],
        "tot_nodes": [
            ("tot-b1", "sess-b", None, 0, 0, "ctx2", "raw2", "clean2",
             json.dumps({"utility": {"load_summary": "b"}}), 3.0, "completed", "2026-09-04 12:00:00"),
        ],
        "history": [
            ("tot-b1", "sess-b", json.dumps({"utility": {"load_summary": "b"}}), 3.0, 0, "2026-09-04 12:00:00"),
        ],
    })

    ra = bf.backfill(a_db, "sidney", snapshot_dir=os.path.join(workdir, "snaps"))
    rb = bf.backfill(b_db, "server2", snapshot_dir=os.path.join(workdir, "snaps"))

    A = Mem20Sync(a_db, node_id="sidney")
    B = Mem20Sync(b_db, node_id="server2")
    A.project(); B.project()
    pre_a, pre_b = A.state_hash(), B.state_hash()

    A.sync_with(B)
    A.project(); B.project()
    post_a, post_b = A.state_hash(), B.state_hash()

    # idempotency: a second round must change nothing
    A.sync_with(B)
    A.project(); B.project()
    idem_a, idem_b = A.state_hash(), B.state_hash()

    out = {
        "backfill_a": ra, "backfill_b": rb,
        "pre_hashes": {"sidney": pre_a, "server2": pre_b},
        "post_hashes": {"sidney": post_a, "server2": post_b},
        "identical": post_a == post_b,
        "idempotent": (idem_a == post_a and idem_b == post_b),
        "snapshots_exist": (os.path.exists(ra["snapshot"]) and os.path.exists(rb["snapshot"])),
        "memories_on_both": sorted(r["entity_key"] for r in A.dump("proj_memories")),
    }
    A.close(); B.close()
    return out


# ---------------------------------------------------------------------------
# Invariants — one event per write, stable keys, idempotent ingest
# ---------------------------------------------------------------------------

def scenario_invariants(workdir: str) -> Dict[str, Any]:
    db = os.path.join(workdir, "inv.db")
    N = Mem20Sync(db, node_id="sidney", clock_ms=1_700_000_000_000)

    def count() -> int:
        return N.ledger_size()

    c0 = count()
    N.persist_memory("hello world", topic="t", session_id="s")
    c1 = count()
    N.persist_node("tot-x", "s", status="active", score_delta=1.0)
    c2 = count()
    N.prune_failed_approach("tot-x")
    c3 = count()

    one_per_write = (c1 - c0 == 1) and (c2 - c1 == 1) and (c3 - c2 == 1)

    # stable keys
    k_mem = memory_key("s", "t", "hello world")
    key_ok = (k_mem.startswith("mem:") and len(k_mem) == 4 + 16
              and k_mem == "mem:" + hashlib.sha256(b"s|t|hello world").hexdigest()[:16])
    hk = history_key("sidney", 7)
    hist_ok = hk == "hist:sidney:7"
    node_ok = node_key("tot-x") == "tot-x"

    # content-addressed idempotence: same content -> same key
    N.persist_memory("hello world", topic="t", session_id="s")
    N.project()
    mem_rows = [r for r in N.dump("proj_memories") if r["entity_key"] == k_mem]
    content_addressed = len(mem_rows) == 1

    # idempotent ingest
    peer = Mem20Sync(os.path.join(workdir, "inv_peer.db"), node_id="server2")
    evs = N.events_after({})
    a1, _ = peer.ingest(evs)
    a2, _ = peer.ingest(evs)
    ingest_idempotent = (a1 == len(evs)) and (a2 == 0)

    N.close(); peer.close()
    return {
        "one_event_per_write": one_per_write,
        "counts": [c0, c1, c2, c3],
        "key_ok": key_ok, "hist_ok": hist_ok, "node_ok": node_ok,
        "content_addressed": content_addressed,
        "ingest_idempotent": ingest_idempotent,
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    workdir = tempfile.mkdtemp(prefix="mem20-accept-")
    try:
        g2 = scenario_g2(workdir)
        g3 = scenario_g3(workdir)
        inv = scenario_invariants(workdir)

        # ---- G-2: the eight reference properties --------------------------
        check("G-2 P1a baseline converges before the partition", g2["baseline_ok"])
        check("G-2 P1b nodes diverge during the partition", g2["pre_sync_diverged"])
        check("G-2 P2  no data loss across a partition", g2["P2_no_loss"])
        check("G-2 P3  a conflicting key converges to one identical value",
              g2["P3_conflict_converges"], f"winner={g2['conflict_winner_origin']}")
        check("G-2 P4  both nodes reach a byte-identical state hash", g2["converged"],
              g2["convergence_hash"][:16])
        check("G-2 P5  the losing value is retained in the audit ledger",
              g2["P5_audit_trail_present"])
        check("G-2 --  tombstone respected (no resurrection)", g2["tombstone_honored"])
        check("G-2 --  prune (status transition) propagated", g2["prune_propagated"])

        # ---- G-3: HARD GATE ------------------------------------------------
        check("G-3 backfill snapshots exist (rollback artefact)", g3["snapshots_exist"])
        check("G-3 backfill yields byte-identical state_hash on both nodes",
              g3["identical"], g3["post_hashes"]["sidney"][:16])
        check("G-3 a second anti-entropy round is a no-op (idempotent)",
              g3["idempotent"])

        # ---- invariants ----------------------------------------------------
        check("INV each wrapped write path emits exactly one event",
              inv["one_event_per_write"], str(inv["counts"]))
        check("INV memory key = mem: + sha256(session|topic|content)[:16]", inv["key_ok"])
        check("INV history key = hist:<node_id>:<seq>", inv["hist_ok"])
        check("INV tot_nodes key = node_id (unchanged)", inv["node_ok"])
        check("INV content-addressed key is idempotent", inv["content_addressed"])
        check("INV ingest is idempotent by event_id", inv["ingest_idempotent"])

        print("=================== ACCEPTANCE ===================")
        for label, ok, detail in RESULTS:
            suffix = f"  ({detail})" if detail else ""
            print(f"  [{'PASS' if ok else 'FAIL'}] {label}{suffix}")
        print("==================================================")
        passed = sum(1 for _, ok, _ in RESULTS if ok)
        total = len(RESULTS)
        print(f"=== {passed} passed, {total - passed} failed ===")
        print(f"G-2 convergence hash: {g2['convergence_hash']}")
        print(f"G-3 converged hash:   {g3['post_hashes']['sidney']}")
        all_ok = passed == total
        print("ALL GATES PASS" if all_ok else "GATE FAILURE")
        return 0 if all_ok else 1
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
