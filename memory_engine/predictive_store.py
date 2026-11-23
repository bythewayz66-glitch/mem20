"""Predictive recall state store."""
from __future__ import annotations
import json, math, sqlite3, threading, time
from pathlib import Path
from typing import Any

HALF_LIFE_SECONDS = 7 * 24 * 3600

class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(str(self.path), timeout=15)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        return c

    def _init(self) -> None:
        with self._lock, self._conn() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS recall_events (
                    id TEXT PRIMARY KEY, ts REAL NOT NULL, context_topic TEXT,
                    context_tags TEXT, returned_ids TEXT, returned_topics TEXT, useful INTEGER);
                CREATE TABLE IF NOT EXISTS transitions (
                    from_topic TEXT NOT NULL, to_topic TEXT NOT NULL,
                    count REAL NOT NULL DEFAULT 0, last_ts REAL NOT NULL,
                    PRIMARY KEY (from_topic, to_topic));
                CREATE TABLE IF NOT EXISTS access (
                    key TEXT NOT NULL, kind TEXT NOT NULL,
                    count REAL NOT NULL DEFAULT 0, last_ts REAL NOT NULL, PRIMARY KEY (key));
                CREATE TABLE IF NOT EXISTS outcomes (
                    id TEXT PRIMARY KEY, prediction_id TEXT, ts REAL NOT NULL,
                    used_ids TEXT, useful INTEGER NOT NULL);
            """)

    def record_event(self, event_id, ts, context_topic, context_tags, returned_ids, returned_topics):
        with self._lock, self._conn() as db:
            db.execute(
                "INSERT OR REPLACE INTO recall_events"
                "(id,ts,context_topic,context_tags,returned_ids,returned_topics,useful) VALUES(?,?,?,?,?,?,NULL)",
                (event_id, ts, context_topic or "", json.dumps(list(context_tags)),
                 json.dumps(list(returned_ids)), json.dumps(list(returned_topics))))
            for topic in returned_topics:
                self._bump(db, f"topic:{topic}", "topic", ts)
            for tag in context_tags:
                self._bump(db, f"tag:{tag}", "tag", ts)
            if context_topic:
                for to_t in returned_topics:
                    if to_t and to_t != context_topic:
                        self._bump_transition(db, context_topic, to_t, ts)

    def _bump(self, db, key, kind, now):
        row = db.execute("SELECT count, last_ts FROM access WHERE key=?", (key,)).fetchone()
        if row is None:
            db.execute("INSERT INTO access(key,kind,count,last_ts) VALUES(?,?,1,?)", (key, kind, now))
            return
        age = max(0.0, now - float(row["last_ts"]))
        decay = math.pow(0.5, age / HALF_LIFE_SECONDS)
        db.execute("UPDATE access SET count=?, last_ts=? WHERE key=?",
                   (float(row["count"]) * decay + 1.0, now, key))

    def _bump_transition(self, db, frm, to, now):
        row = db.execute(
            "SELECT count, last_ts FROM transitions WHERE from_topic=? AND to_topic=?", (frm, to)
        ).fetchone()
        if row is None:
            db.execute("INSERT INTO transitions(from_topic,to_topic,count,last_ts) VALUES(?,?,1,?)",
                       (frm, to, now))
            return
        age = max(0.0, now - float(row["last_ts"]))
        decay = math.pow(0.5, age / HALF_LIFE_SECONDS)
        db.execute(
            "UPDATE transitions SET count=?, last_ts=? WHERE from_topic=? AND to_topic=?",
            (float(row["count"]) * decay + 1.0, now, frm, to))

    def record_outcome(self, outcome_id, prediction_id, ts, used_ids, useful):
        with self._lock, self._conn() as db:
            db.execute(
                "INSERT OR REPLACE INTO outcomes(id,prediction_id,ts,used_ids,useful) VALUES(?,?,?,?,?)",
                (outcome_id, prediction_id, ts, json.dumps(list(used_ids)), 1 if useful else 0))
            db.execute("UPDATE recall_events SET useful=? WHERE id=?",
                       (1 if useful else 0, prediction_id))

    def topic_scores(self, now=None):
        now = now or time.time()
        out = {}
        with self._lock, self._conn() as db:
            for row in db.execute("SELECT key, count, last_ts FROM access WHERE kind='topic'"):
                age = max(0.0, now - float(row["last_ts"]))
                decay = math.pow(0.5, age / HALF_LIFE_SECONDS)
                out[row["key"].split(":", 1)[1]] = float(row["count"]) * decay
        return out

    def transitions_from(self, topic, now=None):
        now = now or time.time()
        out = {}
        with self._lock, self._conn() as db:
            for row in db.execute(
                "SELECT to_topic, count, last_ts FROM transitions WHERE from_topic=?", (topic,)
            ):
                age = max(0.0, now - float(row["last_ts"]))
                decay = math.pow(0.5, age / HALF_LIFE_SECONDS)
                out[row["to_topic"]] = float(row["count"]) * decay
        return out

    def stats(self):
        with self._lock, self._conn() as db:
            events = db.execute("SELECT COUNT(*) c FROM recall_events").fetchone()["c"]
            outcomes = db.execute("SELECT COUNT(*) c FROM outcomes").fetchone()["c"]
            topics = db.execute("SELECT COUNT(*) c FROM access WHERE kind='topic'").fetchone()["c"]
            transitions = db.execute("SELECT COUNT(*) c FROM transitions").fetchone()["c"]
            useful = db.execute("SELECT COUNT(*) c FROM outcomes WHERE useful=1").fetchone()["c"]
            return {
                "events": events, "outcomes": outcomes, "topics_tracked": topics,
                "transitions": transitions,
                "hit_rate": round(useful / max(1, outcomes), 4) if outcomes else 0.0,
            }
