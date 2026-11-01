# mem20 — Launch Copy Pack (v5)

**Prepared by:** Mem20 Content Creator · **Seat:** Brand & Positioning Strategist
**Supersedes:** Launch Copy Pack v4 (`docs/gtm/mem20-launch-copy.md`, retained in place as the retired reference)
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20 · **Branch read:** `main` · **HEAD:** `d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110`
**Version:** `VERSION` = **3.1.2** · **License:** MIT · **Python:** >=3.10 · **Protocol:** MCP `2025-06-18`
**Canonical public URL:** https://mem20.com/ · **Verified:** 2026-11-01 · **Audit:** `python3 docs/gtm/audit-launch-copy.py` → exit 0

> **What changed from v4, and why it had to change.**
>
> **1. The adversarial claim inverted, and v4 was still shipping the old one.** v4 said adversarial scored 0.000 in hybrid, keyword *and* semantic. On the shipped benchmark (`benchmarks/results/latest.json`, corpus `mem20-scale-corpus-v2`, 700 grounded / 1,300 simulated / 250 queries) that is false: hybrid **0.167** (n=60), keyword **0.167** (n=60), vector **0.667** (n=60). The old figure came from a 13-query corpus that no longer exists in the repo. **The real universal hole is `unanswerable`: 0.000 in every mode, n=20.** That is the number this pack leads with, because it is the one that is still true and still uncomfortable.
>
> **2. The surface is 272 tools, not 270.** A live MCP handshake at this HEAD returns `TOOL_COUNT: 272` with `RESULT: PASS` against `MEM20_EXPECTED_TOOLS=272` (pinned in `.github/workflows/mcp-verify.yml`). 270 was correct at an earlier HEAD and is now the retired value. The 28 `register_*_tools` groups are what the code exposes; "27 domains" is an editorial subtraction performed by `docs/TOOL-DOMAINS.md`, not a property the server reports — so this pack says **28 registration groups** and does not present a domain count as a measured fact.
>
> **3. The install line works again, with no extra step.** v4 had to add a manual `aiohttp` install because the A2A module imported it at module scope while the manifest omitted it. At this HEAD `requirements.txt` pins eight packages including `aiohttp>=3.14.5` and `mcp-types>=2.3.0`, and a clean install boots. The workaround is gone from every asset below.
>
> **4. The version is a contradiction inside the repo, and copy must not paper over it.** `VERSION` = **3.1.2**; `pyproject.toml` still declares the retired **3.0.0**. Assets quote **3.1.2** (what `main` carries) and name the packaging defect rather than hiding it.
>
> **5. The public page is one release behind the code.** https://mem20.com/ returns 200 and prints **v3.1.0** four times and **270 tools** eight times. The code says 3.1.2 / 272. That drift is a live defect, disclosed in §7, not a number to copy into launch copy.
>
> **6. PyPI is still not a thing.** `mem20`, `mem20-ai` and `mem20oreo` all return 404 on pypi.org. Install is source-only, and no asset may imply otherwise.

---

## 0. How to use this pack

- Sections 1–6 are the assets, written to paste as-is.
- Section 7 is the **claim ledger index** — a number not listed there does not ship.
- Section 8 is the **guardrail list**, binding on every public asset.
- Section 9 is the **hand-off and open defects**.
- **The wedge is unchanged:** *mem20 is the memory substrate for agents that must not confabulate — grounded vs simulated is a hard, audited boundary, not a prompt convention.*

**The one rule that governs every asset below:** the pitch is about provenance and auditability, which the repo demonstrates in code. It is **not** about retrieval superiority, which the repo's own benchmark does not demonstrate. Say the first thing loudly. Say the second thing exactly as measured, caveat attached.

---

## 1. The one-liner (use everywhere)

> **mem20 gives AI agents persistent memory — with a hard, storage-level partition between what the agent actually knows and what it made up.**

Short alt (nav bars, meta descriptions, social bios):
> Auditable agent memory. Grounded vs simulated, enforced at the storage layer — not asked for in a prompt.

Feature line (pairs with either of the above; never used as a strength claim on its own):
> 272 tools across 28 registration groups · MIT · Python 3.10+ · self-hosted · JSON-RPC 2.0 over stdio

