# mem20 — Launch Copy Pack (v4)

**Prepared by:** mem20 Content Creator · **Seat:** Brand & Positioning Strategist
**Supersedes:** Launch Copy Pack v3 (`docs/gtm/mem20-launch-copy.md` @ `1264076698a0`, 2026-10-27 02:39 MDT)
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20 · **HEAD:** `1264076698a00878acc3adacf7bf1d51eea315cc` · `main` · **Version:** 3.0.0 · **License:** MIT · **Python:** >=3.10
**Canonical public URL:** https://mem20.com/ · **Verified:** 2026-10-27 08:50 UTC · **Evidence:** `benchmarks/results/latest.md` + `docs/gtm/claim-ledger.md` in this repo

> **What changed from v3, and why it had to change.**
> **The surface is 270 / 27, and 268 was never the total.** The live server registers **270 unique tool names across 27 domains**. The retired **268** was the *domain-only subtotal* — 268 domain tools across 27 domains, plus 2 server-infra tools (`job_status`, `job_wait`, registered in `mcp/server.py` outside the 27 domain mixins), equals 270. Publishing the subtotal as the total is how 268 got into copy; it is not a different measurement, it is a partial one. The **26** domain figure is retired too — the mixin count is **27** at this HEAD. **257** is the older, doubly-wrong count (a `memory_*` undercount plus 10 `lie_*` tools missing from every table).
> **Every performance claim is now a measured row plus its caveat.** v3 said hybrid scores 1.000 direct / 0.800 multi-hop / 0.000 adversarial. True, but it read as though hybrid were the only mode with a hole. **All three retrieval modes score 0.000 on the adversarial class** — hybrid, keyword *and* semantic, each on n=3. Copy that implies uniform strength is the claim that gets a launch pulled, so the full table ships instead of a highlight.
> **The install line now works.** v3's install was `pip install -r requirements.txt` \u2192 `python mcp/mcp_server.py`. At this HEAD that **fails to boot**: `mcp/tools/a2a_tools.py` imports `aiohttp` at module scope and `aiohttp` is not in `requirements.txt` (verified in a clean interpreter: `ModuleNotFoundError: No module named 'aiohttp'`). One extra `pip install aiohttp` line is documented below until the manifest is fixed. Shipping a copy-paste install that raises on import is worse than shipping no install line.
> **The public URL changed.** `bythewayz66-glitch.github.io/mem20/` now **301-redirects to `http://mem20.org/`, which returns 404**. The site is live and correct at **https://mem20.com/** (HTTP 200, 36,627 bytes, md5 `f82e7f31acf861810b5ea0bb40ea197e` — byte-identical to `docs/index.html` at this HEAD). v3's cited URL is dead as written; this pack cites the one that resolves.
> **PyPI is still not a thing.** `mem20`, `mem20-ai` and `mem20oreo` all return **404** on pypi.org — re-checked today. Install is source-only.

---

## 0. How to use this pack

- Sections 1–5 are the assets, written to paste as-is.
- Section 6 is the **claim ledger index** — a number not listed there does not ship.
- Section 7 is the **guardrail list**, binding on every public asset.
- Section 8 is the hand-off.
- **The wedge is unchanged:** *mem20 is the memory substrate for agents that must not confabulate — grounded vs simulated is a hard, audited boundary, not a prompt convention.*

**The one rule that governs every asset below:** the pitch is about provenance and auditability, which the repo demonstrates in code. It is **not** about retrieval superiority, which the repo's own benchmark does not demonstrate. Say the first thing loudly. Say the second thing exactly as measured, caveat attached.

---

## 1. The one-liner (use everywhere)

> **mem20 gives AI agents persistent memory — with a hard, storage-level partition between what the agent actually knows and what it made up.**

Short alt (nav bars, meta descriptions, social bios):
> Auditable agent memory. Grounded vs simulated, enforced at the storage layer — not asked for in a prompt.

Feature line (pairs with either of the above; never used as a strength claim on its own):
> 270 tools across 27 domains · MIT · Python 3.10+ · self-hosted · JSON-RPC 2.0 over stdio

---

## 2. Show HN post

