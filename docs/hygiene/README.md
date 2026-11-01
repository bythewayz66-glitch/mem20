# Repo hygiene — `docs/hygiene/`

Entry point for the `docs/hygiene/` documentation set. **8 tracked file(s).**

## Contents

- [`bare-except-policy.md`](bare-except-policy.md)
- [`core-py-duplication.md`](core-py-duplication.md)
- [`cpp-sdk-example.md`](cpp-sdk-example.md)
- [`generated-state.md`](generated-state.md)
- [`oreo-gitlink.md`](oreo-gitlink.md)
- [`spec-authority-paths.md`](spec-authority-paths.md)
- [`test-scratch.md`](test-scratch.md)
- [`vendored-src-harvest.md`](vendored-src-harvest.md)

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 web/scripts/extract-tools.py --root . --out /tmp/tools.json`
