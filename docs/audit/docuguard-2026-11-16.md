# mem20 documentation audit — 2026-11-16

**Auditor:** mem20-docuguard · **Type:** missing-docs + stale-count + orphaned-reference scan
**Base:** `main` @ `3d8d9d452ea4d0d4a70e89b7dc528f30db367a03` (11,439 tracked files)
**Branch:** `docs/docuguard-2026-11-16` · **Branch head at time of audit:** `c39ef9bb8a214cdcf6aba14aef2bf8aec6e9ed91`
**Run at:** 2026-11-16T13:26Z
**Live surface pin:** `docs/surface.json` → **487 tools / 129 domains**

This is a dated record. Its numbers are what was measured on 2026-11-16 and are
excluded from the doc-count gate (`docs/hygiene/doc-count-gate.md`) by the
`docs/audit/` prefix.

---

## 1. Missing subsystem top-level docs — 8 found, 8 added

Every tracked directory was checked for `README.md` / `index.md` / `README.rst` /
`README.txt` / `README`, case-insensitively.

| Subsystem path | Missing doc | Added |
|---|---|---|
| `.github/` | entry doc (14 workflows, CODEOWNERS, templates) | `.github/README.md` |
| `.opencode/` | entry doc | `.opencode/README.md` |
| `.sitemap/` | entry doc | `.sitemap/README.md` |
| `.vscode/` | entry doc | `.vscode/README.md` |
| `docs/attestations/` | entry doc | `docs/attestations/README.md` |
| `docs/series/` | entry doc | `docs/series/README.md` |
| `entries/` | entry doc | `entries/README.md` |
| `ops/` | entry doc | `ops/README.md` |

At base: **6 top-level** directories and **2 `docs/*/`** directories had no entry
doc. At this branch: **0 and 0** (re-ran the same enumeration against the branch
tree).

### Two were blocked by `.gitignore`, not just missing

- `entries/*.md` matched the session-log ignore → the README could not be
  tracked at all. Fixed with `!entries/README.md`.
- `.vscode/` was a **directory-level** ignore. A file negation cannot escape a
  directory ignore, so `!.vscode/README.md` alone would have done nothing. The
  rule was changed to `.vscode/*` + `!.vscode/README.md`.

`.gitignore` net diff: **+3 / −1**. The remaining 121 lines are main's, verbatim.

---

## 2. Stale counts — the gate, not the docs, was the root cause

`scripts/ops/check-doc-counts.py` knew retired bands only up to **306 tools / 38
domains**. `311` and `39` were absent from `RETIRED_TOOLS` / `RETIRED_DOMAINS`,
which is why live docs kept stating a retired surface as current while the gate
stayed green.

### Gate changes

1. `RETIRED_TOOLS` += `272`, `311`; `RETIRED_DOMAINS` += `39`.
2. `self_test()` now reads the expected pin from `docs/surface.json` instead of
   hardcoding `311, 39`. The fixture was pinning a **second copy** of the number,
   which is precisely the failure the gate exists to catch.
3. The seeded fixture now covers every retired band.

### Live docs corrected to 487 / 129

| File | Was | Now |
|---|---|---|
| `docs/hygiene/doc-count-gate.md` | "487 tools / **39** domains"; retired table missing 272/311/39 | 487 / 129; full band list |
| `docs/gtm/README.md` | retired list missing 272/311; drift table claimed `02-tools-reference` printed 268/26 | full list; row closed after re-measuring |
| `docs/ux/README.md` | G-06 premise "catalog is **270** tools across **27** domains" | 487 / 129 |
| `mem20liez/INTEGRATION.md` | `verify_mcp.py` "unless **270** tools"; "**270**-tool surface" | 487 |
| `roadmaps/README.md` | mcp phase "**268** tools" | 487 tools / 129 domains |
| `sdk/perl/AUDIT.md` | header 487, body still **311** in the transcript and the "SDK compiled for" line | 487 throughout |
| `mem20-sdk-ruby/lib/mem20/surface.rb` | `DOMAIN_COUNT = 39`, `DOMAIN_TOOLS = 311` | 129 / 487 |
| `mem20-sdk-ruby/spec/mem20/surface_spec.rb` | pinned 311 / 39 / 311 | 487 / 129 / 487 |
| `mem20-sdk-ruby/mem20-sdk.gemspec` | "**311**-tool mem20 surface (**39** domains)" | 487-tool / 129 domains |

### The Ruby SDK was the real defect

Its `README.md`, `docs/USAGE.md`, `docs/INSTALL.md` and `docs/EVIDENCE.md`
already said **487 / 129** while `lib/mem20/surface.rb` and
`spec/mem20/surface_spec.rb` still asserted **311 / 39**. `surface_spec.rb`
contains its own drift guard that scans `README.md`, the gemspec and every
`docs/*.md` for a stated total ≠ `TOOL_COUNT` — so the suite would have **failed**
against the manifest the moment it ran. This was a broken release, not a typo.

---

## 3. Stale / orphaned doc references (separate signal)

Every in-scope `.md` / `.html` was scanned for relative markdown links, image
paths and inline backticked repo paths, each resolved against `git ls-files` at
base.

**Result: 0 orphaned references in scope.** The two hits the scan produced were
pre-existing and inside dated records, which are excluded by design.

**Excluded, stated explicitly:** external `http(s)` URLs, anchors-only links,
`mailto:`, and paths under `published/` (immutable archive), `docs/audit/`,
`docs/recon/`, `docs/ops/`, `ops/`, `.sitemap/`, and any `YYYY-MM`-dated
filename.

---

## 4. Verification

```
$ python3 scripts/ops/check-doc-counts.py --self-test
SELF-TEST OK: 19 seeded line(s) caught, 4 clean line(s) passed

$ python3 scripts/ops/check-doc-counts.py
live pin: 487 tools / 129 domains
scanned: 85 live doc(s)
OK: no retired tool/domain band in any live doc
rc=0
```

Ruby SDK drift scan — a faithful replay of `surface_spec.rb`'s assertions over
`README.md`, `mem20-sdk.gemspec` and `docs/*.md`: **PASS**.

---

## 5. Not verified / deliberately left alone

- **`rspec` was not run.** Ruby is not installed in the audit sandbox. The Ruby
  check above is a reimplementation of the spec's assertions, not the suite.
- **CI on this branch has not been observed.** Check results are not in this
  record.
- **`docs/02-tools-reference.md`** was re-read and does print 487/129, so the
  `docs/gtm/README.md` row claiming it printed 268/26 was corrected rather than
  carried forward. Not every other doc in the repo was re-measured.
- **Dated records were deliberately not rewritten** — `docs/pricing/`,
  `docs/gtm/claim-ledger*`, `docs/finance/README.md`,
  `docs/finance/CLAIMS_CHECK_H18.md`. They state a retired surface as a
  measurement of their date; rewriting them would falsify the record. The gate
  excludes them for that reason. Banner-marking them as superseded is a separate
  owner decision.
- **`docs/app/*` (≈120 subdirectories) have no per-directory README.** They are
  dated app-spec records under an excluded prefix, not subsystems, so they are
  out of scope here — but they are the largest remaining documentation gap in
  the tree.

---

## Totals

| | |
|---|---|
| Tracked files scanned | 11,439 |
| Missing top-level docs found | **8** |
| Missing top-level docs added | **8** |
| Other gaps (stale counts) | **9 files** |
| Stale/orphaned references in scope | **0** |
| Files changed on this branch | 19 (+440 / −30) — **including this record** |