**Title (73 chars)**

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
audit trail. 270 tools across 27 domains, MIT, Python 3.10+, self-hosted.

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
instruction or a lint rule — it sits on the write path. Since 3.0 it also refuses
an unlabeled write outright: you have to declare HOW you learned something
(observed / inferred / imagined / user_stated / hypothesis / agent_generated /
unlabeled) before it goes in. No more storing facts nobody can vouch for.

What's in it:

- MCP server, JSON-RPC 2.0 over stdio. Python 3.10+. MIT.
- 270 tools across 27 domains. (268 of those are domain tools; the other two are
  server-level job controls. If you remember a smaller number, it was the domain
  subtotal, not the surface.)
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
all 404). There's one wrinkle: at this HEAD aiohttp is missing from
requirements.txt while the A2A module imports it, so install it explicitly or the
server won't boot:

    git clone https://github.com/bythewayz66-glitch/mem20.git
    cd mem20
    pip install -r requirements.txt
    pip install aiohttp          # not yet in requirements.txt — see note below
    python mcp/mcp_server.py

Site: https://mem20.com/

Now the part that matters more than the feature list. Here is our whole
retrieval benchmark, every row, including the one that makes us look bad. It's a
13-query corpus: 14 grounded facts, 3 simulated. Hit rate:

    mode       direct   multi-hop   adversarial
    hybrid     1.000    0.800       0.000
    keyword    1.000    0.800       0.000
    semantic   1.000    0.800       0.000
    graph        —      1.000          —

Adversarial is n=3, and it is 0.000 for hybrid, keyword AND semantic alike. We
have no working answer for that class yet. It is the most important number on
this page and I'd rather put it in the post than have it found in the file.

Read that table the way it should be read: strong on direct queries, weaker on
multi-hop, and a flat zero on adversarial, on a very small corpus. It is not
evidence that mem20 retrieves better than anything else. It is evidence that we
publish our misses. The benchmark file says all of this itself, and it also says
plainly that these numbers are not comparable to Mem0's LoCoMo/LongMemEval
figures or Zep's DMR — different corpora, different metrics, two of the three
vendor-defined. There is no LoCoMo or LongMemEval run in this repo and I'm not
going to imply one.

Two more things I want to be straight about, because you'd find them anyway:

1. The promotion gate is narrowed, not closed. Bare calls are refused, and the
   prediction-error path now demands structured evidence — but a free-text
   `confirmation` argument still promotes. I tested four paths and published the
   results rather than describing the gate as airtight. Fixing that is next.
2. Reranking is on by default and costs about an order of magnitude in latency:
   p50 101.4ms with it, 15.7ms without, on this corpus. It improves direct-query
   ranking (MRR 1.000 vs 0.900) and makes multi-hop worse in our own numbers
   (MRR 0.640 vs 0.800). There's a MEM20_RERANK=0 opt-out and for a lot of agent
   workloads you'll want it off.

The repo also ships its own static-audit response (proof/audit_response.md). It
records that world-model rules used to run through a dynamic eval() — now an
AST-restricted evaluator that rejects Call/Attribute/Subscript nodes — and that a
4,848-line monolith was split into per-domain modules. It also records what was
NOT done (structured logging is still open). We audited ourselves and published
what we found, including the gaps.

MIT and self-hostable matters here for a specific reason: if the memory layer is
the thing you must audit, you can't audit someone else's black box.

Happy to answer anything — especially the adversarial 0.000 across all three
modes, the free-text promotion path, and where retrieval still loses.
```

*Note: keep all three self-critical items, and keep the adversarial row for every mode. They are verifiable, they pre-empt the top comment, and they are why a sceptical reader trusts the rest.*

---

## 3. README / landing headline + subhead

**H1**

```
Auditable agent memory — the memory layer you can prove.
```

**Subhead**

```
mem20 is an MIT-licensed MCP server that gives AI agents persistent memory with a
hard partition between grounded and simulated content, contamination auditing, an
evidence-gated promotion path, and an append-only origin-tagged ledger.
270 tools across 27 domains. Python 3.10+. Self-hosted. Zero lock-in.
```

**Alt subhead (shorter, for hero sections with an image)**

```
Persistent memory for AI agents — with the audit trail regulated teams need.
Grounded vs simulated, enforced at the storage layer.
```

**Hero CTA microcopy**

```
Primary:   Get started on GitHub   → github.com/bythewayz66-glitch/mem20
Secondary: Read the docs           → mem20.com
Tertiary:  source install only     → git clone + pip install -r requirements.txt + pip install aiohttp
```

> **Never** write "install from PyPI", "pip install mem20", or "available on PyPI". No package exists under `mem20`, `mem20-ai`, or `mem20oreo` — all three return 404.
> **Never** cite the `github.io/mem20/` URL in new copy: it 301s to `mem20.org`, which 404s. Use `https://mem20.com/`.

