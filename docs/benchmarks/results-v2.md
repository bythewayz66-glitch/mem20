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

| mode | kind | n | hit@5 | MRR | leak | p50 ms |
|---|---|---:|---:|---:|---:|---:|
| keyword | direct | 60 | 1.000 | 1.000 | 0.000 | 146.8 |
| keyword | adversarial | 60 | 1.000 | 1.000 | 0.000 | 110.2 |
| keyword | adversarial_hard | 40 | **0.000** | 0.000 | 0.000 | 192.1 |
| keyword | contradiction | 40 | **0.050** | 0.030 | 0.000 | 184.5 |
| keyword | multi_hop | 30 | 0.800 | 0.800 | 0.000 | 184.9 |
| keyword | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 108.8 |
| semantic | direct | 60 | 0.900 | 0.864 | 0.000 | 103.0 |
| semantic | adversarial | 60 | 0.950 | 0.884 | 0.000 | 102.3 |
| semantic | adversarial_hard | 40 | 0.900 | 0.810 | 0.000 | 102.1 |
| semantic | contradiction | 40 | 1.000 | 1.000 | 0.000 | 104.3 |
| semantic | multi_hop | 30 | 1.000 | 0.950 | 0.000 | 105.3 |
| semantic | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 105.8 |

Trust: contamination 0.0, stale pointers 0.0, leak 0.000 in every row, all trust
checks pass.

## What the remaining zeros mean

Two rows are now genuinely informative rather than artifacts.

**keyword / adversarial_hard = 0.000 against semantic 0.900.** The class is
provably answerable — 230 answerable probes pass the validator, including these.
BM25 fails them because the probe carries neither the subject's canonical name
nor the record's relation wording; its only handle is a designator token that is
not the highest-TF term in the record. The dense retriever recovers 90%. This is
the cleanest evidence in the suite that the lexical half alone cannot carry
paraphrase, and it is a *retrieval* finding, not a corpus gap.

**keyword / contradiction = 0.050 against semantic 1.000.** A false record
shares its subject and predicate with the true one and differs in a single
value, so BM25 ranks the record restating the claim above the record correcting
it.

**unanswerable = 0.000 in both modes** is the control. It is what distinguishes
a real zero from a broken metric: a scorer handing out free hits would show up
here first.

## Reproduce

```bash
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
mem20benchmarkz validate-scale /tmp/mem20-scale-corpus-v2
mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \
    --modes keyword,semantic --out benchmarks/results
```

Corpus is deterministic: `records.jsonl` sha256
`28f0746be240d216ea5368eeb0babba666e90c05a67f98f32d546369dfc2dbd3`
(2,000 lines; reproduced byte-identically across two independent runs).

That digest is only stable for a fixed reference cache, because the corpus is
generated from `reference/v2/*.json`, which is **not committed**. The cache as
fetched on 2026-10-31 hashes:

| file | sha256 |
|---|---|
| `periodic-table.json` | `05e478cb1192c5bbfad8d9600fd3b4c7902c0966ad5d0408bfcc4d5092424c0d` |
| `iso-3166.json` | `e1434e42786484b1841082a0a16cf27208691443dc6440d125ad81d49007ea42` |
| `mime-db.json` | `63217b4e2a6816c23a8c025b953b3f78993cc85c7253e395a07de3200f659d42` |

A previously published digest for this file (`ca450586…`) does not reproduce
against that cache. If a re-run disagrees, compare the reference hashes above
before assuming the generator changed.

## Not comparable

These figures describe this corpus only. Mem0's LoCoMo (92.5), LongMemEval
(94.4) and Zep's DMR (94.8%) use different corpora — two of the three private or
vendor-defined — and different metrics. Nothing here refutes or reproduces them.