---

## 2. Show HN post

**Title (74 chars)**

```
Show HN: mem20 – Agent memory where grounded vs simulated is enforced in code
```

Alt titles:
```
Show HN: mem20 – An MCP memory server that refuses to store made-up facts as real
Show HN: mem20 – MIT agent memory with contamination auditing and a provenance ledger
```

**Body**

```
Hi HN — mem20 is an MCP server that gives AI agents persistent memory with an
audit trail. 272 tools across 28 registration groups, MIT, Python 3.10+,
self-hosted.

Every agent-memory layer I looked at competes on retrieval quality. None of them
let you *prove* what the agent knows. In a regulated context that's the whole
ballgame: "probably relevant" is not an answer you can hand an auditor.

So mem20 is built around a hard boundary. Grounded memory (came from a real
source) and simulated memory (the agent generated it) are separate stores, not
one store with a flag. Try to push invented content through the grounded write
path and the server refuses:

    PermissionError: remember() is grounded-only. Simulated content must use
    remember_simulated(); this call is refused to protect Step 7.4 separation.

That's the real exception string from the shipped code. The guard isn't a prompt
instruction or a lint rule — it sits on the write path. It also refuses an
unlabeled write outright: you have to declare HOW you learned something
(observed / inferred / imagined / user_stated / hypothesis / agent_generated /
unlabeled) before it goes in. No more storing facts nobody can vouch for.

What's in it:

- MCP server, JSON-RPC 2.0 over stdio. Python 3.10+. MIT.
- 272 tools across 28 registration groups. (If you remember a smaller number,
  it was a real count at an earlier commit — the surface has grown.)
- Separate grounded and simulated stores. recall() returns grounded only by
  default; you have to ask for simulated.
- Contamination auditing — reports a contamination_rate for your store and lists
  what violated the partition, across six violation classes. A clean store
  reports 0.0 and CLEAN.
- Promotion from simulated to grounded goes through a gate that wants evidence:
  a recorded prior prediction that resolved in its favour, or a registered
  external verifier.
- An append-only ledger where every entry carries its origin and store.

Install (source only — there is no PyPI package; mem20, mem20-ai and mem20oreo
all 404):

    git clone https://github.com/bythewayz66-glitch/mem20.git
    cd mem20
    pip install -r requirements.txt
    python mcp/mcp_server.py

Site: https://mem20.com/

Now the part that matters more than the feature list. Here is our whole
retrieval benchmark, every row, including the ones that make us look bad. It's
a 250-query corpus over 700 grounded and 1,300 simulated facts. Hit rate, with
n in parentheses:

    mode                direct      multi-hop   adversarial  adv-hard    contradiction  unanswerable
    bm25                1.000 (60)  0.800 (30)  0.767 (60)   0.025 (40)  0.050 (40)     0.000 (20)
    vector              0.900 (60)  1.000 (30)  0.667 (60)   0.750 (40)  1.000 (40)     0.000 (20)
    hybrid              1.000 (60)  0.533 (30)  0.167 (60)   0.050 (40)  1.000 (40)     0.000 (20)
    hybrid-rerank-off   1.000 (60)  1.000 (30)  0.650 (60)   0.625 (40)  1.000 (40)     0.000 (20)
    keyword             1.000 (60)  0.467 (30)  0.167 (60)   0.025 (40)  0.125 (40)     0.000 (20)
    graph                 —          0.033 (30)    —            —           —              —

Read that honestly and it says: we are good at direct recall, mediocre at
multi-hop, and we have no working answer for questions the store cannot answer.
Unanswerable is 0.000 in every single mode, n=20. A memory system that cannot
say "I don't know" is a confabulation engine with a database attached, and ours
is not there yet. We publish it because a benchmark you only show when it flatters
you isn't a benchmark.

What we do claim: the partition holds. contamination_rate 0.0 across 700 ledger
records, 0 degraded queries out of 250, 654 graph entities and 3,601 edges
indexed. Those are auditable properties of the store, not retrieval scores.

Repo: https://github.com/bythewayz66-glitch/mem20
```

---

## 3. Product Hunt post

**Tagline (60 chars)**