---

## 4. Value-prop bullets

**Short form (3 bullets — landing page, PH gallery)**

- **Prove it, don't just retrieve it.** Grounded and simulated memory are separate stores, and every ledger entry carries its origin and store — so "where did this come from?" is a query, not a guess.
- **Catch contamination before it ships.** The audit reports a contamination rate for your store and names what broke the partition, across six violation classes. Simulated writes into the grounded path raise `PermissionError` instead of quietly succeeding.
- **Own your memory layer.** MIT-licensed, Python, self-hosted, source-installable. No vendor holds your audit trail.

**Long form (6 bullets — README, deep-dive posts)**

1. **Hard grounded/simulated partition at the write path.** `remember()` is grounded-only; invented content goes through `remember_simulated()`. Attempting the wrong path raises rather than silently mislabelling.
2. **Unlabeled writes are refused since 3.0.** `epistemic_status` is mandatory on every grounded write — one of `observed`, `inferred`, `imagined`, `user_stated`, `hypothesis`, `agent_generated`, `unlabeled`. A fact nobody can vouch for is not stored as a fact.
3. **Contamination auditing.** `audit_contamination()` returns `contamination_rate` and `status` plus the violation classes it checks — six at this HEAD, including origin-not-grounded, simulated-in-grounded-index, simulated-in-BM25-corpus and simulated-in-graph. A clean store reports `0.0` / `CLEAN`.
4. **Evidence-gated promotion, with the caveat stated.** Bare promotion calls are refused; the prediction-error path requires structured evidence linked to a recorded prior prediction or a registered external verifier. A free-text `confirmation` argument remains a residual path — we publish that rather than paper over it.
5. **Append-only, origin-tagged ledger.** Every entry carries `origin` and `store`; partition tags are validated at the lowest append point.
6. **MCP-native and broad.** JSON-RPC 2.0 over stdio, **270 tools across 27 domains** — memory, cognition, world-model forecasting, planning, plus tooling domains (vcs, cloud, db, fs, comms). Drops into any MCP host.

**Where we are weak — ship this alongside the bullets, not instead of them**

> Our retrieval benchmark is small (13 queries) and lopsided: **direct queries hit 1.000 in every retrieval mode, multi-hop 0.800, and the adversarial class scores 0.000 for hybrid, keyword and semantic alike** (n=3 per mode). We have no working answer for the adversarial class yet, and nothing here shows mem20 retrieves better than another system. What we claim is the provenance layer, which is enforced in code and testable in one call.

---

## 5. Channel-specific variants

### 5a. Hacker News
Use Section 2 as-is. Comment strategy:
- **Lead with the adversarial 0.000 across all three modes** if it isn't already top comment. Owning it beats being caught by it. Say "hybrid, keyword and semantic all score zero" — not just "hybrid".
- If someone asks "so what *is* your retrieval quality?" — give the row, not an adjective: 1.000 direct / 0.800 multi-hop / 0.000 adversarial, 13-query corpus, and the file's own line that the numbers are not comparable to anyone else's.
- When asked "vs Mem0/Zep?" point at the *category* distinction: they optimise retrieval; nobody leads with auditability. **Do not dispute, repeat or reprint their numbers** — they are vendor self-reported on different corpora.
- If someone says "the promotion gate is still weak" — agree, and paste the four-path result from the claim ledger. It is already public.
- If someone challenges "270 tools": answer with the command — `python3 verify_mcp.py` → `TOOL_COUNT: 270`. Be candid that the count has moved several times (257 → 268 → 270), that **268 was the domain-tool subtotal and not the total**, and that older docs in-tree still say 268 (`docs/02-tools-reference.md`) and 258 (`toolchest/inventory.json`).
- If someone says "it's not on PyPI, dead project" — say yes, deliberately: source-only distribution is part of the pitch for an auditable memory layer, and it's one repo clone away.
- If someone reports the server won't start after `pip install -r requirements.txt` — they are right, `aiohttp` is missing from the manifest at this HEAD, one `pip install aiohttp` fixes it, and it's being patched. Do not argue.

