# Permanent URL Record — mem20 Investor & Board Deck

**Recorded:** 2026-11-01
**Baseline commit:** `2ea4492209dfaae6afb22ca884132a0d1849bfcf` (main head, 2026-11-01T13:20:25Z)
**Deck source (this directory):** `docs/app/deck/`
**Branch:** `deck/ws3-rebuild-2026-11-01`
**Supersedes:** the `45445f48` cut recorded 2026-10-27 (171 commits behind)

> **Why this record was rebuilt.** The previous cut was pinned to `45445f48`
> and its central honesty exhibit was an adversarial retrieval hit rate of
> `0.000` on `n=3`. Both are now wrong. The tree has moved 171 commits, and
> `benchmarks/results/latest.md` has been replaced wholesale: the corpus went
> from 17 records to 2,000, and the adversarial class is scored at `n=60` with
> real rates. Keeping the old number would have been the least honest option
> available. Every figure below was re-read at `2ea44922`, not carried over.

Every slide below was published to permanent storage and asserted `HTTP 200`
before this record was written. These `static.teamily.ai` URLs are the live
copies; the `docs/app/deck/` files are the reviewable source.

## Slide URLs

| # | Slide title | Permanent URL | HTTP |
|---|---|---|---|
| 01 | Cover | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_01.html | 200 |
| 02 | The rebuild — what moved | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_02.html | 200 |
| 03 | What mem20 is | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_03.html | 200 |
| 04 | The tool surface | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_04.html | 200 |
| 05 | Market sizing | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_05.html | 200 |
| 06 | The SOM arithmetic | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_06.html | 200 |
| 07 | Business model | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_07.html | 200 |
| 08 | The adversarial row, shown | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_08.html | 200 |
| 09 | The rerank inversion | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_09.html | 200 |
| 10 | Trust surface | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_10.html | 200 |
| 11 | Our own audit findings | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_11.html | 200 |
| 12 | The ask | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_12.html | 200 |
| 13 | Source register | https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_13.html | 200 |

**Entry point:** slide_01.html (the deck presentation card renders the rest automatically).

## How the 200s were asserted

```bash
for i in 01 02 03 04 05 06 07 08 09 10 11 12 13; do
  curl -sL -o /dev/null -w "slide_$i %{http_code} %{size_download}b\n" \
    "https://static.teamily.ai/sites/bed58ebd-3d4c-4874-9214-6a02240b268d/presentations/mem20-investor-board-deck/slide_$i.html"
done
```

Result: all thirteen returned `200`. The deck is text-only (no images, no
charts), so every slide is a single self-contained HTML document with Google
Fonts as its only external asset.

## Baseline numbers used in this deck — and nothing else

| Fact | Value | Source at `2ea4492209dfaae6afb22ca884132a0d1849bfcf` |
|---|---|---|
| Main / baseline commit | `2ea4492209dfaae6afb22ca884132a0d1849bfcf` | `GITHUB_GET_A_BRANCH` (main) + `git rev-parse HEAD` |
| Tracked files | **8,536** | `git ls-files \| wc -l` |
| VERSION | **3.1.0** | `cat VERSION` |
| Tool surface | **270 tools / 27 domains** | `verify_mcp.py:5`, `.github/workflows/mcp-verify.yml:63`, `README.md:161/184/227/242`, `docs/finance/inputs.json` |
| Open PRs / issues | **0 / 0** | GitHub API `pulls?state=open` + `search/issues?is:issue+is:open` |
| Blended ACV | **$14,000** | `docs/finance/inputs.json` → `house_numbers.blended_acv_usd` |
| TAM | **$1.28B** | `docs/finance/inputs.json` (carried input) |
| SAM | **$282M** | `docs/finance/inputs.json` (carried input) |
| SOM | **$1.68M** | `docs/finance/inputs.json` → 120 accounts × $14,000, $0 variance |
| Retrieval corpus | **2,000 records / 250 queries** | `benchmarks/results/latest.json` → `facts` 700, `simulated` 1300, `queries` 250 |

No other figure was invented. Secondary numbers on the slides (churn 12%,
NRR 1.15, $1,880 hosting, 40/80/120 ramp, tier ladder, retrieval table,
trust checks, corpus scale, latency) are each attributed on-slide to
`docs/finance/inputs.json` or `benchmarks/results/latest.md`.

## What changed from the `45445f48` cut

| Fact | At `45445f48` | At `2ea44922` | Direction |
|---|---:|---:|---|
| Commits since baseline | — | 171 | — |
| Tracked files | 7,975 | 8,536 | +561 |
| VERSION | 3.0.0 | 3.1.0 | released |
| Tool surface | 270 / 27 | 270 / 27 | unchanged |
| Open PRs / issues | 10 / 5 | 0 / 0 | cleared |
| Retrieval corpus | 17 records, 13 queries | 2,000 records, 250 queries | 118× |
| Adversarial `n` | 3 | 60 | 20× |
| Adversarial hit rate | 0.000 (all 3 modes) | 0.167–0.767 (6 modes) | measured |
| `aiohttp` in requirements | absent | `requirements.txt:13` | fixed |

## Deliberately shown, not hidden

- **The rerank inversion.** Production `hybrid` (reranker on) scores `0.167`
  adversarial hit rate at `168.5 ms` p50. The same path with the reranker off
  scores `0.650` at `25.6 ms`. We are paying 6.6× latency for a 48-point
  regression. Slide 09. This is the most useful number in the report and it
  does not flatter the product.
- **That inversion is our reading, not the harness's claim.** The report's
  `trust.rerank_off_comparison` field is `null`; `hybrid-rerank-off` is scored
  as a standalone mode, not as an A/B. `rerank_off_note` says so explicitly.
  Slide 09 states this rather than presenting the contrast as a harness result.
- **Leak rate `0.000` on every row** — the system fails closed rather than
  answering from a stale record.
- **Not comparable to Mem0 92.5 / 94.4 or Zep 94.8** — different corpora, two
  of three private or vendor-defined, different metrics. Nothing here
  reproduces or refutes them.
- **No LoCoMo result is claimed.** The harness has not been run against the
  LoCoMo originals (10 conversations, 1,986 QA). Slide 10 says so.
- **`docs/finance/inputs.json` records `tracked_files: 9873`** against a
  measured **8,536** — stale by 1,337. The gap shrank from 1,898 only because
  the tree grew, not because the file was corrected. Slide 11, finding 01.
- **`lie_status` is registered twice** (`mcp/tools/lie_tools.py:69` and `:77`),
  so 271 assignments expose 270 tools. Recorded in
  `docs/ops/tool-count-270-27.md` as a deliberate, scheduled fix — removing it
  changes the exposed schema.
- **The trust table has no dedicated unanswerable set.** Contradiction is
  scored at `n=40`, but refusal behaviour — the product claim — has no
  dedicated scored corpus. Slide 11, finding 03.

## Closed since the previous cut

- **`aiohttp` is now declared.** `requirements.txt:13` pins `aiohttp>=3.14.5`,
  with a comment naming `mcp/tools/a2a_tools.py:19` as the module-scope
  importer. The clean-install boot defect the last deck raised is fixed.
- **The adversarial class is properly sized.** `n=3` → `n=60` on a
  2,000-record corpus. The `0.000` the last deck led with is gone from every
  real mode; it survives only on the `constant` baseline, where it belongs.

## Files in this directory

```
docs/app/deck/
  PERMANENT_URL.md   this record
  index.html         deck index: slide list, claims, sources, verification table
  slides/slide_01.html ... slide_13.html    the 13 slide documents
```
