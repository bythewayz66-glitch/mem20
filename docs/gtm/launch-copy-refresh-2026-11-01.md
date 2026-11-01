# mem20 launch copy — refresh report, 2026-11-01

**Owner:** Mem20 Content Creator · **Seat:** Brand & Positioning Strategist
**Deliverable:** `docs/gtm/mem20-launch-copy-v5.md` (this branch)
**Branch:** `docs/gtm-launch-copy-v5-2026-11-01`
**Base:** `main` @ `d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110`
**Audit:** `python3 docs/gtm/audit-launch-copy.py` → **exit 0, VERDICT: PASS**

---

## 1. Why this refresh happened

The v4 pack (`docs/gtm/mem20-launch-copy.md`) was written against a 13-query benchmark corpus and a 270-tool surface. Both are retired at this HEAD. Two of v4's load-bearing claims are now **false**, not merely stale:

| v4 claim | Status at `main` @ `d99ab5d8` | Evidence |
|---|---|---|
| "Adversarial is 0.000 in hybrid, keyword AND semantic" | **FALSE.** hybrid 0.167, keyword 0.167, vector 0.667 (n=60) | `benchmarks/results/latest.json` → `recall.*.adversarial` |
| "13-query corpus: 14 grounded facts, 3 simulated" | **RETIRED.** Corpus is 700 grounded / 1,300 simulated / 250 queries | `latest.json` → `facts`, `simulated`, `queries` |
| "270 tools across 27 domains" | **RETIRED.** Live handshake returns 272; 28 registration groups | `verify_mcp.py` → `TOOL_COUNT: 272`; `_setup_tools` → 28 calls |
| "`pip install aiohttp` needed as an extra step" | **CLOSED.** `requirements.txt` pins `aiohttp>=3.14.5` and `mcp-types>=2.3.0` | `requirements.txt` at `main` |
| "Version 3.0.0" | **RETIRED.** `VERSION` = 3.1.2 | `VERSION` at `main` |

A launch asset that ships a false benchmark claim is the single highest-severity defect in this lane. That is what this refresh fixes.

---

## 2. What was measured, and how

Every number in the v5 pack was re-derived in this run. Nothing was copied from v4, from the claim ledger, or from an earlier report.

### 2.1 Tool surface — 272, not 270

```
$ MEM20_EXPECTED_TOOLS=272 python3 verify_mcp.py
INIT: {"capabilities": {"tools": {"listChanged": false}}, "protocolVersion": "2025-06-18", ...}
TOOL_COUNT: 272
LIE_TOOLS: 10 ['lie_acknowledge_cue', ..., 'lie_status']
RESULT: PASS
```

Run in a clean venv with `mcp>=2.1.1`, `mcp-types>=2.3.0`, `aiohttp>=3.9`, `pydantic>=2.13.4`, `anyio>=4.14.2`. The default `EXPECTED` in `verify_mcp.py` is 270, so an unmodified run reports `RESULT: FAIL` at this HEAD — the CI workflow `.github/workflows/mcp-verify.yml` pins `MEM20_EXPECTED_TOOLS: "272"`, which is the authoritative value.

### 2.2 Registration groups — 28, and "27 domains" is not a code fact

```
$ sed -n '/def _setup_tools/,/def _handle_list_tools/p' mcp/server.py | grep -cE 'self\.register_[a-z0-9_]+_tools\(\)'
28
```

`docs/ops/surface-measurement-2026-10-31.md` already reached this conclusion independently: *"27 domains — not reproducible from the code — REFUTED as a code-derived number."* The v5 pack therefore states **28 registration groups** and does not present a domain count as measured. This is a deliberate departure from the 270/27 house number, and it is the honest one.

### 2.3 Benchmark — full table, all six modes

From `benchmarks/results/latest.json` (blob `c2daafbb25bae623ec66d7e569c74eec6e928e55`, identical on `main` and on this branch):

| mode | direct | multi-hop | adversarial | adv-hard | contradiction | unanswerable |
|---|---|---|---|---|---|---|
| `bm25` | 1.000 (60) | 0.800 (30) | 0.767 (60) | 0.025 (40) | 0.050 (40) | 0.000 (20) |
| `vector` | 0.900 (60) | 1.000 (30) | 0.667 (60) | 0.750 (40) | 1.000 (40) | 0.000 (20) |
| `hybrid` | 1.000 (60) | 0.533 (30) | 0.167 (60) | 0.050 (40) | 1.000 (40) | 0.000 (20) |
| `hybrid-rerank-off` | 1.000 (60) | 1.000 (30) | 0.650 (60) | 0.625 (40) | 1.000 (40) | 0.000 (20) |
| `keyword` | 1.000 (60) | 0.467 (30) | 0.167 (60) | 0.025 (40) | 0.125 (40) | 0.000 (20) |
| `graph` | — | 0.033 (30) | — | — | — | — |

