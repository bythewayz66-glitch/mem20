# Benchmark results v2 — the adversarial 0.000 explained

Supersedes `mem20-agent-kb-v1` (14 grounded facts, 3 simulated, 13 queries).
Current corpus: **2,000 records** (700 grounded / 650 ungrounded / 650 false),
**250 probes**, seed `20261027`, validator PASS with 0 errors.

## The finding

The previous run reported every adversarial row at exactly 0.000 hit rate across
hybrid, keyword and semantic. That number was not a measurement of the store.
It was produced by two independent mistakes that happened to agree.

1. **The probes were answer-free.** Adversarial queries were constructed with
   `supports=(), expect=()` — "is Zephyra a real city with a mem20 node". No
   record in the corpus could answer one. Given no gold record and no expected
   evidence, 0.000 is the only arithmetic outcome available.
2. **The scorer hardcoded the verdict.** `bench.py` contained
   `if q.kind == "adversarial": hit, rank = False, None`. A store returning the
   exact correct record would still have been scored a miss.

So the old 0.000 answered "can the harness score an adversarial query?" — no —
and said nothing about mem20's retrieval. Both causes are now fixed and both are
covered by a regression check.

## What makes the new class answerable

An adversarial probe must satisfy two conditions, and the validator enforces
both per probe:

- the gold record **is** in the corpus, and the expected evidence string
  appears verbatim in that record's content;
- the expected evidence does **not** appear in the probe text, so the probe is a
  retrieval task rather than an echo.

Difficulty comes from paraphrase, not from removing the answer:

| kind | how it is hard |
|---|---|
| `adversarial` | subject named by a *different designator* — element symbol for element name, alpha-2 for country name |
| `adversarial_hard` | same, plus the relation label replaced by a synonym so the record's own wording is unavailable |
| `contradiction` | a false claim is quoted and the true value requested; the truth is in the corpus |
| `unanswerable` | **control** — fictional subject, nothing in the corpus can answer it, must read 0.000 |

## Measured results

Rendered from `benchmarks/results/latest.json` (the artifact of record).
The full per-kind table with dataset and run-command columns is in
`benchmarks/results/latest.md`.

| mode | kind | n | hit@5 | MRR | leak | p50 ms |
|---|---|---:|---:|---:|---:|---:|
| bm25 | direct | 60 | 1.000 | 1.000 | 0.000 | 101.6 |
| bm25 | adversarial | 60 | 0.767 | 0.592 | 0.000 | 102.0 |
| bm25 | adversarial_hard | 40 | 0.025 | 0.006 | 0.000 | 101.8 |
| bm25 | contradiction | 40 | 0.050 | 0.030 | 0.000 | 195.9 |
| bm25 | multi_hop | 30 | 0.800 | 0.800 | 0.000 | 102.7 |
| bm25 | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 149.7 |
| vector | direct | 60 | 0.900 | 0.864 | 0.000 | 202.0 |
| vector | adversarial | 60 | 0.667 | 0.608 | 0.000 | 203.5 |
| vector | adversarial_hard | 40 | 0.750 | 0.583 | 0.000 | 203.9 |
| vector | contradiction | 40 | 1.000 | 1.000 | 0.000 | 296.0 |
| vector | multi_hop | 30 | 1.000 | 0.950 | 0.000 | 299.6 |
| vector | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 297.1 |
| hybrid | direct | 60 | 1.000 | 0.978 | 0.000 | 1691.0 |
| hybrid | adversarial | 60 | 0.167 | 0.167 | 0.000 | 1694.7 |
| hybrid | adversarial_hard | 40 | 0.050 | 0.050 | 0.000 | 1897.8 |
| hybrid | contradiction | 40 | 1.000 | 0.988 | 0.000 | 1899.2 |
| hybrid | multi_hop | 30 | 0.533 | 0.533 | 0.000 | 1799.0 |
| hybrid | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 2003.1 |
| hybrid-rerank-off | direct | 60 | 1.000 | 0.979 | 0.000 | 77.9 |
| hybrid-rerank-off | adversarial | 60 | 0.650 | 0.633 | 0.000 | 25.4 |
| hybrid-rerank-off | adversarial_hard | 40 | 0.625 | 0.515 | 0.000 | 25.5 |
| hybrid-rerank-off | contradiction | 40 | 1.000 | 0.546 | 0.000 | 25.7 |
| hybrid-rerank-off | multi_hop | 30 | 1.000 | 0.929 | 0.000 | 76.4 |
| hybrid-rerank-off | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 78.6 |
| graph | multi_hop | 30 | 0.033 | 0.033 | 0.000 | 208.5 |
| keyword | direct | 60 | 1.000 | 0.983 | 0.000 | 1399.1 |
| keyword | adversarial | 60 | 0.167 | 0.167 | 0.000 | 1800.1 |
| keyword | adversarial_hard | 40 | 0.025 | 0.006 | 0.000 | 3198.4 |
| keyword | contradiction | 40 | 0.125 | 0.108 | 0.000 | 2102.3 |
| keyword | multi_hop | 30 | 0.467 | 0.467 | 0.000 | 380.4 |
| keyword | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 895.9 |
| constant | direct | 60 | 0.000 | 0.000 | 0.000 | 0.0 |
| constant | adversarial | 60 | 0.000 | 0.000 | 0.000 | 0.0 |
| constant | adversarial_hard | 40 | 0.000 | 0.000 | 0.000 | 0.0 |
| constant | contradiction | 40 | 0.000 | 0.000 | 0.000 | 0.0 |
| constant | multi_hop | 30 | 0.000 | 0.000 | 0.000 | 0.0 |
| constant | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 0.0 |

Trust: contamination 0.0, stale pointers 0.0, leak 0.000 in every row, all trust
checks pass.

## What the remaining zeros mean

Two rows are now genuinely informative rather than artifacts.

**keyword / adversarial_hard = 0.025 against vector 0.750.** The class is
provably answerable — 230 answerable probes pass the validator, including these.
BM25 fails them because the probe carries neither the subject's canonical name
nor the record's relation wording; its only handle is a designator token that is
not the highest-TF term in the record. The dense retriever recovers 75%. This is
the cleanest evidence in the suite that the lexical half alone cannot carry
paraphrase, and it is a *retrieval* finding, not a corpus gap.

**keyword / contradiction = 0.125 against vector 1.000.** A false record
shares its subject and predicate with the true one and differs in a single
value, so BM25 ranks the record restating the claim above the record correcting
it.

**unanswerable = 0.000 in every mode** is the control. It is what distinguishes
a real zero from a broken metric: a scorer handing out free hits would show up
here first. `constant` reads 0.000 on every kind for the same reason — it is the
adversarial control retriever.

## Reproduce

```bash
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
mem20benchmarkz validate-scale /tmp/mem20-scale-corpus-v2
mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \
    --modes bm25,vector,hybrid,hybrid-rerank-off,graph,keyword,constant \
    --out benchmarks/results
```

Corpus is deterministic: `records.jsonl` sha256
`28f0746be240d216ea5368eeb0babba666e90c05a67f98f32d546369dfc2dbd3`.

## Not comparable

These figures describe this corpus only. Mem0's LoCoMo (92.5), LongMemEval
(94.4) and Zep's DMR (94.8%) use different corpora — two of the three private or
vendor-defined — and different metrics. Nothing here refutes or reproduces them.
