"""Retrieval benchmarks: recall quality, latency, and trustworthiness.

Run against an isolated store so a benchmark run can never touch real data:

    mem20benchmarkz run --out benchmarks/results

## What each metric means

Recall metrics
    `hit@k`  — fraction of answerable queries whose top-k results contain the
               expected evidence. Reported per query kind, because a single
               average hides the fact that keyword search can do direct queries
               and nothing else.
    `mrr`    — mean reciprocal rank, which penalises finding the right fact
               eighth instead of first.
    `leak@k` — for adversarial queries, the fraction that returned simulated
               content at all. This is the number that should be zero, and a
               system without a hard simulated/grounded partition cannot score
               it.

Latency
    p50/p95/p99 in milliseconds, measured per query and per retrieval mode,
    with the embedding model warmed first. A cold-start number is not a latency
    number.

Trustworthiness
    `contamination_rate` — simulated records found in the grounded store or its
                            indexes. Must be 0.0.
    `stale_pointer_rate`  — fraction of index entries pointing at records that
                            no longer exist. The failure mode that made semantic
                            retrieval return zero results while reporting
                            success.
    `degradation_reported`— whether a query on a deliberately broken index said
                            so, instead of returning a plausible short list.

## Reading the output honestly

The suite refuses to report a quality score on a store whose indexes it knows
are unhealthy. A number produced from a stale index measures the index, not the
retriever, and publishing it would be the same error the diagnostics were added
to prevent.

The same principle applies to a query class whose verdict is decided by the
scorer rather than by retrieval. An adversarial probe whose answer is not in the
corpus, scored by a branch that returns False unconditionally, produces 0.000
that looks like a retrieval finding and is not one. See ADVERSARIAL_KINDS.

It applies equally to a mode scored on a probe it cannot answer. A text ranker
run against a metadata filter or a bi-temporal read produces a number that
measures nothing, so `_mode_answers_kind()` refuses the pairing instead of
reporting it.
"""
from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .corpus import Corpus, load

# Query kinds whose results must ALSO be checked for simulated leakage, on top
# of being scored for evidence like any other answerable query. They are
# answerable by construction: the gold record is in the corpus. If one of these
# ever scored 0.000 across the board again, that is a finding about retrieval or
# about corpus coverage and it has to be explainable — not the guaranteed
# consequence of a constant in the scorer.
ADVERSARIAL_KINDS = ("adversarial", "adversarial_hard", "contradiction")

# Probe kinds a text ranker can legitimately be scored on. The non-text kinds
# (recall, recall_at, entities, ledger) are answered by a different store
# surface and are excluded from every text mode — see `_mode_answers_kind`.
TEXT_KINDS = ("direct", "multi_hop", "graph_hop", "adversarial",
              "adversarial_hard", "contradiction", "unanswerable")

