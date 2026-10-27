# mem20 — Launch Copy Pack (v3)

**Prepared by:** mem20 GTM Team Lead · **Seat:** Brand & Positioning Strategist
**Supersedes:** Launch Copy Pack v2 (`published/sites/66161135-…/documents/mem20-gtm-v2/mem20-launch-copy-v2.md`, 2026-10-14)
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20 · **HEAD:** `7c0b3e8` · `main` · **Version:** 3.0.0 · **License:** MIT
**Canonical public URL:** https://bythewayz66-glitch.github.io/mem20/ · **Verified:** 2026-10-26 · **Evidence:** `claim-ledger.md` in this directory

> **What changed from v2, and why it had to change.**
> **268/26 → 270/27.** The live handshake at this HEAD returns 270 tools across 27 registered domains. v2's number is retired.
> **PyPI is not a thing.** `mem20`, `mem20-ai` and `mem20oreo` all return **404** on pypi.org — re-checked today. The install line is source-only, and v2's softer "(Not on PyPI *yet*)" phrasing is gone: it implied a package was coming, and nothing in the repo says it is.
> **The `/sites/` CDN is not public.** Every `/sites/` URL returns **403** to an anonymous request. Any copy that pointed a reader there pointed them at a wall. The only public web surface is the GitHub Pages site above.
> **The benchmark exists now.** v2 correctly said the repo shipped no benchmark. At this HEAD `benchmarks/results/latest.{md,json}` ship on `main`. So the table is back — with its own "not comparable to competitors" warning welded to it, adversarial 0.000 included.

---

## 0. How to use this pack

- Sections 1–5 are the assets, written to paste as-is.
- Section 6 is the **claim ledger index** — a number not listed there does not ship.
- Section 7 is the **guardrail list**, binding on every public asset.
- Section 8 is the hand-off.
- **The wedge is unchanged:** *mem20 is the memory substrate for agents that must not confabulate — grounded vs simulated is a hard, audited boundary, not a prompt convention.*

---

## 1. The one-liner (use everywhere)

> **mem20 gives AI agents persistent memory — with a hard, storage-level partition between what the agent actually knows and what it made up.**

Short alt (nav bars, meta descriptions, social bios):
> Auditable agent memory. Grounded vs simulated, enforced at the storage layer — not asked for in a prompt.

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
- 270 tools across 27 domains.
- Separate grounded and simulated stores. recall() returns grounded only by
  default; you have to ask for simulated.
- Contamination auditing — reports a contamination_rate for your store and lists
  what violated the partition, across six violation classes. A clean store
  reports 0.0 and CLEAN.
- Promotion from simulated to grounded goes through a gate that wants evidence:
  a recorded prior prediction that resolved in its favour, or a registered
  external verifier.
- An append-only ledger where every entry carries its origin and store.

Install (source only — there is no PyPI package, I checked again this morning;
mem20, mem20-ai and mem20oreo all 404):

    git clone https://github.com/bythewayz66-glitch/mem20.git
    cd mem20
    pip install -r requirements.txt
    python mcp/mcp_server.py

Site: https://bythewayz66-glitch.github.io/mem20/

Three things I want to be straight about, because you'd find them anyway:

1. There IS a benchmark in the repo (benchmarks/results/latest.md), and it is
   small: a 13-query corpus with 14 grounded facts and 3 simulated. Hybrid scores
   1.000 on direct queries, 0.800 on multi-hop, and 0.000 on adversarial. That
   last number is a real weakness and I'm not burying it. There is no published
   LoCoMo or LongMemEval run and nothing here is comparable to Mem0's or Zep's
   figures — different corpora, different metrics. The file says so itself.
2. The promotion gate is narrowed, not closed. Bare calls are refused, and the
   prediction-error path now demands structured evidence — but a free-text
   `confirmation` argument still promotes. I tested four paths and published the
   results rather than describing the gate as airtight. Fixing that is next.
3. Reranking is on by default and costs about 10x latency for direct queries
   (101ms vs 16ms p50 on that corpus). It improves direct-query ranking and makes
   multi-hop slightly worse in our own numbers. There's a MEM20_RERANK=0 opt-out
   and for a lot of agent workloads you'll want it off.

The repo also ships its own static-audit response (proof/audit_response.md). It
records that world-model rules used to run through a dynamic eval() — now an
AST-restricted evaluator that rejects Call/Attribute/Subscript nodes — and that a
4,848-line monolith was split into per-domain modules. It also records what was
NOT done (structured logging is still open). We audited ourselves and published
what we found, including the gaps.

MIT and self-hostable matters here for a specific reason: if the memory layer is
the thing you must audit, you can't audit someone else's black box.

Happy to answer anything — especially the free-text promotion path, the
adversarial 0.000, and where retrieval still loses.
```

*Note: keep all three self-critical items. They are verifiable, they pre-empt the top comment, and they are why a sceptical reader trusts the rest.*

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
Secondary: Read the docs           → bythewayz66-glitch.github.io/mem20/
Tertiary:  source install only     → git clone + pip install -r requirements.txt
```

> **Never** write "install from PyPI", "pip install mem20", or "available on PyPI". No package exists under `mem20`, `mem20-ai`, or `mem20oreo`.

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

---

## 5. Channel-specific variants