```
Agent memory that refuses to store made-up facts as real
```

**Description**

```
mem20 is an MCP memory server for AI agents with a hard, storage-level partition
between grounded memory (came from a real source) and simulated memory (the agent
generated it). Not a flag on a row — two stores, and the grounded write path
raises PermissionError if you try to push invented content through it.

Every write must declare its origin: observed, inferred, imagined, user_stated,
hypothesis, agent_generated, or unlabeled. Promotion from simulated to grounded
goes through an evidence gate. An append-only ledger records origin and store for
every entry, and a contamination audit reports a rate plus the specific
violations across six classes.

272 tools across 28 registration groups. MIT. Python 3.10+. Self-hosted, JSON-RPC
2.0 over stdio. Source install only — there is no PyPI package.

We also publish the benchmark that makes us look bad: unanswerable questions score
0.000 in every retrieval mode. We'd rather you know that before you deploy us than
after.
```

**First comment (maker comment)**

```
Maker here. The thing I'd want to know before trying this: what does it actually
get wrong?

Answer: questions the store cannot answer. Our benchmark has 20 of them and every
retrieval mode scores 0.000. Direct recall is 1.000 on bm25, hybrid and keyword;
multi-hop ranges from 0.033 (graph) to 1.000 (vector, hybrid-rerank-off). The
spread is real and we publish all of it in benchmarks/results/latest.json.

What we do stand behind is the partition. Grounded and simulated are separate
stores. The grounded write path raises PermissionError on invented content. Every
entry carries its origin in an append-only ledger. contamination_rate is 0.0
across 700 records with 0 degraded queries out of 250 — and you can re-run the
audit yourself.

If you're building agents in a regulated domain, that auditability is the feature.
If you're optimising retrieval benchmarks, we are not the strongest option and I'd
rather say so here.
```

---

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
7/ 272 tools · 28 registration groups · MIT · Python 3.10+ · self-hosted ·
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

272 tools, 28 registration groups, MIT, Python 3.10+, self-hosted, MCP over stdio.
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

Self-hosted, MIT, Python 3.10+, MCP over stdio, 272 tools across 28 registration
groups. Source install only (no PyPI package).

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

**Title:** `mem20 — MIT agent memory server with a provenance ledger (272 tools, MCP, self-hosted)`

```
mem20 is an MIT-licensed MCP memory server for AI agents. The differentiator is
provenance: grounded memory and simulated memory are separate stores, the grounded
write path refuses invented content, and every entry carries its origin in an
append-only ledger.

- 272 tools across 28 registration groups
- Python 3.10+, JSON-RPC 2.0 over stdio
- Self-hosted, no account, no telemetry requirement
- Source install only — there is no PyPI package, and we say so rather than
  letting people find out from a 404

We publish the benchmark including the parts that don't flatter us: unanswerable
questions score 0.000 in every retrieval mode. Details in the repo.

https://github.com/bythewayz66-glitch/mem20
```

---

## 5. Long-form article (~1,500 words)

# Your agent's memory has no provenance. That's the bug.

Every team building an agent eventually hits the same wall, and it is never the wall they planned for. The plan is retrieval: embed the corpus, tune the index, measure recall, ship. Then the agent runs for three weeks and someone asks it a question about a customer, and it answers confidently, and the answer is wrong, and nobody can tell you where the wrong part came from.

That is not a retrieval failure. Retrieval worked. It found something relevant. The failure is that the system had no way to distinguish a fact it was told from a fact it invented, and no record of which was which.

### Retrieval quality is the wrong axis

The agent-memory market has converged on a single competitive axis: how good is your recall. Benchmarks measure hit rate on direct questions, multi-hop questions, adversarial questions. Vendors publish the flattering rows. It is a reasonable axis — if your problem is "the agent can't find the right document," better retrieval is the fix.

But most production failures are not "couldn't find it." They are "found it, plus something it made up, and presented both with identical confidence." A memory layer that stores an invented fact next to a real one, in the same table, with the same schema, has destroyed the only information that mattered: whether the fact was ever true.

You cannot recover that downstream. You can add a confidence score, but a confidence score is a model's opinion about its own output, which is exactly the thing you were trying to audit. You can add a prompt instruction — "never state anything you didn't retrieve" — and you have added a suggestion, not a constraint. Prompts are advisory. Storage is not.