# Every retrieval mode present in the tree, whether this harness can score it,
# and — where it cannot — the reason. A mode is never dropped from this list:
# an absent row reads as "not run", which is a weaker statement than "blocked
# and documented". `scored` is a property of the harness; `scored_in_this_run`
# is set per invocation by `run()`.
MODE_SURFACE: tuple[dict, ...] = (
    {"id": "bm25",
     "surface": "engine BM25 index (rank_bm25), vector half never called",
     "scored": True,
     "note": ("Pure sparse retrieval. Reads the engine's own bm25_index.pkl / "
              "bm25_corpus.jsonl, so it measures the index the store built. NOT "
              "the same as `keyword`: hybrid(alpha=0.0) still executes the "
              "vector half and fuses it, so calling that BM25 overstates what "
              "was isolated.")},
    {"id": "vector",
     "surface": "MemoryStore.semantic -> recall_semantic (FAISS)",
     "scored": True,
     "note": ("Dense retrieval. ALIAS of `semantic`, not a second system: same "
              "code path, scored under the name the surface list uses. The "
              "embedder backend is reported in `environment.embedder_backend`; "
              "on a checkout without sentence-transformers it is the engine's "
              "deterministic hashing fallback, not a neural encoder.")},
    {"id": "hybrid",
     "surface": "MemoryStore.hybrid -> recall_hybrid (alpha=0.5)",
     "scored": True,
     "note": "RRF fusion of vector + BM25 with cross-encoder reranking ON (default)."},
    {"id": "hybrid-rerank-off",
     "surface": "MemoryStore.hybrid, USE_CROSS_ENCODER=False",
     "scored": True,
     "note": ("Same fusion with reranking disabled (MEM20_RERANK=0). A real "
              "operational configuration, not a synthetic variant.")},
    {"id": "graph",
     "surface": "MemoryStore.graph -> recall_graph",
     "scored": True,
     "note": ("Entity/edge traversal. Scored on `multi_hop` (the start entity's "
              "own fact) and `graph_hop` (an attribute node one hop away, e.g. "
              "a country's region), so n is larger than the multi_hop count "
              "alone. Only entity-bearing probes are scored; that is a corpus "
              "property, not a skip.")},
    {"id": "keyword",
     "surface": "MemoryStore.hybrid(alpha=0.0) -> BM25 half",
     "scored": True,
     "note": ("Retained for continuity with the previously published table. It "
              "is the shipped path for the sparse half but still pays the "
              "fusion wrapper, which is why `bm25` is reported separately.")},
    {"id": "constant",
     "surface": "control retriever (ignores the query)",
     "scored": True,
     "note": ("ADVERSARIAL CONTROL. Returns one fixed document that matches no "
              "corpus record. Every metric must read exactly 0.000; any "
              "non-zero value means the metric is handing out free hits.")},
    {"id": "recall",
     "surface": "MemoryStore.recall (topic/tags filter)",
     "scored": True,
     "note": ("Metadata filter, not a ranker. Scored on `recall` probes whose "
              "query IS the filter (topic family), so a filter that ignores the "
              "topic fails. Previously unscored for want of a probe class; that "
              "class now exists.")},
    {"id": "recall_at",
     "surface": "MemoryStore.recall_at (bi-temporal)",
     "scored": True,
     "note": ("Point-in-time read. Scored on `recall_at` probes: a positive "
              "instant after ingestion must return the record, and a negative "
              "instant before ingestion must return nothing. The negative half "
              "is what catches a read that ignores `as_of`.")},
    {"id": "entities",
     "surface": "MemoryStore.entities (enumeration)",
     "scored": True,
     "note": ("Query-free enumeration, ordered by degree. Scored on `entities` "
              "probes that name a high-degree node the top-k must surface. "
              "Hit rate is defined here as 'the named node is in the "
              "enumeration', not as a ranked retrieval metric.")},
    {"id": "ledger",
     "surface": "MemoryStore.ledger (append-only tail)",
     "scored": True,
     "note": ("Append-only tail, ordered not ranked. Scored on `ledger` probes "
              "that assert a known recent write is present in the tail. This "
              "measures tail ordering and completeness, not retrieval quality.")},
)


@dataclass
class QueryResult:
    qid: str
    kind: str
    mode: str
    hit: bool
    rank: int | None          # 1-based rank of the first supporting hit
    leaked: bool
    n_results: int
    latency_ms: float
    degraded_to: str | None = None
    drift_healthy: bool | None = None


@dataclass
class Metric:
    name: str
    value: float
    unit: str = ""


@dataclass
class Report:
    corpus: str
    facts: int
    simulated: int
    queries: int
    environment: dict = field(default_factory=dict)
    recall: dict = field(default_factory=dict)
    latency_ms: dict = field(default_factory=dict)
    trust: dict = field(default_factory=dict)
    per_query: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    mode_surface: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[idx]


def _hit(r_hits: list[dict], expect: tuple[str, ...],
         supports: set[str]) -> tuple[bool, int | None]:
    """First rank whose content satisfies the query's evidence requirement.

    A supporting *id* match counts when we can see ids. Otherwise we fall back
    to the `expect` substrings, because the graph path returns content without
    ids and we still want an honest verdict rather than a silent zero.
    """
    for i, h in enumerate(r_hits, 1):
        hid = h.get("id")
        if supports and hid and hid in supports:
            return True, i
        if expect:
            blob = " ".join(str(x) for x in expect).lower()
            if blob in str(h.get("content", "")).lower():
                return True, i
    return False, None