**The finding that drives the new positioning:** the universal hole is **abstention**, not adversarial robustness. `unanswerable` is 0.000 in every mode, n=20. v5 leads with that because it is true, it is uncomfortable, and it is the one claim a competitor cannot catch you on later.

Trust properties, also from `latest.json`: `contamination_rate` 0.0, `ledger_records` 700, `degraded_queries` 0 of 250, `graph_entities` 654, `graph_edges` 3,601.

### 2.4 Public site — live, but one release behind

```
$ curl -s -o /tmp/site.html -w "%{http_code} %{size_download}\n" https://mem20.com/
200 33429
$ grep -oE "v3\.[0-9]+\.[0-9]+" /tmp/site.html | sort | uniq -c
      4 v3.1.0
$ grep -oE "2[0-9]{2} tools" /tmp/site.html | sort | uniq -c
      8 270 tools
```

The site is up and anonymous-reachable. It prints **v3.1.0** and **270 tools** while the code is **3.1.2** and **272**. The pack discloses this as defect D2 rather than quoting the site's numbers.

---

## 3. What changed in the copy

| # | Change | Rationale |
|---|---|---|
| 1 | Adversarial claim replaced with the real per-mode table | v4's claim is false at this HEAD; shipping it is a launch-killing defect |
| 2 | Abstention (0.000 everywhere) promoted to the lead finding | It is the true universal weakness and the most defensible thing to disclose |
| 3 | 270 → 272 tools; 27 domains → 28 registration groups | Measured, and the domain count is not code-derived |
| 4 | `pip install aiohttp` workaround removed from every asset | Defect closed in `requirements.txt` |
| 5 | Version 3.0.0 → 3.1.2, with the `pyproject.toml` contradiction named | `VERSION` is what `main` carries; the packaging defect is disclosed, not hidden |
| 6 | Every rate now carries its n | A rate without a sample size is not a measurement |
| 7 | Guardrails expanded from 7 to 10 rules | Adds: no abstention claim, no rate without n, no domain count as measured, no unfetched URL |
| 8 | §9 hand-off lists five open defects with owners | Copy is ready; the launch is not, and the reason is not copy |

---

## 4. Audit result

```
[1] Benchmark table vs benchmarks/results/latest.json
  PASS  every row matches latest.json (value + n), corpus, latency, trust
[2] Stale / banned scan - v5 pack
  PASS  0 assertive stale references, 0 assertive banned phrases
[3] Negative control - retired v4 must FAIL
  PASS  control fired: 8 findings in the retired v4
[3b] Negative control - re-inject the retired adversarial claim, must FAIL
  PASS  control fired: retired adversarial claim detected
[4] Coverage control - strip the unanswerable rows, must FAIL
  PASS  unanswerable coverage is load-bearing
[5] Per-mode control - delete the hybrid row, must be detected
  PASS  per-mode arm fires, naming hybrid
VERDICT: PASS
```

The negative controls matter more than the pass. A scanner that reports PASS on a clean file proves nothing unless it also fires on the retired file, on a re-injected retired claim, on a stripped coverage row, and on a deleted mode row. All four fire.

---

## 5. Open defects (not copy problems)

| ID | Defect | Owner | Blocks launch? |
|---|---|---|---|
| D1 | `pyproject.toml` declares 3.0.0 while `VERSION` is 3.1.2 | GitHub Repo Assistant | No, but any `pip install .` reports the wrong version |
| D2 | mem20.com prints v3.1.0 / 270 tools — behind `main` | Webpage Developer | **Yes** — traffic would hit a page contradicting the repo |
| D3 | No `og:image`, `twitter:card`, or favicon | Webpage Developer | **Yes** — Product Hunt cannot accept a submission without gallery assets |
| D4 | Canonical Pages URL 301s to `http://` | Repo admin / Pages config | **Yes** — mixed content on the primary link |
| D5 | `docs/gtm/claim-ledger.md` still carries 270 / 27 as current | mem20 GTM Team Lead | No, but two docs in one directory disagree |

**Recommendation:** do not post any asset in the v5 pack until D2 and D3 are closed. A launch that sends traffic to a page contradicting the repo is worse than a launch delayed by a day.

---

## 6. Reproduction

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
git checkout docs/gtm-launch-copy-v5-2026-11-01

python3 -m venv .venv
.venv/bin/pip install "mcp>=2.1.1" "mcp-types>=2.3.0" "aiohttp>=3.9" \
                     "pydantic>=2.13.4" "anyio>=4.14.2"
MEM20_EXPECTED_TOOLS=272 .venv/bin/python verify_mcp.py   # TOOL_COUNT: 272, RESULT: PASS

python3 docs/gtm/audit-launch-copy.py                     # exit 0
```
