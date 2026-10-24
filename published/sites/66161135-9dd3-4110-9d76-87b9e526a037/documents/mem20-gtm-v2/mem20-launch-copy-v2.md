# mem20 — Launch Copy Pack (v2)

**Prepared by:** mem20 GTM Team Lead · **Seat:** Brand & Positioning Strategist
**Supersedes:** Launch Copy Pack v1 (`documents/mem20-launch-copy/mem20-launch-copy.md`)
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20 · **HEAD:** `c274404` · `main` · **Version:** 2.1.0rc2 · **License:** MIT
**Verified against the shipped repo on:** 2026-10-14 · **Evidence:** `claim-ledger.md` in this directory + `gtm_assets/verify/partition_demo_output.json`

> **What changed from v1 and why.** v1 pointed at `JaysonAIOnline/mem20`, which **404s** — the canonical repo is `bythewayz66-glitch/mem20`. v1 also opened with a benchmark table (`hit rate 1.000 / 0.800 / 0.000`, `leak rate 0.000`) that **has no source in the shipped repository**: there is no `benchmarks/` directory and no such number anywhere in the tree at this HEAD. Rather than invent a replacement, v2 leads with something stronger and actually reproducible: **the exact refusal the server throws when you try to pollute grounded memory**, captured live from the shipped code. Every number below appears in the claim ledger with its command.

---

## 0. How to use this pack

- Sections 1–5 are the assets. Section 6 is the **claim ledger index** — a number not in the ledger does not ship.
- Section 7 is the **guardrail list**. Section 8 is the hand-off.
- Copy is written to paste as-is. Bracketed `[ ]` items need a human decision.
- **The wedge is unchanged and now better supported:** *mem20 is the memory substrate for agents that must not confabulate — grounded vs simulated is a hard, audited boundary, not a prompt convention.*

---

## 1. The one-liner (use everywhere)

> **mem20 gives AI agents persistent memory — with a hard, storage-level partition between what the agent actually knows and what it made up.**

Short alt (nav bars, meta descriptions):
> Auditable agent memory. Grounded vs simulated, enforced at the storage layer — not asked for in a prompt.

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
Hi HN — I'm launching mem20, an MCP server that gives AI agents persistent memory
with an audit trail.

Every agent-memory layer I looked at competes on retrieval quality. None of them
let you *prove* what the agent knows. In a regulated context that's the whole
ballgame: "probably relevant" is not an answer you can hand an auditor.

So mem20 is built around a hard boundary. Grounded memory (came from a real
source) and simulated memory (the agent generated it) are two separate classes,
not one store with a flag. Try to push invented content through the grounded
write path and the server refuses:

    PermissionError: remember() is grounded-only. Simulated content must use
    remember_simulated(); this call is refused to protect Step 7.4 separation.

That's the real exception string from the shipped code — I ran it this morning to
paste it here. The guard isn't a prompt instruction or a lint rule; it sits on the
write path.

What's in it:

- MCP server, JSON-RPC 2.0 over stdio. Python 3.10+. MIT licensed.
- 268 tools across 26 domains.
- Separate grounded and simulated stores. recall() returns grounded only by
default; you have to ask for simulated.
- contamination auditing — it reports a contamination_rate for your store and
lists what violated the partition. A clean store reports 0.0 and CLEAN.
- Promotion from simulated to grounded goes through a gate that wants evidence:
a linked prior prediction that resolved in its favour, or a registered external
verifier.
- An append-only ledger where every entry carries its origin and store.

