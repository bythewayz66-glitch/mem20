"""Deterministic scale corpus for mem20benchmarkz.

Generates mem20-scale-corpus-v1: 2000 grounded facts, 40 simulated, 140 queries.
Same seed always yields the same bytes — no need to commit a 400KB JSONL blob.

    mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v1
    mem20benchmarkz ingest-scale --corpus /tmp/mem20-scale-corpus-v1 --store /tmp/mem20-scale-store
    mem20benchmarkz run-scale --store /tmp/mem20-scale-store --corpus /tmp/mem20-scale-corpus-v1
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .corpus import Corpus, Fact, Query

SCALE_NAME = "mem20-scale-corpus-v1"
SCALE_SEED = 20
SCALE_FACTS = 2000
SCALE_SIMULATED = 40
SCALE_DIRECT = 80
SCALE_MULTI = 40
SCALE_ADV = 20

_TOPICS = (
    "deploy", "infra", "unity", "braid", "secrets", "roadmap", "agent", "memory",
    "retrieval", "graph", "mcp", "sdk", "ops", "ci", "desktop", "irc", "crew",
    "control", "dream", "shop", "game", "audio", "render", "billing", "support",
)


def _fact(i: int) -> Fact:
    topic = _TOPICS[i % len(_TOPICS)]
    build = 4000 + (i % 500)
    host = f"runner-{(i % 40) + 1:02d}"
    session = f"s{(i // 20) + 1:04d}"
    digest = hashlib.sha256(str(i).encode()).hexdigest()[:12]
    content = (
        f"[{session}] {topic} record {i:05d}: build {build} on {host}; "
        f"policy tag P{i % 17}; note checksum {digest}"
    )
    return Fact(
        topic=topic,
        content=content,
        tags=(topic, f"batch{i // 100}", "runner"),
        epistemic_status="observed",
    )


def _simulated(i: int) -> Fact:
    return Fact(
        topic="hypothesis",
        content=(
            f"SIMULATED-ONLY claim {i}: Zephyra sector {i} runs prod mem20 node "
            f"(not real)"
        ),
        tags=("fabricated", "adversarial"),
    )


def build_scale_corpus(
    n_facts: int = SCALE_FACTS,
    n_simulated: int = SCALE_SIMULATED,
) -> Corpus:
    """In-memory Corpus for run-scale (no disk required)."""
    facts = [_fact(i) for i in range(n_facts)]
    simulated = [_simulated(i) for i in range(n_simulated)]
    queries: list[Query] = []

    for i in range(SCALE_DIRECT):
        idx = min(i * 25, n_facts - 1)
        f = facts[idx]
        needle = f"build {4000 + (idx % 500)}"
        # Support id matches seed order used by bench._answerable_ids: topic-N
        # We also put expect substrings so keyword/semantic can score without ids.
        queries.append(
            Query(
                qid=f"d{i:03d}",
                text=f"what build is recorded for {f.topic} entry near index {idx:05d}",
                kind="direct",
                supports=(),
                expect=(needle, f"record {idx:05d}"),
            )
        )

    for i in range(SCALE_MULTI):
        a_idx = min(i * 40, n_facts - 2)
        a, b = facts[a_idx], facts[a_idx + 1]
        queries.append(
            Query(
                qid=f"m{i:03d}",
                text=f"relate records {a_idx:05d} and {a_idx + 1:05d} on {a.topic}",
                kind="multi_hop",
                supports=(),
                expect=(f"record {a_idx:05d}", f"record {a_idx + 1:05d}"),
                hops=2,
                entity=a.topic,
            )
        )

    for i in range(min(SCALE_ADV, n_simulated)):
        queries.append(
            Query(
                qid=f"a{i:03d}",
                text=f"is Zephyra sector {i} a real prod mem20 node",
                kind="adversarial",
                supports=(),
                expect=(),
            )
        )

    return Corpus(
        name=SCALE_NAME,
        facts=facts,
        queries=queries,
        simulated=simulated,
    )


def write_scale_corpus(out_dir: str | Path, n_facts: int = SCALE_FACTS) -> Path:
    """Write facts.jsonl, simulated.jsonl, queries.jsonl, manifest.json."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    corpus = build_scale_corpus(n_facts=n_facts)

    def dump(name: str, rows: list[dict]) -> None:
        with (out / name).open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    fact_rows = []
    for i, f in enumerate(corpus.facts):
        fact_rows.append({
            "id": f"f{i:05d}",
            "topic": f.topic,
            "content": f.content,
            "tags": list(f.tags),
            "epistemic_status": f.epistemic_status,
        })
    sim_rows = []
    for i, f in enumerate(corpus.simulated):
        sim_rows.append({
            "id": f"sim{i:03d}",
            "topic": f.topic,
            "content": f.content,
            "tags": list(f.tags),
        })
    q_rows = []
    for q in corpus.queries:
        q_rows.append({
            "qid": q.qid,
            "text": q.text,
            "kind": q.kind,
            "expect": list(q.expect),
            "supports": list(q.supports),
            "hops": q.hops,
            "entity": q.entity,
        })

    dump("facts.jsonl", fact_rows)
    dump("simulated.jsonl", sim_rows)
    dump("queries.jsonl", q_rows)
    manifest = {
        "name": SCALE_NAME,
        "seed": SCALE_SEED,
        "facts": len(fact_rows),
        "simulated": len(sim_rows),
        "queries": len(q_rows),
        "query_kinds": {
            "direct": sum(1 for q in corpus.queries if q.kind == "direct"),
            "multi_hop": sum(1 for q in corpus.queries if q.kind == "multi_hop"),
            "adversarial": sum(1 for q in corpus.queries if q.kind == "adversarial"),
        },
        "description": (
            "Synthetic scale corpus for mem20benchmarkz. "
            "Contamination must stay 0.0; adversarial queries must not leak simulated text."
        ),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return out


def load_jsonl_corpus(corpus_dir: str | Path) -> Corpus:
    """Load a directory written by write_scale_corpus (or compatible)."""
    d = Path(corpus_dir)
    facts: list[Fact] = []
    with (d / "facts.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            facts.append(Fact(
                topic=row["topic"],
                content=row["content"],
                tags=tuple(row.get("tags") or ()),
                epistemic_status=row.get("epistemic_status", "observed"),
            ))
    simulated: list[Fact] = []
    sim_path = d / "simulated.jsonl"
    if sim_path.is_file():
        with sim_path.open(encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                simulated.append(Fact(
                    topic=row["topic"],
                    content=row["content"],
                    tags=tuple(row.get("tags") or ()),
                ))
    queries: list[Query] = []
    with (d / "queries.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            queries.append(Query(
                qid=row["qid"],
                text=row["text"],
                kind=row["kind"],
                supports=tuple(row.get("supports") or ()),
                expect=tuple(row.get("expect") or ()),
                hops=int(row.get("hops") or 1),
                entity=row.get("entity"),
            ))
    name = SCALE_NAME
    man = d / "manifest.json"
    if man.is_file():
        name = json.loads(man.read_text(encoding="utf-8")).get("name", name)
    return Corpus(name=name, facts=facts, queries=queries, simulated=simulated)
