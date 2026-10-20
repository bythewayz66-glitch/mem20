#!/usr/bin/env python3
"""
mem20 distributed sync layer — origin-tagged append-only event log + deterministic projection
=============================================================================================

Implements Option D from `mem20-distributed-design.md` (v2.0) on top of mem20's
**real** v1.0.1 schema (`github.com/JaysonAIOnline/mcp-cognitive-substrate`,
`src/mcp_cognitive_substrate/memory.py`).

What this module adds, beside mem20's existing three tables
(`tot_nodes`, `cognitive_substrate_history`, `memories`):

  * ``replication_state`` — node identity + bookkeeping (key/value)
  * ``events``            — the append-only, origin-tagged ledger (never mutated)
  * ``proj_memories`` / ``proj_tot_nodes`` / ``proj_history`` — deterministic
    projections rebuilt from the ledger

Public surface (the seven functions the build handoff names):

  ``hlc_now()``  ``_emit()``  ``project()``  ``vector_clock()``
  ``ingest()``   ``sync_with(peer)``  ``state_hash()``

plus the three wrapped write paths, each of which emits **exactly one** event:

  ``persist_memory()``  ``persist_node()``  ``prune_failed_approach()``

Stable logical keys (the one real migration):

  * memories  -> ``mem:`` + sha256(session_id|topic|content)[:16]   (content-addressed)
  * history   -> ``hist:`` + node_id + ``:`` + seq                 (per-origin)
  * tot_nodes -> ``node_id`` unchanged (already TEXT PRIMARY KEY)

Ordering contract: every event sorts by ``(hlc, origin, seq)``. Because ``hlc``
embeds the origin as its final field, that tuple is a **total order** — two nodes
replaying the same event set necessarily produce identical projections.

Deps: Python 3.11+ stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 0. mem20 v1.0.1 schema — verbatim table shapes from memory.py `_SCHEMA`.
#    Kept here so the sync layer can create/verify the base tables itself.
# ---------------------------------------------------------------------------

MEM20_SCHEMA = """
CREATE TABLE IF NOT EXISTS tot_nodes (
    node_id        TEXT PRIMARY KEY,
    session_id     TEXT NOT NULL,
    parent_node_id TEXT,
    branch_index   INTEGER DEFAULT 0,
    depth          INTEGER DEFAULT 0,
    prompt_context TEXT,
    raw_llm_output TEXT,
    cleaned_output TEXT,
    substrate_payload TEXT,
    heuristic_score_delta REAL DEFAULT 0.0,
    status         TEXT CHECK(status IN ('pending','active','pruned','completed','selected'))
                   DEFAULT 'pending',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cognitive_substrate_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id       TEXT NOT NULL,
    session_id    TEXT NOT NULL,
    substrate_payload TEXT,
    heuristic_score_delta REAL DEFAULT 0.0,
    is_pruned     INTEGER DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS memories (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    topic     TEXT,
    content   TEXT NOT NULL,
    tags      TEXT,
    trust     REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# ---------------------------------------------------------------------------
# 1. The replication layer — migration DDL added alongside mem20's tables.
# ---------------------------------------------------------------------------

SYNC_SCHEMA = """
-- Identity: who wrote this, and how far we've seen each other.
CREATE TABLE IF NOT EXISTS replication_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
-- The ledger: append-only, origin-tagged, never mutated, never deleted.
CREATE TABLE IF NOT EXISTS events (
    event_id   TEXT PRIMARY KEY,          -- "<origin>:<seq>"
    origin     TEXT NOT NULL,
    seq        INTEGER NOT NULL,
    hlc        TEXT NOT NULL,             -- "<ms:013d>-<ctr:04d>-<origin>"
    entity     TEXT NOT NULL,             -- 'memory' | 'tot_node' | 'history'
    entity_key TEXT NOT NULL,             -- stable logical key
    op         TEXT NOT NULL,             -- 'upsert' | 'tombstone'
    payload    TEXT NOT NULL,             -- JSON
    UNIQUE(origin, seq)
);
CREATE INDEX IF NOT EXISTS idx_events_hlc ON events(hlc, origin, seq);
CREATE INDEX IF NOT EXISTS idx_events_key ON events(entity, entity_key);

-- Projections (derived; rebuilt from `events`, never written by hand).
CREATE TABLE IF NOT EXISTS proj_memories (
    entity_key TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    topic      TEXT,
    content    TEXT NOT NULL,
    tags       TEXT,
    trust      REAL DEFAULT 0.5,
    created_hlc TEXT NOT NULL,
    origin     TEXT NOT NULL,
    superseded TEXT DEFAULT NULL         -- JSON of the losing value(s), kept for audit
);
CREATE TABLE IF NOT EXISTS proj_tot_nodes (
    entity_key TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    parent_node_id TEXT,
    prompt_context TEXT,
    cleaned_output TEXT,
    substrate_payload TEXT,
    heuristic_score_delta REAL DEFAULT 0.0,
    status     TEXT NOT NULL,
    created_hlc TEXT NOT NULL,
    origin     TEXT NOT NULL,
    superseded TEXT DEFAULT NULL
);
CREATE TABLE IF NOT EXISTS proj_history (
    entity_key TEXT PRIMARY KEY,
    node_id    TEXT NOT NULL,
    session_id TEXT NOT NULL,
    substrate_payload TEXT,
    heuristic_score_delta REAL DEFAULT 0.0,
    is_pruned  INTEGER DEFAULT 0,
    created_hlc TEXT NOT NULL,
    origin     TEXT NOT NULL
);
"""

# ---------------------------------------------------------------------------
# 2. Stable logical keys.
# ---------------------------------------------------------------------------

def memory_key(session_id: str, topic: str, content: str) -> str:
    """Content-addressed key: re-storing the same memory is idempotent, and two
    nodes that independently learn the same fact converge on one row."""
    raw = f"{session_id}|{topic}|{content}".encode("utf-8")
    return "mem:" + hashlib.sha256(raw).hexdigest()[:16]


def history_key(node_id: str, seq: int) -> str:
    """History rows are intrinsically per-origin (they record *who* reasoned)."""
    return f"hist:{node_id}:{seq}"


def node_key(node_id: str) -> str:
    """tot_nodes.node_id is already a stable TEXT PRIMARY KEY — unchanged."""
    return node_id


# ---------------------------------------------------------------------------
# 3. Hybrid logical clock — a total order without trusting wall clocks.
# ---------------------------------------------------------------------------

class HLC:
    """``hlc = "<millis:013d>-<counter:04d>-<origin>"``.

    Keeps wall-clock intuition while guaranteeing a total order: the origin is
    the final field, so two events with the same millisecond and counter still
    sort deterministically.
    """

    def __init__(self, node: str, last_ms: int = 0, counter: int = 0) -> None:
        self.node = node
        self.last_ms = last_ms
        self.counter = counter

    def tick(self, now_ms: Optional[int] = None) -> str:
        now_ms = int(time.time() * 1000) if now_ms is None else int(now_ms)
        if now_ms > self.last_ms:
            self.last_ms, self.counter = now_ms, 0
        else:
            self.counter += 1
        return f"{self.last_ms:013d}-{self.counter:04d}-{self.node}"

    def observe(self, remote_hlc: str) -> None:
        """Merge a remote timestamp so our next tick sorts after it."""
        try:
            ms_s, ctr_s, _ = remote_hlc.split("-")
            r_ms, r_ctr = int(ms_s), int(ctr_s)
        except (ValueError, AttributeError):
            return
        if r_ms > self.last_ms:
            self.last_ms, self.counter = r_ms, r_ctr
        elif r_ms == self.last_ms:
            self.counter = max(self.counter, r_ctr)


# ---------------------------------------------------------------------------
# 4. The sync layer.
# ---------------------------------------------------------------------------

def connect(path: str) -> sqlite3.Connection:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


class Mem20Sync:
    """One server running mem20 + the replication layer.

    ``db_path`` is mem20's own SQLite file (``$MCP_COGNITIVE_SUBSTRATE_DB`` or
    ``~/.mcp_cognitive_substrate/cognitive.db``). The sync tables live in the
    *same* file, so a single ``sqlite3 .backup`` captures everything.
    """

    def __init__(self, db_path: str, node_id: Optional[str] = None,
                 clock_ms: Optional[int] = None) -> None:
        self.path = db_path
        self.conn = connect(db_path)
        self.conn.executescript(MEM20_SCHEMA)
        self.conn.executescript(SYNC_SCHEMA)
        if node_id:
            self.conn.execute(
                "INSERT OR IGNORE INTO replication_state(key,value) VALUES('node_id',?)",
                (node_id,),
            )
        self.conn.commit()
        self.node_id = self._get_state("node_id") or node_id or "unnamed"
        self.hlc = HLC(self.node_id)
        self._fixed_ms = clock_ms
        self._next_seq = self._load_seq()

    # -- replication_state helpers ------------------------------------------
    def _get_state(self, key: str) -> Optional[str]:
        row = self.conn.execute(
            "SELECT value FROM replication_state WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def set_state(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO replication_state(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()

    def _load_seq(self) -> int:
        row = self.conn.execute(
            "SELECT COALESCE(MAX(seq),0) AS s FROM events WHERE origin=?", (self.node_id,)
        ).fetchone()
        return int(row["s"])

    # -- clock ---------------------------------------------------------------
    def hlc_now(self) -> str:
        """Return the next HLC stamp for this node (and advance the clock)."""
        return self.hlc.tick(self._fixed_ms)

    # -- write path ----------------------------------------------------------
    def _emit(self, entity: str, entity_key: str, op: str,
              payload: Dict[str, Any], hlc: Optional[str] = None) -> str:
        """Append exactly one event to the ledger. Returns the event_id."""
        self._next_seq += 1
        seq = self._next_seq
        hlc = hlc or self.hlc_now()
        eid = f"{self.node_id}:{seq}"
        self.conn.execute(
            "INSERT INTO events(event_id,origin,seq,hlc,entity,entity_key,op,payload) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (eid, self.node_id, seq, hlc, entity, entity_key, op,
             json.dumps(payload, sort_keys=True)),
        )
        self.conn.commit()
        return eid

    # -- explicit-key variants (used by the acceptance suite to reproduce the
    #    reference conflict scenario, and by callers that already hold a key) --
    def persist_memory_keyed(self, key: str, content: str, topic: str = "general",
                             tags: str = "", session_id: str = "default",
                             trust: float = 0.5) -> str:
        """Emit one ``memory`` upsert under a caller-supplied stable key."""
        return self._emit("memory", key, "upsert", {
            "session_id": session_id, "topic": topic, "content": content,
            "tags": tags, "trust": trust,
        })

    def delete_memory_keyed(self, key: str, reason: str = "user requested") -> str:
        """Emit one ``memory`` tombstone under a caller-supplied stable key."""
        return self._emit("memory", key, "tombstone", {"reason": reason})

    # -- the three wrapped write paths (each emits EXACTLY ONE event) --------
    def persist_memory(self, content: str, topic: str = "general", tags: str = "",
                       session_id: str = "default", trust: float = 0.5) -> Dict[str, Any]:
        """Wrap mem20's ``ToTMemory.store()``.

        Emits one ``memory`` upsert event, then writes the legacy ``memories``
        row so mem20's own ``recall()`` keeps working unchanged.
        """
        key = memory_key(session_id, topic, content)
        eid = self._emit("memory", key, "upsert", {
            "session_id": session_id, "topic": topic, "content": content,
            "tags": tags, "trust": trust,
        })
        cur = self.conn.execute(
            "INSERT INTO memories (session_id, topic, content, tags, trust) VALUES (?,?,?,?,?)",
            (session_id, topic, content, tags, trust),
        )
        self.conn.commit()
        return {"event_id": eid, "entity_key": key, "legacy_id": int(cur.lastrowid)}

    def persist_node(self, node_id: str, session_id: str = "default",
                     parent_node_id: Optional[str] = None, branch_index: int = 0,
                     depth: int = 0, prompt_context: str = "", raw_output: str = "",
                     cleaned_output: str = "", substrate: Optional[dict] = None,
                     score_delta: float = 0.0, status: str = "pending") -> Dict[str, Any]:
        """Wrap mem20's ``ToTMemory.persist_node()``.

        Emits one ``tot_node`` upsert event. The projection derives BOTH the
        ``proj_tot_nodes`` row and the corresponding ``proj_history`` row from
        that single event (mem20 always writes both tables together), so the
        write path still emits exactly one event.
        """
        substrate = substrate or {}
        is_pruned = 1 if score_delta <= -100 else 0
        key = node_key(node_id)
        eid = self._emit("tot_node", key, "upsert", {
            "session_id": session_id, "parent_node_id": parent_node_id,
            "branch_index": branch_index, "depth": depth,
            "prompt_context": prompt_context, "cleaned_output": cleaned_output,
            "substrate_payload": json.dumps(substrate, sort_keys=True),
            "heuristic_score_delta": score_delta, "status": status,
            "is_pruned": is_pruned,
        })
        # legacy tables, so mem20's own tools keep working
        self.conn.execute(
            """
            INSERT INTO tot_nodes (node_id, session_id, parent_node_id, branch_index,
                                   depth, prompt_context, raw_llm_output, cleaned_output,
                                   substrate_payload, heuristic_score_delta, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(node_id) DO UPDATE SET
                cleaned_output = excluded.cleaned_output,
                substrate_payload = excluded.substrate_payload,
                heuristic_score_delta = excluded.heuristic_score_delta,
                status = excluded.status
            """,
            (node_id, session_id, parent_node_id, branch_index, depth,
             prompt_context, raw_output, cleaned_output,
             json.dumps(substrate), score_delta, status),
        )
        self.conn.execute(
            "INSERT INTO cognitive_substrate_history "
            "(node_id, session_id, substrate_payload, heuristic_score_delta, is_pruned) "
            "VALUES (?,?,?,?,?)",
            (node_id, session_id, json.dumps(substrate), score_delta, is_pruned),
        )
        self.conn.commit()
        return {"event_id": eid, "entity_key": key}

    def prune_failed_approach(self, node_id: str) -> Dict[str, Any]:
        """Wrap mem20's module-level ``prune_failed_approach()``.

        A status transition is just an ordered upsert — emits exactly one event.
        """
        row = self.conn.execute(
            "SELECT session_id, substrate_payload, heuristic_score_delta "
            "FROM tot_nodes WHERE node_id=?", (node_id,)
        ).fetchone()
        session_id = row["session_id"] if row else "default"
        substrate = row["substrate_payload"] if row else "{}"
        score = row["heuristic_score_delta"] if row else 0.0
        eid = self._emit("tot_node", node_key(node_id), "upsert", {
            "session_id": session_id, "parent_node_id": None, "branch_index": 0,
            "depth": 0, "prompt_context": "", "cleaned_output": "",
            "substrate_payload": substrate or "{}",
            "heuristic_score_delta": score, "status": "pruned", "is_pruned": 1,
        })
        self.conn.execute(
            "UPDATE tot_nodes SET status='pruned' WHERE node_id=?", (node_id,)
        )
        self.conn.commit()
        return {"event_id": eid, "entity_key": node_key(node_id)}

    def delete_memory(self, session_id: str, topic: str, content: str,
                      reason: str = "user requested") -> Dict[str, Any]:
        """Tombstone — never a physical DELETE. The ledger stays append-only."""
        key = memory_key(session_id, topic, content)
        eid = self._emit("memory", key, "tombstone", {"reason": reason})
        return {"event_id": eid, "entity_key": key}

    # -- deterministic projection -------------------------------------------
    def project(self) -> Dict[str, int]:
        """Rebuild every projection table from the ledger.

        Pure function of the event set: sort by ``(hlc, origin, seq)``, replay.
        Conflict rules (design §6.4):
          * disjoint keys         -> both survive (union)
          * same key, both upsert -> highest (hlc, origin, seq) wins; loser kept
          * tombstone vs upsert   -> later HLC wins (delete is not sticky)
        """
        self.conn.execute("DELETE FROM proj_memories")
        self.conn.execute("DELETE FROM proj_tot_nodes")
        self.conn.execute("DELETE FROM proj_history")

        rows = self.conn.execute(
            "SELECT * FROM events ORDER BY hlc, origin, seq"
        ).fetchall()

        newest: Dict[Tuple[str, str], sqlite3.Row] = {}
        hist_seen: Dict[str, sqlite3.Row] = {}

        for r in rows:
            if r["entity"] == "history":
                hist_seen.setdefault(r["entity_key"], r)
                continue
            newest[(r["entity"], r["entity_key"])] = r

        mem_n = tot_n = hist_n = 0
        for (entity, key), r in newest.items():
            payload = json.loads(r["payload"])
            if entity == "memory":
                if r["op"] == "tombstone":
                    continue
                loser = self._loser_for(entity, key, r, rows)
                self.conn.execute(
                    "INSERT INTO proj_memories(entity_key,session_id,topic,content,tags,trust,"
                    "created_hlc,origin,superseded) VALUES(?,?,?,?,?,?,?,?,?)",
                    (key, payload["session_id"], payload.get("topic", ""),
                     payload["content"], payload.get("tags", ""), payload.get("trust", 0.5),
                     r["hlc"], r["origin"], loser),
                )
                mem_n += 1
            elif entity == "tot_node":
                loser = self._loser_for(entity, key, r, rows)
                self.conn.execute(
                    "INSERT INTO proj_tot_nodes(entity_key,session_id,parent_node_id,"
                    "prompt_context,cleaned_output,substrate_payload,heuristic_score_delta,"
                    "status,created_hlc,origin,superseded) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (key, payload["session_id"], payload.get("parent_node_id"),
                     payload.get("prompt_context", ""), payload.get("cleaned_output", ""),
                     payload.get("substrate_payload", "{}"),
                     payload.get("heuristic_score_delta", 0.0), payload["status"],
                     r["hlc"], r["origin"], loser),
                )
                tot_n += 1
                # derive the history row from the SAME event (mem20 writes both)
                hkey = history_key(r["origin"], r["seq"])
                self.conn.execute(
                    "INSERT OR IGNORE INTO proj_history(entity_key,node_id,session_id,"
                    "substrate_payload,heuristic_score_delta,is_pruned,created_hlc,origin) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (hkey, key, payload["session_id"],
                     payload.get("substrate_payload", "{}"),
                     payload.get("heuristic_score_delta", 0.0),
                     payload.get("is_pruned", 0), r["hlc"], r["origin"]),
                )
                hist_n += 1

        for key, r in hist_seen.items():
            payload = json.loads(r["payload"])
            self.conn.execute(
                "INSERT OR IGNORE INTO proj_history(entity_key,node_id,session_id,"
                "substrate_payload,heuristic_score_delta,is_pruned,created_hlc,origin) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (key, payload["node_id"], payload["session_id"],
                 payload.get("substrate_payload", "{}"),
                 payload.get("heuristic_score_delta", 0.0),
                 payload.get("is_pruned", 0), r["hlc"], r["origin"]),
            )
            hist_n += 1

        self.conn.commit()
        return {"memories": mem_n, "tot_nodes": tot_n, "history": hist_n}

    def _loser_for(self, entity: str, key: str, winner: sqlite3.Row,
                   rows: List[sqlite3.Row]) -> Optional[str]:
        """JSON of every *other* upsert for this key — the audit trail."""
        losers = []
        for r in rows:
            if r["entity"] != entity or r["entity_key"] != key:
                continue
            if r["event_id"] == winner["event_id"]:
                continue
            if r["op"] != "upsert":
                continue
            losers.append({"event_id": r["event_id"], "hlc": r["hlc"],
                           "origin": r["origin"], "payload": json.loads(r["payload"])})
        return json.dumps(losers, sort_keys=True) if losers else None

    # -- anti-entropy --------------------------------------------------------
    def vector_clock(self) -> Dict[str, int]:
        rows = self.conn.execute(
            "SELECT origin, MAX(seq) AS s FROM events GROUP BY origin"
        ).fetchall()
        return {r["origin"]: int(r["s"]) for r in rows}

    def events_after(self, remote_vc: Dict[str, int]) -> List[Dict[str, Any]]:
        """Everything this node holds that the peer has not acknowledged."""
        out = []
        for r in self.conn.execute("SELECT * FROM events ORDER BY origin, seq"):
            if r["seq"] > remote_vc.get(r["origin"], 0):
                out.append(dict(r))
        return out

    def ingest(self, events: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Idempotent apply. Returns ``(applied, conflicts_absorbed)``."""
        applied = conflicts = 0
        for e in events:
            exists = self.conn.execute(
                "SELECT 1 FROM events WHERE event_id=?", (e["event_id"],)
            ).fetchone()
            if exists:
                continue
            self.conn.execute(
                "INSERT INTO events(event_id,origin,seq,hlc,entity,entity_key,op,payload) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (e["event_id"], e["origin"], e["seq"], e["hlc"], e["entity"],
                 e["entity_key"], e["op"], e["payload"]),
            )
            self.hlc.observe(e["hlc"])
            if e["hlc"] < self._current_hlc_for(e["entity"], e["entity_key"]):
                conflicts += 1
            applied += 1
        self.conn.commit()
        own = self.conn.execute(
            "SELECT COALESCE(MAX(seq),0) AS s FROM events WHERE origin=?", (self.node_id,)
        ).fetchone()
        self._next_seq = max(self._next_seq, int(own["s"]))
        return applied, conflicts

    def _current_hlc_for(self, entity: str, key: str) -> str:
        row = self.conn.execute(
            "SELECT MAX(hlc) AS h FROM events WHERE entity=? AND entity_key=?",
            (entity, key),
        ).fetchone()
        return row["h"] or ""

    def sync_with(self, peer: "Mem20Sync") -> Dict[str, int]:
        """Full bidirectional anti-entropy (one round is enough to converge)."""
        a_to_b = self.events_after(peer.vector_clock())
        b_to_a = peer.events_after(self.vector_clock())
        applied_b, _ = peer.ingest(a_to_b)
        applied_a, _ = self.ingest(b_to_a)
        return {"a_to_b": applied_b, "b_to_a": applied_a}

    # -- verification --------------------------------------------------------
    def state_hash(self) -> str:
        """Hash of the *projected logical state* — the thing that must match."""
        h = hashlib.sha256()
        for tbl, cols in (
            ("proj_memories", "entity_key,session_id,topic,content,tags,trust,created_hlc,origin"),
            ("proj_tot_nodes", "entity_key,session_id,status,heuristic_score_delta,created_hlc,origin"),
            ("proj_history", "entity_key,node_id,session_id,is_pruned,created_hlc,origin"),
        ):
            for r in self.conn.execute(f"SELECT {cols} FROM {tbl} ORDER BY entity_key"):
                h.update(json.dumps(dict(r), sort_keys=True).encode())
        return h.hexdigest()

    def ledger_size(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"])

    def dump(self, tbl: str) -> List[Dict[str, Any]]:
        return [dict(r) for r in self.conn.execute(f"SELECT * FROM {tbl} ORDER BY 1")]

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 5. Convenience: open a node from the environment (matches mem20's own default).
# ---------------------------------------------------------------------------

def default_db_path() -> str:
    return os.environ.get(
        "MCP_COGNITIVE_SUBSTRATE_DB",
        os.path.join(os.path.expanduser("~"), ".mcp_cognitive_substrate", "cognitive.db"),
    )


def open_node(node_id: Optional[str] = None, db_path: Optional[str] = None) -> Mem20Sync:
    return Mem20Sync(db_path or default_db_path(), node_id=node_id)