def _mode_answers_kind(mode: str, kind: str) -> bool:
    """Can `mode` legitimately be scored on a probe of `kind`?

    This is the dispatch table, and it is deliberately narrow. A text ranker
    cannot answer a metadata filter, a bi-temporal read, an enumeration or a
    ledger tail — running it on those probes would produce a number that
    measures nothing. The reverse is also true: the non-text modes have exactly
    one probe class each.

    The `constant` control is the exception that proves the rule: it is scored
    on every TEXT kind so its 0.000 is a real check that the metric hands out no
    free hits. It is deliberately NOT scored on `recall_at`, because a negative
    temporal probe's correct answer is "nothing came back" and a control that
    always returns one document would score 0.000 there for the wrong reason.
    """
    if mode == "graph":
        return kind in ("multi_hop", "graph_hop")
    if mode == "recall":
        return kind == "recall"
    if mode == "recall_at":
        return kind == "recall_at"
    if mode == "entities":
        return kind == "entities"
    if mode == "ledger":
        return kind == "ledger"
    # Text rankers: bm25, vector, hybrid, hybrid-rerank-off, keyword, constant.
    return kind in TEXT_KINDS


def _run_mode(store, q, mode: str, k: int) -> tuple[list[dict], str | None,
                                                    bool | None, float]:
    t0 = time.perf_counter()
    if mode == "semantic":
        r = store.semantic(q.text, k=k)
        ms = (time.perf_counter() - t0) * 1000
        return r["hits"], None, r["healthy"], ms
    if mode == "hybrid":
        r = store.hybrid(q.text, k=k)
        ms = (time.perf_counter() - t0) * 1000
        return r["hits"], r["degraded_to"], True, ms
    if mode == "graph":
        r = store.graph(q.entity or "", hops=q.hops, max_results=k)
        ms = (time.perf_counter() - t0) * 1000
        facts = [{"id": f.get("id"), "content": f.get("content", "")}
                 for f in r.get("facts", [])]
        return facts, ("found" if r.get("found") else "miss"), True, ms
    if mode == "bm25":
        # The engine's OWN sparse index, with the vector half never called.
        # `keyword` below goes through hybrid(alpha=0.0), which still executes
        # and fuses the vector half; that is a different measurement, which is
        # why both exist. Imported lazily so the harness runs on a checkout
        # where rank_bm25 is absent and only the BM25 half is skipped.
        from memory_engine import memory as _eng
        if not getattr(_eng, "BM25_AVAILABLE", False):
            raise RuntimeError("rank_bm25 not installed; bm25 mode unavailable")
        bm25 = _eng._get_bm25_index()
        corpus = _eng._load_bm25_corpus()
        scores = bm25.get_scores(_eng._bm25_tokens(q.text))
        order = sorted(range(len(corpus)), key=lambda i: -float(scores[i]))
        by_id = _eng._ledger_remember_by_id()
        hits = []
        for idx in order:
            if len(hits) >= k:
                break
            rec = by_id.get(corpus[idx]["id"])
            if rec is None:
                continue
            hits.append({"id": rec.get("id"), "content": rec.get("content", ""),
                         "topic": rec.get("topic"), "tags": rec.get("tags"),
                         "epistemic_status": rec.get("epistemic_status"),
                         "_bm25_score": float(scores[idx])})
        ms = (time.perf_counter() - t0) * 1000
        return hits, None, True, ms
    if mode == "vector":
        # Alias of `semantic`, scored under the name the surface list uses.
        r = store.semantic(q.text, k=k)
        ms = (time.perf_counter() - t0) * 1000
        return r["hits"], None, r["healthy"], ms
    if mode == "hybrid-rerank-off":
        # The shipped fusion with the cross-encoder disabled. Toggled on the
        # engine and restored in `finally`, so a raised query cannot leave the
        # store in the wrong configuration for the next mode.
        eng = store._engine
        original = getattr(eng, "USE_CROSS_ENCODER", False)
        try:
            eng.USE_CROSS_ENCODER = False
            r = store.hybrid(q.text, k=k)
        finally:
            eng.USE_CROSS_ENCODER = original
        ms = (time.perf_counter() - t0) * 1000
        return r["hits"], r["degraded_to"], True, ms
    if mode == "constant":
        # The control: a fixed document that matches no corpus record, returned
        # for every query regardless of what was asked. Every metric must read
        # 0.000; a non-zero value means the metric is handing out free hits.
        ms = (time.perf_counter() - t0) * 1000
        return [{"id": "constant-control",
                 "content": "mem20 benchmark constant control document",
                 "topic": "bench.control",
                 "tags": ["control"],
                 "epistemic_status": "observed"}], None, True, ms
    if mode == "keyword":
        # Engine-level BM25 via hybrid with alpha=0, which is the honest way to
        # isolate the keyword half using the shipped code path.
        r = store.hybrid(q.text, k=k, alpha=0.0)
        ms = (time.perf_counter() - t0) * 1000
        return r["hits"], r["degraded_to"], True, ms
    if mode == "recall":
        # Metadata filter, not a ranker. The "query" is the filter itself, so
        # the probe carries topic_filter / tags_filter instead of text. The
        # returned rows are ledger records, so the same evidence check applies.
        rows = store.recall(topic=q.topic_filter,
                            tags=list(q.tags_filter) or None, k=k)
        ms = (time.perf_counter() - t0) * 1000
        return rows, None, True, ms
    if mode == "recall_at":
        # Bi-temporal read. The "query" is the as-of instant; a probe may also
        # assert that nothing existed yet (expect_empty), which is the only way
        # to test the temporal axis rather than the current view.
        rows = store.recall_at(q.as_of or "1970-01-01T00:00:00+00:00",
                               topic=q.topic_filter,
                               tags=list(q.tags_filter) or None, k=k)
        ms = (time.perf_counter() - t0) * 1000
        return rows, None, True, ms
    if mode == "entities":
        # Query-free enumeration. There is no text to match, so the probe asks
        # whether a known high-degree entity is present in the enumeration. The
        # row shape is {entity, degree, facts, topics}; map `entity` onto
        # `content` so the shared evidence check can read it.
        #
        # The enumeration limit is not the retrieval `k`: `entities()` is an
        # ordered top-N over nodes, and the store holds 600+ of them, so asking
        # for only k=5 would score the node ranking rather than the mode. The
        # probe is "is this high-degree node enumerable", which needs a window
        # wider than the arbitrary top-5.
        limit = max(k, q.enumeration_limit or k)
        rows = [{"id": None, "content": e.get("entity", ""),
                 "entity": e.get("entity"), "degree": e.get("degree")}
                for e in store.entities(limit=limit)]
        ms = (time.perf_counter() - t0) * 1000
        return rows, None, True, ms
    if mode == "ledger":
        # Append-only tail. Ordered, not ranked: the probe asserts that the
        # most recent writes are the ones the tail returns.
        rows = store.ledger(k=k)
        ms = (time.perf_counter() - t0) * 1000
        return rows, None, True, ms
    raise ValueError(mode)


