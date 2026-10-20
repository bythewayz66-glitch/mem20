# Product Hunt — publish-ready (v3 · canonical-repo-corrected)

**Channel:** Product Hunt · **Launch day:** Day 2 (never same day as HN)
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20
**Verified this run:** repo HTTP 200 · MIT · Python · branch `main`

---

## Tagline (57 chars)

```
Auditable memory for AI agents — grounded vs simulated
```

## Description

```
mem20 gives AI agents persistent memory you can actually prove. A hard partition
separates grounded memory from simulated content, contamination auditing catches
bleed between them, and an append-only origin-tagged ledger records where every
memory came from. MIT-licensed MCP server, Python, self-hosted — 257 tools
across 26 domains. Built for teams who need "here's the evidence," not
"probably relevant."
```

## Maker's first comment

```
Maker here. Every agent-memory tool on the market competes on retrieval quality.
We built mem20 around a different question: can you *prove* what your agent
knows? That's the grounded/simulated partition plus the audit ledger. It's MIT
and self-hosted because you can't audit a black box.

How the partition actually works: it isn't a boolean flag on one store. The
vector and BM25 indexes assert grounded-only on write, so a simulated record
reaching either one raises immediately; the ledger validates origin/store tags
at its lowest append path; and promotion out of the simulated partition
requires prediction_error_evidence attached to the promotion.

Honest caveats, up front:
- Our adversarial hit rate is 0.000 today. That's a known weakness — hard
  adversarial queries defeat the retrieval path. We'd rather tell you than have
  you find it.
- The benchmarks are self-reported on our own harness, not independently audited.
- We don't publish a LoCoMo/LongMemEval comparable to Mem0 or Zep, so we don't
  claim one.
- Promotion is evidence-based with an append-only audit trail; it is not
  tamper-proof, because the evidence attestation is self-reported rather than
  cryptographically enforced.

Install from source today (not on PyPI yet):
  git clone https://github.com/bythewayz66-glitch/mem20.git
  cd mem20
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py

Also ships a systemd installer, a Dockerfile and a .deb target.
```

## Topic tags

`Developer Tools` · `Artificial Intelligence` · `Open Source` · `Privacy` · `Software Engineering`

## Assets to attach

- Gallery: hero + partition diagram (from the launch page assets)
- Optional 30s GIF: agent stores a memory → simulated entry flagged → promotion with evidence

## First-hour comment plan

1. Pin the maker comment above.
2. Reply to every "how is this different from Mem0/Zep?" with the category answer: they optimise retrieval; mem20 optimises provenance. Never disparage their numbers.
3. When someone asks "does it actually enforce that?" point at the three enforcement sites (index write assert, ledger tag validation, promotion evidence requirement) — mechanism, not adjectives.

## Guardrail check

- [x] No LoCoMo/LongMemEval claim
- [x] Adversarial 0.000 disclosed in the maker comment
- [x] Benchmarks labelled self-reported
- [x] Promotion framed as evidence-based, not tamper-proof
- [x] No banned phrasings
- [x] Canonical repo link only; no `pip install mem20`
