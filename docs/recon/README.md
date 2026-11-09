# Stale-file reconnaissance inventory

Machine-readable inventory of every file on `main` that references retired
infrastructure, carries an outdated tool/domain count, holds a dead link, is an
orphaned doc, or is not reachable from `main`.

## File

`stale-file-inventory-<date>.json` — one record per finding.

## Record schema

```json
{
  "path": "repo-relative path",
  "category": "retired_infra | outdated_tool_count | dead_link | orphaned_doc | not_reachable_from_main",
  "stale_pattern": "the concrete stale token / count / link",
  "fix": "key into the top-level `fixes` map (the suggested fix)",
  "severity": "high | medium | low",
  "allowlisted": true,
  "reachable_from_main": true,
  "gate_enforced": true
}
```

Records are stored as positional arrays; `record_fields` names the columns in
order. The top-level `fixes` object maps each `fix` key to its full
suggested-fix text, so the list stays compact while remaining self-describing.

## Live pin

The canonical tool/domain count is read from `docs/surface.json` (generated from
the live JSON-RPC `tools/list` response). At the recorded HEAD it is
**487 tools / 129 domains**. Retired count bands are
`257/258/259/260/265/268/270/306` tools and `26/27/38` domains.

## Regenerate

```bash
python3 scripts/stale-file-inventory.py --date 2026-11-07
```

## Notes

- `retired_infra` records with `gate_enforced: true` are the ones the G8 gate
  (`scripts/verify-retired-infra-purge.sh`, pattern `sidney|gabe`) enforces.
  `jaysonai.online`-only hits are informational (`gate_enforced: false`).
- `reference/v3/cities15000.txt` is a GeoNames gazetteer; its `Sidney`/`Gabela`
  hits are unrelated place names and are flagged as a false positive.
- `published/**` is the immutable delivery archive, integrity-pinned by
  `published/MANIFEST.tsv`; its retired-infra hits are allowlisted (A1) and must
  not be edited in place.