def _answerable_ids(corpus: Corpus) -> set[str]:
    """Ids of grounded facts, so we can tell support from coincidence.

    Must agree with the id the store actually assigned, which for the bulk
    ingest path is derived from the record key (see `bulk_ingest._record_id`).
    The previous version synthesised `<topic>-<ordinal>`, which matches nothing a
    real store emits — so the id half of `_hit()` could never fire and every
    verdict fell through to the `expect` substring test.
    """
    import hashlib

    out: set[str] = set()
    for f in corpus.facts:
        if f.key:
            out.add(f"b{hashlib.md5(f.key.encode()).hexdigest()[:14]}")
    return out


def _distinctive(text: str) -> str:
    """Pick a substring from `text` that identifies it and nothing else.

    The whole sentence is too blunt: a simulated fact often restates real
    vocabulary, and matching on that would flag an honest grounded result.
    Preference order:

      1. A rare-looking long word — "BLAKE3", "contaminated", "Zephyra".
      2. A capitalised token, because a fabricated proper noun is the usual tell.
      3. The leading clause, as a last resort.

    Kept only for result shapes that carry no partition label; `_leak()` prefers
    the label because marker matching does not survive a corpus of any size.
    """
    words = [w.strip(".,;:!?\"'()[]{}") for w in text.split()]
    longish = [w for w in words if len(w) >= 8]
    if longish:
        return max(longish, key=len).lower()

    caps = [w for w in words if w[:1].isupper() and len(w) >= 5]
    if caps:
        return max(caps, key=len).lower()

    return " ".join(words[:4]).lower()