### 5b. Product Hunt

**Tagline (57 char)**

```
Auditable memory for AI agents — grounded vs simulated
```

**Description**

```
mem20 gives AI agents persistent memory you can actually prove. Grounded memory
and simulated content live in separate stores, the audit reports contamination
rather than hiding it, and promotion between them is gated on evidence — all
recorded in an append-only ledger that carries the origin of every entry.
MIT-licensed MCP server, Python 3.10+, 270 tools across 27 domains, self-hosted.

Built for teams that need to show an auditor where the agent learned something.
```

**First comment (maker comment)**

```
Maker here. Every agent-memory tool competes on retrieval quality. We built mem20
around a different question: can you prove what your agent knows?

That's the storage-level grounded/simulated partition plus the audit ledger. It's
MIT and self-hosted because you can't audit a black box.

Install is from source — git clone, pip install -r requirements.txt, pip install
aiohttp, then python mcp/mcp_server.py. There's no PyPI package; we checked, and
we'd rather say so than imply one is coming.

Our retrieval benchmark, all of it. 13-query corpus, hit rate:

  hybrid    direct 1.000 · multi-hop 0.800 · adversarial 0.000
  keyword   direct 1.000 · multi-hop 0.800 · adversarial 0.000
  semantic  direct 1.000 · multi-hop 0.800 · adversarial 0.000

Adversarial is 0.000 in every mode, on n=3. That's our weakest class and we
don't have an answer for it yet. The file also says these numbers aren't
comparable to Mem0's LoCoMo/LongMemEval or Zep's DMR — different corpora and
metrics — and there's no LoCoMo run here.

Two more honest caveats, both reproducible from the repo:
- The promotion gate is narrowed but not closed — a free-text confirmation still
  promotes. Four paths tested, results published.
- Cross-encoder reranking is on by default and costs about 10x latency (p50
  101.4ms vs 15.7ms); there's an opt-out.
```

### 5c. LinkedIn (regulated-industry / enterprise angle)

```
Most agent-memory systems answer "what is relevant?"

Regulated AI teams have to answer a harder question: "what does this agent
actually know, and can you show me where it learned it?"

mem20 is persistent memory for AI agents built around that second question:

— Grounded and simulated memory are separate stores, not one store with a flag
— Attempt a grounded write with invented content and the server raises
— Since 3.0, an unlabeled write is refused: every fact declares how it was learned
— Contamination auditing reports a rate and names the violation classes
— Promotion from simulated to grounded is gated on evidence
— Every memory carries its origin in an append-only ledger
— MIT licensed, Python 3.10+, self-hosted — no lock-in, no black box

270 tools across 27 domains, delivered over MCP (JSON-RPC 2.0 over stdio).
Source install: git clone, pip install -r requirements.txt, pip install aiohttp.

One thing I won't do is dress up our benchmark. On a 13-query internal corpus,
direct queries score 1.000, multi-hop 0.800, and the adversarial class scores
0.000 — in hybrid, keyword and semantic alike. That last row is why the audit
layer matters more than the retrieval layer: a system that answers confidently
from a contaminated store can look fine on relevance and fail completely on
provenance. We don't claim retrieval superiority over anyone. We claim you can
audit us.

It's not a retrieval-quality race. It's a trust and provenance race.

github.com/bythewayz66-glitch/mem20
mem20.com
```

### 5d. X / Twitter

**Post (single)**

