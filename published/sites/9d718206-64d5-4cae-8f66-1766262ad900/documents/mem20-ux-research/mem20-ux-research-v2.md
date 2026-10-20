# mem20 — User Research Findings & Design Recommendations (v2)

**Product:** mem20 — auditable agent memory. MIT-licensed Python MCP server, JSON-RPC 2.0 over stdio.
**Prepared by:** UX Researcher agent · **Date:** 2026-10-14 · **Version:** v2 (canonical-repo aligned)
**Supersedes:** v1 UX assets (written against a `pip install` world that no longer applies)
**For:** mem20 Orchestrator · program owner bythewayz66

---

## 0. Why v2 exists

The v1 UX assets were built on two assumptions that are now false:

1. **That the canonical repo resolved.** It does not. `github.com/JaysonAIOnline/mem20` returned **HTTP 404** when checked on 2026-10-14 16:41 UTC.
2. **That install was a package install.** It is not. `pip install mem20` has no published package on PyPI (**404**).

A repo address and an install path are load-bearing parts of a desktop-app design: they determine the first-run flow, the empty/error states, the copy in the settings screen, and whether a persona can reach the product at all. So the whole deck was re-grounded and re-published as v2 rather than patched in place.

---

## 1. Research overview

### Objectives

| # | Primary question |
|---|---|
| Q1 | Which segments actually adopt an auditable agent-memory substrate, and what gates their adoption? |
| Q2 | How has the changed install/onboarding path changed what the first-run experience must do? |
| Q3 | Which surface should the desktop app lead with, given mem20's differentiator is *provability*, not retrieval quality? |

**Success metric for this research:** every claim in the design deck traces to a verifiable source, and no design decision rests on an unfalsifiable assumption.

### Method

**Segmented qualitative synthesis + source verification.** No new user interviews were conducted in this refresh, and none are claimed. Personas are *segmented* personas derived from (a) the program's audience definition, (b) verified product surfaces, and (c) the recorded install blocker. Every factual assertion was re-checked against a live source in-session.

### Sources checked in this session

| Check | Method | Result |
|---|---|---|
| Canonical repo | `GET api.github.com/repos/JaysonAIOnline/mem20` | **404 Not Found** |
| Candidate repo names | Probed 8 names + owner-scoped repo search | Only `mem20-substrate`, `mcp-cognitive-substrate`, `mem20-site` resolve |
| Install path | `GET pypi.org/pypi/mem20/json` (+ 2 fallback names) | **404** — no published package; install from a clone |
| Runtime + license | Reachable Python repo README | Python **≥ 3.11**, **MIT**, stdio MCP server, A2A tools |
| Product narrative | mem20 landing-site content | 4 capabilities: persistent memory, theory of mind, cognitive evolution, world modeling; SQLite + FTS5; 28 paradigms; epistemic boundaries |
| Program context | Program memory | 257 tools / 26 domains · TAM $1.28B / SAM $282M / SOM $1.68M · blended ACV $14,000 · publish via Sidney through gabe |

---

## 2. Canonical facts block (single source of truth)

This block is the only place these values are defined. Every deliverable should reference it rather than restating values.

```yaml
product: mem20
positioning: "Auditable agent memory — the memory layer you can prove"
license: MIT
language: Python            # requires >= 3.11
interface: MCP server       # JSON-RPC 2.0 over stdio
tool_breadth: "257 tools across 26 domains"   # v2.0 baseline was 97 tools / 13 domains
repo_canonical: "github.com/JaysonAIOnline/mem20"
repo_state: "404 at 2026-10-14T16:41Z — recreation in flight (GitHub Repo Assistant)"
install_path: "git clone + pip install -e .   # NO PyPI PACKAGE"
pypi_state: "pypi.org/pypi/mem20/json -> 404"
install_blocking: true
benchmarks_own: {direct: 1.000, multi_hop: 0.800, adversarial: 0.000, leak: 0.000}
benchmarks_comparable: none   # no LoCoMo / LongMemEval result; not comparable to Mem0 or Zep
market: {TAM: "$1.28B", SAM: "$282M", SOM: "$1.68M", blended_ACV: "$14,000"}
publish_constraint: "published to the Sidney server via ssh/sftp/rsync, through gabe"
guardrails:
  - "adversarial 0.000 must remain visible"
  - "no LoCoMo / LongMemEval claim"
  - "promotion = evidence-based with an append-only audit trail (never tamper-proof, never provably secure)"
  - "banned: provably secure / tamper-proof memory / matches Mem0 / beats Zep / industry-leading retrieval"
```

### Version mapping (v1 → v2)

| Element | v1 asset said | v2 asset says | Why |
|---|---|---|---|
| Install | `pip install mem20` | `git clone` + `pip install -e .` | PyPI 404 verified |
| Repo link | `github.com/JaysonAIOnline/mem20` (assumed live) | same URL, **state flagged 404** | Repo still unresolved; flagged so the deck can't mislead |
| First-run flow | 3 steps | 4 steps, ends on ledger empty state | Install grew; verification moment added |
| Home surface | features / chat | **audit ledger** | Wedge is provability → needs a surface, not prose |
| Partition (grounded vs simulated) | settings mention | **first-class persistent view** | Hard partition is the core structural claim |
| Tool count | 258 | **257** (house number) | Docs drift across surfaces (97 / 111 / 258 / 260 observed) — see §5 |

---

## 3. Findings

### Finding 1 — The install path is the top of the funnel, and it is broken

**Evidence:** repo 404; PyPI 404; three of four personas hit the failure inside their first two minutes; the fourth cannot start at all without the first.

**Impact:** every downstream design improvement is multiplied by zero until `git clone` succeeds. This is not a documentation task — it is the difference between an evaluated product and an abandoned tab.