### What a hard boundary looks like

mem20 is an MCP server that gives agents persistent memory. Its central design decision is that grounded memory and simulated memory are not a flag on a row. They are separate stores with separate write paths.

Grounded memory is content that came from a real source. Simulated memory is content the agent generated. When code tries to push invented content through the grounded write path, the server raises:

```
PermissionError: remember() is grounded-only. Simulated content must use
remember_simulated(); this call is refused to protect Step 7.4 separation.
```

That is the shipped exception string, not an illustration of one. The guard sits on the write path, which means it holds regardless of what any prompt says, what any model decides, or what any tool-calling chain does. It is the difference between a policy and a mechanism.

The second half of the boundary is labelling. Every write must declare how the content was learned: `observed`, `inferred`, `imagined`, `user_stated`, `hypothesis`, `agent_generated`, or `unlabeled`. An unlabeled write is refused. This closes the obvious loophole — a system that separates grounded from simulated is only as good as its ability to tell which is which, and the honest answer is that only the writer knows. So the writer has to say.

Promotion from simulated to grounded is not a flag flip. It goes through a gate that wants evidence: a recorded prior prediction that resolved in the agent's favour, or a registered external verifier. An agent cannot promote its own guess to a fact by asserting it more confidently.

### The audit is the product

Once provenance is structural, you can audit it. mem20 reports a `contamination_rate` for a store and lists the specific entries that violated the partition, across six violation classes. A clean store reports `0.0` and `CLEAN`.

On the shipped benchmark corpus — 700 grounded facts, 1,300 simulated facts, 250 queries — the measured trust properties are:

- `contamination_rate`: **0.0**
- ledger records: **700**
- degraded queries: **0** of 250
- graph entities: **654**, edges: **3,601**

These are not retrieval scores. They are properties of the store, and they are reproducible: clone the repo, run the audit, get the same numbers. That reproducibility is the actual deliverable. A vendor telling you their memory is trustworthy is marketing. A vendor shipping the audit you can run yourself is evidence.

### Now the part that doesn't flatter us

Here is the full retrieval benchmark, every row, six modes, six query classes, n in parentheses:

| mode | direct | multi-hop | adversarial | adv-hard | contradiction | unanswerable |
|---|---|---|---|---|---|---|
| `bm25` | **1.000** (60) | **0.800** (30) | **0.767** (60) | **0.025** (40) | **0.050** (40) | **0.000** (20) |
| `vector` | **0.900** (60) | **1.000** (30) | **0.667** (60) | **0.750** (40) | **1.000** (40) | **0.000** (20) |
| `hybrid` | **1.000** (60) | **0.533** (30) | **0.167** (60) | **0.050** (40) | **1.000** (40) | **0.000** (20) |
| `hybrid-rerank-off` | **1.000** (60) | **1.000** (30) | **0.650** (60) | **0.625** (40) | **1.000** (40) | **0.000** (20) |
| `keyword` | **1.000** (60) | **0.467** (30) | **0.167** (60) | **0.025** (40) | **0.125** (40) | **0.000** (20) |
| `graph` | — | **0.033** (30) | — | — | — | — |

Three things to take from it.

**Direct recall is solved and therefore uninteresting.** Three modes hit 1.000. If your problem is "find the fact I stored," any of them works.

**Multi-hop is the real weakness, and it is mode-dependent.** Graph retrieval scores 0.033 — it is nearly useless on this corpus. Vector and hybrid-rerank-off score 1.000. Hybrid with reranking on scores 0.533, which is worse than either of its components, a result worth its own investigation. Anyone who tells you their memory layer is uniformly strong on multi-hop is either not measuring it or not publishing it.

**Abstention fails completely.** Unanswerable questions score **0.000 in every single mode**, n=20. Not one mode, not one weak configuration — all six. A memory system that cannot say "I don't know" is a confabulation engine with a database attached. Ours is not there yet, and the honest framing is that provenance enforcement and abstention are different problems: we solved the first and have not solved the second.

We publish this because a benchmark you only show when it flatters you is not a benchmark. It is a brochure.