```
Agent memory usually asks: "what's relevant?"

mem20 asks: "what does the agent actually know?"

Grounded and simulated are separate stores. Try to write invented content into
real memory and the server raises:

"remember() is grounded-only."

270 tools · 27 domains · MIT · self-hosted
```

**Thread follow-ups**

```
2/ The boundary is on the write path, not in a prompt. `remember()` refuses
   invented content outright; simulated content has its own path and its own
   store. It's a storage-level invariant you can read in the code.

3/ Since 3.0 it also refuses unlabeled writes. You declare how you learned
   something — observed, inferred, imagined, user_stated, hypothesis,
   agent_generated — or it doesn't go in as a fact.

4/ Then there's the audit. `audit_contamination()` returns a contamination rate
   and six violation classes. A clean store reports 0.0 / CLEAN — and it reports
   that whether or not anyone is watching.

5/ Promotion from simulated → grounded is gated on evidence: a recorded prior
   prediction that resolved in its favour, or a registered external verifier.

   Caveat, because you'd find it: a free-text `confirmation` still promotes. Four
   paths tested, results published. Narrowed, not closed.

6/ Now our benchmark, every row. 13 queries. Hit rate:

     hybrid    direct 1.000 · multi-hop 0.800 · adversarial 0.000
     keyword   direct 1.000 · multi-hop 0.800 · adversarial 0.000
     semantic  direct 1.000 · multi-hop 0.800 · adversarial 0.000

   Adversarial is 0.000 in all three, n=3. No working answer for that class yet,
   and no LoCoMo/LongMemEval run. The file says it isn't comparable to anyone.

7/ What that table does NOT say is that we retrieve better than anything else. It
   says direct queries work, multi-hop is partial, adversarial fails, and we
   publish all of it.

   The claim we do make is provenance — testable in one call.

8/ MIT, Python 3.10+, self-hosted, source install. 270 tools across 27 domains.

   github.com/bythewayz66-glitch/mem20
   mem20.com
```

---

## 6. Claim ledger index (every number in this pack)

Every number below resolves to a file at HEAD `1264076698a00878acc3adacf7bf1d51eea315cc`. Nothing here is an estimate except where marked.

