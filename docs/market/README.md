# Market research — `docs/market/`

Entry point for the `docs/market/` documentation set. **10 tracked file(s).**

## Contents

### Current (2026-11-16) — measured against the 487-tool / 129-domain surface

- [`competitive-market-analysis-2026-11-16.md`](competitive-market-analysis-2026-11-16.md) — the
  competitive and market analysis. Baseline `0224a64`, v4.0.0. Supersedes the 2026-11-01 matrix.
- [`competitive-matrix-2026-11-16.csv`](competitive-matrix-2026-11-16.csv) — 16 rows (13 named
  players + 2 new + mem20 reference), every cell carrying an `S`/`R` source id.
- [`source-register-2026-11-16.md`](source-register-2026-11-16.md) — the lookup table for every
  figure in the two files above. 34 `R` ids, 48 `S` ids.

### Prior (2026-11-01) — measured against the 270-tool / 27-domain surface

- [`competitive-matrix-2026-11-01.md`](competitive-matrix-2026-11-01.md) — superseded by the
  2026-11-16 analysis; retained as the dated record.
- [`competitive-matrix-2026-11-01.csv`](competitive-matrix-2026-11-01.csv)
- [`source-register-2026-11-01.md`](source-register-2026-11-01.md)
- [`price-positioning-2026-11-01.md`](price-positioning-2026-11-01.md)
- [`price-positioning-2026-11-01.csv`](price-positioning-2026-11-01.csv)

### Audits

- [`market-claims-consistency-2026-10-31.md`](market-claims-consistency-2026-10-31.md) — 174/174
  bound market-size statements match the standing figures; exit 0.

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 scripts/surface_manifest.py --check` (exit 0 = no drift), or read
  `docs/surface.json` → `cross_check`.
- **House numbers are carried, never re-derived.** TAM $1.28B / SAM $282M / SOM $1.68M and
  blended ACV $14,000 come from `docs/finance/inputs.json` → `house_numbers` on every run.
  A market-research file asserts them equal to the house figure; it does not re-open them.
- **The benchmark bounds every retrieval claim.** Any asset quoting a retrieval number must
  reproduce the weakest measured row (`bm25`/`keyword` adversarial_hard 0.025 at n=40) in the
  same asset. See `docs/gtm/claim-ledger.md` §0.
- **Competitor figures are snapshots, not commitments.** Mem0 changed its published pricing four
  times in 2026. Treat any row older than a quarter as needing a re-read before it goes in
  customer-facing copy.
- **No competitor disparagement.** Competitor numbers are cited as their own claims, never
  repeated as mem20's. Where a competitor's number is disputed in its own sources, say "sources
  disagree" rather than picking the flattering one.
