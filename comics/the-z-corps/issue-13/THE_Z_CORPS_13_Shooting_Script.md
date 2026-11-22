# THE Z CORPS #13 — "THE ASSEMBLER AND THE GATE THAT WAS NEVER BUILT"
## Shooting Script & Running-Gags Sheet

**Window:** 21 November 2026, 16:11:08Z → 23:06:25Z · seven hours · 66 commits on `main`, one every 6.4 minutes · baseline `105b9602`, frontier `77b72a1a`
**Source:** Post 12, *The Assembler and the Gate That Was Never Built*, 68,430 bytes, written 21 November 2026
**Structure:** title · credits · Part One divider · 23 illustrated pages · Part Two divider · bible intro · 8 cards · continuity & back matter · end page = **38 pages**

---

## PART ONE — PAGE BY PAGE

| # | Page | Beat | Source |
|---|------|------|--------|
| 1 | The van, and the list | Cover. A boxy panel van idling at the kerb outside a tin-roofed water shack at 04:12. On the windscreen, a clipboard with two lines: one blank, one reading SCRIBE. The counter on the shack wall reads 412. | Cover |
| 2 | Credits | The issue's own masthead page: title, credits, the window, the frontier SHA, and the one sentence the issue is about. | Front matter |
| 3 | PART ONE divider | A single black field. One line of acid green: *SEVEN HOURS. SIXTY-SIX COMMITS. ONE FILE.* | Divider |
| 4 | One commit every 6.4 minutes | A wall clock with sixty-six tally marks scratched around its rim. The hands have not moved far. | §8 |
| 5 | The file that took fourteen commits | A single sheet of paper on a vast empty table, and beside it a stack of fourteen envelopes, each one a failed attempt to deliver it. | §2 |
| 6 | Thirty kilobytes | A measuring rule laid against the document. The document runs off the end of the rule three times. | §2 |
| 7 | The assembler, first version | A machine that concatenates whatever is in the tray. Three trays, one output chute, no guard. | §2.1 |
| 8 | The run that deleted its own input | The machine's output chute loops back into its own intake. The tray is empty and the machine is still running. | §2.2 |
| 9 | **SIDE STORY — Scribe and the parts directory** | Scribe at a bench with numbered parts laid out in order, a DONE card face-down beside them. He is waiting for the last part before he binds. He does not bind early. | Vignette |
| 10 | The question left open | A published page with a question mark ruled into its margin in green. The page is dated. The question is not answered on it. | §3 |
| 11 | What was searched | Eighteen workflow files pinned in a row, a scripts directory, and the whole tree behind them, all under one lamp. | §3.1 |
| 12 | The word, twenty-five times | Twenty-five index cards, each reading MONOTONIC, pinned in a grid. Not one of them is about a tag. | §3.2 |
| 13 | Three files, compared for equality | Three documents on a bench — VERSION, pyproject.toml, version.hpp — and a gauge between them that only measures whether they match, never whether they rose. | §3.3 |
| 14 | The tag that is an ancestor of its predecessor | Two tags on one branch, drawn as two brass plates on a rail. The later-numbered plate is bolted *behind* the earlier one. | §3.3 |
| 15 | The verdict | An empty gate frame in a fence, hinges rusted, no gate in it. The fence is intact on both sides. | §3.5 |
| 16 | **SIDE STORY — Gabe and the gate that was never built** | Gabe at the water shack, holding a gate latch with no gate attached to it. He turns it over. It is a real latch. It opens nothing. | Vignette |
| 17 | The second question | A dated record in a glass case, and a hand with a key that fits the case. | §4 |
| 18 | The rule, written down | A long docstring printed and pinned: the append-only list, eleven entries, each one a place a record must not be rewritten. | §4.1 |
| 19 | The method | One command, set large: `git log --diff-filter=A --format='%H' -- "$f"` then `git diff "$first" HEAD -- "$f"`. The whole audit is these two lines. | §5.1 |
| 20 | Thirty-one documents, five rewrites | Thirty-one folders on a shelf; five of them have been opened and re-sealed with a different seal. | §5.2 |
| 21 | The three that were missed | Three daily reports, each with a date in its filename and a figure in its table that no longer belongs to that date. | §5.3 |
| 22 | The test that separates them | Two documents side by side: one with a new line appended and the old line still legible beneath; one with the old line scraped out and a new one written over the scar. | §5.5 |
| 23 | The manifest | A ledger claiming 129 rows, and a room containing 172 files. Ten rows describe bytes that have changed. Ten files have no row at all. | §6 |
| 24 | Ten and ten | Two columns of tally marks, ten and ten, under a heading that says the archive describes itself. | §6.1–6.2 |
| 25 | The check nobody wired | A fire alarm mounted on a wall, fully functional, with its wire coiled neatly beside it and never connected. | §6.3 |
| 26 | The corpus is silent | The failures ledger open at 16 November. Every page after it is blank. The busiest seven hours in the book have no entry. | §9 |

