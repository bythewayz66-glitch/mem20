# Repository scripts — `scripts/`

Operational and maintenance scripts. None of these are imported by the server;
they are run by hand or by CI.

**13 tracked file(s)** (`README.md` plus the 12 scripts below).

## Contents

- `surface_manifest.py` — **canonical** surface generator and drift checker. Reads
  the live JSON-RPC `tools/list`, cross-checks it against the AST catalog, and
  writes `docs/surface.json`, `docs/TOOL-DOMAINS.md` and `web/src/data/tools.json`.
  `--check` also fails if a current-facing doc quotes a stale tool/domain count or
  version.
- `surface_measure.py` — measures the runtime registry and proves the registrar
  groups partition it with no overlap (`RUNTIME_TOOLS`, `REGISTRAR_METHODS`).
- `sweep-tool-counts.py` — rewrites retired count bands in generated frontend
  surfaces. It reads the replacement numbers from `docs/surface.json`; it is not
  the source of truth.
- `check_launch_gate.py` — launch-gate assertions (anonymous, version, social
  preview, https hop, crawlable, analytics, repo homepage).
- `check_artifact_evidence.py` — verifies artifacts cited by a commit range exist.
- `check_gtm_claims.py` — checks GTM claim/source pairs.
- `audit_market_claims.py` — checks market claims against their sources.
- `verify_competitive_matrix.py` — audits a dated competitive matrix against the
  repo it describes.
- `verify_price_ladder.py` — checks the published price ladder.
- `verify-retired-infra-purge.sh` — asserts retired infrastructure is gone.
- `validate_controlz_desktop.py` — desktop control-surface validation.
- `vendor_into_members.sh` — vendors shared code into member packages.

## Usage

```bash
# Regenerate the one surface manifest, then verify it (CI runs --check):
python3 scripts/surface_manifest.py --write
python3 scripts/surface_manifest.py --check

# Offline docs/version check only:
python3 scripts/surface_manifest.py --check-docs

# Measure the runtime registry directly:
python3 scripts/surface_measure.py
```

## Notes

`scripts/surface_manifest.py` is the only place that decides the canonical
tool/domain count. Do not hardcode a count elsewhere: `--check` scans
current-facing docs, `docs/finance/inputs.json`, `verify_mcp.py` and the CI
workflows, and fails on any mismatch. Dated reports and audits are deliberately
excluded because their numbers are historical record, not current claims.

`sweep-tool-counts.py` is a helper for the generated frontend surfaces. It reads
its target numbers from `docs/surface.json` and aborts if that file is missing,
so it cannot rewrite a page to a stale constant.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
