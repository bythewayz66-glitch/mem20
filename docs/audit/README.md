# Repository audits — `docs/audit/`

Entry point for the `docs/audit/` documentation set. **7 tracked file(s).**

## Contents

- [`2026-10-gitlink-audit.md`](2026-10-gitlink-audit.md)
- [`2026-10-pages-build-failure.md`](2026-10-pages-build-failure.md)
- [`2026-10-repository-audit.md`](2026-10-repository-audit.md)
- [`2026-10-sales-readiness-evaluation.md`](2026-10-sales-readiness-evaluation.md)
- [`mem20agentz-upgrade-plan.md`](mem20agentz-upgrade-plan.md)
- [`mem20controlz-desktop-overhaul-plan.md`](mem20controlz-desktop-overhaul-plan.md)
- [`mem20crewz-upgrade-plan.md`](mem20crewz-upgrade-plan.md)

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 web/scripts/extract-tools.py --root . --out /tmp/tools.json`