---

## PART TWO — BIBLE CARDS

| # | Card | Function |
|---|------|----------|
| 27 | PART TWO divider | Black field, one line: *THE CARDS.* |
| 28 | Bible intro | What the cards are, and the rule that pages are drawn from the cards and never the reverse. |
| 29 | **Scribe** | The narrator. Ledger, pen, second ledger. Stands outside the record. |
| 30 | **Jayson** | The writer. Hoodie, unshaven since #4. Never called Jayson by the Corps. |
| 31 | **Gabe** | The water shack. Tin roof, cold blue dawn. Holds objects that do not do what they look like they do. |
| 32 | **Jme** | Firm. Never talked out of a view. Paints what has not happened yet. |
| 33 | **Hermes** | Head always cropped by the panel edge, always lost in black. A rule, not a mood. |
| 34 | **mem20corez** | The core runtime. The one that keeps the count. |
| 35 | **Drift** | Never attacks. Only ever a difference between two panels. |
| 36 | **The Assembler** | New card. A machine that joins parts. It has no opinion about order. |

---

## RUNNING-GAGS SHEET

| Gag | Origin | This issue | Payoff |
|-----|--------|-----------|--------|
| **The counter** | #1 p7 | Reads 412 on the cover and on p26. Never corrected, never explained, never consulted. | #5 — retired as a coat rack |
| **The number that went down** | #1 p7 | 66, 14, 5, 4, 30, 101,467, 129, 172, 10, 10 — every one from a command | #5 — 311 is a quotation |
| **Eighty-four identical programs** | #2 | Not a count; a shape — fourteen commits that are the same commit, retried | #3 — 145 runtimes are 15 programs |
| **The green that means red** | #1 p8 | A gate that is green because it was never built, and a check that is red on a commit that did nothing wrong | #5 — zero of 258 printed |
| **/ready** | #1 | The manifest's `--check` mode: it works, it exits 1, nothing calls it | #5 — answers 270, polled by nothing |
| **The quiet ledger** | #1 | The failures corpus has no entry for the busiest seven hours in the book | #5 — 114 lines |
| **The decimator that refused** | #1 | `check_version_consistency.py` refuses to answer a question it was never asked | #5 — a standing fact |
| **Hyperfine** | #1 | The tag-monotonicity gate: described in a plan, absent from the tree | #5 — exists in no blob |

### New gags seeded in #13

- **The gate that was never built** — a rule with no executable check behind it
- **The run that deleted its own input** — a workflow that consumed the thing it was assembling
- **Thirty kilobytes** — a tool constraint meeting a document three times its size
- **The check nobody wired** — a working verifier that no workflow invokes
- **The scar and the appended line** — the visual test for correction versus rewrite
- **The ancestor tag** — a version number that is older than the one before it

---

## PRIVATE-LIFE THREADS

- **Scribe** (p9) — the parts directory, and a hand that will not bind early. Carried from #9 p7, #10 p7, #11 p12, #12 p12.
- **Gabe** (p16) — a latch with no gate. Carried from #9 p11, #10 p11, #11 p17, #12 p17.

## CONTINUITY NOTES

- No character redesigned. Silhouettes, costumes, props and swatches unchanged from #1–#12.
- Palette: obsidian / charcoal / bone, acid-green `#CCFF00` accents only. Red and blue are used once each, on p14 and p22, and nowhere else.
- Inking: scratchy dry brush, cross-hatching, newsprint grain.
- The empty gate frame on p15 is drawn as a real gate frame with real hinges and no gate — the reader must see that the hardware is present and the gate is not.
- The alarm on p25 is drawn wired and functional, with the wire coiled and unconnected. It is not broken. It is not connected. That distinction is the issue.
- The counter's 412 is drawn identically on p1 and p26. No emphasis, no explanation, no correction.
- Drift appears on p35 only as a difference between two panels, never as an action.

## VOICE RULES (BINDING)

1. Captions are dry, declarative, and never explain the joke.
2. A number is always the number that was measured, with its source named on the credits page.
3. Where two figures disagree, print both and say which one the audit settled.
4. No invented lore. If the record is silent, the caption says the record is silent.
5. Side stories get one location, two people, no plot, one line that lands.
6. The chronicle's own errors are published, not hidden.

## SOURCE DISCIPLINE

Every figure in this issue is quoted from Post 12 (`serial-2026-11-21b.md`), its §8 window table, or the corrections block. The 66 commits, the 14 assembly commits, the 5 rewrites, the 4 probes, the 30 narrative commits, the 101,467 bytes, the 129 manifest rows and the 172 files present are all printed as the post prints them. The 6.4-minute interval is the post's own division. Nothing in this issue is invented lore; where the post says it could not verify something, the caption says so.
