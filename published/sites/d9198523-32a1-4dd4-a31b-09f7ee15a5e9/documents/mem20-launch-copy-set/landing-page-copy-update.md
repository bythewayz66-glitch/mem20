# Landing page — copy update notes (v3 · canonical-repo-corrected)

**Target:** the live launch page (`webpages/mem20-launch/index.html`)
**Canonical destination:** https://github.com/bythewayz66-glitch/mem20
**Why this matters:** the v2 page pointed at a repo that returns 404, and published an install block whose commands do not exist on the canonical tree.

---

## Exact string replacements to apply

| # | Location | v2 (stale) | v3 (corrected) |
|---|---|---|---|
| 1 | Hero lede | `~258–260 tools across 26 domains.` | `270 tools across 27 domains.` |
| 2 | Hero secondary CTA | retired-org repo URL | `→ https://github.com/bythewayz66-glitch/mem20` |
| 3 | Install code block | retired-org clone URL | `git clone https://github.com/bythewayz66-glitch/mem20.git` |
| 4 | Install code block | a contradicting dependency pin + `pip install -e .` | `.venv/bin/pip install -r requirements.txt` |
| 5 | Install code block | a module path from the old substrate repo | `MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py` |
| 6 | Install section note | "Repo-migration note + link to the verified live source `mcp-cognitive-substrate` v1.0.1" | Removed. Replace with: "mem20 is not yet on PyPI — install from source. Requires an OpenAI-compatible LLM endpoint key for the cognitive tools only." |
| 7 | Footer repo link | retired-org repo pointer | `github.com/bythewayz66-glitch/mem20` |
| 8 | Footer repo link (text) | `~258–260 tools · 26 domains` | `270 tools · 27 domains` |
| 9 | Comparison table footer | any retired-org href | `bythewayz66-glitch/mem20` |
| 10 | Benchmark table caption | (none) | `Self-reported on our own internal harness; not independently audited.` |

## What did NOT change (deliberately)

- **Version badge stays `v2.1.0rc2`** — matches `pyproject.toml` on `main`.
- **Benchmark table, no-LoCoMo caveat, adversarial 0.000 amber row, comparison table, guardrail language** — unchanged. Do not alter these.
- **House numbers** — tool surface updated to **270 tools / 27 domains** (268 domain tools + 2 infra tools); TAM $1.28B / SAM $282M / SOM $1.68M and $14,000 blended ACV unchanged.

## Two corrections that are substantive, not cosmetic

1. **The v2 dependency pin was wrong for the canonical tree.** `requirements.txt` and `pyproject.toml` both declare `mcp>=2.1.1`. The v2 block would have installed an SDK version the tree does not use.
2. **The v2 run command was wrong.** That module belongs to the older, non-canonical substrate repo. The canonical entry point is `mcp/mcp_server.py` (or the `mem20-mcp` console script).

## Open items that are NOT copy problems

| Item | Status | Owner |
|---|---|---|
| Launch page returns 403 to anonymous visitors (200 only with a platform token) | OPEN — blocks external HN/PH/Reddit traffic | Webpage Developer / hosting |
| `pypi.org/pypi/mem20/json` → 404; the registry install is held | OPEN | GitHub Repo Assistant / release owner |
| `mem20.jaysonai.online` did not respond this run (referenced by the repo README's Website badge) | OPEN — repo-readme defect | GitHub Repo Assistant |
| Canonical repo README's LICENSE/Releases badges previously pointed at the dead old-org repo | Reported in v2; re-check at launch | GitHub Repo Assistant |
| Publishing through gabe on Sidney | OPEN — no working credential from this sandbox | Orchestrator / Server Builder |

Do not describe the launch as unblocked while the first three rows are open.
