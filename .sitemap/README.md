# `.sitemap/` — generated repository sitemap snapshot

**Owner:** mem20 sitemap tooling · **Status:** generated, do not hand-edit

A machine-generated snapshot of the repository tree, written by the sitemap tooling
(`mem20sitemapz`). It exists so tooling can answer "what is in this repo" without a
full walk, and so drift between the tree and the published sitemap is detectable.

## What lives here

| File | What it is |
|---|---|
| [`sitemap.json`](./sitemap.json) | Generated tree snapshot: `generated_at`, `root`, `root_files`, and the per-directory file listing. |
| [`.gitignore`](./.gitignore) | Keeps transient sitemap scratch files out of the tree. |

## Rules

1. **Generated — never hand-edit.** `sitemap.json` carries a `generated_at` timestamp
   and a `root` path. Editing it by hand makes the snapshot lie about the tree.
2. **Regenerate, don't patch.** Re-run the sitemap tooling to refresh it.
3. **Excluded from the doc-count gate.** `.sitemap/` is a generated snapshot, so
   `scripts/ops/check-doc-counts.py` skips it — a count inside a snapshot is a
   measurement of the past, not a live claim.

## Related

- [`SITEMAP.md`](../SITEMAP.md) — the human-readable sitemap and its counts.
- [`mem20sitemapz/`](../mem20sitemapz/) — the subsystem that generates this snapshot.
