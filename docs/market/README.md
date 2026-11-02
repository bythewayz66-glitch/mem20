# Market research — `docs/market/`

Entry point for the `docs/market/` documentation set. **1 tracked file(s).**

## Contents

- [`market-claims-consistency-2026-10-31.md`](market-claims-consistency-2026-10-31.md)

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 web/scripts/extract-tools.py --root . --out /tmp/tools.json`
