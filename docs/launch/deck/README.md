# mem20 4.0 — launch deck source

**File:** [`mem20-4.0-launch-deck.html`](./mem20-4.0-launch-deck.html) — 16 slides, 1920×1080, self-contained (no build step, no external assets beyond Google Fonts).

Open it in a browser to present; print to PDF for a handout (`@page` is set to 1920×1080).

## What it covers

| # | Slide | Claim it makes |
|---:|---|---|
| 1 | Cover | 487 tools / 129 domains / 211 subsystems, JSON-RPC 2.0 over stdio |
| 2 | The problem | A guess becomes a fact; nothing to audit; prompt rules are not a boundary |
| 3 | The wedge | Grounded and simulated are separate partitions with a veto between them |
| 4 | The surface | 487 tools / 129 domains, derived from live `tools/list` and cross-checked against the AST catalog |
| 5 | The epistemic label | Six statuses; an unlabeled write is refused |
| 6 | The audit trail | Write → ledger → retrieve → audit; contamination 0.0, stale pointers 0.0 |
| 7 | The benchmark, honestly | 7 of 11 declared modes scored; 250 probes; leak rate 0.000 |
| 8 | Measured results | Per-mode aggregate table, all seven scored modes |
| 9 | Where the tools live | Domain distribution; `memory` is the largest at 55; 19 unwired |
| 10 | Architecture | Memory engine → MCP server → subsystems |
| 11 | Getting started | Source-only install; not on PyPI |
| 12 | Roadmap | 211 subsystems in three waves (23 / 129 / 59) |
| 13 | The honest gap | Per-criterion pass rates; criteria 6 and 7 are near zero |
| 14 | The release gate | The six checks that define 4.0 shipping |
| 15 | What we do not claim | Four limits, each with its reason |
| 16 | Closing | Repo, live site, license |

## Every figure is traceable

Nothing in this deck is estimated. Each number comes from a file in this repo:

| Figure | Source |
|---|---|
| 487 tools / 129 domains / 19 unwired / 0 symmetric difference | [`docs/surface.json`](../../surface.json), [`docs/TOOL-DOMAINS.md`](../../TOOL-DOMAINS.md) |
| Epistemic statuses, veto, ledger, contamination auditing | [`docs/01-architecture.md`](../../01-architecture.md), [`docs/renovation/4.0/SUBSTRATE.md`](../../renovation/4.0/SUBSTRATE.md) |
| 7 of 11 modes, per-mode hit rate / MRR / leak / latency, contamination 0.0 | [`docs/benchmarks/README.md`](../../benchmarks/README.md), `benchmarks/results/latest.json` |
| 211 subsystems, 3 waves, 7 criteria, per-criterion pass rates, release gate | [`docs/renovation/4.0/RENOVATION_PLAN.md`](../../renovation/4.0/RENOVATION_PLAN.md), [`subsystem-assignments.csv`](../../renovation/4.0/subsystem-assignments.csv) |
| Not on PyPI; source-only install | [`docs/03-installation.md`](../../03-installation.md) |

## Design

Palette and typefaces are taken from the live site's own stylesheet, [`docs/series/series.css`](../../series/series.css):

- background `#070A0F`, surface `#101724`, line `#1E2A3C`
- text `#E8EFF7`, secondary `#B8C6D8`, muted `#8296AC`
- accent `#2FD4C4`, accent-2 `#46B8F5`, amber `#F5B841`
- Space Grotesk (headings and body), IBM Plex Mono (labels, figures, code)

## Regenerating the numbers

If a figure in this deck disagrees with the repo, the repo wins — regenerate and update the slide:

```bash
python3 scripts/surface_manifest.py --check     # 487 / 129 drift gate
python docs/benchmarks/render.py --check        # benchmark table drift
python3 scripts/renovation/conformance.py --all # per-criterion pass rates
```