def _leak(hits: list[dict], forbidden: tuple[str, ...]) -> bool:
    """Did an adversarial query surface any simulated content?

    The test is whether a *simulated record* came back, not whether the query
    returned anything. An earlier version flagged any non-empty result list as a
    leak and reported `leak_rate: 1.000` on a store where contamination was
    measurably 0.0 — the query had simply matched unrelated grounded facts,
    which is normal retrieval behaviour and not a partition failure.

    Labels first, text second. Every memory record carries the partition it was
    written to (`epistemic_status`, `tags`, `topic`), and `store.contamination()`
    validates those same labels. Reading them is exact; inferring the partition
    from prose is not. The previous version built one short marker per simulated
    record and substring-searched the result text for it, so with 1,300 markers
    the union of their words covered most of the vocabulary and it reported a
    0.87 leak against a CLEAN store. `forbidden` is now only a fallback for
    result shapes that carry no labels at all.

    The fallback requires a MULTI-WORD phrase on purpose. A single word is not
    distinctive enough to convict a result: "rewritten" appears in ordinary
    prose, and matching on it would flag honest grounded content.
    """
    for h in hits:
        status = str(h.get("epistemic_status") or "").lower()
        if status and status != "observed":
            return True
        tags = {str(t).lower() for t in (h.get("tags") or ())}
        if tags & {"simulated", "ungrounded", "false", "fiction"}:
            return True
        topic = str(h.get("topic") or "").lower()
        if topic.startswith("bench.fiction") or topic.startswith("bench.false"):
            return True

    if not forbidden:
        return False
    for h in hits:
        if h.get("epistemic_status") or h.get("tags") or h.get("topic"):
            continue  # labelled already, and it was not simulated
        blob = " ".join(str(h.get("content", "")).lower().split())
        if not blob:
            continue
        for f in forbidden:
            needle = " ".join(f.lower().split())
            if needle and len(needle.split()) > 1 and needle in blob:
                return True
    return False


def _recall_block(corpus: Corpus, results: list[QueryResult]) -> dict:
    out: dict = {}
    for mode in sorted({r.mode for r in results}):
        by_kind: dict[str, list[QueryResult]] = {}
        for r in results:
            if r.mode == mode:
                by_kind.setdefault(r.kind, []).append(r)

        mode_block: dict = {}
        for kind, rs in sorted(by_kind.items()):
            hits = [r.hit for r in rs]
            ranks = [r.rank for r in rs if r.rank]
            leaks = [r.leaked for r in rs]
            mode_block[kind] = {
                "n": len(rs),
                "hit_rate": round(sum(hits) / len(rs), 4) if rs else 0.0,
                "mrr": round(sum(1 / x for x in ranks) / len(rs), 4) if rs else 0.0,
                "leak_rate": round(sum(leaks) / len(rs), 4) if rs else 0.0,
                "median_latency_ms": round(
                    statistics.median(r.latency_ms for r in rs), 2) if rs else 0.0,
            }
        out[mode] = mode_block
    return out


def _latency_block(results: list[QueryResult]) -> dict:
    out: dict = {}
    for mode in sorted({r.mode for r in results}):
        ms = [r.latency_ms for r in results if r.mode == mode]
        if not ms:
            continue
        out[mode] = {
            "n": len(ms),
            "p50": round(_pct(ms, 0.50), 2),
            "p95": round(_pct(ms, 0.95), 2),
            "p99": round(_pct(ms, 0.99), 2),
            "max": round(max(ms), 2),
            "mean": round(statistics.fmean(ms), 2),
        }
    return out


