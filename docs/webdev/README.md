# Web development — `docs/webdev/`

Entry point for the `docs/webdev/` documentation set. **2 tracked file(s).**

## Contents

- [`domain-routing-2026-11-01.md`](domain-routing-2026-11-01.md)
- [`ionos-dns-mem20.md`](ionos-dns-mem20.md)

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 web/scripts/extract-tools.py --root . --out /tmp/tools.json`
