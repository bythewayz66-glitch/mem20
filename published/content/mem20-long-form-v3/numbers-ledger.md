# Numbers ledger — v3 (single source of truth)

Every number published in `published/content/mem20-long-form-v3/` traces to a row here.
If a number is not in this table, it does not go into copy.

## 1. Canonical references

| Item | Value | Evidence |
|---|---|---|
| Canonical repo | `github.com/bythewayz66-glitch/mem20` — `main`, MIT, Python | GitHub REST API **200**; `LICENSE`, `pyproject.toml` |
| Public site | `https://bythewayz66-glitch.github.io/mem20/` | HTTP **200** (only public URL permitted in copy) |
| Version | `v2.1.0rc2` | `pyproject.toml` |
| Protocol | JSON-RPC 2.0 over stdio, `2025-06-18` | `mcp/server.py` |
| Install | **source-only** | PyPI `mem20`, `mem20-ai`, `mem20oreo` all **404** |
| Internal static hosts | **never cite** | `/sites/` URLs return **403** to anonymous visitors |

## 2. Tool surface — was → now

| Value | Status | Replaced by | Why |
|---|---|---|---|
| `257 tools / 26 domains` | **RETIRED** | `270 tools / 27 domains` | Older published pages/catalogue pills |
| `268 tools / 26 domains` | **RETIRED** | `270 tools / 27 domains` | Stale in `README.md` + `docs/index.html` |
| `~258` / `~258–260` | **RETIRED** | `270 tools / 27 domains` | v1 hedged range |
| `97 tools / 13 domains` | historical | — | Pre-split server, per `proof/audit_response.md`. Cite only as growth history. |
| **`270 tools / 27 domains`** | **CURRENT** | — | `CHANGELOG.md` tool-count reconcile ("the handshake count is the authority"); corroborated by **27** distinct `register_*_tools` mixins under `mcp/` |

## 3. House numbers (unchanged this round)

| Metric | Value |
|---|---|
| TAM | **$1.28B** |
| SAM | **$282M** |
| SOM | **$1.68M** |
| Blended ACV | **$14,000** |

## 4. Benchmarks — provenance attached

| Metric | Result | Provenance |
|---|---|---|
| Hit rate — direct | 1.000 | Self-reported, internal harness |
| Hit rate — multi-hop | 0.800 | Self-reported, internal harness |
| Hit rate — adversarial | **0.000** | Self-reported — a disclosed weakness, not a win |
| Leak rate (clean stores) | 0.000 | Self-reported; mechanism checkable via `memory_audit_contamination()` |

**Never** describe these as independently audited, and do not claim a LoCoMo/LongMemEval result — none is published, comparable to Mem0's or Zep's.

## 5. Guardrails held in v3

- Promotion is described as **"evidence-based promotion with an append-only audit trail"** — never "tamper-proof", never "unfakeable". The promotion gate's self-attestation hole is disclosed.
- Adversarial hit rate `0.000` disclosed wherever benchmarks are shown.
- No competitor disparagement; competitor numbers are not repeated as our own.
- Install is source-only everywhere; no bare `pip install mem20` presented as a working command.
- Only the GitHub Pages URL is cited; no `/sites/` host appears in shipped copy.
