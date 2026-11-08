## 4. Social threads

### 4.1 X / Twitter (7 posts)

```
1/ Most agent memory systems compete on retrieval quality. Almost none let you
prove what the agent actually knows. That's the gap mem20 fills. 🧵
```

```
2/ mem20 keeps grounded memory (came from a real source) and simulated memory
(the agent made it up) in SEPARATE STORES. Not one table with an is_fake column.
Two stores, two write paths.
```

```
3/ Try to push invented content through the grounded path and the server refuses:

PermissionError: remember() is grounded-only. Simulated content must use
remember_simulated(); this call is refused to protect Step 7.4 separation.

That's the shipped exception string. The guard is on the write path, not in a
prompt.
```

```
4/ Every write must declare HOW it was learned: observed, inferred, imagined,
user_stated, hypothesis, agent_generated, unlabeled. Unlabeled writes are
refused. No more facts nobody can vouch for.
```

```
5/ Promotion from simulated → grounded needs evidence: a recorded prior
prediction that resolved in its favour, or a registered external verifier.
Append-only ledger, origin and store on every entry.
```

```
6/ Now the honest part. Our benchmark, 250 queries:

direct recall: 1.000 (bm25, hybrid, keyword)
multi-hop: 0.033 (graph) → 1.000 (vector)
unanswerable: 0.000 in EVERY mode, n=20

We have no working answer for "I don't know" yet. Published anyway.
```

```
7/ 311 tools · 39 domains · MIT · Python 3.10+ · self-hosted ·
JSON-RPC 2.0 over stdio. Source install only, no PyPI.

https://github.com/bythewayz66-glitch/mem20
https://mem20.com/
```

### 4.2 LinkedIn (1 post)

```
Most AI agent memory systems are optimised for one thing: returning something
relevant. Very few are built so you can prove what the agent actually knows.

mem20 takes the other bet. Grounded memory — content that came from a real source
— and simulated memory — content the agent generated — live in separate stores
with separate write paths. Attempting to write invented content through the
grounded path raises PermissionError. Every write must declare its origin
(observed, inferred, imagined, user_stated, hypothesis, agent_generated), and
promotion from simulated to grounded requires recorded evidence.

The result is an auditable store: an append-only ledger with origin and store on
every entry, a contamination audit that reports a rate and names the violations,
and 0.0 contamination across 700 records with 0 degraded queries out of 250.

It is also not the strongest retrieval system on the market, and we publish the
numbers that show it. Direct recall is 1.000 on three of six modes; multi-hop
ranges from 0.033 to 1.000; unanswerable questions score 0.000 in every mode. A
memory layer that cannot say "I don't know" is a confabulation engine with a
database attached, and we are not there yet.

311 tools, 39 domains, MIT, Python 3.10+, self-hosted, MCP over stdio.
Source install only.

https://github.com/bythewayz66-glitch/mem20
```

### 4.3 Reddit — r/LocalLLaMA

**Title:** `mem20: an MCP memory server where grounded vs simulated is enforced in code, not in a prompt`

```
I kept running into the same problem with agent memory: everything optimises for
retrieval, nothing lets you audit provenance. If your agent invents a fact and
stores it next to real ones, you find out in production.

mem20 splits the store. Grounded memory (real source) and simulated memory (agent
generated) are separate, with separate write paths. The grounded path raises
PermissionError on invented content — that's the shipped exception string, not a
description of one. Every write declares its origin, and promotion from simulated
to grounded needs recorded evidence.

Self-hosted, MIT, Python 3.10+, MCP over stdio, 311 tools across 39 domains.
Source install only (no PyPI package).

Benchmark, all of it, 250 queries over 700 grounded / 1,300 simulated facts:

  mode                direct      multi-hop   adversarial  adv-hard    contradiction  unanswerable
  bm25                1.000 (60)  0.800 (30)  0.767 (60)   0.025 (40)  0.050 (40)     0.000 (20)
  vector              0.900 (60)  1.000 (30)  0.667 (60)   0.750 (40)  1.000 (40)     0.000 (20)
  hybrid              1.000 (60)  0.533 (30)  0.167 (60)   0.050 (40)  1.000 (40)     0.000 (20)
  hybrid-rerank-off   1.000 (60)  1.000 (30)  0.650 (60)   0.625 (40)  1.000 (40)     0.000 (20)
  keyword             1.000 (60)  0.467 (30)  0.167 (60)   0.025 (40)  0.125 (40)     0.000 (20)
  graph                 —          0.033 (30)    —            —           —              —

The unanswerable row is the one I care about: 0.000 everywhere. We don't have a
working "I don't know" yet. Happy to hear how others are handling abstention.

https://github.com/bythewayz66-glitch/mem20
```

### 4.4 Reddit — r/MachineLearning

**Title:** `[P] mem20: provenance-enforced agent memory — full benchmark published, including the abstention failure`

```
Sharing a memory substrate we've been building, mostly because the evaluation is
the interesting part.

Design: grounded and simulated memory are separate stores with separate write
paths. The grounded path refuses invented content at the storage layer
(PermissionError, not a prompt instruction). Every write carries a declared origin
and lands in an append-only ledger. Promotion simulated → grounded requires
recorded evidence.

Evaluation: 250 queries over 700 grounded / 1,300 simulated facts, six retrieval
modes, six query classes. Full table in the repo at
benchmarks/results/latest.json.

Headline findings, stated plainly:
- Direct recall saturates: 1.000 on bm25, hybrid, keyword.
- Multi-hop is the weak axis and it is mode-dependent: 0.033 (graph) to 1.000
  (vector, hybrid-rerank-off).
- Abstention fails completely: unanswerable 0.000 in every mode, n=20.
- Trust properties hold: contamination_rate 0.0 over 700 ledger records, 0
  degraded queries out of 250, 654 entities / 3,601 edges.

We are not claiming retrieval superiority. We are claiming the partition is
auditable and reproducible. Critique welcome, especially on the abstention gap.

https://github.com/bythewayz66-glitch/mem20
```

### 4.5 Reddit — r/opensource

**Title:** `mem20 — MIT agent memory server with a provenance ledger (311 tools, MCP, self-hosted)`

```
mem20 is an MIT-licensed MCP memory server for AI agents. The differentiator is
provenance: grounded memory and simulated memory are separate stores, the grounded
write path refuses invented content, and every entry carries its origin in an
append-only ledger.

- 311 tools across 39 domains
- Python 3.10+, JSON-RPC 2.0 over stdio
- Self-hosted, no account, no telemetry requirement
- Source install only — there is no PyPI package, and we say so rather than
  letting people find out from a 404

We publish the benchmark including the parts that don't flatter us: unanswerable
questions score 0.000 in every retrieval mode. Details in the repo.

https://github.com/bythewayz66-glitch/mem20
```

---