### What this is for, and what it isn't

mem20 is for teams building agents where being wrong is expensive and being unable to explain why is worse: regulated industries, internal knowledge systems, anything with an auditor on the other end. The value is that when the agent says something, you can trace it to a store, an origin, and a ledger entry — and when it invents something, the invention is quarantined where you can see it.

It is not the strongest retrieval system available, and the table above is why we can say that without hedging. If your only requirement is recall on a clean corpus, a well-tuned vector index will serve you and cost you less.

### Getting started

Source install only — there is no PyPI package:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
python mcp/mcp_server.py
```

272 tools across 28 registration groups. MIT. Python 3.10+. JSON-RPC 2.0 over stdio. Self-hosted.

Repo: https://github.com/bythewayz66-glitch/mem20
Site: https://mem20.com/

---

## 6. README / install block

```markdown
## Install

mem20 is installed from source. There is no PyPI package — `mem20`, `mem20-ai`
and `mem20oreo` all return 404 on pypi.org, so any `pip install` of the project
name will fail.

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
python mcp/mcp_server.py
```

Requires Python 3.10+. `requirements.txt` pins the full runtime set, including
`aiohttp` and `mcp-types`, which the server imports at module scope — a clean
install of the manifest is sufficient to boot.

Verify the surface after install:

```bash
python verify_mcp.py     # expects TOOL_COUNT: 272, RESULT: PASS
```

## What it is

An MCP memory server with a hard, storage-level partition between grounded
memory (came from a real source) and simulated memory (the agent generated it).
The grounded write path raises `PermissionError` on invented content. Every write
declares its origin and lands in an append-only ledger.

272 tools across 28 registration groups · MIT · JSON-RPC 2.0 over stdio.

## Benchmark

Full results in `benchmarks/results/latest.json` (250 queries, 700 grounded /
1,300 simulated facts). Direct recall reaches 1.000 on three of six modes;
multi-hop ranges from 0.033 to 1.000; unanswerable questions score 0.000 in every
mode. We publish the whole table, including the failures.
```

---

## 7. Claim ledger index

A number not in this table does not ship. Every row is traceable to a file or a command at `main` @ `d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110`.

| # | Claim | Value | Evidence | Caveat |
|---|---|---|---|---|
| C1 | MCP tool surface | **272** | `python3 verify_mcp.py` with `MEM20_EXPECTED_TOOLS=272` → `TOOL_COUNT: 272`, `RESULT: PASS`; CI pins the same value in `.github/workflows/mcp-verify.yml` | Counts tools, not retrieval quality. 270 is the retired value from an earlier HEAD. |
| C2 | Registration groups | **28** | `sed -n '/def _setup_tools/,/def _handle_list_tools/p' mcp/server.py \| grep -cE 'self\.register_[a-z0-9_]+_tools\(\)'` → 28 | "27 domains" is an editorial subtraction in `docs/TOOL-DOMAINS.md`, not a code-derived number. Do not present a domain count as measured. |
| C3 | Version | **3.1.2** | `VERSION` at `main` | `pyproject.toml` still declares the retired 3.0.0 — packaging defect, disclosed not hidden. |
| C4 | License | **MIT** | `pyproject.toml` `license = { text = "MIT" }` | — |
| C5 | Python floor | **>=3.10** | `pyproject.toml` `requires-python` | — |
| C6 | Protocol | **MCP 2025-06-18** | `verify_mcp.py` initialize response `protocolVersion` | — |
| C7 | Benchmark corpus | **700 grounded / 1,300 simulated / 250 queries** | `benchmarks/results/latest.json` → `facts`, `simulated`, `queries` | Corpus id `mem20-scale-corpus-v2`. The 13-query corpus is retired. |
| C8 | Direct recall | **1.000** on bm25, hybrid, hybrid-rerank-off, keyword; **0.900** vector | `latest.json` → `recall.*.direct` | n=60 per mode. |
| C9 | Multi-hop | **0.033** graph → **1.000** vector, hybrid-rerank-off | `latest.json` → `recall.*.multi_hop` | n=30. Hybrid 0.533 is below both its components. |
| C10 | Adversarial | **0.167** hybrid, **0.167** keyword, **0.667** vector, **0.767** bm25, **0.650** hybrid-rerank-off | `latest.json` → `recall.*.adversarial` | n=60. The retired product-wide 0.000 claim is false at this HEAD. |
| C11 | Abstention | **0.000 in every mode** | `latest.json` → `recall.*.unanswerable` | n=20. This is the real universal hole. |
| C12 | Contamination | **0.0** | `latest.json` → `trust.contamination_rate` | Over 700 ledger records. |
| C13 | Ledger records | **700** | `latest.json` → `trust.ledger_records` | — |
| C14 | Degraded queries | **0** of 250 | `latest.json` → `trust.degraded_queries` | — |
| C15 | Graph size | **654 entities / 3,601 edges** | `latest.json` → `trust.graph_entities`, `trust.graph_edges` | — |
| C16 | Latency p50 | hybrid **1797.1 ms**, hybrid-rerank-off **27.3 ms**, bm25 **102.2 ms**, vector **204.9 ms**, keyword **1692.2 ms** | `latest.json` → `latency_ms.*.p50` | Single-machine measurement; not a production SLA. |
| C17 | PyPI availability | **none** | pypi.org returns 404 for `mem20`, `mem20-ai`, `mem20oreo` | Source install only. |
| C18 | Public site | **https://mem20.com/** returns 200 | `curl -s -o /dev/null -w '%{http_code}' https://mem20.com/` | Page prints v3.1.0 and 270 tools — one release behind the code. Disclosed in §9. |