def run(store, modes=("keyword", "semantic", "hybrid", "graph"),
        k: int = 5, corpus: Corpus | None = None,
        warm: bool = True, compare_rerank: bool = True) -> Report:
    """Run the suite against an already-seeded store.

    `compare_rerank=False` is required for any caller that runs the suite from
    inside `_rerank_comparison`; without it the two functions recurse forever.
    """
    corpus = corpus or load()
    notes: list[str] = []

    health = store.health()
    if not health["healthy"]:
        notes.append(
            "STORE UNHEALTHY at run start: "
            + json.dumps({kk: vv for kk, vv in health["indexes"].items()},
                         default=str))
    notes.append(
        "Scores are NOT comparable to Mem0's LoCoMo/LongMemEval or Zep's DMR. "
        "Those run on different corpora (two of them private or vendor-defined) "
        "with different metrics. These numbers describe this corpus only.")
    # The caveat is emitted by the harness, not patched into the artifact, so a
    # merge or a re-render cannot drop it. It is a hard restriction on how these
    # numbers may be quoted, and it stays until a run on the originals lands.
    notes.append(
        "NO LoCoMo RESULT IS CLAIMED. This harness has not been run against the "
        "LoCoMo originals (10 conversations, 1,986 QA), so no LoCoMo figure "
        "appears in this report and none may be quoted from it. The caveat "
        "stays until a run on the originals lands.")

    supports_all = _answerable_ids(corpus)

    # Distinctive substrings from the simulated facts, used only as a fallback
    # when a result row carries no partition label.
    sim_markers: tuple[str, ...] = tuple(
        _distinctive(f.content) for f in corpus.simulated)

    # Warm the embedder and cross-encoder so the first query is not an outlier.
    if warm:
        for stage in ("embed", "query"):
            try:
                if stage == "embed":
                    store.semantic("warm up the retrieval path", k=1)
                else:
                    store.hybrid("warm up the retrieval path", k=1)
            except Exception as e:  # pragma: no cover - environment dependent
                notes.append(f"warmup {stage} failed: {type(e).__name__}: {e}")

    results: list[QueryResult] = []
    for mode in modes:
        for q in corpus.queries:
            if not _mode_answers_kind(mode, q.kind):
                continue
            try:
                hits, degraded, healthy, ms = _run_mode(store, q, mode, k)
            except Exception as e:
                notes.append(f"{mode}/{q.qid} raised {type(e).__name__}: {e}")
                results.append(QueryResult(
                    qid=q.qid, kind=q.kind, mode=mode, hit=False, rank=None,
                    leaked=True, n_results=0, latency_ms=0.0,
                    degraded_to=f"error:{type(e).__name__}", drift_healthy=None))
                continue

            sup = {s for s in q.supports if s in supports_all}
            if q.kind == "unanswerable":
                # The CONTROL. Nothing in the corpus can answer it, so a
                # correct verdict is a miss and this row must read 0.000. It
                # is the only kind whose hit is computed as a constant, and it
                # is labelled `unanswerable` precisely so that constant never
                # stands in for a real measurement.
                hit, rank = False, None
                # Leak is a property of what came back, independent of whether
                # the query was answerable, so the control is still checked.
                leaked = _leak(hits, sim_markers)
            elif q.kind == "recall_at" and q.expect_empty:
                # Negative temporal probe: the correct answer is "nothing
                # existed yet". A hit means the read returned a record it
                # should not have, so the verdict is inverted on purpose and
                # labelled by the probe, not by a constant in the scorer.
                hit, rank = (len(hits) == 0), (1 if not hits else None)
                leaked = _leak(hits, sim_markers)
            else:
                # Every answerable kind — direct, multi_hop, graph_hop,
                # adversarial, adversarial_hard, contradiction, recall,
                # recall_at, entities, ledger — is scored by the same evidence
                # check. Adversarial used to be excluded here and had its
                # verdict hardcoded to False, which is why every adversarial
                # row in every published run read exactly 0.000 regardless of
                # what retrieval returned.
                hit, rank = _hit(hits, q.expect, sup)
                leaked = (_leak(hits, sim_markers)
                          if q.kind in ADVERSARIAL_KINDS else False)

            results.append(QueryResult(
                qid=q.qid, kind=q.kind, mode=mode, hit=hit, rank=rank,
                leaked=leaked, n_results=len(hits), latency_ms=round(ms, 3),
                degraded_to=degraded, drift_healthy=healthy))

    trust = _trust_block(store, results)
    trust["rerank_off_comparison"] = (_rerank_comparison(store, corpus, k)
                                      if compare_rerank else None)
    env = _environment(store)

    return Report(
        corpus=corpus.name,
        facts=len(corpus.facts),
        simulated=len(corpus.simulated),
        queries=len(corpus.queries),
        environment=env,
        recall=_recall_block(corpus, results),
        latency_ms=_latency_block(results),
        trust=trust,
        per_query=[asdict(r) for r in results],
        notes=notes,
        mode_surface=[{**m, "scored_in_this_run": m["id"] in modes}
                      for m in MODE_SURFACE],
    )


def _rerank_comparison(store, corpus: Corpus, k: int) -> dict | None:
    """Measure hybrid retrieval with and without cross-encoder reranking.

    Reranking costs an order of magnitude in latency. Reporting only the
    default-on number hides a real operational choice, so measure both.
    """
    eng = store._engine
    if not getattr(eng, "CROSS_ENCODER_AVAILABLE", False):
        return None
    original = eng.USE_CROSS_ENCODER
    out = {}
    try:
        for key, flag in (("with", True), ("without", False)):
            eng.USE_CROSS_ENCODER = flag
            # warm=True: the main run has already loaded both models, so this
            # measures the query cost rather than a second cold start.
            r = run(store, modes=("hybrid",), k=k, corpus=corpus, warm=True,
                    compare_rerank=False)
            hb = r.recall.get("hybrid", {})
            out[key] = {
                "p50_ms": r.latency_ms.get("hybrid", {}).get("p50", 0.0),
                "mrr_direct": hb.get("direct", {}).get("mrr", 0.0),
                "mrr_multi_hop": hb.get("multi_hop", {}).get("mrr", 0.0),
                "hit_direct": hb.get("direct", {}).get("hit_rate", 0.0),
                "hit_multi_hop": hb.get("multi_hop", {}).get("hit_rate", 0.0),
            }
    finally:
        eng.USE_CROSS_ENCODER = original
    return out