Repo: https://github.com/bythewayz66-glitch/mem20
(Not on PyPI yet — it's git clone + pip install . for now.)

Two things I want to be straight about, because you'd find them anyway:

1. There is no published LoCoMo / LongMemEval run. None. If someone tells you we
   have numbers comparable to Mem0 or Zep, they're wrong, and I'm not going to
   put a table up that I can't reproduce from the repo.
2. The promotion gate is narrowed, not closed. Bare calls are refused, and the
   prediction-error path now demands structured evidence — but a free-text
   `confirmation` argument still promotes. I tested all four paths and published
   the results rather than describing the gate as airtight. Fixing that is the
   next piece of work.

While we're on honesty: the repo ships its own static-audit response
(proof/audit_response.md). It records that world-model rules used to run through
a dynamic eval() — now an AST-restricted evaluator that rejects Call/Attribute/
Subscript nodes — and that a 4,848-line monolith was split into per-domain
modules. It also records what was NOT done (structured logging is still open).
We audited ourselves and published what we found.

MIT and self-hostable matters here for a specific reason: if the memory layer is
the thing you must audit, you can't audit someone else's black box.

Happy to answer anything — especially the promotion gate's residual path and
where retrieval still loses.
```

*Note: keep both self-critical items. They are verifiable, they pre-empt the top comment, and they are the reason a sceptical reader trusts the rest.*

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
268 tools across 26 domains. Python 3.10+. Self-hosted. Zero lock-in.
```

**Alt subhead (shorter, for hero sections with an image)**

```
Persistent memory for AI agents — with the audit trail regulated teams need.
Grounded vs simulated, enforced at the storage layer.
```

**Hero CTA microcopy**

```
Primary:   Get started on GitHub   → github.com/bythewayz66-glitch/mem20
Secondary: Read the architecture   → docs/01-architecture.md
Tertiary:  git clone && pip install .   (no PyPI package yet — do not print pip install mem20)
```

---

## 4. Value-prop bullets

**Short form (3 bullets — landing page, PH gallery)**

- **Prove it, don't just retrieve it.** Grounded and simulated memory are separate stores, and every ledger entry carries its origin and store — so "where did this come from?" is a query, not a guess.
- **Catch contamination before it ships.** The audit reports a contamination rate for your store and names what broke the partition. Simulated writes into the grounded path raise `PermissionError` instead of quietly succeeding.
- **Own your memory layer.** MIT-licensed, Python, self-hosted, no PyPI lock-in and no vendor holding your audit trail.

**Long form (6 bullets — README, deep-dive posts)**

1. **Hard grounded/simulated partition at the write path.** `remember()` is grounded-only; invented content goes through `remember_simulated()`. Attempting the wrong path raises rather than silently mislabelling.
2. **Contamination auditing.** `audit_contamination()` returns `contamination_rate` and `status`, plus the violation classes it checks — three at this HEAD: origin-not-grounded, simulated-in-grounded-index, simulated-in-BM25-corpus. A clean store reports `0.0` / `CLEAN`.
3. **Evidence-gated promotion, with the caveat stated.** Bare promotion calls are refused; the prediction-error path requires structured evidence linked to a recorded prior prediction or a registered external verifier. A free-text `confirmation` argument remains a residual path — we publish that rather than paper over it.
4. **Append-only, origin-tagged ledger.** Every entry carries `origin` and `store`; partition tags are validated at the lowest append point.
5. **MCP-native and broad.** JSON-RPC 2.0 over stdio, **268 tools across 26 domains** — memory, cognition, world-model forecasting, planning, plus tooling domains (vcs, cloud, db, fs, comms). Drops into any MCP host.
6. **MIT, self-hosted, Python 3.10+.** Audit the code you depend on; run it in your own VPC. Clone it and the whole thing is readable.

---

## 5. Channel-specific variants

### 5a. Hacker News
Use Section 2 as-is. Comment strategy:
- Lead with the **no-benchmark** disclosure if it isn't already top comment. Owning it beats being caught by it.
- When asked "vs Mem0/Zep?" point at the *category* distinction: they optimise retrieval; nobody leads with auditability. **Do not dispute or repeat their numbers** — they are vendor self-reported.
- If someone says "the promotion gate is still weak" — agree, and paste the four-path result from the claim ledger. It's already public.
- If someone challenges "268 tools": it is the README's own headline, corroborated by an independent grep and by `toolchest/inventory.json`. Be candid that the repo has grown fast and older docs still say 97/111.

### 5b. Product Hunt

**Tagline (58 char)**

```
Auditable memory for AI agents — grounded vs simulated
```

**Description**

```
mem20 gives AI agents persistent memory you can actually prove. Grounded memory
and simulated content live in separate stores, the audit reports contamination
rather than hiding it, and promotion between them is gated on evidence — all
recorded in an append-only ledger that carries the origin of every entry.
MIT-licensed MCP server, Python 3.10+, 268 tools across 26 domains, self-hosted.

Built for teams that need to show an auditor where the agent learned something.
```

**First comment (maker comment)**

```
Maker here. Every agent-memory tool competes on retrieval quality. We built mem20
around a different question: can you prove what your agent knows?

That's the storage-level grounded/simulated partition plus the audit ledger. It's
MIT and self-hosted because you can't audit a black box.

Two honest caveats up front, both reproducible from the repo:
- There is no published LoCoMo/LongMemEval run. We're not claiming parity with
anything.
- The promotion gate is narrowed but not closed — a free-text confirmation still
promotes. We tested all four paths and published the results.
```

### 5c. LinkedIn (regulated-industry / enterprise angle)

```
Most agent-memory systems answer "what is relevant?"

Regulated AI teams have to answer a harder question: "what does this agent
actually know, and can you show me where it learned it?"

mem20 is persistent memory for AI agents built around that second question:

— Grounded and simulated memory are separate stores, not one store with a flag
— attempt a grounded write with invented content and the server raises
— Contamination auditing reports a rate and names the violation classes
— Promotion from simulated to grounded is gated on evidence
— Every memory carries its origin in an append-only ledger
— MIT licensed, Python 3.10+, self-hosted — no lock-in, no black box

268 tools across 26 domains, delivered over MCP (JSON-RPC 2.0 over stdio).

It's not a retrieval-quality race. It's a trust and provenance race.

github.com/bythewayz66-glitch/mem20
```

### 5d. X / Twitter

**Post (single)**

```
Agent memory usually asks: "what's relevant?"

mem20 asks: "what does the agent actually know?"

Grounded and simulated are separate stores. Try to write invented content into
real memory and the server raises:

"remember() is grounded-only."

268 tools · 26 domains · MIT · self-hosted
```

**Thread follow-ups**

```
2/ The boundary is on the write path, not in a prompt. `remember()` refuses
   invented content outright; simulated content has its own path and its own
   store. It's a storage-level invariant you can read in the code.

3/ Then there's the audit. `audit_contamination()` returns a contamination rate
   and the violation classes it checks. A clean store reports 0.0 / CLEAN — and
   it reports that whether or not anyone is watching.

4/ Promotion from simulated → grounded is gated on evidence: a linked prior
   prediction that resolved in its favour, or a registered external verifier.

   Caveat, because you'd find it: a free-text `confirmation` still promotes. Four
   paths tested, results published. Narrowed, not closed.

5/ And no published LoCoMo/LongMemEval run. Not hiding it — there isn't one. If
   you want numbers comparable to Mem0 or Zep, we don't have them yet.

6/ MIT, Python 3.10+, self-hosted. 268 tools across 26 domains.

   github.com/bythewayz66-glitch/mem20
```

---

## 6. Claim ledger index (every number above)

| Number / claim used in this pack | Source |
|---|---|
| Repo `bythewayz66-glitch/mem20` | GitHub API (public, `main`, MIT, pushed 2026-10-14T16:39:03Z) |
| HEAD `c274404` | `git log -1` |
| 2.1.0rc2 / MIT / Python 3.10+ | `pyproject.toml`, `LICENSE` |
| **268 tools** | README §Tool domains ("counting `server.tools`"); `grep 'self\.tools\[' mcp/` = 268; `toolchest/inventory.json` `counts.mcp` = 268 |
| **26 domains** | 26 `register_*_tools` mixins; README domain table |
| Stdio / JSON-RPC 2.0 | `mcp/server.py:1048`; README |
| `PermissionError: remember() is grounded-only…` | captured run, HEAD `c274404` |
| `origin=simulated, store=simulated, epistemic_status=imagined` | captured run |
| `contamination_rate 0.0 / CLEAN` + 3 violation classes | captured run, `audit_contamination()` |
| Promotion gate: 3 refusal paths + 1 residual promotion path | captured run, 4 paths |
| Static-audit content (`proof/audit_response.md`) | `proof/audit_response.md` in the repo |
| **No LoCoMo/LongMemEval/DMR number** | repo-wide search: whole `benchmarks/` tree absent at this HEAD |

---

## 7. Guardrail list (binding on every public asset)

1. **No LoCoMo / LongMemEval / DMR claim, and no mem20-native benchmark table.** The v1 numbers (1.000/0.800/0.000, leak 0.000) have no source in the repo. Do not reintroduce them.
2. **Do not describe the promotion gate as airtight, tamper-proof, or unfakeable.** State the residual free-text path wherever the gate is described in detail.
3. **Do not claim parity or superiority against Mem0 / Zep / Letta.** Their figures are vendor self-reported; never cite them as a mem20 baseline.
4. **Never print `pip install mem20`.** The package is not on PyPI. The install path is `git clone` + `pip install .`.
5. **Banned phrases:** *provably secure, tamper-proof memory, matches Mem0, beats Zep, industry-leading retrieval, 0.0 leak rate (as a published benchmark), 65 distinct implementations.*
6. **Every number must appear in Section 6.** If it isn't there, it doesn't ship.

---

## 8. Hand-off note

This pack is the corrected source of truth for downstream page, campaign and content assets. The launch page must be rebuilt from **this** pack, not v1 — the repo links, the tool count and the entire benchmark section change.

**Blocker to flag in every asset that prints a clone command:** the repo's own `README.md` still shows `git clone https://github.com/JaysonAIOnline/mem20.git` in its Quick Start (line 186) and its badges point at the same dead org — 6 references in `README.md` and 17 across the shipped top-level docs. Landing-page copy is correct; the repo a reader lands on is not. That fix belongs to the repo owner, not to GTM.
