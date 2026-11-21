# THE Z CORPS #11 — "THE SAME FILE UNDER NINETY-TWO NAMES"
## Shooting Script & Running-Gags Sheet

**Window:** 20 October 2026 · the window is still empty · 171 commits on `main`, 186 across all refs, HEAD `ac75689f`
**Source:** Post 10, *The Same File Under Ninety-Two Names*, 10,128 words, written 20 October 2026
**Structure:** title · credits · Part One divider · 23 illustrated pages · Part Two divider · bible intro · 8 cards · continuity & back matter · end page = **38 pages**

---

## PART ONE — PAGE BY PAGE

| # | Page | Beat | Source |
|---|------|------|--------|
| 1 | The window, still empty | `git rev-list --count HEAD` returns 171; `--all` returns 186; `git log --all --oneline ac756..` returns nothing. The post says so in its opening rather than implying movement. | Post 10; index |
| 2 | PROOF.md, section 1b | The heading: **228 of 293 packages are clones.** A document that will be quoted for a year. | PROOF.md:88 |
| 3 | The table | 293 scanned · 65 distinct · 228 redundant · 62 unique. Four numbers, one page, no command shown. | PROOF.md:96–99 |
| 4 | Three groups | A: 94 copies at 273 lines. B: 93 at 683. C: 44 at 348. 231 members, and the arithmetic of 231 against 228 is not asked about. | PROOF.md:101–108 |
| 5 | "Verified by direct diff, not inference" | The sentence, set large. It is the most load-bearing sentence in the document and it is about to be tested. | PROOF.md:110 |
| 6 | The exemplar | `mem20adaptiveforgettingenginez` and `mem20adaptivepricingbrainz` — "identical file structure and byte-identical content once each package's own name is substituted." | PROOF.md:111–114 |
| 7 | The names promise | "The names promise distinct capabilities that do not exist." A shelf of identically-labelled jars. | PROOF.md:118 |
| 8 | The re-measurement | Hashing every package: **296** and **220**, in three groups. Not 293. Not 228. The audit's own numbers do not survive being run. | Post 10 |
| 9 | The walk | Eleven files, package name normalised out of both the relative path and the bytes, compared by SHA-256. | Corrections log, Post 10 |
| 10 | SAME 3, DIFF 8 | `runtime.py`, `tests/__init__.py`, `capability.py` shared. `domain.py` and `test_domain.py` differ. | Corrections log, Post 10 |
| 11 | The two that carry the logic | `head -3` on each `domain.py`: one is a forgetting curve, the other a price elasticity fit. The least identical thing two files have ever done. | Corrections log, Post 10 |
| 12 | **SIDE STORY — Scribe and the standing rule** | The ledger open at *publish the grep, never the hand sum*. A hand flat on the page, not writing. | Vignette |
| 13 | The first attempt | The walk compared raw file paths. The package name lives in the path. Every file looked distinct. A measurement that could only return the answer it got. | Corrections log, Post 10 |
| 14 | SAME 1, DIFF 10 | The number the first attempt produced, and the number the post printed. Both wrong, in the same direction, for the same reason. | Corrections log, Post 10 |
| 15 | The narrower claim | "Differs in the files that carry the domain logic" — narrower, and still decisive. The correction that costs the argument nothing. | Corrections log, Post 10 |
| 16 | 142 manifests | One hundred and forty-two generated manifests asserting **PASS**. A validation file whose status field is a signature on a document nobody read. | Post 10 |
| 17 | **SIDE STORY — Gabe and the pencil takings** | The tin of stubs, and beside it a handoff file that says exactly what it did and did not. Gabe reads it twice. | Vignette |
| 18 | The most honest document in the tree | The handoff file. A compliment that lands like a diagnosis, because it is the only document that does not oversell itself. | Post 10 |
| 19 | Six characters where a dash should be | Two literal `\u2014` escape sequences in Post 10's prose. Found by the escape-leak scan, not by reading. | Corrections log, Post 10 |
| 20 | The counter, unconsulted | A fixture now. This issue asks it for the command and it does not have one. | Running gag |
| 21 | The title's own number | "Ninety-Two" appears in the title and in no command in the run. The issue prints the number and prints the absence beside it. | Post 10, self-audit |
| 22 | The ledger, 20 October | Four rows against Post 10, and the log calls them one error. The most precise thing in the run. | Corrections log |
| 23 | The corridor | One door sealed, one open, light on the floor. The count was assembled; the comparison was measured; the difference is the whole book. | Post 10, closing |

---

## RUNNING-GAGS SHEET

| Gag | Origin | This issue | Payoff |
|-----|--------|-----------|--------|
| **The counter** | #1 p7 | A fixture, not a subject; asked for its command, and it has none | #5 — retired as a coat rack |
| **The number that went down** | #1 p7 | Adds 228, 293, 65, 62, 296, 220, 94, 93, 44, 3, 8, 11, 142 — then takes one back | #5 — 311 is a quotation |
| **Eighty-four identical programs** | #2 | Meets its source: 231 members of three groups, and the two picked to prove it are the two that differ | #3 — 145 runtimes are 15 programs |
| **The green that means red** | #1 p8 | A manifest asserting PASS is the greenest object in the repository; 142 of them ran nothing | #5 — zero of 258 printed |
| **/ready** | #1 | A validation file whose status says PASS and whose subject is a corpus, not a service | #5 — answers 270, polled by nothing |
| **The quiet ledger** | #1 | The corrections log's best day: four rows, called one error | #5 — 114 lines |
| **The decimator that refused** | #1 | The per-file walk refused to return a number until the name was normalised out of the path | #5 — a standing fact |
| **Hyperfine** | #1 | Beside it, a harness that measures a corpus and a manifest that certifies without running | #5 — exists in no blob |

### New gags seeded in #11

- **Verified by direct diff, not inference** — and then inferred
- **The exemplar that refuted itself** — a forgetting curve and a price elasticity fit
- **The path that could only say different** — the name inside the path
- **SAME 3, DIFF 8** — the correction that is narrower and still decisive
- **142 signatures, no reader** — the manifest that asserts PASS
- **The most honest document in the tree** — a compliment that lands like a diagnosis
- **Six characters where a dash should be** — found by a scanner, not a reader
- **The title's own number** — the one figure no command produced

---

## PRIVATE-LIFE THREADS

- **Scribe** (p12) — the standing rule, and a hand that does not write. Carried from #9 p7 and #10 p7.
- **Gabe** (p17) — the pencil takings, and a document that undersells itself. Carried from #9 p11 and #10 p11.

## CONTINUITY NOTES

- No character redesigned. Silhouettes, costumes, props and swatches unchanged from #1–#10.
- Palette: obsidian / charcoal / bone, acid-green `#CCFF00` accents only.
- Inking: scratchy dry brush, cross-hatching, newsprint grain.
- The redaction on p21 is drawn as a black bar, not a missing panel — the reader sees that something was removed and the fact survived.
