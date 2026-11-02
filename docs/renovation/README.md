# Renovation — `docs/renovation/`

Entry point for the `docs/renovation/` documentation set. **2 tracked file(s).**

## Contents

- [`4.0/RENOVATION_PLAN.md`](4.0/RENOVATION_PLAN.md)
- [`4.0/subsystem-assignments.csv`](4.0/subsystem-assignments.csv)

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 web/scripts/extract-tools.py --root . --out /tmp/tools.json`
