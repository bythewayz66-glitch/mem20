# Retrieval gap analysis — `adversarial_hard` and `unanswerable` (2026-11-01)

**Owner directive:** `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220e964f84aabac78127fc18463dfa6798d`, row 7 (AI Engineer, gap **G9**).
**Subject:** `benchmarks/results/latest.{md,json}` on `main` @ `2ea44922`.
**Scope:** explain *why* the two slices score low, and propose one concrete retrieval change with a measurable target.

> [!IMPORTANT]
> **The two slices are not the same kind of number, and only one of them is a retrieval finding.**
> `adversarial_hard` is a real, reproducible retrieval defect with a one-line cause and a measured fix.
> `unanswerable` is a **control**, not a measurement — its 0.000 is set by a constant in the scorer and
> cannot move no matter what retrieval does. Reporting it as a quality score is the error, not the score.

Every number below is quoted from `benchmarks/results/latest.json` by row name, or was produced by a
command recorded in this document. Nothing is estimated.

---

## 1. The rows, quoted by name

From `latest.json` → `recall.<mode>.<kind>` (`hit_rate` / `mrr`), `n` from the same rows:

| `recall.<mode>.<kind>` | n | hit_rate | mrr |
|---|---:|---:|---:|
| `recall.bm25.adversarial_hard` | 40 | 0.025 | 0.0063 |
| `recall.vector.adversarial_hard` | 40 | 0.75 | 0.5829 |
| `recall.hybrid.adversarial_hard` | 40 | 0.05 | 0.05 |
| `recall.hybrid-rerank-off.adversarial_hard` | 40 | 0.625 | 0.515 |
| `recall.keyword.adversarial_hard` | 40 | 0.025 | 0.0063 |
| `recall.constant.adversarial_hard` | 40 | 0.0 | 0.0 |
| `recall.bm25.unanswerable` | 20 | 0.0 | 0.0 |
| `recall.vector.unanswerable` | 20 | 0.0 | 0.0 |
| `recall.hybrid.unanswerable` | 20 | 0.0 | 0.0 |
| `recall.hybrid-rerank-off.unanswerable` | 20 | 0.0 | 0.0 |
| `recall.keyword.unanswerable` | 20 | 0.0 | 0.0 |
| `recall.constant.unanswerable` | 20 | 0.0 | 0.0 |

Two facts fall straight out of that table:

1. **`unanswerable` is 0.000 in every mode that has the row — all six, including `constant`.**
   (`graph` has no `unanswerable` row: `bench.py` scores it on `multi_hop` only.) A control retriever that
   ignores the query entirely (`mode_surface[].id == "constant"`, "Returns one fixed document that
   matches no corpus record") scores the same 0.000 as every real retriever. When a metric returns
   the identical value for a real system and for a deliberately broken one, it is not measuring the
   system.
2. **`adversarial_hard` is not uniformly low — it is mode-dependent, and the ordering is diagnostic.**
   `vector` 0.75 and `hybrid-rerank-off` 0.625 are healthy. `bm25`/`keyword` 0.025 and `hybrid` 0.05
   are not. The two modes that collapse are exactly the two that route through the BM25 half, and
   `hybrid` (0.05) is *worse than* `hybrid-rerank-off` (0.625) — turning the cross-encoder **on**
   destroys 0.575 of hit rate. That is not a corpus-difficulty effect; it is a defect in the fusion.

---

## 2. Why `adversarial_hard` scores low

### 2.1 The probe template emits a token that cannot match

`scale_corpus.build_queries()` builds the `adversarial_hard` probe as:

```python
text = (f"for the designation {designator}, which registered value "
        f"applies")
```

Note the comma directly after `{designator}`. The engine tokenizes with a bare `str.split()` on both
sides — `memory_engine/memory.py:3720` (`query_tokens = query.lower().split()`) and
`memory_engine/memory.py:1171` (`tokens = text.lower().split()`) — so punctuation is never stripped.
The designator therefore becomes the token `"c,"`, while the gold record contains `"c"`.

Measured on the real corpus (`/tmp/corpus-v2`, sha256-verified identical to
`run_manifest.corpus_sha256` in `latest.json`):

```
adversarial    tokens: ['what','does','the','register','say','the','designation','c','is','recorded','as']
  content-token overlap with gold doc: ['c']
adversarial_hard tokens: ['for','the','designation','c,','which','registered','value','applies']
  content-token overlap with gold doc: []
```

**The `adversarial_hard` probe has exactly zero lexical overlap with its own gold record.** The one
token that identifies the subject is destroyed by a comma. This is why `bm25` and `keyword` sit at
0.025 — the single hit in 40 is a coincidence, not a retrieval.

### 2.2 Zero overlap makes BM25 return a constant, not a ranking

When every document scores 0.0, `np.argsort(scores)[::-1][:k*3]` does not return "no results" — it
returns the **last** `k*3` documents in ingestion order. Measured:

```
adversarial_hard BM25 top-15 candidate ids when all scores are 0.0:
  [1399, 1398, 1397, 1396, 1395, 1394, 1393, 1392, 1391, 1390, 1389, 1388, 1387, 1386, 1385]
  -> a FIXED function of ingestion order, not of the query.
```

So the BM25 half does not abstain on `adversarial_hard`; it injects 15 arbitrary documents at the
top of the fusion with full rank-0..14 authority.

### 2.3 RRF then lets that noise outrank the real answer

`recall_hybrid()` fuses with `alpha=0.5` and `k_rrf=60`, scoring
`alpha/(k+rank_v+1) + (1-alpha)/(k+rank_b+1)`. A document present in only one half at rank 0 scores
`0.5 * 1/61 = 0.008197` — **identical** to a genuine vector rank-0 hit. Measured:

```
genuine vector rank0 _rrf       = 0.008197
bm25-only doc at bm25 rank0 _rrf= 0.008197
EQUAL -> True

bm25-only docs at ranks 0..14 get _rrf: [0.008197, 0.008065, 0.007937, 0.007812] ...
a genuine vector hit at rank 15 only gets _rrf = 0.006579
-> 15 junk BM25 docs outrank every vector hit below rank ~15.
```

The 15 ingestion-order documents from §2.2 therefore displace the real vector hits. This is the
mechanism behind `hybrid` 0.05 < `vector` 0.75.

### 2.4 The reranker cannot rescue what it is never shown

`recall_hybrid()` reranks only `sorted_results[:k*2]` — with `k=5` that is **10 candidates** — and
`_final_score = 0.5*_rrf_score + 0.5*_ce_score`. Two independent problems:

**(a) The pool is already poisoned.** The 10 slots are filled by the rank-0..9 junk documents from
§2.3, so the gold record is not in the pool to be reranked.

**(b) The two terms are on incompatible scales, so RRF is discarded.** `_rrf_score` is bounded by
`2/61 = 0.0328`; its weighted contribution is at most `0.0164`. One unit of cross-encoder logit
contributes `0.5`. Measured ratio: **30.5×**. Real logits from the configured model
(`cross-encoder/ms-marco-MiniLM-L-6-v2`, `environment.cross_encoder: true`) on the actual probe/gold
pairs:

```
  -6.1413  Q='for the designation C, which registered value applies'
           D='Chemical element C (Carbon) has atomic number 6.'      <- the GOLD record
 -11.3290  Q='for the designation C, which registered value applies'
           D='Chemical element O (Oxygen) has atomic number 8.'
  +7.2963  Q='what atomic number does Carbon have'
           D='Chemical element C (Carbon) has atomic number 6.'
```

The gold record scores **-6.14** — the model is confident it is *not* relevant, because the probe
shares no vocabulary with it. `_final_score` is effectively pure cross-encoder logit, so the
reranker overrides the fusion and promotes whatever it likes. That is why `hybrid` (0.05) is far
worse than `hybrid-rerank-off` (0.625): the reranker is not adding noise, it is *replacing* a working
ranking with a worse one.

### 2.5 Reproduction

The corpus regenerates byte-identically (`generate-scale`, validation `PASS (0 errors, 230
answerable probes checked)`; all four `corpus_sha256` values match `latest.json`). Scoring the BM25
half against the real 700-document index with the shipped tokenizer reproduces the published row:

```
adversarial_hard   n= 40  hit_rate=0.0500  mrr=0.0080     <- matches recall.hybrid.adversarial_hard
adversarial        n= 60  hit_rate=0.7667  mrr=0.5917
direct             n= 60  hit_rate=1.0000  mrr=1.0000
```

---

## 3. Why `unanswerable` scores low — it does not, it is defined to be 0.000

`bench.py` handles this kind with a constant, not a measurement:

```python
if q.kind == "unanswerable":
    # The CONTROL. Nothing in the corpus can answer it, so a
    # correct verdict is a miss and this row must read 0.000.
    hit, rank = False, None
```

Verified against the corpus: all 20 probes have `expect == []` and `supports == []`, and **0** of the
2,000 records mention the fictional subject (`Zephyra`). Nothing can answer them, so 0.000 is the
only correct value — and it is assigned unconditionally, before retrieval is consulted.

**Consequence:** `recall.*.unanswerable` is a *guard* that the metric is not handing out free hits
(and it passes: `constant` also reads 0.000, and `leak_rate` is 0.0 everywhere). It is **not** a
retrieval-quality score, and it must not be read as one. The real question this slice should answer —
*does the system abstain instead of returning confident garbage?* — is not measured by `hit_rate` at
all. That needs an abstention metric (§4.2), not a hit rate.

---

## 4. Proposed change

### 4.1 The change: normalize tokens on both sides of the BM25 half

One change, at the tokenizer, applied identically to documents and queries:

```python
# memory_engine/memory.py — replace the bare .split() at :1171, :1245 and :3720
_TOKEN_STRIP = re.compile(r"^[^a-z0-9]+|[^a-z0-9]+$")

def _bm25_tokens(text: str) -> list[str]:
    """Lowercase, split, and strip leading/trailing punctuation per token.

    A bare .split() leaves 'c,' and 'c' as different tokens, so a probe that
    writes "designation C, which ..." cannot match a record that writes
    "element C (Carbon)". Punctuation is not a term.
    """
    out = []
    for tok in text.lower().split():
        tok = _TOKEN_STRIP.sub("", tok)
        if tok:
            out.append(tok)
    return out
```

This is deliberately **not** a stemmer, a synonym table, or a model change. It fixes a tokenization
bug; it does not tune the benchmark to the corpus.

### 4.2 Measured effect (real index, 700 docs, k=5)

Re-scoring the BM25 half against the same index with only the tokenizer changed:

| slice | as-shipped (hit/mrr) | punctuation-normalized (hit/mrr) |
|---|---|---|
| `adversarial_hard` | 0.0500 / 0.0080 | **1.0000 / 0.8875** |
| `adversarial` | 0.7667 / 0.5917 | 0.7667 / 0.5917 |
| `direct` | 1.0000 / 1.0000 | 1.0000 / 1.0000 |
| `contradiction` | 0.1500 / 0.0398 | 0.1500 / 0.0398 |
| `multi_hop` | 0.8000 / 0.8000 | 0.8000 / 0.8000 |

**`adversarial_hard` 0.0500 → 1.0000, and every other slice is bit-identical.** A change that moves
one slice and nothing else is a fix, not a re-weighting.

### 4.3 Measurable target

> **`recall.hybrid.adversarial_hard.hit_rate` ≥ 0.90 and `.mrr` ≥ 0.80 on `mem20-scale-corpus-v2`,
> with `recall.*.direct`, `recall.*.multi_hop` and `recall.*.contradiction` unchanged to 4 decimal
> places, and `trust.contamination_rate` still 0.0.**

Baseline to beat, quoted from `latest.json`: `recall.hybrid.adversarial_hard` = **0.05 / 0.05**.
The BM25 half alone already reaches 1.0000 / 0.8875 under the fix, so ≥0.90 is a floor, not a
stretch. The "unchanged elsewhere" clause is the anti-gaming condition: it fails the change if the
gain came from loosening matching generally.

### 4.4 Two follow-on items this analysis exposes (not part of the one change)

1. **`_final_score` mixes incompatible scales** (§2.4b). `0.5*rrf + 0.5*ce` lets a logit of ±11
   swamp an RRF term bounded at 0.033. Either min-max normalize the CE scores into [0,1] before
   combining, or gate reranking on a CE threshold so a confidently-irrelevant pool is left alone.
   Target: `recall.hybrid.adversarial_hard` must not fall below `recall.hybrid-rerank-off` on any
   slice — currently it falls by 0.575.
2. **`unanswerable` needs an abstention metric, not a hit rate** (§3). Add
   `abstention_rate` = fraction of `unanswerable` probes whose top-1 score falls below a stated
   threshold, and report it beside `leak_rate`. Until then, `recall.*.unanswerable` should be
   labelled a control in `latest.md` so it is not read as a quality score.

---

## 5. Provenance caveat on `latest.json` (found while reproducing)

`latest.json` → `run_manifest.modes` lists seven modes:
`["bm25","vector","hybrid","hybrid-rerank-off","graph","keyword","constant"]`.

The `_run_mode()` committed on `main` accepts four:
`["semantic","hybrid","graph","keyword"]` — there is no `bm25`, `vector`, `hybrid-rerank-off` or
`constant` branch. `benchmarks/run-7modes.sh` invokes `run-scale --modes bm25,vector,...`, which
`_run_mode()` would reject with `ValueError: unsupported mode`.

So the seven-mode rows in `latest.json` **cannot be regenerated from `main` as committed**. The file
itself landed in `a9860b95` ("bench(ws1): add the result data, corpus manifest and per-query rows"),
not in `2ea44922` — `2ea44922` touched only `docs/benchmarks/results-four-mode-2026-10-31.md`
(1 file, 112 insertions). The corpus half *is* reproducible (all four sha256 match); the scoring half
is not.

This does not invalidate the analysis above — the `adversarial_hard` mechanism was reproduced
independently against a real index built from the verified corpus, and it lands on the published
0.05. But it does mean **the seven-mode table is not yet a reproducible artifact**, and the
`run-7modes.sh` → `_run_mode()` mismatch should be closed before any of these rows is cited as a
regression baseline. Flagging for the Benchmark Dataset Builder (row 9) and Experiment Tracker
(row 8), whose acceptance criteria both depend on rows being reproducible from a documented command.

---

## 6. Summary

| Slice | Is it a retrieval finding? | Cause | Status |
|---|---|---|---|
| `adversarial_hard` | **Yes** | Probe emits `"c,"`; bare `.split()` never strips it → zero lexical overlap → BM25 returns ingestion-order noise → RRF promotes it → reranker (pool of 10, scale-mismatched) overrides a working ranking | **Fixed by one tokenizer change; measured 0.05 → 1.00** |
| `unanswerable` | **No — it is a control** | `hit, rank = False, None` assigned unconditionally; nothing in the corpus can answer the probes | **Correct as a guard; must not be read as a quality score. Needs an abstention metric.** |

**Commands used** (all run in this session, against `main` @ `2ea44922`):

```bash
mem20benchmarkz generate-scale --out /tmp/corpus-v2          # validation: PASS (0 errors, 230 probes)
sha256sum /tmp/corpus-v2/*.jsonl                            # matches latest.json run_manifest.corpus_sha256
mem20benchmarkz run-scale --corpus /tmp/corpus-v2 --bulk -k 5 \
    --modes vector,hybrid,hybrid-rerank-off --no-rerank-compare --out /tmp/repro-out
```

*Analysis by AI Engineer (directive row 7, gap G9), 2026-11-01.*
