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
> **2. The surface is 311 tools across 39 domains.** Read from `docs/surface.json` (live `tools/list`, AST cross-checked) and pinned in CI as `MEM20_EXPECTED_TOOLS: "311"` in `.github/workflows/mcp-verify.yml`; `python3 scripts/surface_manifest.py --check-docs` → `OK`. The 39 domains are a measured partition — `domain_counts` sums to 311 with no remainder. 270 and 272 were real counts at earlier commits and are now **retired**.
>
> **3. The install line works again, with no extra step.** v4 had to add a manual `aiohttp` install because the A2A module imported it at module scope while the manifest omitted it. At this HEAD `requirements.txt` pins eight packages including `aiohttp>=3.14.5` and `mcp-types>=2.3.0`, and a clean install boots. The workaround is gone from every asset below.
>
> **4. The version is a contradiction inside the repo, and copy must not paper over it.** `VERSION` = **3.1.2**; `pyproject.toml` still declares the retired **3.0.0**. Assets quote **3.1.2** (what `main` carries) and name the packaging defect rather than hiding it.
>
> **5. The public page is one release behind the code.** https://mem20.com/ returns 200 and prints **v3.1.0** four times and the retired **270 tools** eight times. The code says 3.1.2 / 311. That drift is a live defect, disclosed in §7, not a number to copy into launch copy.
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
> 311 tools across 39 domains · MIT · Python 3.10+ · self-hosted · JSON-RPC 2.0 over stdio

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
audit trail. 311 tools across 39 domains, MIT, Python 3.10+,
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
- 311 tools across 39 domains. (If you remember a smaller number,
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

311 tools across 39 domains. MIT. Python 3.10+. Self-hosted, JSON-RPC
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

