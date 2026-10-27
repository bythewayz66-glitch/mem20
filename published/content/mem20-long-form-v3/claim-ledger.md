# Claim ledger (v3)

Every claim published in this directory traces to a row here.

## Verified facts

| # | Claim | Value | Evidence |
|---|---|---|---|
| V1 | Repository | github.com/bythewayz66-glitch/mem20, main | GitHub API 200 |
| V2 | License / language | MIT / Python | GitHub API |
| V3 | Version | 2.1.0rc2 | pyproject.toml |
| V4 | Transport | JSON-RPC 2.0 over stdio, health on 8080 | README |
| V5 | Install | source only, pip install -r requirements.txt | requirements.txt, install.sh |
| V6 | SDK dependency | mcp>=2.1.1 | requirements.txt, pyproject.toml |
| V7 | Tool surface | **270 tools** | CHANGELOG tool-count reconcile; 27 register mixins under mcp/ |
| V8 | Tool domains | **27** | 27 distinct register_*_tools mixins |
| V9 | PyPI | 404 on mem20, mem20-ai, mem20oreo | PyPI JSON API |
| V10 | Public site | GitHub Pages, 200 | verified |

## Copy claims and dispositions

| # | Claim | Disposition | Text used |
|---|---|---|---|
| C1 | Repo path | **CORRECTED** | canonical bythewayz66-glitch/mem20 |
| C2 | Tool count 258-260 / 257 / 268 | **RETIRED** | 270 tools across 27 domains |
| C3 | Domain count 26 | **RETIRED** | 27 domains |
| C4 | Revocation listed as a domain | **REMOVED** | not one of the 27 |
| C5 | Install via registry | **RETIRED** | source install only |
| C6 | Run via old module path | **CORRECTED** | mcp/mcp_server.py |
| C7 | Promotion tamper-proof | **REWORDED** | evidence-based promotion with an append-only audit trail |
| C8 | Benchmark parity with incumbent | **NOT CLAIMED** | self-reported only, no LoCoMo or LongMemEval |

## Benchmark provenance

Hit rate 1.000 direct, 0.800 multi-hop, **0.000 adversarial**; leak rate 0.000 on clean stores. All self-reported on the project's own internal harness. Not independently audited. No reproduction script is claimed. The adversarial 0.000 is disclosed as a known weakness wherever the table appears.

## Historical note

The in-tree audit at proof/audit_response.md describes the pre-split server as 97 tools across 13 domains. The repo therefore contains 97 to 270 as its own growth story. Cite 270 for the current surface; cite 97 only as history.

## Open inconsistencies elsewhere in the tree

docs/01-architecture.md and docs/02-tools-reference.md still say 111 tools / 15 domains. README.md and docs/index.html were corrected to 270 / 27 in this round. Remaining drift is tracked by the repo owner.