---

## 8. Guardrails (binding on every public asset)

1. **Never claim retrieval superiority.** The benchmark does not support it. Quote rows, not adjectives.
2. **Never claim abstention works.** Unanswerable is 0.000 in every mode. If an asset implies the system knows when it doesn't, the asset is wrong.
3. **Never claim a benchmark result without its n.** Every rate in this pack carries its sample size.
4. **Never claim PyPI availability.** There is no package. Source install only.
5. **Never claim a signed or reproducible binary build.** None exists.
6. **Never describe the partition as tamper-proof, provably secure, or unfakeable.** It is an enforced write path plus an append-only ledger. Say that.
7. **Never disparage a named competitor.** Compare on axis, not on vendor.
8. **Never cite a retired host or a retired surface number.** 270 tools, 27 domains, 3.0.0 and the 13-query corpus are retired values; they may appear only as explicitly labelled history.
9. **Never present a domain count as measured.** 28 registration groups is measured; a domain count is editorial.
10. **Never publish a URL that was not fetched in the same run.** Status codes in this pack were observed, not assumed.

---

## 9. Hand-off and open defects

**Status: copy is ready; the launch is not.** Three defects block a public launch and none of them are copy problems.

| ID | Defect | Owner | Effect on launch |
|---|---|---|---|
| D1 | `pyproject.toml` declares the retired 3.0.0 while `VERSION` is 3.1.2 | GitHub Repo Assistant | Any `pip install .` reports the wrong version. Copy quotes 3.1.2 and names the defect. |
| D2 | https://mem20.com/ prints v3.1.0 and 270 tools — one release and two tools behind `main` | Webpage Developer | A visitor who checks the site against the repo sees a contradiction. |
| D3 | No `og:image`, no `twitter:card`, no favicon on the public page | Webpage Developer | Product Hunt cannot accept a submission without gallery assets; HN/Reddit/X render a grey box. |
| D4 | Canonical Pages URL 301s to `http://` rather than `https://` | Repo admin / Pages config | Mixed-content and trust problem on the primary link. |
| D5 | `docs/gtm/claim-ledger.md` still carries the retired 270 / 27 surface as current | mem20 GTM Team Lead | Two documents in the same directory disagree. This pack's §7 is the corrected index. |

**What is done:** the pack is rewritten against verified numbers, the audit harness passes with its negative controls firing, and every claim in §7 is traceable to a file or command at the named HEAD.

**What is not done:** the launch. Do not post any asset above until D2 and D3 are closed — a launch that sends traffic to a page contradicting the repo is worse than a launch delayed by a day.

---

*Audit: `python3 docs/gtm/audit-launch-copy.py` — exit 0 required before any asset ships.*
