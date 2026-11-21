# THE Z CORPS #12 — "THE RERANK THAT RANKED NOTHING"
## Shooting Script & Running-Gags Sheet

**Window:** 20 October 2026 · the window is still empty · 171 commits on `main`, 186 across all refs, HEAD `ac75689f`
**Source:** Post 11, *The Rerank That Ranked Nothing*, 10,260 words, written 20 October 2026
**Structure:** title · credits · Part One divider · 23 illustrated pages · Part Two divider · bible intro · 8 cards · continuity & back matter · end page = **38 pages**

---

## PART ONE — PAGE BY PAGE

| # | Page | Beat | Source |
|---|------|------|--------|
| 1 | The window, still empty | `git rev-list --count HEAD` returns 171; `--all` returns 186; `git log --all --oneline ac756..` returns nothing. The post says so in its opening rather than implying movement. | Post 11; index |
| 2 | PROOF.md, the defect | The heading: the cross-encoder rerank **silently did nothing**. The fix is marked **NOT DONE**. | PROOF.md |
| 3 | The revision is named | `HEAD at time of writing: efd5b23c`. A document that dates itself, which is the thing that will save it. | PROOF.md:1–3 |
| 4 | Every cite lands | 3814 is the `for d in returned:` loop; 3808 is the `_ce_score` lookup. At the revision the document names, both are exactly right. | Corrections log, Post 11 |
| 5 | The machine that ranks nothing | Documents in, the same documents out, in the same order. A gauge pinned at zero. It ran. It returned. It ranked nothing. | Post 11 |
| 6 | Forty-four and twenty | Forty-four documents on the table, twenty with a green mark, twenty-four blank. The arithmetic the code actually contains. | Post 11 |
| 7 | The negative logit | A scored item sorted against unscored ones. A cross-encoder with negative logits sorts **below** items that were never scored at all. | Post 11 |
| 8 | Two of the top ten | Ten ranked slots, two marked. The smallest honest benchmark in the series. | Post 11 |
| 9 | Two entries, one condition | Two index cards both headed HIGH SEVERITY, held together by one pin. A defect counted twice because it was written down twice. | Post 11 |
| 10 | The mechanism that cannot arise | A blueprint of a machine with a pipe that enters and exits without touching anything inside. The explanation the code cannot produce. | Post 11 |
| 11 | The duller arithmetic | The real mechanism laid out as parts: a scoring wheel that only touches twenty of forty-four slips. The rest fall past it unmarked. | Post 11 |
| 12 | **SIDE STORY — Scribe and the wrong revision** | Two copies of the same dated document open side by side. A hand flat between them, a pen unused. He has been comparing them without checking which one the document was written against. | Vignette |
| 13 | Compared against HEAD | A dated printout and a printout headed `HEAD`, a red line drawn between two line numbers that do not match. The error is in the method, not the document. | Corrections log, Post 11 |
| 14 | The draft that was deleted | A title page reading **THE DEFECT THAT FIXED ITSELF**, dropped whole into a bin rather than corrected. Deleted, not patched. | Corrections log, Post 11 |
| 15 | Nothing to fix | One file, two date tags, and a diff printout that is completely empty. The code has run unchanged since `413f175` on 11 October. | Corrections log, Post 11 |
| 16 | The ledger did it properly | A bound ledger dense with dated entries, beside a decimator whose needle stopped short of green and a probe dial reading NO ZERO. | Post 11 |
| 17 | **SIDE STORY — Gabe and the deleted draft** | A page torn out and set aside, its ragged edge visible. Gabe reads the gap where it was, holding the torn page against the binding. | Vignette |
| 18 | Three times, one method | A wall of pinned claims. `SAME 1, DIFF 10` and `LINE NUMBERS DRIFTED` both crossed out. Three figures assembled to fit an argument already believed. | Corrections log |
| 19 | The counter, unconsulted | Dark, unlit, a coat hanging on it. A chalk note: *asked for its command. It has none.* A fixture now, not a character. | Running gag |
| 20 | The ledger, 20 October | The press running sheets of the corrections log. Two rows against Post 11, both applied in place. | Corrections log |
| 21 | Run the command, then read the sentence | The method that caught all three errors, set large. | Corrections log |
| 22 | The room between the answers | Three doors, one open, an empty chair facing it. Right about the revision, wrong about the cause. | Post 11, closing |
| 23 | The corridor | One door sealed, one open, light on the floor. The rerank ranked nothing; the document said so; the reason it gave was not the reason. | Post 11, closing |

---

## RUNNING-GAGS SHEET

| Gag | Origin | This issue | Payoff |
|-----|--------|-----------|--------|
| **The counter** | #1 p7 | A fixture; this issue's count is 44 documents and 20 scored, both from a command | #5 — retired as a coat rack |
| **The number that went down** | #1 p7 | Adds 44, 20, 24, 2, 10, 3802, 3808, 3814 — then withdraws the drift entirely, because the numbers never moved | #5 — 311 is a quotation |
| **Eighty-four identical programs** | #2 | Not a count this issue; a shape — two entries that look like two defects and are one condition | #3 — 145 runtimes are 15 programs |
| **The green that means red** | #1 p8 | A fix marked NOT DONE is the only honest green in the document; beside it a rerank that returns a result set and ranks nothing in it | #5 — zero of 258 printed |
| **/ready** | #1 | A reranker that is wired, called, and returns the input unchanged | #5 — answers 270, polled by nothing |
| **The quiet ledger** | #1 | The failures ledger did this work properly: a decimator that refused, a probe that declined to return a zero | #5 — 114 lines |
| **The decimator that refused** | #1 | The ledger's decimator refused to report success while doing nothing. The reranker did not refuse, and that is the whole defect | #5 — a standing fact |
| **Hyperfine** | #1 | Beside it, a measurement of two of the top ten — the smallest honest benchmark in the series | #5 — exists in no blob |

### New gags seeded in #12

- **The mechanism that cannot arise** — right about the revision, wrong about the cause
- **The defect that fixed itself** — a draft deleted rather than patched
- **The wrong revision** — comparing a dated document against HEAD
- **Two entries, one condition** — the high-severity pair
- **Two of the top ten** — the smallest honest benchmark in the series
- **The probe that declined to return a zero** — the ledger doing it properly

---

## PRIVATE-LIFE THREADS

- **Scribe** (p12) — the wrong revision, and a hand that does not write. Carried from #9 p7, #10 p7 and #11 p12.
- **Gabe** (p17) — the deleted draft, and a gap read rather than filled. Carried from #9 p11, #10 p11 and #11 p17.

## CONTINUITY NOTES

- No character redesigned. Silhouettes, costumes, props and swatches unchanged from #1–#11.
- Palette: obsidian / charcoal / bone, acid-green `#CCFF00` accents only.
- Inking: scratchy dry brush, cross-hatching, newsprint grain.
- The deleted draft on p14 is drawn as a physical object being binned, not as a missing panel — the reader sees that something was removed and that the removal was the honest act.
- The line numbers on p4 are printed as they appear in the document, not as they appear at HEAD. That distinction is the issue.