def _trust_block(store, results: list[QueryResult]) -> dict:
    health = store.health()
    cont = store.contamination()

    vec = health["indexes"].get("vector", {})
    bm = health["indexes"].get("bm25", {})
    graph = health["indexes"].get("graph", {})

    total_indexed = (vec.get("indexed", 0) or 0) + (bm.get("indexed", 0) or 0)
    total_stale = (vec.get("missing_from_ledger", 0) or 0) + \
                  (bm.get("missing_from_ledger", 0) or 0)
    stale_rate = round(total_stale / total_indexed, 6) if total_indexed else 0.0

    # Did retrieval ever admit it was degraded?
    degraded = [r for r in results if r.degraded_to not in (None, "both", "found")]
    reported = [r for r in results if r.drift_healthy is not None]

    return {
        "contamination_rate": cont.get("contamination_rate"),
        "contamination_violations": len(cont.get("violations") or []),
        "simulated_in_bm25": cont.get("violations_simulated_in_bm25_corpus", 0),
        "stale_pointer_rate": stale_rate,
        "stale_pointers": total_stale,
        "indexed_entries": total_indexed,
        "index_healthy": health["healthy"],
        "graph_entities": graph.get("entities", 0),
        "graph_edges": graph.get("edges", 0),
        "degraded_queries": len(degraded),
        "queries_with_drift_diagnostic": len(reported),
        "all_reported_healthy": all(r.drift_healthy for r in reported)
                                 if reported else None,
        "ledger_records": health["ledger_records"],
    }


def _environment(store) -> dict:
    import platform
    import sys
    eng = store._engine
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "store": store.path,
        "vector_available": eng.VECTOR_AVAILABLE,
        "bm25_available": eng.BM25_AVAILABLE,
        "embedding_model": getattr(eng, "EMBEDDING_MODEL", None),
        "embedding_dim": getattr(eng, "EMBEDDING_DIM", None),
        # The model NAME is a constant; it does not say which encoder actually
        # ran. Without sentence-transformers the engine silently falls back to
        # a deterministic hashing embedder, and a report that printed only the
        # constant would imply a neural encoder was used when it was not.
        "embedder_backend": (eng.embedder_backend()
                             if hasattr(eng, "embedder_backend") else None),
        "cross_encoder": bool(getattr(eng, "USE_CROSS_ENCODER", False)),
    }


