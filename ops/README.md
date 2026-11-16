# `ops/` — dated operations records

**Owner:** mem20-admin · **Status:** append-only record directory

This directory holds **dated, point-in-time operations records** — owner directives,
workload rosters and launch-page correction logs. It is deliberately *not* a
subsystem: nothing here is imported, executed or shipped. Each file is a snapshot of
what was true on the date in its filename.

## What lives here

| File | What it records |
|---|---|
| [`launch-page-corrections-2026-11-01.md`](./launch-page-corrections-2026-11-01.md) | Wave-2 owner directive: deterministic string-replacement rebuild of the launch pages, with the baseline SHA and the exact stale values replaced. |
| [`workload-roster-2026-11-01.md`](./workload-roster-2026-11-01.md) | Wave-2 workload roster: baseline `main` SHA, tracked-file count, `VERSION`, open PR/issue counts, at-risk commit total, deadline and the evidence rule. |

## Rules for this directory

1. **Dated, never rewritten.** A record states what was measured on its date. Do not
   update its numbers to today's surface — that would falsify the record. If a figure
   has moved, write a new dated file.
2. **Not a live doc.** `scripts/ops/check-doc-counts.py` excludes `ops/` from the
   doc-count drift gate for exactly this reason (see
   [`docs/hygiene/doc-count-gate.md`](../docs/hygiene/doc-count-gate.md)).
3. **Evidence, not assertion.** A record that claims a change landed must carry the
   40-char commit SHA or a committed `/sites/` URL. A chat message does not count.

## Related

- [`docs/ops/`](../docs/ops/) — the larger, older operations log set (dated audits,
  branch dispositions, surface measurements).
- [`docs/hygiene/doc-count-gate.md`](../docs/hygiene/doc-count-gate.md) — why dated
  records are exempt from the live-surface count gate.
