# SDK docs — `docs/sdk/`

Entry point for the `docs/sdk/` documentation set. **9 tracked file(s).**

## Contents

- [`cpp-release-2026-11-01.md`](cpp-release-2026-11-01.md)
- [`cpp/README.md`](cpp/README.md)
- [`cpp/api-reference.md`](cpp/api-reference.md)
- [`cpp/examples/store_recall_audit.cpp`](cpp/examples/store_recall_audit.cpp)
- [`cpp/protocol.md`](cpp/protocol.md)
- [`cpp/source-ledger.md`](cpp/source-ledger.md)
- [`evidence/ctest-asan-2026-11-01.txt`](evidence/ctest-asan-2026-11-01.txt)
- [`evidence/ctest-release-2026-11-01.txt`](evidence/ctest-release-2026-11-01.txt)
- [`evidence/install-export-2026-11-01.txt`](evidence/install-export-2026-11-01.txt)

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 web/scripts/extract-tools.py --root . --out /tmp/tools.json`