### 5a. Hacker News
Use Section 2 as-is. Comment strategy:
- **Lead with the adversarial 0.000** if it isn't already top comment. Owning it beats being caught by it.
- When asked "vs Mem0/Zep?" point at the *category* distinction: they optimise retrieval; nobody leads with auditability. **Do not dispute or repeat their numbers** — they are vendor self-reported on different corpora.
- If someone says "the promotion gate is still weak" — agree, and paste the four-path result from the claim ledger. It is already public.
- If someone challenges "270 tools": answer with the command — `python3 verify_mcp.py` → `TOOL_COUNT: 270`. Be candid that the count has moved several times (257 → 268 → 270) and that older docs in-tree still say 268 and 258.
- If someone says "it's not on PyPI, dead project" — say yes, deliberately: source-only distribution is part of the pitch for an auditable memory layer, and it's one repo clone away.

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

Install is from source — git clone plus pip install -r requirements.txt. There's
no PyPI package; we checked, and we'd rather say so than imply one is coming.

Three honest caveats, all reproducible from the repo:
- Our own benchmark is a 13-query corpus. Direct 1.000, multi-hop 0.800,
  adversarial 0.000. No LoCoMo/LongMemEval run, and no comparison to anyone.
- The promotion gate is narrowed but not closed — a free-text confirmation still
  promotes. Four paths tested, results published.
- Cross-encoder reranking is on by default and costs about 10x latency; there's
  an opt-out.
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
Source install: git clone, then pip install -r requirements.txt.

It's not a retrieval-quality race. It's a trust and provenance race.

github.com/bythewayz66-glitch/mem20
bythewayz66-glitch.github.io/mem20/
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

6/ Our benchmark is honest to the point of being uncomfortable. 13 queries.
   Direct 1.000, multi-hop 0.800, adversarial 0.000. No LoCoMo/LongMemEval run.

   The 0.000 stays in the table.

7/ MIT, Python 3.10+, self-hosted, source install. 270 tools across 27 domains.

   github.com/bythewayz66-glitch/mem20
```

---

## 6. Claim ledger index (every number above)

| Number / claim used in this pack | Source (claim-ledger.md) |
|---|---|
| Repo `bythewayz66-glitch/mem20` | V1 |
| HEAD `7c0b3e8`, version 3.0.0 | V2, V4 |
| MIT / Python 3.10+ | V5, V6 |
| **270 tools** | **V7** — live `verify_mcp.py` `TOOL_COUNT: 270`; grep 270 unique; `docs/README.md` |
| **27 domains** | **V8** — 27 `register_*_tools` mixins |
| Stdio / JSON-RPC 2.0 | V9 |
| `PermissionError: remember() is grounded-only…` | A2 |
| `epistemic_status` mandatory; 7 allowed values | V14, A7 |
| `contamination_rate 0.0 / CLEAN` + **6** violation classes | A6 |
| Promotion gate: 3 refusal paths + 1 residual promotion path | §3 |
| Benchmark 1.000 / 0.800 / 0.000, leak 0.000, 13 queries, rerank 101ms vs 16ms | §6 |
| No LoCoMo / LongMemEval / DMR run | §6 rule 3 |
| No PyPI package (`mem20`, `mem20-ai`, `mem20oreo` → 404) | D1 |
| Source install via `requirements.txt` | D2 |
| Public URL = `bythewayz66-glitch.github.io/mem20/` (200, byte-identical to `docs/index.html`) | D4 |
| Static-audit content (`proof/audit_response.md`) | C8 |

---

## 7. Guardrail list (binding on every public asset)

1. **270 tools / 27 domains.** Never 257, 258 or 268 in a public asset.
2. **No PyPI implication.** No `pip install mem20`, no PyPI badge, no "coming soon". Source install is `git clone` + `pip install -r requirements.txt`.
3. **No `/sites/` URL.** Every `/sites/` path returns 403 to an anonymous reader. The only public web surface is `https://bythewayz66-glitch.github.io/mem20/`.
4. **Benchmark numbers ship only with the file's own warning** and with the adversarial 0.000 row visible. Never set them against Mem0 / Zep / Letta figures.
5. **Never describe the promotion gate as airtight, tamper-proof or unfakeable.** State the residual free-text path wherever the gate is described in detail.
6. **House numbers ($1.28B TAM / $282M SAM / $1.68M SOM / $14,000 ACV) are house numbers**, not new measurements. Carry that qualifier.
7. **Banned phrases:** *provably secure · tamper-proof memory · matches Mem0 · beats Zep · industry-leading retrieval · 0.0 leak rate (as a published benchmark) · 65 distinct implementations · 257 tools · 268 tools · available on PyPI.*
8. **Every number must appear in Section 6.** If it isn't there, it doesn't ship.

---

## 8. Hand-off note

This pack is the corrected source of truth for downstream page, campaign and content assets. The launch page and the campaign plan must both be rebuilt from **this** pack — the tool count, the install line and the entire public-URL scheme change.

**Not a GTM fix:** the GitHub repository's `homepage` field is currently set to a `/sites/` URL that returns **403**. Every visitor who clicks it from the repo hits a wall. That is a one-field change for whoever holds repo admin: point it at `https://bythewayz66-glitch.github.io/mem20/`. Also unresolved: `docs/CNAME` names `mem20.jaysonai.online`, which has **no DNS record** — the Pages site therefore serves on `github.io` only.
