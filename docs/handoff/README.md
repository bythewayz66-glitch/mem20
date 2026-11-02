# Agent handoff — `docs/handoff/`

Entry point for the `docs/handoff/` documentation set. **5 tracked file(s).**

## Contents

- [`AGENT-OPERATING-PROTOCOL.md`](AGENT-OPERATING-PROTOCOL.md)
- [`HANDOFF_TEMPLATE.md`](HANDOFF_TEMPLATE.md)
- [`STATE.md`](STATE.md)
- [`claims/README.md`](claims/README.md)
- [`claims/archive/.gitkeep`](claims/archive/.gitkeep)

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 web/scripts/extract-tools.py --root . --out /tmp/tools.json`