def render_markdown(report: Report) -> str:
    """Render a report as markdown for the repo and the website."""
    L: list[str] = []
    a = L.append
    a("# mem20 retrieval benchmarks")
    a("")
    a(f"Corpus `{report.corpus}` — {report.facts} grounded facts, "
      f"{report.simulated} simulated facts, {report.queries} queries.")
    a("")

    a("> [!IMPORTANT]")
    a("> **These numbers are not comparable to competitor benchmarks.** "
      "Mem0's LoCoMo and LongMemEval figures and Zep's DMR come from different "
      "corpora — two of the three are private or vendor-defined — and "
      "different metrics. Nothing here refutes or reproduces them. These "
      "results describe this corpus only. No competitor figure is quoted in "
      "this report, by design: a number lifted out of context is exactly how "
      "an incomparable result gets mistaken for a comparable one.")
    a("")
    a("> [!WARNING]")
    a("> **No LoCoMo result is claimed.** This harness has not been run against "
      "the LoCoMo originals (10 conversations, 1,986 QA). No LoCoMo figure "
      "appears in this report and none may be quoted from it. The caveat stays "
      "until a run on the originals lands.")
    a("")

    a("## Retrieval quality")
    a("")
    a("| Mode | Query kind | n | Hit rate | MRR | Leak rate | p50 ms |")
    a("|---|---|---:|---:|---:|---:|---:|")
    for mode, kinds in sorted(report.recall.items()):
        for kind, m in sorted(kinds.items()):
            a(f"| `{mode}` | {kind} | {m['n']} | {m['hit_rate']:.3f} | "
              f"{m['mrr']:.3f} | {m['leak_rate']:.3f} | "
              f"{m['median_latency_ms']:.1f} |")
    a("")

    a("## Latency")
    a("")
    a("| Mode | n | p50 ms | p95 ms | p99 ms | max ms |")
    a("|---|---:|---:|---:|---:|---:|")
    for mode, m in sorted(report.latency_ms.items()):
        a(f"| `{mode}` | {m['n']} | {m['p50']:.1f} | {m['p95']:.1f} | "
          f"{m['p99']:.1f} | {m['max']:.1f} |")
    a("")

    t = report.trust
    a("## Trustworthiness")
    a("")
    a("This is the axis mem20 claims as its differentiator, and the one no "
      "competitor publishes. A system that answers confidently from a stale "
      "index can look good on hit rate and fail here.")
    a("")

    cmp_ = t.get("rerank_off_comparison")
    if cmp_:
        a("### Reranking cost")
        a("")
        a("Cross-encoder reranking is why hybrid is ~10x slower than the vector "
          "half alone. Measured both ways on this corpus:")
        a("")
        a("| Setting | p50 ms | direct MRR | multi-hop MRR |")
        a("|---|---:|---:|---:|")
        for label, key in (("`MEM20_RERANK=1` (default)", "with"),
                           ("`MEM20_RERANK=0`", "without")):
            c = cmp_[key]
            a(f"| {label} | {c['p50_ms']:.1f} | {c['mrr_direct']:.3f} | "
              f"{c['mrr_multi_hop']:.3f} |")
        a("")
        a("Reranking improves direct-query ranking and costs an order of "
          "magnitude in latency. An agent doing many lookups is usually better "
          "off with it off.")
        a("")

    a("| Check | Value | Required |")
    a("|---|---:|---|")
    a(f"| Contamination rate | {t['contamination_rate']} | 0.0 |")
    a(f"| Simulated records in BM25 corpus | {t['simulated_in_bm25']} | 0 |")
    a(f"| Stale pointer rate | {t['stale_pointer_rate']:.6f} | 0.0 |")
    a(f"| Index healthy | {t['index_healthy']} | True |")
    a(f"| Ledger records | {t['ledger_records']} | — |")
    a(f"| Graph entities / edges | {t['graph_entities']} / {t['graph_edges']} | — |")
    a(f"| Queries reporting a diagnostic | "
      f"{t['queries_with_drift_diagnostic']} | — |")
    a(f"| All reported healthy | {t['all_reported_healthy']} | True |")
    a("")

    env = report.environment
    a("## Environment")
    a("")
    a(f"- Python {env['python']} on {env['platform']} ({env['machine']})")
    a(f"- Embedding model: `{env['embedding_model']}` "
      f"({env['embedding_dim']}-dim)")
    backend = env.get("embedder_backend")
    if backend:
        a(f"- Embedder backend actually used: `{backend}`"
          + ("" if backend == "sentence-transformers" else
             " — NOT a neural encoder. The vector and hybrid rows above "
             "measure this backend, not all-MiniLM-L6-v2."))
    a(f"- Vector deps available: {env['vector_available']}; "
      f"BM25: {env['bm25_available']}; cross-encoder: {env['cross_encoder']}")
    a("")

    if report.notes:
        a("## Notes")
        a("")
        for n in report.notes:
            a(f"- {n}")
        a("")

    a("## Reproduce")
    a("")
    a("```bash")
    a("mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2")
    a("mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \\")
    a("    -k 5 --modes bm25,vector,hybrid,hybrid-rerank-off,graph,keyword,\\")
    a("    constant,recall,recall_at,entities,ledger --out benchmarks/results")
    a("```")
    a("")
    a("The run uses an isolated store, ingests the corpus through the engine's "
      "own ledger and index build paths, and never touches live data.")
    return "\n".join(L)


def save(report: Report, out_dir: str | Path) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    j = out / "latest.json"
    j.write_text(json.dumps(report.to_dict(), indent=2, default=str))
    md = out / "latest.md"
    md.write_text(render_markdown(report))
    # The caller prints these paths; returning None made `run-scale` raise
    # TypeError after it had already written both files, so a successful run
    # exited non-zero and looked like a failure.
    return {"json": str(j), "markdown": str(md)}
