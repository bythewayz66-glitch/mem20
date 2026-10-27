# mem20 — Launch Copy Pack (v3 · canonical repo)

**Prepared by:** Mem20-Content (Content Creator) · **Program:** mem20 launch / repo migration
**Change in v3:** every asset points at the single canonical repo (live, 200) and nothing else; the install block is the one that works against that repo.
**Audience:** AI platform/infra engineers · regulated-industry AI teams · OSS / self-host-first / MCP builders
**Wedge (holds across every asset):** Auditable agent memory — the memory layer you can prove.

---

## 0. Canonical references (v3 — the ONLY ones to use)

| Thing | Canonical value | Status |
|---|---|---|
| Repo (canonical) | `https://github.com/bythewayz66-glitch/mem20` | Live — 200 |
| Branch / license / language | main · MIT · Python | ✓ |
| Install | from source (§3). `pip install mem20` is not on PyPI | PyPI 404 — do not publish the pip command |
| Transport / protocol | MCP · JSON-RPC 2.0 over stdio · protocol 2025-06-18 | ✓ |
| Version / tool surface | v2.1.0rc2 · **270 tools across 27 domains** | repo-verified |
| Run | `mem20-mcp` (console entry point) | from pyproject.toml |
| Public site | GitHub Pages | 200 — the only public URL cited |

> Rule: if a repo, install or tool-count reference is not in this table, it does not go into an asset.

---

## 1. The one-liner (use everywhere)

> **mem20 is persistent memory for AI agents — with a hard partition between what an agent actually knows and what it made up.**

Short alt (nav bars, meta descriptions):
> Auditable agent memory. Grounded vs simulated, enforced — not hoped for.

---

## 2. Show HN

See `show-hn-post.md` for the paste-ready post. Title:

```
Show HN: mem20 – Auditable memory for AI agents (grounded vs simulated)
```

Keep the self-critical paragraph (adversarial-retrieval weakness plus no benchmark claim). This audience rewards it and it pre-empts the top comment.

---

## 3. README / landing headline + subhead

**H1**

```
Auditable agent memory — the memory layer you can prove.
```

**Subhead**

```
mem20 is an MIT-licensed MCP server that gives AI agents persistent memory with
a hard partition between grounded and simulated content, contamination auditing,
evidence-based promotion with an append-only audit trail, and an append-only,
origin-tagged ledger. 270 tools across 27 domains. Self-hosted. Zero lock-in.
```

**Alt subhead (shorter, for hero sections with an image)**

```
Persistent memory for AI agents — with the audit trail that regulated teams need.
Grounded vs simulated, enforced in the architecture.
```

**Hero CTA microcopy**

```
Primary:   Get started on GitHub   -> https://github.com/bythewayz66-glitch/mem20
Secondary: Read the architecture docs
Install:   git clone https://github.com/bythewayz66-glitch/mem20.git && cd mem20 && pip install -e .
```

**Install block (canonical — use verbatim everywhere)**

```markdown
**Install (from source — PyPI release pending)**

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -e .     # installs mem20 + its declared dependencies
mem20-mcp            # start the stdio server
```

`pip install mem20` is not yet published to PyPI. Do not use it until the package is live.
```

---

## 4. Value-prop bullets

**Short form (3 bullets — landing page, PH gallery)**

- **Prove it, don't just retrieve it.** A hard grounded/simulated partition plus an append-only origin-tagged ledger tells you where every memory came from.
- **Catch contamination before it ships.** Contamination auditing detects simulated content bleeding into grounded memory before it becomes a decision (note: hard adversarial queries still defeat the retrieval path today — a disclosed known weakness, on the roadmap).
- **Own your memory layer.** MIT licensed, Python, self-hosted. No lock-in, no black box, no vendor holding your audit trail.

**Long form (6 bullets — README, deep-dive posts)**

1. **Hard grounded/simulated partition.** Not a boolean flag on one store — two distinct memory classes, so "the agent made this up" is structurally visible.
2. **Contamination auditing.** Detect when simulated content has entered grounded memory, before it becomes a decision.
3. **Evidence-based promotion with an append-only audit trail.** Nothing graduates from simulated to grounded without evidence attached to the promotion.
4. **Append-only, origin-tagged ledger.** Every memory carries its source; history cannot be quietly rewritten.
5. **MCP-native and broad.** JSON-RPC 2.0 over stdio, 270 tools across 27 domains — drops into LangGraph, CrewAI, Pydantic AI and the rest of the MCP ecosystem.
6. **MIT, self-hosted, Python.** Audit the code you depend on. Run it in your own VPC.

---

## 5. Channel-specific variants

- **Hacker News:** `show-hn-post.md` as-is.
- **Product Hunt:** `product-hunt-post.md` as-is.
- **LinkedIn + X + Reddit:** `social-threads.md` as-is.

---

## 6. Claim ledger (every number, with source)

| Claim in copy | Number | Source |
|---|---|---|
| Tools / domains | **270 tools, 27 domains** | CHANGELOG tool-count reconcile; 27 register mixins |
| Transport / license / language | JSON-RPC 2.0 over stdio · MIT · Python | pyproject.toml + README |
| Version | v2.1.0rc2 | pyproject.toml |
| Protocol | 2025-06-18 | server serverInfo |
| Install | from source; `pip install -e .` | pyproject.toml dependencies |
| Run | `mem20-mcp` | pyproject.toml [project.scripts] |
| Benchmark figures | none published — no numeric retrieval benchmark claimed | Deliberate: no LoCoMo/LongMemEval-comparable data exists |
| Known weakness | hard adversarial queries defeat the retrieval path today | Disclosed wherever limits are discussed |
| Repo (canonical) | github.com/bythewayz66-glitch/mem20 | GitHub API 200 |
| PyPI status | 404 | PyPI JSON API |

**Rule for downstream assets:** if it isn't in this table, it doesn't go in the asset.

---

## 7. Guardrails — do not overclaim (MANDATORY)

1. **No LoCoMo/LongMemEval claim.** mem20 has no published benchmark comparable to Mem0 or Zep. Never imply parity, never cite their numbers as ours.
2. **The adversarial-retrieval weakness must be disclosed** in any asset that discusses limits. State it plainly as a known weakness with a roadmap — never omit it from the HN post or the maker comment.
3. **Evidence-based promotion, not tamper-proof.** Describe promotion as evidence-based with an append-only audit trail. Use auditable, never unfakeable.
4. **No stale references.** Never publish a bare registry install while PyPI returns 404, and never use the retired repository as a live URL.

**Banned phrasings:** provably secure, tamper-proof memory, matches Mem0, beats Zep, industry-leading retrieval, any unqualified superlative.

---

## 8. Handoff note for Webpage Developer

Page should be built around the wedge, not a feature grid:
- **Hero:** H1 plus subhead from §3, primary CTA to the canonical repo.
- **Section 2:** the 3 short value-prop bullets from §4.
- **Section 3:** "How the partition works" — grounded vs simulated, promotion, ledger (three-tier diagram).
- **Section 4:** the limits statement — the adversarial-retrieval weakness visible — with the no-benchmark caveat directly under it.
- **Section 5:** comparison table built only from §6 rows.
- **Section 6:** install block from §3 (git clone plus editable install), MIT badge, self-host note.
- **Footer:** market context stats with attributions.

Exact on-page string corrections for the live page are in `landing-page-copy-update.md`.
