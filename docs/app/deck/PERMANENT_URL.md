# Permanent URL Record — mem20 Investor & Board Deck

**Recorded:** 2026-10-27
**Baseline commit:** `45445f4850377814cd95b7fa50c0a9153f76c163` (main head)
**Deck source (this directory):** `docs/app/deck/`
**Branch:** `content/ws3-investor-deck`

> **Rebase note.** This branch was rebased from `75243c4c6dd5` (4 ahead / 1
> behind) onto main `45445f48`. The only commit it was behind was the
> docs/ops workload roster (#116), which touches no file this deck reads, so
> the rebase was conflict-free. Every figure was then **re-read at
> `45445f48`** rather than carried over: tracked files moved 7,974 -> **7,975**
> and the finance file's staleness moved 1,899 -> **1,898**. The previous
> baseline `1264076698a00878acc3adacf7bf1d51eea315cc` is superseded and is no
> longer cited anywhere in the deck.

Every slide below was published to permanent storage and asserted `HTTP 200` before this record was written. These `static.teamily.ai` URLs are the live copies; the `docs/app/deck/` files are the reviewable source.

## Slide URLs

| # | Slide title | Permanent URL | HTTP |
|---|---|---|---|
| 01 | Cover | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_01.html | 200 |
| 02 | The baseline, pinned | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_02.html | 200 |
| 03 | What mem20 is | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_03.html | 200 |
| 04 | The tool surface | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_04.html | 200 |
| 05 | Market sizing | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_05.html | 200 |
| 06 | The SOM arithmetic | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_06.html | 200 |
| 07 | Business model | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_07.html | 200 |
| 08 | The adversarial row, shown | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_08.html | 200 |
| 09 | What 0.000 means | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_09.html | 200 |
| 10 | Trust surface | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_10.html | 200 |
| 11 | Our own audit findings | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_11.html | 200 |
| 12 | The ask | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_12.html | 200 |
| 13 | Source register | https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_13.html | 200 |

**Entry point:** slide_01.html (the deck presentation card renders the rest automatically).

## How the 200s were asserted

```bash
for i in 01 02 03 04 05 06 07 08 09 10 11 12 13; do
  curl -sL -o /dev/null -w "slide_$i %{http_code} %{size_download}b\n" \
    "https://static.teamily.ai/sites/52de7e66-b182-4074-bb00-30144dc0bf53/presentations/mem20-investor-board-deck/slide_$i.html"
done
```

Result: all thirteen returned `200`, sizes 9,102-17,829 bytes. Slide 08
(17,829 B) is the largest because it carries the full nine-row retrieval table.

## Baseline numbers used in this deck — and nothing else

| Fact | Value | Source at `45445f4850377814cd95b7fa50c0a9153f76c163` |
|---|---|---|
| Main / baseline commit | `45445f4850377814cd95b7fa50c0a9153f76c163` | `GITHUB_GET_A_BRANCH` (main) + `git rev-parse HEAD` |
| Tracked files | **7,975** | `git ls-files \| wc -l` |
| VERSION | **3.0.0** | `cat VERSION` |
| Tool surface | **270 tools / 27 domains** | `verify_mcp.py:5`, `.github/workflows/mcp-verify.yml:63`, `README.md:161/184/227/242`, `docs/finance/inputs.json` |
| Blended ACV | **$14,000** | `docs/finance/inputs.json` -> `blended_acv` |
| TAM | **$1.28B** | `docs/finance/inputs.json` (carried input) |
| SAM | **$282M** | `docs/finance/inputs.json` (carried input) |
| SOM | **$1.68M** | `docs/finance/inputs.json` -> 120 accounts x $14,000, $0 variance |

No other figure was invented. Secondary numbers on the slides (churn 12%,
NRR 1.15, $1,880 hosting, 40/80/120 ramp, tier ladder, retrieval table,
trust checks, corpus scale, latency) are each attributed on-slide to
`docs/finance/inputs.json` or `benchmarks/results/latest.md`.

## Deliberately shown, not hidden

- **Adversarial retrieval: hit rate `0.000`, MRR `0.000`, on `n=3`** for all
  three modes (hybrid, keyword, semantic) - slide 08, with slide 09 reading it.
- **Leak rate `0.000` on every row** - the system fails closed rather than
  answering from a stale record.
- **Not comparable to Mem0 92.5 / 94.4 or Zep 94.8** - different corpora, two
  of three private or vendor-defined, different metrics. Nothing here
  reproduces or refutes them.
- **`docs/finance/inputs.json` records `tracked_files: 9873`** against a
  measured **7,975** - stale by 1,898.
- **`aiohttp`** imported at module scope in `mcp/tools/a2a_tools.py:19`, reached
  from `mcp/server.py:87`, and absent from both `requirements.txt` and
  `requirements-optional.txt` - a clean install cannot boot the server.
- **Drift:** none. This deck is pinned to `45445f48`, which is main's head at
  the time of writing, so a reviewer diffing against main sees the same tree.
  The earlier cut at `1264076` is superseded.

## Files in this directory

```
docs/app/deck/
  PERMANENT_URL.md   this record
  index.html         deck index: slide list, claims, sources, verification table
  slides/slide_01.html ... slide_13.html    the 13 slide documents
```