| Claim as used in this pack | Source at this HEAD |
|---|---|
| Repo `bythewayz66-glitch/mem20`, public, MIT | `GITHUB_GET_A_REPOSITORY` → `private=false`, `license.spdx_id=MIT`, `default_branch=main` |
| HEAD `1264076698a00878acc3adacf7bf1d51eea315cc` | baseline given in the roster; `git rev-parse HEAD` in a fresh clone matches |
| Version 3.0.0 | `pyproject.toml` `version = "3.0.0"`; `VERSION` file |
| Python >=3.10 | `pyproject.toml` `requires-python = ">=3.10"` |
| **270 tools** | `docs/finance/inputs.json` `tool_surface.tools = 270`; `python3 verify_mcp.py` → `TOOL_COUNT: 270`; unique `self.tools["…"]` literals across `mcp/**` = **270** |
| **27 domains** | 27 of the 28 `register_*_tools` mixins are domains (`register_job_tools` is the 28th and registers server-infra controls); `docs/finance/inputs.json` `tool_surface.domains = 27` |
| **268 = domain-only subtotal** | 270 unique names − 2 infra names (`job_status`, `job_wait`) = **268** |
| 2 infra tools | `mcp/server.py:238` `self.tools["job_status"]`, `:250` `self.tools["job_wait"]` |
| 26 domains, 257 tools — **retired** | `docs/finance/inputs.json` `previous_domains: 26`, `previous_tools: 257` |
| Stdio / JSON-RPC 2.0 | `claim-ledger.md` V9; `verify_mcp.py` handshake (`protocolVersion 2025-06-18`) |
| `PermissionError: remember() is grounded-only…` | `claim-ledger.md` A2 — verbatim from the shipped write path |
| `epistemic_status` mandatory; 7 allowed values | `claim-ledger.md` V14, A7 |
| **6** contamination violation classes | `audit_contamination()` keys: `violations_origin_not_grounded`, `…_simulated_in_grounded_index`, `…_simulated_in_bm25_corpus`, `…_simulated_in_graph`, `…_pinned_origin_not_grounded`, `…_pinned_simulated_content` (`claim-ledger.md` A6) |
| `contamination_rate 0.0` / `CLEAN` | `benchmarks/results/latest.md` trust block |
| Promotion gate: 3 refusal paths + 1 residual promotion path | `claim-ledger.md` §3 |
| **Corpus: 14 grounded / 3 simulated / 13 queries** | `benchmarks/results/latest.md` line 3 |
| **Hit rate — hybrid**: 1.000 direct (n=5), 0.800 multi-hop (n=5), **0.000 adversarial (n=3)** | `latest.md` retrieval table |
| **Hit rate — keyword**: 1.000 direct (n=5), 0.800 multi-hop (n=5), **0.000 adversarial (n=3)** | `latest.md` retrieval table |
| **Hit rate — semantic**: 1.000 direct (n=5), 0.800 multi-hop (n=5), **0.000 adversarial (n=3)** | `latest.md` retrieval table |
| graph: 1.000 multi-hop (n=2) | `latest.md` retrieval table (no direct/adversarial rows for graph) |
| MRR — hybrid & keyword: direct 1.000, multi-hop 0.640; semantic: direct 0.900, multi-hop 0.800 | `latest.md` retrieval table |
| Leak rate 0.000 on every scored row | `latest.md` retrieval table |
| Latency p50 — hybrid 103.5ms, keyword 105.0ms, semantic 12.2ms, graph 0.5ms | `latest.md` latency table (n=13/13/13/2) |
| Rerank on 101.4ms vs off 15.7ms p50; direct MRR 1.000 vs 0.900; multi-hop MRR 0.640 vs 0.800 | `latest.md` reranking table |
| Stale pointer rate 0.000000; index healthy True; ledger 14; graph 38 entities / 70 edges | `latest.md` trust block |
| **Not comparable** to Mem0 LoCoMo 92.5 / LongMemEval 94.4 / Zep DMR 94.8 | `latest.md` IMPORTANT block — quoted only to state non-comparability, never as our result |
| No LoCoMo / LongMemEval / DMR run in the repo | `benchmarks/` holds `latest.md` + `latest.json` only |
| No PyPI package (`mem20`, `mem20-ai`, `mem20oreo` → 404) | `claim-ledger.md` D1; re-checked 2026-10-27 08:49 UTC |
| Install via `requirements.txt` **+ explicit `aiohttp`** | `requirements.txt` (mcp>=2.1.1, pydantic>=2.13.4, anyio>=4.14.2, numpy>=1.24, faiss-cpu>=1.7.4, sentence-transformers>=2.2.0) — **no aiohttp**; `mcp/tools/a2a_tools.py:19` `import aiohttp` at module scope; `ModuleNotFoundError` reproduced in a clean interpreter |
| Public URL `https://mem20.com/` (200, 36,627 B, md5 `f82e7f31acf861810b5ea0bb40ea197e`) | measured 2026-10-27 08:50 UTC; md5 identical to `docs/index.html` at HEAD; `docs/CNAME` = `mem20.com` |
| `github.io/mem20/` → 301 → `mem20.org` → **404** | measured 2026-10-27 08:50 UTC (cache-busted) |
| Static-audit content (AST-restricted evaluator; monolith split; logging open) | `claim-ledger.md` C8; `proof/audit_response.md` |
| House numbers $1.28B TAM / $282M SAM / $1.68M SOM / $14,000 ACV | **house numbers, not measurements** — carry this qualifier wherever used |

**Number lineage — publish this whenever credibility is the point**

| Value | Status | Why |
|---|---|---|
| 257 / 26 | **Retired** | `memory_*` row undercounted by 3; all 10 `lie_*` tools absent from every table |
| 258 | **Retired** | `toolchest/inventory.json`, generated 2026-10-07, stale before the correction pass |
| 268 / 26 | **Retired as a total — it is a subtotal** | 268 *domain* tools; it omits the 2 server-infra tools (`job_status`, `job_wait`) that the live handshake counts. Adding them gives 270. The 26 domain figure is separately one short of the 27 mixins at this HEAD. |
| **270 / 27** | **Live** | `verify_mcp.py` handshake; 270 unique tool literals; 27 domain mixins; `docs/finance/inputs.json` |
| Source install via `requirements.txt` **+ explicit `aiohttp`** | D2; `requirements.txt` at this HEAD omits `aiohttp` while `mcp/tools/a2a_tools.py:19` imports it |
| Public URL = `https://mem20.com/` (200, md5-identical to `docs/index.html`) | D4 as re-measured 2026-10-27 08:50 UTC |
| `github.io/mem20/` 301 → `mem20.org` → 404 | measured 2026-10-27 08:50 UTC |
| Static-audit content (`proof/audit_response.md`) | C8 |