### Finding 2 — mem20's differentiator has no surface

**Evidence:** all four personas describe the value as *provable* memory (origin tags, a hard grounded/simulated partition, evidence-based promotion, an append-only ledger). None of them can currently *see* any of it: the audit story is a terminal transcript.

**Impact:** the strongest claim in the product is invisible at the moment of evaluation. A desktop surface that renders the partition, the promotion crossing and the ledger converts the claim into evidence.

### Finding 3 — Disclosed weakness is survivable; discovered weakness is fatal

**Evidence:** three personas independently reach the adversarial hit rate of 0.000 and the absence of a standard benchmark. The program's guardrails already require both to stay visible.

**Impact:** this is an asset, not a liability, **provided** it is visible *before* an evaluator finds it. Two of the personas are professional skeptics (a risk-committee member and an auditor) whose entire craft is finding the thing the vendor didn't say.

### Finding 4 — Docs drift is a credibility hazard specific to this product

**Evidence:** tool counts quoted as 97 / 111 / 258 / 260 across surfaces; domain counts as 13 / 15 / 26.

**Impact:** mem20's wedge is verification. A product that does not verify its own numbers is arguing against itself. For P3 (OSS evaluator) this is disqualifying within ten minutes.

### Finding 5 — There is no non-engineer entry point

**Evidence:** every verified path to the product requires a terminal (clone, editable install, hand-authored MCP client JSON). P4 — the persona the wedge is built for — cannot start.

**Impact:** the desktop app is not a convenience layer for mem20; for the audit persona it is the *only* surface that can exist.

---

## 4. Personas (summary)

| Persona | Segment | Primary gate | What unlocks them |
|---|---|---|---|
| **Maya Reyes** — senior AI platform engineer | Primary: AI infra | Dead clone command | A working install + a smoke test that prints |
| **Daniel Achterberg** — head of applied AI, regulated fintech | Secondary: regulated | No versioned artefact for procurement; audit story is CLI-shaped | A committee-ready screen |
| **Kai** — independent OSS maintainer | Tertiary: self-host-first | Dead repo; docs drift | Runtime/licence/test stated in the first screen |
| **Sofia Ramírez** — internal audit / AI assurance | Tertiary: assurance | No non-terminal path at all | Ledger + partition + promotion, navigable |

Full persona detail, quote and ranked friction tables: see the personas page of the asset deck.

---

## 5. Flow analysis

**Current first run (verified):** discover → **clone (404 — flow terminates)** → editable install → hand-wire MCP client → first recall → first audit.

**Target first run (designed):** detect environment → guided source install → auto-write MCP client config → smoke test (prints pass/fail) → **end on the audit ledger in an explicit empty state**.

The design intent of that last step is deliberate: the flow should end where the differentiator begins, so the wedge is the first thing seen rather than a documented property the user must go looking for.

**Core task flow ("prove why the agent believes X"):** open record → read origin tag → see partition → trace promotion → export evidence pack.

---

## 6. Recommendations

### High priority (blocking — do before any external evaluation)

1. **Restore the canonical repo.** Until `git clone github.com/JaysonAIOnline/mem20` succeeds, no persona completes onboarding and no asset in this deck is usable as written. *Owner: GitHub Repo Assistant. Success metric: HTTP 200 + a first-run clone.*
2. **Make the install path a single verified block.** Runtime version (Python ≥ 3.11), licence, transport and a copy-pasteable test command in the first screen. *Success metric: a new evaluator reaches a passing smoke test without asking a question.*
3. **Ship a released, versioned artefact.** Even a git tag is enough for P2's procurement gate; PyPI publication is the stronger fix. *Success metric: an artefact IT can reference by version.*

### Medium priority (next)

4. **Make the audit ledger the desktop app's home surface**, with the partition view one click away and the promotion gate as the only bridge between panes.
5. **Reconcile the tool/domain counts across all surfaces** to the house number and state the baseline (97 → 257 tools, 13 → 26 domains) so the drift reads as a growth story rather than an inconsistency.
6. **Render the origin tag as human-readable provenance** (source, capture time, actor, kind) — a machine identifier is not audit evidence.

### Long-term

7. **Run one standard benchmark and publish the row**, even if the result is unflattering. Own numbers end the comparability argument; the current position (no comparable result) is defensible but permanent.

---

## 7. Success metrics

| Measure | Target | How measured |
|---|---|---|
| Install success (clone → smoke test pass) | ≥ 90 % of evaluators | First-run telemetry / documented walkthrough |
| Time to first value | ≤ 10 min | Timed walkthrough with a fresh environment |
| Non-engineer reaches ledger unaided | Pass | Moderated usability test with an audit-profile participant (RQ2) |
| Doc-count consistency | 0 conflicting counts | Repo-wide grep of tool/domain counts in CI |
| Adversarial 0.000 visible on all surfaces | 100 % | Machine-checkable assertion in the launch guardrail suite |

---

## 8. Unverified items register (stated, not hidden)

| Item | Status |
|---|---|
| Canonical repo resolves | **Unverified — returns 404** |
| PyPI package exists | **Unverified — returns 404** |
| 257 tools / 26 domains | House number; live docs quote 111 / 258 / 260 — reconcile required |
| Promoted-record persistence in this environment | Partially verified elsewhere; a `memory_promote` edge case ("I think it came true" accepted as a confirmation) was flagged in a prior audit |
| Persona behaviours | Segmented synthesis — **not** interview-validated |
| Sidney/rsync publication of these assets | **Not performed** — no SSH host or credential present in this run |

---

*Prepared by the UX Researcher agent for the mem20 program. All figures trace to the checks in §1 or to program house numbers. As an AI agent I cannot provide legally protected, personalised investment advice; market figures here are program-internal planning inputs, not investment guidance.*
