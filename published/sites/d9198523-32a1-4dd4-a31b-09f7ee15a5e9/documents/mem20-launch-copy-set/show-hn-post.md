# Show HN — publish-ready (v3 · canonical-repo-corrected)

**Channel:** Hacker News · **Format:** Show HN
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20
**Verified this run:** repo HTTP 200 · MIT · Python · branch `main` · `pyproject.toml` 2.1.0rc2

> **Post gate (still open):** `pypi.org/pypi/mem20/json` returns **404**, so the post uses the source install only. The marketing site `mem20.jaysonai.online` did **not** respond this run (connection failed) — do not link it as a live destination until it is re-verified.

---

## Title (74 chars)

```
Show HN: mem20 – Auditable memory for AI agents (grounded vs simulated)
```

Alt titles:

```
Show HN: mem20 – Agent memory with contamination auditing and a provenance ledger
Show HN: mem20 – MIT agent-memory server that keeps provenance as its invariant
```

## Body (paste verbatim)

```
Hi HN — I'm launching mem20, an MCP server that gives AI agents persistent
memory with an audit trail.

The problem I kept hitting: every memory layer competes on retrieval quality,
and none of them let you *prove* what the agent knows. In a regulated context
that's the whole ballgame — you don't need "probably relevant", you need
"here is where this came from and here is the evidence it was allowed in."

What mem20 is:

- An MCP server (JSON-RPC 2.0 over stdio), Python, MIT licensed.
- 268 tools across 26 domains.
- A HARD partition between grounded memory (came from a real source) and
  simulated memory (the agent generated it). These are not the same store with
  a flag — they are separate classes, enforced at the storage layer: the vector
  and BM25 indexes assert grounded-only on write, and a simulated record
  reaching either one raises immediately.
- Contamination auditing, so you can detect when simulated content has bled
  into grounded memory.
- Evidence-based promotion: content moves from simulated to grounded only with
  prediction_error_evidence attached — a linked prior prediction resolved in
  its favour, or a registered external verifier. Not by asserting it.
- An append-only, origin-tagged ledger — every entry carries its origin (user /
  tool / simulated) and store (memory / imaginated), validated at the append
  path.

Self-reported benchmarks on our own harness:
  hit rate  — 1.000 direct | 0.800 multi-hop | 0.000 adversarial
  leak rate — 0.000 on clean stores

I want to be straight about those numbers. The 0.000 adversarial hit rate is a
real weakness, not a marketing smudge: hard adversarial queries defeat the
retrieval path today, and it's on the roadmap. They're self-reported and not
independently audited. And we do not have a published LoCoMo/LongMemEval
comparable to Mem0 or Zep — so I'm not claiming one.

The other honest caveat: the promotion gate is only as strong as its
attestation, and that attestation is currently self-reported rather than
cryptographically enforced. So the accurate claim is "evidence-based promotion
with an append-only audit trail", not tamper-proof.

Why MIT and self-hosted matters here: if your memory layer is the thing you
must audit, you can't audit someone else's black box. Run it on your own
infrastructure, read the code, no lock-in.

Repo: https://github.com/bythewayz66-glitch/mem20

Install (not on PyPI yet — install from source):
  git clone https://github.com/bythewayz66-glitch/mem20.git
  cd mem20
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py

There's also a systemd installer (./install.sh), a Dockerfile, and a .deb
target if you want it always-on with /health and /metrics on :8080.

Happy to answer anything — especially the adversarial hit rate and where the
promotion gate needs hardening. That's the stuff I'd ask about too.
```

*Keep the self-critical paragraphs. This audience rewards them and they pre-empt the top comment.*

---

## Comment strategy

- **Lead with the 0.000 adversarial weakness** if it isn't already the top comment. Owning it first beats defending it.
- State plainly: benchmarks are **self-reported on our harness**, not independently audited.
- "Why not Mem0/Zep?" → the category answer: *they optimise retrieval; nobody leads with auditability.* Do not disparage their numbers.
- If asked about the MCP transport: it's stdio JSON-RPC 2.0; `mcp/` is a script directory **without** `__init__.py` on purpose, so importing it as `mcp.*` can't shadow the upstream `mcp` SDK. That's why the console script goes through `launcher.py`.
- If asked "is this just a vector DB with a flag?" → no: two write paths, `_assert_grounded()` on both index writers, `_validate_partition_tags()` at the ledger append, simulated records never indexed.
- If asked about the 293 `mem20*z` subsystem packages: be accurate — it's a monorepo, the memory substrate is one part of it, and not every subsystem is production-grade. The repo's own sitemap records 632 of 875 registered capabilities reporting `ok`, 142 `unpackaged`, 101 `degraded`. Say that rather than implying 293 polished products.

---

## Guardrail check

- [x] No LoCoMo/LongMemEval claim
- [x] Adversarial 0.000 disclosed, framed as known weakness, labelled self-reported
- [x] Promotion described as "evidence-based with an append-only audit trail"
- [x] No banned phrasings, no competitor disparagement
- [x] No stale repo reference; no `pip install mem20`
- [x] Install path matches the canonical tree