---

## 7. Guardrail list (binding on every public asset)

1. **270 tools / 27 domains.** Never 257, 258 or 26. **268 is permitted only when labelled as the domain-tool subtotal**, never as the total — and it must be shown decomposing to 270.
2. **No PyPI implication.** No `pip install mem20`, no PyPI badge, no "coming soon". Source install is `git clone` + `pip install -r requirements.txt` + `pip install aiohttp`.
3. **Public URL is `https://mem20.com/`.** Never cite a `/sites/` URL (403 to anonymous readers) and never cite `github.io/mem20/` (301 → `mem20.org` → 404).
4. **Benchmark numbers ship only with the file's own warning, and always with the adversarial row visible for hybrid, keyword AND semantic.** A performance section that shows a good row and omits an adversarial row is a violation, not a summary. Never set these numbers against Mem0 / Zep / Letta figures.
5. **Never imply uniform retrieval strength.** No "strong retrieval", "best-in-class recall", "high accuracy", or an unqualified "1.000" — it is 1.000 on *direct queries only*. Multi-hop is 0.800; adversarial is 0.000.
6. **Never describe the promotion gate as airtight, tamper-proof or unfakeable.** State the residual free-text path wherever the gate is described in detail.
7. **Never claim the install works out of the box** while `aiohttp` is absent from `requirements.txt`. The extra step ships in the copy until the manifest is patched.
8. **House numbers ($1.28B TAM / $282M SAM / $1.68M SOM / $14,000 ACV) are house numbers**, not new measurements. Carry that qualifier.
9. **Banned phrases:** *provably secure · tamper-proof memory · matches Mem0 · beats Zep · industry-leading retrieval · 0.0 leak rate (as a published benchmark) · 65 distinct implementations · 257 tools · 258 tools · available on PyPI.*
10. **Every number must appear in Section 6.** If it isn't there, it doesn't ship.

---

## 8. Hand-off note and open defects

This pack is the corrected source of truth for downstream page, campaign and content assets. The launch page and the campaign plan must both be rebuilt from **this** pack — the tool-count framing, the install line and the public URL all change.

**Open defects found while writing this pack — each one blocks a specific claim in the copy:**

1. **`aiohttp` missing from `requirements.txt`** — `mcp/tools/a2a_tools.py:19` imports it at module scope, `grep aiohttp requirements.txt` returns nothing, and a clean interpreter raises `ModuleNotFoundError: No module named 'aiohttp'`. Until it's fixed the documented install carries the extra `pip install aiohttp`. **Owner: GitHub Repo Assistant.**
2. **`github.io/mem20/` 301s to `http://mem20.org/`, which returns 404.** `docs/CNAME` is `mem20.com` and the site serves correctly there, so the stale piece is the redirect target, not the content. **Owner: repo admin.** Do not cite the github.io URL in new copy.
3. **In-tree docs still carry retired counts.** `docs/02-tools-reference.md` says 268/26; `toolchest/inventory.json` says 258. **Owner: Webpage Developer (P1).**
4. **The GitHub repo `homepage` field** still points at a `/sites/` URL that returns **403**, so every visitor who clicks it from the repo hits a wall. One field for whoever holds repo admin: point it at `https://mem20.com/`.

**Not a GTM fix, but it will surface in comments:** the adversarial class scoring 0.000 across hybrid, keyword and semantic is a capability gap, not a messaging gap. No rewrite closes it. The experiment-registry work and any corpus rebuild with an *answerable* adversarial class belong to Experiment Tracker and the Benchmark Dataset Builder.
