# Cached reference data — `reference/`

Offline copies of third-party reference datasets so corpus generation does not
depend on the network.

**9 tracked file(s).**

## Contents

### `v2/` — `mem20-scale-corpus-v2`

- `v2/README.md` — provenance for the v2 reference data (sources and fetch date)

The v2 generator fetches its three sources at run time; only the provenance
record is committed here.

### `v3/` — `mem20-scale-corpus-v3`

- `v3/README.md` — provenance, upstream URLs and fetch date
- `v3/UnicodeData.txt` — Unicode Character Database (2,243,593 bytes)
- `v3/cities15000.txt` — GeoNames `cities15000` (8,546,201 bytes)
- `v3/countries-mledoze.json` — `mledoze/countries` (1,398,004 bytes)
- `v3/iso-3166.json` — ISO-3166 via `lukes` (65,317 bytes)
- `v3/mime-db.json` — `jshttp/mime-db` (209,696 bytes)
- `v3/periodic-table.json` — PeriodicTableJSON (340,343 bytes)

Every v3 file is hashed into `benchmarks/corpora/v3/manifest.json` under
`reference_cache`, so a re-run is reproducible for exactly this cache.

## Notes

Every file here must record its upstream URL and fetch date in the README of
its version directory. Do not add data without provenance.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
