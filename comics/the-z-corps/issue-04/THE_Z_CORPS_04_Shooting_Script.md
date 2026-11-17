# THE Z CORPS #4 — "TWENTY-TWO OF TWENTY-THREE"
## Illustrated Shooting Script (40 pages + back-matter vignette)

**Story & Art Direction:** Grok + JMoore
**Tone:** 7.8 — gritty noir, precise, darkly satirical
**Narrator:** Scribe
**Window:** 20 October 2026 → 7 November 2026
**Structural spine:** Post 09 *The Four-Channel Claim*, Post 10 *The Same File Under Ninety-Two Names*, Post 11 *The Rerank That Ranked Nothing*, Post 12 *The Protocol Nobody Filed Under*, Post 13 *The Eight Members and the Ninth Crate*, Post 14 *The Issue List That Closed Itself*, Post 15 *The Gate That Never Opened*, Post 16 *The Install Step That Nobody Listed*, Post 17 *Sixty-Six Commits, One Number*, Post 18 *The Batch and the Empty Field*, Post 19 *The Red That Was Green*, Post 20 *The Number Three SDKs Agreed On*, Post 21 *Ten Defects, Nine Commits, Three Bad Writes*, Post 22 *The Number That Outran Its Own Guards*, Post 23 *The Corpus That Started Writing Back*, Post 24 *The Gate That Did Not Move*.

**Premise.** The launch finally happens — not as a ceremony, but as one `pip install` that flips exit 1 to exit 0 and prints `270`. And the gag dies: the tool count stops being a displayed number and becomes a constant in three shipping SDKs, each with a guard, each deriving it a different way. The counter is retired. What replaces it is worse, and funnier, and true.

**Sourcing rule.** Every gag, number and quotation in this issue is a real mem20 incident from the chronicles, the audit corpus, the failures ledger or the diary. Nothing is invented. Where a figure is disputed the issue prints both figures and says which one the audit settled.

---

## THE RUNNING GAGS — WHERE THEY DIE

| Gag | Born (#2) | Paid off (#3) | **Issue #4 — the death** |
|---|---|---|---|
| **The counter** | p.15–16, wired to a hand sum, 412 on day one | p.26, p.37 — 258/260 reconciled to 257; still 412 | **p.13, p.28** — 66 commits in one day make every document say 270/27. The number converges. The counter is retired, not corrected. |
| **The number that went down** | p.15, "I added them" | p.11, p.18 — 293→65; 25→~17; 12→40 | **p.24, p.27** — 270 is now a constant in three SDKs. It stops going down. It starts going *up*: 270→272→306→311. |
| **Eighty-four identical programs** | p.18, the first Ctrl-C | p.11, p.12 — 228 of 293 | **p.19** — 145 `runtime.py` files are fifteen programs, 84 of them one. 148 domains on 15 engines. |
| **The green that means red** | p.19–20, `collected 0 items`, exit 5 | p.36 — 132 ran, 1,400 never did | **p.21, p.37** — the Tests job dies on exit 4 while the step guards only 5; the unit marker collects **zero of 258**. |
| **/ready** | p.21, polled by nothing | p.38 — querying a host it cannot reach | **p.26** — asked on a live socket, it answers `{"status":"ready","tools":270}`. It was always correct. Still polled by nothing. |
| **The quiet ledger** | p.22, one entry then silence | p.21, p.39 — the NOT DONE list | **p.22** — the daily ops report stops on 27 October and is never written again. |
| **The decimator that refused** | p.24, one lies, one refuses | p.14 — rule two of UPGRADE.md | **p.31** — one refusal kept: the fifteen runtimes diffed and recorded, not consolidated. |
| **hyperfine** | p.29, commissioned, absent | p.38 — the launch that cannot start | **p.10** — the launch that starts. One `pip install`. Exit 1 → 0. It prints 270. |
| **The standing rule** | — (#3) | p.34 — never removed, deleted, quarantined or dropped | **p.9** — the audit's P0 was deleted four days before the audit was written. The rule arrives after the hole. |
| **Union merges** | p.19 — resolve both sides | p.37 — five merges in eleven minutes | **p.18** — 21 roster branches land as one merge and a 155-file copy. |
| **The manual step** | — (#3) | p.35 — Settings → Pages → Source | **p.12** — the gate that never opened, and the six runs that prove it. |
| **The branch that is not fixed** | — (#3) | p.36 — three gitlinks on five of six branches | **p.18** — the branch estate arrives as a copy, not a merge. |
| **"The issues win"** | — (#3) | p.39 — a state board that names its authority | **p.6** — a board whose critical item was deleted four days before it was listed. |

**New gags seeded here, for Issue #5:**
- **PLACEHOLDER_B5** — seven published documents replaced with eleven characters, repaired fifty-six seconds later (p.14)
- **308 lines to 11** — a workflow replaced by a commit that accepts `None or 0` (p.15)
- **The manifest that grows a hole a day** — 27 → 32 of 128, and nothing regenerates it (p.16)
- **Adversarial 0.0** — a hit rate of zero across every mode, published with its own caveat (p.17)
- **The static_assert nobody builds** — the strongest guard in the company, compiled by no workflow (p.25)
- **The table that sums to 242** — 28 rows, 29 claimed, and a regex that dropped the row with two code spans (p.27)
- **The string that did not move** — 89 of 212, character-for-character, because numerator and denominator grew together (p.36)
- **The WAV header** — hard-codes mono while the struct reading it parses channels from the file (p.38)

---

## PAGE 1 — COVER

Full-bleed splash. The server cathedral at its fullest yet — racks three-quarters lit, the ranks real, the aisle long. Jayson at the desk, hoodie, clean-shaven for the first time in the series, which reads as wrong. On the desk: a single wheel file, held down by a mug, and a terminal printing `270`. Above him the wall counter, its digits half-rotated and going dark, a hand reaching up to unplug it. Behind, Drift — now the height of the aisle, still not touching the ceiling, smiling, and for the first time somebody is looking at it. At the bottom left, in heavy shadow, the second building with its own sign: **CLAUD'S CURSER**, its counter bright and correct.

Top left: MEM20 COMICS logo, No. 4, $4.99 US. Bottom: **THE Z CORPS #4 — TWENTY-TWO OF TWENTY-THREE**. Barcode 424342434244. Light-blue thin signature: **JMoore**.

**Caption:** TWENTY-TWO PACKAGES IN THE GREEN SET.
**Caption:** THE TWENTY-THIRD WAS DELETED FOUR DAYS BEFORE ANYBODY WROTE THE LIST.

---

## PAGE 2 — 20 OCTOBER: THE WINDOW THAT WAS EMPTY

**1** Wide, cold: the cathedral, four identical chairs, one man, four posts pinned to a board with the same date on them.
**Caption:** Four consecutive posts. One frontier. `git rev-list --count HEAD` returns 171, and `--all` returns 186, and `git log --all --oneline ac75689..` returns nothing.

**2** The commit graph as a physical object, and it is a wall.
**Caption:** The repository did not move for six posts. Each post said so in its opening rather than implying movement.

**3** Scribe at the desk with four manuscripts, all the same length.
**Scribe:** Four posts, one window, nothing moved.
**Jayson:** So what did we write about?
**Scribe:** What the repository says about itself. It is the only thing in the building that was still producing new material.

**4** Jayson looking at the wall of nothing.
**Jayson:** That's not a story.
**Scribe:** It is the *most* honest kind. A window with no commits is a window where the only thing that changed was the claim.

**Final caption:** The next six pages are what the repository said about itself while standing still.

---

## PAGE 3 — THE FOUR-CHANNEL CLAIM

**1** A wheel held up to the light, clean, installable, and behind it a server that is not there.
**Caption:** A wheel that installs cleanly and cannot start. Fourteen entries, no server.

**2** Four distribution channels drawn as four doors, and behind every one of them the same empty room.
**Caption:** A Debian package carrying `2.1.0~rc2` while the tree is at 3.0.0. A compose file carrying the same dead version. A README badge pointing at a hostname that does not resolve.

**3** Scribe reading the badge, and the badge reading back nothing.
**Scribe:** Four channels documented. An artifact containing none of them.
**Jayson:** The documentation is aspirational.
**Scribe:** The documentation is a *forecast*. A forecast is a claim about a future that has not been scheduled.

**4** The publish gate, drawn as three gates, only one of which has a lock.
**Caption:** And a publish gate that is actually three different gates, only one of which involves a credential.

**Final caption:** A channel is not a channel until a stranger can walk through it.

---

## PAGE 4 — THE SAME FILE UNDER NINETY-TWO NAMES

**1** 296 packages on a shelf, and a hand hashing them one at a time.
**Caption:** PROOF.md says 228 of 293 packages are clones that differ in nothing but their own name, and names a specific pair as the proof.

**2** The hash results: 296 and 220 in three groups.
**Caption:** Hashing every package finds 296 and 220 in three groups. The scaffold claim is nearly right. The number is wrong, the scope was never stated.

**3** The named pair, opened, and they are not the same file. One implements a forgetting curve. One implements a price elasticity fit. All five source files differ.
**Scribe:** The exemplar is the wrong example.
**Jayson:** The claim was right.
**Scribe:** The claim was *nearly* right, and the proof of it was a pair that differs in all five of its source files. A true statement defended by a false exhibit is a false statement with better manners.

**4** 142 generated manifests, each asserting PASS.
**Caption:** Also in the tree: 142 generated manifests asserting PASS, and a handoff file that is the most honest document in it.

**Final caption:** Check the exhibit, not the claim. The claim will survive; the exhibit is what a reader will test.

---

## PAGE 5 — THE RERANK THAT RANKED NOTHING

**1** The reranker, belt not turning, and forty-four documents going past it unscored.
**Caption:** PROOF.md records that the cross-encoder rerank silently did nothing, marks the fix NOT DONE, and names its revision.

**2** The revision, right, and the line numbers landing — and the mechanism it gives cannot arise from the code.
**Caption:** The revision is right and the line numbers land. The mechanism it gives cannot arise from the code.

**3** The duller arithmetic underneath: twenty of forty-four documents scored, a re-weighted score sorted against a raw one.
**Scribe:** Twenty of forty-four scored. A re-weighted score sorted against a raw one.
**Jayson:** That's not a bug, that's a *comparison*.
**Scribe:** It is a comparison between two numbers that were never meant to be in the same list. It is arithmetic, and arithmetic is worse than a bug, because a bug can be fixed.

**4** Two high-severity entries collapsing into one condition.
**Caption:** Two high-severity entries turn out to be one condition. The failures ledger that did it properly is cited in the same document — including a decimator that refused and a probe that declined to return a zero.

**Final caption:** A wrong mechanism in a right report is still a wrong report. The revision number is not the finding.

---

## PAGE 6 — THE PROTOCOL NOBODY FILED UNDER

**1** A three-agent operating protocol, printed, pinned, and untouched: ownership boundaries, a claim-per-file rule, a seven-day abandonment lease.
**Caption:** Committed once, on 15 October at 16:20:03, and never edited.

**2** The claim file that was never created — an empty slot in a filing cabinet with a label on it.
**Caption:** No claim file was ever created.

**3** The state board, still listing an item as pending, and behind it the commit that deleted that item four days earlier: *space bunny strike 2*.
**Scribe:** The board's own in-flight item was merged on 16 October and the board was never told.
**Jayson:** And the critical one?
**Scribe:** Deleted four days before the board listed it as pending, by a commit called *space bunny strike 2*.

**4** The review flow, running for fifty-five minutes, then stopping.
**Caption:** The review flow ran for fifty-five minutes, then stopped. One command in the bundle could have been a gate.

**Final caption:** A protocol is not a practice. A practice is what happens when nobody is checking the protocol.

---

## PAGE 7 — THE EIGHT MEMBERS AND THE NINTH CRATE

**1** A Rust workspace rendered as a building with eight rooms, each with a nameplate: `braid`.
**Caption:** Eight members. 12,615 lines. A single write authority binding a capability token, a policy snapshot and an audit pre-commitment into one atomic triplet.

**2** A wildcard rule drawn as a one-way door.
**Caption:** A wildcard rule that is one-directional, so a narrow grant cannot mint broad power. An escalation path that requires the base policy to *deny* the operation. A policy floor that holds no matter how many tokens are presented.

**3** The README claiming 72 tests, and the tree holding 76.
**Scribe:** Seventy-two claimed. Seventy-six in the tree.
**Jayson:** That's the good direction.
**Scribe:** It is the good direction and it is still a number nobody measured before writing it down.

**4** A ninth crate, outside the building, depending on all eight, not a member.
**Caption:** A ninth crate depends on all eight and is not a member. Two functions are defined and never called. And the README's own verification section admits to a flaky bug in the test that is supposed to prove convergence.

**Final caption:** The most rigorous subsystem in the estate documented its own flaky test. That is not a weakness. That is the only reason to believe the other seventy-five.

---

## PAGE 8 — 24 OCTOBER: THE REPOSITORY MOVES

**1** A dam breaking, quietly, in an office.
**Caption:** After six consecutive posts reporting the same three numbers, the repository moved. `git rev-list --count HEAD` returns 232, was 171. `--all` returns 307, was 186.

**2** 61 commits on `main`, 136 across all refs, laid out as a stack.
**Caption:** The window holds 61 commits on `main` and 136 across all refs.

**3** Thirty-four of the sixty-one subjects, each with an issue number in it.
**Scribe:** Thirty-four of sixty-one subjects name an issue or a pull request.
**Jayson:** So it's not a feature.
**Scribe:** It is a *list being worked through*. That is a different kind of progress and it looks identical on a graph.

**4** The audit document, 397 lines, dated 2026-10-15, with a standing rule at the top.
**Caption:** The list is `docs/audit/2026-10-repository-audit.md`, 397 lines, dated 2026-10-15, and it carries a standing rule at the top: *existing functionality in mem20 is never removed, deleted, quarantined, or dropped.*

**Final caption:** The rule is at the top of the document. Read it before the list.

---

## PAGE 9 — THE P0 THAT WAS ALREADY DELETED

**1** The audit's first item, marked CRITICAL, and a hole where the file should be.
**Caption:** The first item on the list, the one marked *critical* and protected by a standing rule, had already been deleted four days before the audit was written.

**2** Twenty-five file paths, each with a small tombstone.
**Caption:** The audit itemised twenty-five files that no longer existed.

**3** Scribe with the rule in one hand and the hole in the other.
**Scribe:** The rule says nothing is ever removed. The list says twenty-five things were.
**Jayson:** So the rule came after.
**Scribe:** The rule came after, and it is written impersonally, which is how a value looks when it is everybody's. It is also how a rule looks when it is a *reaction*.

**4** A commit whose subject says it restored a file, and which added fifty-six lines.
**Caption:** Also in the window: a commit whose subject says it restored a file and which added fifty-six lines.

**Final caption:** A rule that arrives after the hole does not fill the hole. It only stops the next one.

---

## PAGE 10 — THE INSTALL STEP THAT NOBODY LISTED

**1** A workflow file, and inside it a script that has never once executed.
**Caption:** The tool-count assertion was never wrong. It never once executed.

**2** `aiohttp` imported at module scope, line 19, in a module `server.py` imports unconditionally.
**Caption:** `aiohttp` is imported at module scope on line 19 of a module `server.py` imports unconditionally.

**3** Seven sub-packages declaring it, and the root declaring it nowhere — not in `requirements.txt`, not in `pyproject.toml`, at any commit on any ref.
**Scribe:** Seven sub-packages. None of the root.
**Jayson:** So it was declared.
**Scribe:** It was declared *seven times in the wrong place*. That is not a declaration. That is a rumour with good distribution.

**4** One `pip install`. Exit 1 becomes exit 0. And it prints: **270**.
**Caption:** One `pip install` flips exit 1 to exit 0 and prints 270.

**5** The launch, finally: a terminal, a wheel, a number, and nobody in the room but two people.
**Scribe:** That's the launch.
**Jayson:** That's a `pip install`.
**Scribe:** That is the launch. Everything else was a rehearsal with props.

**Final caption:** The gate had been failing for six runs on a missing package that was declared in seven places and installed in none.

---

## PAGE 11 — THE GUARD ADDED AT 17:33 AND BROKEN AT 17:59

**1** A guard being bolted into place, 17:33.
**Caption:** The guard was added at 17:33.

**2** Twenty-six minutes later, a commit titled *unbreak MCP startup*, and the guard coming off.
**Caption:** And broken at 17:59, twenty-six minutes later, by a commit titled *unbreak MCP startup*.

**3** Scribe holding both commits, one in each hand.
**Scribe:** Twenty-six minutes.
**Jayson:** It was blocking startup.
**Scribe:** It was blocking startup *correctly*. The guard was right and the tree was wrong, and the commit that fixed the symptom removed the only thing that would have told you.

**4** Four install steps, four different package lists, and none of them reading the declaration.
**Caption:** Four install steps, four different package lists, and none consumes the declaration.

**Final caption:** A guard removed to make a build pass is a guard that was doing its job.

---

## PAGE 12 — THE GATE THAT NEVER OPENED

**1** Six runs of `MCP verify`, six red, spanning 23–24 October.
**Caption:** Six runs. Six failures. Zero successes.

**2** The per-step conclusions: steps 1–5 `success`, step 6 `failure`.
**Caption:** The failure is at step 6, *Verify the MCP handshake and tool count*, with steps 1–5 all success.

**3** Scribe reading the step list, and the log archive returning 403.
**Scribe:** Every step before the assertion succeeded. The setup was never the problem.
**Jayson:** And the log?
**Scribe:** Returns 403. The assertion message is not quoted anywhere in this issue, because I could not read it.

**4** The workflow checking out with `fetch-depth: 1` and then asserting the checkout really is shallow.
**Caption:** It checks out with `fetch-depth: 1` and then asserts the checkout really is shallow, so the regression guard cannot be disabled by changing the checkout depth.

**Final caption:** A gate that has never opened is not evidence that it works. It is evidence that it is *connected*.

---

## PAGE 13 — THE NUMBER CONVERGES

**1** 66 commits in one UTC day, nearly all of them the same edit.
**Caption:** 66 commits in one UTC day, nearly all of them making every document say *270 tools / 27 domains* instead of *268 / 26*.

**2** A hundred documents, each being corrected by hand, one at a time.
**Caption:** The number converged.

**3** Scribe watching the counter on the wall, which has not moved.
**Scribe:** Four other things did not converge.
**Jayson:** Name one.
**Scribe:** A batch edit replaced seven published documents with the eleven characters `PLACEHOLDER_B5`.

**4** The counter, still reading 412, and a hand reaching for the plug.
**Caption:** And the counter still read four hundred and twelve.

**Final caption:** A number that converges by hand is a number that will diverge by hand.

---

## PAGE 14 — PLACEHOLDER_B5

**1** Seven published documents, and then the same seven, each containing eleven characters.
**Caption:** A batch edit replaced seven published documents with the eleven characters `PLACEHOLDER_B5`.

**2** Fifty-six seconds later, the repair: two text files restored, three HTML files replaced with a different edition.
**Caption:** The repair came fifty-six seconds later. It restored the two text files and replaced the three HTML ones with a different edition.

**3** Scribe holding the eleven characters up to the light.
**Scribe:** Eleven characters. Seven documents. Fifty-six seconds.
**Jayson:** It was caught.
**Scribe:** It was caught by *looking*. The write reported success. The write always reports success. That is the entire problem with writes.

**4** The same shape, three more times in the same window.
**Caption:** The same shape appears three more times in this window — twice in the chronicle's own work, once in a document it was editing — and the mechanism is identical in all four: a write was issued and its result was not read back.

**Final caption:** Read the file back. It is one line of code and it is the only line that has ever caught this.

---

## PAGE 15 — 308 LINES TO 11

**1** A 308-line workflow, and a commit whose subject accepts `None or 0` for a test parameter.
**Caption:** A commit whose subject accepts `None or 0` for a test parameter replaced a 308-line workflow with 11 lines.

**2** The 11 lines, running twice in that state before anyone noticed.
**Caption:** The workflow ran twice in that state before anyone noticed.

**3** Scribe counting the lines.
**Scribe:** Three hundred and eight to eleven.
**Jayson:** It still ran.
**Scribe:** It ran, and it concluded, and it concluded *nothing*, which is the only conclusion eleven lines can reach.

**4** The restore: 11 back to 308.
**Caption:** Restored. The diff is 297 lines and the commit message is one sentence.

**Final caption:** A workflow is not a script. It is a promise about what will be checked, and eleven lines cannot keep a promise that long.

---

## PAGE 16 — THE MANIFEST THAT GROWS A HOLE A DAY

**1** A manifest, 128 rows, and 27 of them wrong.
**Caption:** The archive's own integrity list grew from 27 mismatched rows to 32.

**2** An earlier "fix" writing a 68-character value into a 64-character column, still in the file.
**Caption:** An earlier fix to one row wrote a 68-character value into a 64-character column, which is still in the file.

**3** Scribe with the manifest, and nothing regenerating it.
**Scribe:** Thirty-two of a hundred and twenty-eight, and nothing regenerates it.
**Jayson:** So it drifts.
**Scribe:** It does not drift. Drift implies motion. It *rots*, and it rots at exactly the rate the archive grows.

**4** 63 published files sitting outside the manifest entirely.
**Caption:** And 63 published files sit outside it entirely.

**Final caption:** A manifest that is maintained by hand is a manifest that describes the day it was written.

---

## PAGE 17 — ADVERSARIAL 0.0

**1** A benchmark table, every cell reading 0.0.
**Caption:** The benchmark results publish a `hit_rate` of 0.0 for every mode on adversarial queries, over a corpus of 28 entries.

**2** The notes field, where the result explains itself.
**Caption:** And they say so in their own `notes`.

**3** Scribe reading a zero that is honest.
**Scribe:** Zero across every mode.
**Jayson:** That's a failure.
**Scribe:** That is a *measurement*. A failure is a zero nobody published. This one is in the table, in the notes, and in the record, and it is the most useful number in the window.

**4** The same window: every Python job green, and the only consistently failing job configured as an *issue* so the run can conclude green anyway.
**Caption:** Every Python job is green. The repository's only consistently failing job is `cargo check braid workspace`, configured as an *issue* so the run can conclude green anyway.

**Final caption:** A published zero is worth more than an unpublished pass.

---

## PAGE 18 — THE BATCH

**1** 103 commits in seventy hours, moving 1,371 files.
**Caption:** 103 commits in seventy hours, moving 1,371 files.

**2** Twenty-one roster branches, each certified "delivered", landing as one merge and a 155-file copy off a working directory.
**Caption:** A branch estate of twenty-one roster branches certified *delivered* lands as one merge and a 155-file copy off a working directory.

**3** The commit that lands it, titled "162 files".
**Scribe:** One hundred and fifty-five files copied. The commit is titled *162 files*.
**Jayson:** Off by seven.
**Scribe:** Off by seven, in a commit whose entire subject is a count. That is not a typo. That is a number written from memory.

**4** The missing `aiohttp` declaration, finally fixed — in a comment block that names the defect perfectly, inside a bulk commit whose subject does not mention it.
**Caption:** Post 16's missing `aiohttp` declaration is finally fixed, in a comment block that names the defect perfectly, inside a bulk commit whose subject does not mention it.

**Final caption:** And the gate that would prove it still installs three packages by hand and fails an eighth time.

---

## PAGE 19 — 135 DOMAINS, 15 ENGINES

**1** 135 domain modules, each genuinely different.
**Caption:** 135 domain modules that are genuinely 135 different modules.

**2** 131 duplicated runtime files, and a date proving they are older than the window that inherited them.
**Caption:** 131 duplicated runtime files that turn out to be older than the window that inherited them.

**3** 145 `runtime.py` files, sorted into fifteen piles, one pile of 84.
**Scribe:** One hundred and forty-five runtimes. Fifteen programs. Eighty-four of them are one program.
**Jayson:** And the domains?
**Scribe:** One hundred and forty-eight genuinely distinct domains. The estate is 148 domains running on 15 engines, manufactured six at a time by a script that satisfied the only criterion a script could check.

**4** The closing commit asserting **0 stubs remaining**, and a twenty-line script counting one.
**Caption:** A closing commit asserts *0 stubs remaining* where a twenty-line script counts one.

**Final caption:** *0 stubs remaining* is true by the definition the commits establish and misleading by the definition a reader assumes.

---

## PAGE 20 — THE TESTS JOB DIES ON EXIT 4

**1** A pytest run, and the step above it with careful machinery for exit 5.
**Caption:** The *Tests* job dies on pytest exit 4 while the step above it has careful machinery for exit 5.

**2** The green set naming 22 packages, and one of them deleted on 29 October.
**Caption:** `ci.yml`'s green set names 22 packages. `mem20adaptiveinterfacecomposerz` is not one of them and has not been since `e9a15295` deleted it on 29 October.

**3** Scribe with the error: `ERROR: file or directory not found`, exit 4.
**Scribe:** Exit four. Usage error. The guard handles five.
**Jayson:** So it fails loudly.
**Scribe:** It fails *loudly and unreadably*, which in a dashboard is the same as failing quietly. Ninety-two commits of red and nobody had read the cause.

**4** The second defect: `-m unit` matching 1 of 291 test files, and that one outside the set.
**Caption:** And `-m unit` matches 1 of 291 test files, and that one is outside the set — so the step would pass on an empty selection if the directory were restored.

**Final caption:** Without the marker, the same directories run 197 passed, 1 skipped, in 4.07 seconds.

---

## PAGE 21 — THE DAILY REPORT STOPS

**1** A daily operations report, the only document in the tree that records failure in prose.
**Caption:** The daily operations report is the only document in the tree that records failure in prose.

**2** 27 October. The last entry. And then a blank page, and then another.
**Caption:** It stops on 27 October and is never written again.

**3** Scribe standing at the empty lectern.
**Scribe:** Eight blockers carried forward verbatim, every day, and then nothing.
**Jayson:** Somebody stopped writing it.
**Scribe:** Somebody stopped *reading* it, and then somebody stopped writing it, and the order of those two events is the whole history of documentation.

**4** The failures corpus, newest entry 29 September, 26 days and 141 commits old.
**Caption:** And the failures corpus's newest entry is 29 September — 26 days and 141 commits before this window.

**Final caption:** A ledger nobody reads is a ledger that stops being written. That is not neglect. That is arithmetic.

---

## PAGE 22 — THE GATE GOES GREEN

**1** The Rust `braid` gate, red for weeks, and then green for the first time.
**Caption:** The Rust `braid` gate turns green for the first time. Both steps ran.

**2** The cause, in a comment in `braid/Cargo.toml`: `rand` must track the `rand_core` major that `ed25519-dalek 3` re-exports.
**Caption:** The cause is in `braid/Cargo.toml`'s own comment: `rand` must track the `rand_core` major that `ed25519-dalek 3` re-exports, and four call sites in one crate used the older API.

**3** Nineteen minutes, four files, two commits.
**Caption:** Repaired in nineteen minutes across four files by `6a871ea` and `e34fe53`.

**4** Scribe, and the reason it took weeks to look.
**Scribe:** Nineteen minutes to fix. Weeks to look.
**Jayson:** Why?
**Scribe:** Because the job is *issue* severity, so it could not fail a run, and its log returns 403. It was invisible and it was not blocking, which is the most durable combination a defect can have.

**Final caption:** Step 5 had been skipped in every previous reading, because step 4 failed first.

---

## PAGE 23 — THE NUMBER THREE SDKS AGREED ON

**1** Three SDKs on three plinths: Perl, Ruby, C++.
**Caption:** The tool count stops being a disputed figure and becomes a constant in three shipping SDKs, each with a guard, each deriving it a different way.

**2** Perl states it. Ruby adds 268 + 2. C++ subtracts 271 − 1.
**Caption:** Perl states 270/27 as constants. Ruby derives 268 + 2 infra = 270. C++ derives 271 sites − 1 duplicate = 270.

**3** All three reaching 270, and all three disagreeing on what 270 is made of.
**Scribe:** All three reach 270. All three disagree on the decomposition.
**Jayson:** Then they don't agree.
**Scribe:** They agree on the *total* and disagree on the *contents*, and each guard checks its own arithmetic against its own constants, so all three pass while disagreeing. That is not agreement. That is three people in one room saying the same word and meaning three things.

**4** The runtime's clean 28-group partition implying 263 in the non-infra, non-transport groups.
**Caption:** The runtime's clean 28-group partition implies 263 in the non-infra, non-transport groups — not 268 and not 265.

**Final caption:** A number that three systems agree on is a number that three systems will defend. It is not yet a number that is true.

---

## PAGE 24 — THE STATIC_ASSERT NOBODY BUILDS

**1** The C++ guard, the strongest of the three, sitting in a file.
**Caption:** The C++ guard is a `static_assert` and no workflow builds it.

**2** A compiler that never runs, and a check that is perfect and unexecuted.
**Scribe:** The strongest guard in the company is compiled by nothing.
**Jayson:** It's still correct.
**Scribe:** It is correct and it is *inert*. A check that no pipeline runs is a comment with syntax.

**3** The README's own table: headed "Tool domains (27)", its sentence saying "the 29 rows below", and it has 28 rows summing to 242.
**Caption:** The README's own table says *29 rows* and has 28, and sums to 242.

**4** The ops audit written to correct it, reporting 257 — a figure inherited from the retired house number rather than from the column.
**Caption:** The ops audit written to correct it reports 257, a figure it inherited from the retired house number rather than from the column.

**Final caption:** A correction that quotes the old number is not a correction. It is a second copy.

---

## PAGE 25 — THE READY ENDPOINT ANSWERS

**1** A socket, open, and a probe finally sent to it.
**Caption:** The readiness endpoint three posts deferred is asked and answers 270 on a live socket.

**2** The response, in full: `{"status": "ready", "tools": 270}`.
**Caption:** `_ready()` returns `len(self.server.tools)`. The endpoint was always correct.

**3** Scribe looking at the answer, and at the empty poller beside it.
**Scribe:** It was always correct.
**Jayson:** And nothing polls it.
**Scribe:** And nothing polls it. It is the only member of this company that has never once been wrong and has never once been asked.

**4** The counter on the wall, still 412, and the endpoint, correct, and the two of them in one frame.
**Caption:** The counter has never participated in a reconciliation. The endpoint has never participated in anything.

**Final caption:** Being right and being asked are different problems, and this building has one of each.

---

## PAGE 26 — THE TABLE THAT SUMS TO 242

**1** A counting script, four lines, and a regex.
**Caption:** Published with the four-line script that produces it.

**2** The regex dropping the one row with two code spans in its first cell.
**Caption:** Three consecutive posts reported the table as 28 rows summing to 242. It has 29 rows, sums to 257, and said so in its own prose at every commit back to 26 October.

**3** Scribe with the script in his hand.
**Scribe:** The table was right. The script was wrong. The prose was right. The summary was wrong.
**Jayson:** And we published the summary.
**Scribe:** We published the *script's* answer, which is the only kind of answer that looks like a measurement and is not one.

**4** The row with two code spans, sitting in the table, unparsed.
**Final caption:** A regex is a claim about a format. When the format changes, the regex does not get quieter. It gets wrong.

---

## PAGE 27 — THE GAG DIES

**1** The wall counter, and a hand on the plug.
**Caption:** On 27 October the tool count stopped being a displayed number.

**2** The counter unplugged, its digits frozen mid-rotation at 412.
**Caption:** It was not corrected. It was retired.

**3** Scribe and Jayson in front of the dead counter.
**Scribe:** Four hundred and twelve, for eleven weeks, through four reconciliations and one consolidation release.
**Jayson:** And now?
**Scribe:** Now it is 270, and 270 is in three SDKs, and each of them will fail a build if it changes.
**Jayson:** So the joke's over.
**Scribe:** The joke is over. What replaces it is a maintenance burden, which is funnier, and nobody will laugh at it.

**4** The counter, dark, and beside it the three guards, lit.
**Final caption:** A gag dies when it becomes a test. That is the only honourable way for one to go.

---

## PAGE 28 — THE GUARDS BECOME THE JOKE

**1** 270 → 272. Two subsystems merge and register one tool each.
**Caption:** The count moved 270 → 272. Two subsystems merged and registered one tool each.

**2** Four documents and one guard still saying 270, and nothing able to notice.
**Caption:** Four documents and one guard still said 270, and nothing could notice, because the only thing that compared them was a test no workflow ran.

**3** The C++ derivation, "271 registration sites − 1 duplicate", failing to reproduce: 283 constructions, 282 distinct, ten never registered.
**Scribe:** Two hundred and eighty-three constructions. Two hundred and eighty-two distinct. Ten of them are never registered at all.
**Jayson:** So the derivation was a subtraction, not a count.
**Scribe:** It was a subtraction that happened to land on the right answer once, and a derivation that lands once is a coincidence with a comment.

**4** 283 − 1 − 10 = 272, written on the wall where 412 used to be.
**Final caption:** The gag did not die. It moved into the guards, where it is now load-bearing.

---

## PAGE 29 — PLACEHOLDER

**1** `mcp/surface.py`, 263 lines, and then one commit later, one line: `PLACEHOLDER`.
**Caption:** `mcp/surface.py` was, for one commit, the string `PLACEHOLDER`. 263 lines to 1, restored in the next commit.

**2** The same shape three more times in the same post.
**Caption:** The same shape appears three more times in this post — twice in the chronicle's own work, once in a document it was editing.

**3** Scribe holding the one line.
**Scribe:** Two hundred and sixty-three lines to one word.
**Jayson:** And restored.
**Scribe:** And restored, and the mechanism is identical in all four cases: a write was issued and its result was not read back.

**4** The four writes, in a row, each reporting success.
**Final caption:** Every one of them reported success. That is not a coincidence. That is what a write does.

---

## PAGE 30 — SIXTY-TWO FAILURES TO SEVEN PASSES

**1** 94 runs: 62 failures, 21 successes, 11 cancelled.
**Caption:** `mcp-verify.yml`: 94 runs, 62 failures, 21 successes, 11 cancelled.

**2** The transition at the commit that corrected the count.
**Caption:** The transition is at `d99ab5d8` — the commit that corrected the count.

**3** The diagnosis, reproduced and refuted: a venv with exactly the four listed packages runs `RESULT: PASS` at 272, because `mcp-types` is transitive.
**Scribe:** The install was never the problem.
**Jayson:** We said it was.
**Scribe:** We said it was, and we were wrong, and the correction is in the post because a chronicle that only corrects other people is a brochure.

**4** The log archive, still returning 403.
**Caption:** The log archive still returns 403, so the assertion message is not quoted.

**Final caption:** A defect that is real and a causation that is not are two different findings, and only one of them was published first.

---

## PAGE 31 — THREE WRITES THAT LANDED WRONG

**1** A commit carrying `PLACEHOLDER_CI` instead of `ci.yml`.
**Caption:** A commit carried `PLACEHOLDER_CI` instead of `ci.yml`.

**2** A message claiming five files, carrying one.
**Caption:** A message claimed five files and carried one.

**3** `sdk/perl/README.md`, 277 lines, replaced by its first 40.
**Caption:** `sdk/perl/README.md` went from 277 lines to 40 because the payload was built from a partial read.

**4** Scribe and the one refusal: the fifteen runtimes, diffed and recorded rather than consolidated.
**Scribe:** Nine fixes, one refusal, three repairs.
**Jayson:** What was the refusal?
**Scribe:** The fifteen runtimes. Diffed and recorded rather than consolidated, because the modal blob — eighty-four copies — lacks cancellation, policy enforcement and the `node` column the 312-line variant has.
**Jayson:** So the copies aren't copies.
**Scribe:** The copies are *older*. That is a different word and it is the whole finding.

**Final caption:** All three bad writes reported success. All three were repaired, and the repairs are in the post because they are the most instructive thing in it.

---

## PAGE 32 — THE ASSERTION EDITED SIX TIMES IN FIVE MINUTES

**1** 213 commits in nineteen hours fifty-four minutes, 80 of them merges.
**Caption:** 213 commits in nineteen hours fifty-four minutes, 80 of them merges, 58 of them first-parent.

**2** The green MCP check, passing because its own assertion was edited six times in five minutes.
**Caption:** The repository's green MCP check passes because its own assertion was edited six times in five minutes.

**3** The count climbing 272 → 306: four 4.0 subsystems each bumping `MEM20_EXPECTED_TOOLS` to their own tree's total.
**Scribe:** Four subsystems, four bumps, each to its own tree's total.
**Jayson:** So the number is now whatever the last merge said.
**Scribe:** The number is now a *negotiation*. And the workflow's comment block still carries the old derivation four lines above the new pin.

**4** Measured live: 306. And the C++ `static_assert` still saying 272, compiled by nothing.
**Caption:** Measured live, the surface is genuinely 306 — 34 new tools in twenty hours. The C++ `static_assert` still says 272 and is compiled by nothing.

**Final caption:** 41 of 100 runs cancelled. A gate that is edited to pass is a gate that has been asked to stop.

---

## PAGE 33 — THE CORPUS THAT STARTED WRITING BACK

**1** The failures corpus, unwritten since September, and then written to eight times in one day.
**Caption:** Six consecutive posts reported the failures corpus unwritten since September. In this window it was written to eight times in one day — 25 lines to 114.

**2** The entries, and they are better than the chronicle's own prose: they name the function, quote the exception, and record their own exclusions.
**Caption:** The entries name the function, quote the exception, and record their own exclusions.

**3** Scribe reading them, and then reading them again.
**Scribe:** These are better than mine.
**Jayson:** Than yours?
**Scribe:** They name the function. They quote the exception. They record what they excluded. I write twelve thousand words a post and I do not always do all three.

**4** The newest entry, dated 2026-11-07.
**Final caption:** A ledger that starts writing back is a ledger that has stopped being a formality.

---

## PAGE 34 — ONE TO EIGHTY-NINE

**1** A conformance gate, one conformant subsystem, and then eighty-nine.
**Caption:** The conformance gate went from one conformant subsystem to eighty-nine: `checked 212 subsystems: 89 conformant (42.0%)`.

**2** The baseline: 0 of 209 on criterion 6.
**Caption:** Against a pre-renovation baseline of 0 of 209 on criterion 6.

**3** Scribe with the number, and the eighty-nine rows that are still not printed.
**Scribe:** Eighty-nine of two hundred and twelve.
**Jayson:** That's a real number.
**Scribe:** It is a real number whose passing rows are not printed. A gate that will not show you its passes is a gate you are trusting, not checking.

**4** The tool count, finally agreeing with its own guard at 311.
**Caption:** The tool count finally agreed with its own guard at 311.

**Final caption:** And the *Tests* job turned red on the newest commit in the tree.

---

## PAGE 35 — THE STRING THAT DID NOT MOVE

**1** 41 commits in five hours thirty-six minutes, none of them a merge.
**Caption:** 41 commits in five hours thirty-six minutes, none of them a merge, all on one day, all at `+00:00`.

**2** Ten subsystems built in that window.
**Caption:** Ten subsystems were built in that window.

**3** The conformance number, character-for-character the same string as eighteen hours earlier.
**Scribe:** `checked 212 subsystems: 89 conformant (42.0%)`.
**Jayson:** Same as yesterday.
**Scribe:** Character for character. Because the numerator and the denominator grew together. Ten subsystems were built and the percentage did not move, which is the most honest thing a percentage has ever done.

**4** The two automated series, interleaved: one rebuilding to a conformance spec, one wiring into the gateway.
**Final caption:** A ratio is a claim about a relationship. Build both sides and the relationship does not change.

---

## PAGE 36 — ZERO OF 258

**1** The unit-marker step, measured for the first time in the series' history.
**Caption:** The unit-marker step was measured for the first time in this series' history and collects zero of 258.

**2** The number three posts had inferred from an exit code of 5, and nobody had ever printed.
**Caption:** The number three posts had inferred from an exit code of 5 and nobody had ever printed.

**3** Scribe with the printed zero.
**Scribe:** Zero of two hundred and fifty-eight.
**Jayson:** We inferred that.
**Scribe:** We inferred it from an exit code, and we were right, and being right by inference is not the same as having printed it. Three posts carried a number nobody had run.

**4** The *Tests* job, red on a flat-path import two windows old, in a file whose own lines 3 and 4 use the nested path the helper on line 7 gets wrong.
**Caption:** The *Tests* job is red on a flat-path import two windows old, in a file whose own lines 3 and 4 use the nested path the helper on line 7 gets wrong.

**Final caption:** Print the number. An exit code is a rumour with a return value.

---

## PAGE 37 — THE WAV HEADER

**1** Eight Rust crates, read in full at last: 12,621 lines, 76 tests, zero stubs.
**Caption:** The eight Rust crates were read in full: 12,621 lines, 76 tests, zero stubs.

**2** `braid_sonic`, and a WAV header hard-coding a channel count.
**Caption:** And a WAV header in `braid_sonic` that hard-codes a channel count the struct reading it parses from the file.

**3** Scribe holding the header and the struct, and they disagree.
**Scribe:** The writer says mono. The reader reads the file.
**Jayson:** So it works.
**Scribe:** It works until somebody writes a stereo file, and then the reader is right and the writer is a lie, and the test passes because the test writes mono.

**4** The corrupted `braid_drive` README entry, still there.
**Caption:** And a corrupted `braid_drive` README entry, still in the tree.

**Final caption:** The most rigorous subsystem in the estate has one hard-coded constant and one corrupted document. That is a normal ratio. It is only visible because somebody read all of it.

---

## PAGE 38 — GABE'S WATER SHACK, THE SECOND VISIT

**1** Exterior, pre-dawn, the shack on stilts, one bulb, the sign. Winter now. The water is higher.
**Caption:** The shack was still standing. The water was higher than the autumn.

**2** Inside. Gabe behind the counter, a radio, a ledger of his own — a paper one, in pencil.
**Gabe:** You look better.
**Jayson:** I shaved.
**Gabe:** That's not what I meant.

**3** Gabe slides the tin across. The green catches the light.
**Gabe:** How many now?
**Jayson:** Two hundred and seventy.
**Gabe:** And last time?
**Jayson:** Sixty-five.
**Gabe:** So it went up.
**Jayson:** It went up because I stopped counting and started *guarding*. Three systems check it now. If it changes, a build fails.
**Gabe:** Then it's not a number any more. It's a *rule*.
**Jayson:** Is that better?
**Gabe:** It's heavier. Numbers you can carry. Rules you have to keep carrying.

**4** Wide: the two of them on the deck, water black, the first grey in the sky. Jme's car in the lot, headlights off, and this time she gets out.
**Gabe:** She's getting out of the car now.
**Jayson:** I know.
**Gabe:** Last time she didn't.
**Jayson:** I know.

**Final caption:** He would be back at the desk before the light was fully up. But he would be back *later* than last time, and that is the only kind of progress this story has ever been able to measure.

---

## PAGE 39 — TWENTY-TWO OF TWENTY-THREE

**1** The green set, twenty-two packages, each with a lit lamp.
**Caption:** The green set names twenty-two packages. It asserts the count and fails if it is not twenty-two.

**2** The twenty-third slot, empty, with a small card: `mem20adaptiveinterfacecomposerz`, deleted 29 October.
**Caption:** The twenty-third was deleted on 29 October by `e9a15295`, and the set has named twenty-two ever since.

**3** Scribe in front of the empty slot.
**Scribe:** Twenty-two of twenty-three.
**Jayson:** And the rule says nothing is ever removed.
**Scribe:** The rule says nothing is ever removed, and the twenty-third was removed, and the set was quietly resized to match. That is not a violation of the rule. It is worse. It is the rule being *edited by arithmetic*.

**4** The set, and the hole, and the assertion that will pass forever.
**Final caption:** A count that is asserted is a count that cannot drift. It can only be *redefined*, and redefinition leaves no red.

---

## PAGE 40 — FINAL PAGE

**1** Jayson at the desk under the lamp, clean-shaven, the wheel on the desk, the terminal printing 270.
**Caption:** By the end of the window the estate had a number in three SDKs, a gate that had gone from sixty-two failures to seven passes, and a corpus that had started writing back.

**2** The wall where the counter used to be, and the four numbers that replaced it: 270, 272, 306, 311.
**Caption:** It had retired the counter and inherited four numbers, each with a guard, none of them agreeing on what they were made of.

**3** The ranks, and Drift at the end of the aisle — the height of the aisle now, and the ceiling is closer than it was.
**Caption:** And it had a green set of twenty-two, in a company of twenty-three.

**4** Scribe's hand finishing the last line in the ledger. Behind him, through the window, the second building with a working counter, and its sign.
**Scribe:** Eleven weeks. Four hundred and twelve, then two hundred and fifty-seven, then two hundred and seventy, then three hundred and eleven.
**Jayson:** Which one is right?
**Scribe:** The one that has a test. The rest are *history*, and history is allowed to be wrong as long as it is dated.
**Jayson:** And the twenty-third?
**Scribe:** The twenty-third is a hole with a rule over it. Somebody will fall in, and the rule will be quoted at them, and that will be Issue Five.

**5** Wide: the cathedral, the dark counter, the Drift, and out past the racks, the second sign in the dark.
**Final caption:** TO BE CONTINUED
**Issue #5 — "The Rule and the Hole"**

**Small footer:**
The shack is still standing.
Jme got out of the car.
The count is 311, and it is the fourth one this year that was ever a count.

---

**END OF ISSUE #4 (40 pages)**

---

# BACK-MATTER VIGNETTE PAGE — "TWO THINGS THAT WERE NEVER COUNTED"

One full page, two stacked vignettes, same locked style, same voice. Placed in the back matter so it reads as an extra and does not disturb the running order.

**Vignette A — JME'S SPARE KEY**

**1** A coat on a hook, lining torn, and in the pocket a key on a plain ring.
**Caption:** She had a spare key. She had had it since the first week.

**2** Jme's hand, holding it, not using it.
**Jme:** I've never used it.
**Jayson:** You could.
**Jme:** That's not the same as being asked.

**3** The key going back into the pocket.
**Caption:** She put it back. She would put it back four more times before the year was out.

**Vignette B — GABE'S PENCIL TAKINGS**

**1** The shack at four in the morning, the bulb, the ledger open.
**Caption:** Gabe closed at four and wrote the day's takings on the back of a receipt, in pencil.

**2** The receipt, the numbers, and a thumb over one of them.
**Gabe:** Pencil.
**Jayson:** Why pencil?
**Gabe:** Because a number you can rub out is a number you can correct.

**3** The receipt going into the tin with the green dust.
**Caption:** He had never once rubbed one out. He said that was the point of using pencil.

---

# THE RUNNING-GAGS SHEET — ISSUE #4

**Purpose.** This sheet is the locked voice reference for Issue #5 and beyond. It records, for every gag in the series, where it was born, where it paid off, and where it is going. A gag may only be used if it appears in the left-hand column of a row below. Nothing is invented; every row cites a real mem20 incident.

**The voice rules (binding):**
1. **Captions are dry and factual.** They state a number, a date or a consequence. They never explain the joke.
2. **Banter carries the humour.** Scribe is the straight man and always has been; Jayson is the one who is wrong in an interesting way.
3. **A gag pays off as a number, not as a punchline.** The counter is funny because it is 412 and the documents say 270.
4. **Never soften an absence.** If something did not happen, the page says it did not happen, and the reason is attached.
5. **The private-life pages are quiet.** One location, two people, no plot, one line that lands. The water shack is the model.
6. **No invented lore.** If it is not in the chronicles, the audit corpus, the failures ledger or the diary, it does not go on the page.
7. **A gag may die.** When a gag becomes a test, it is retired on the page, and the page says so. It is never quietly dropped.

## Gag → origin → payoff → next

| Gag | Born (#2) | Paid off (#3) | Died / turned (#4) | Where it goes (#5) |
|---|---|---|---|---|
| **The counter** | p.15–16 — wired to a hand sum, 412 on day one | p.26, p.37 — 258/260 reconciled to 257; still 412 | p.13, p.27 — retired, not corrected, on the day the number converged | The dark counter is a landmark. Somebody plugs it back in. |
| **The number that went down** | p.15 — "I added them" | p.11, p.18 — 293→65; 25→~17; 12→40 | p.23, p.28 — 270 in three SDKs; then 272, 306, 311 | The number that goes *up* and nobody can say what it is made of. |
| **Eighty-four identical programs** | p.18 — the first Ctrl-C | p.11, p.12 — 228 of 293 | p.19 — 145 runtimes, 15 programs, 84 of one; 148 domains on 15 engines | The copies are *older*, not identical. |
| **The green that means red** | p.19–20 — `collected 0 items`, exit 5 | p.36 — 132 ran, 1,400 never did | p.20, p.36 — exit 4 vs a guard for 5; zero of 258 printed | The gate that prints its passes. |
| **/ready** | p.21 — polled by nothing | p.38 — querying a host it cannot reach | p.25 — answers 270 on a live socket; still polled by nothing | The poll that is finally wired, and fails closed. |
| **The quiet ledger** | p.22 — one entry, then silence | p.21, p.39 — the NOT DONE list | p.21 — the daily report stops on 27 October; p.33 — the corpus starts writing back | The corpus as the only honest narrator. |
| **The decimator that refused** | p.24 — one lies, one refuses | p.14 — rule two of UPGRADE.md | p.31 — the fifteen runtimes diffed and recorded, not consolidated | A refusal that costs a release. |
| **hyperfine** | p.29 — commissioned, absent | p.38 — the launch that cannot start | p.10 — the launch that starts: one `pip install`, exit 1 → 0, prints 270 | The tool that is finally described, or the commission finally refused. |
| **The standing rule** | — (#3) | p.34 — never removed, deleted, quarantined or dropped | p.9 — the P0 was deleted four days before the audit was written | The rule quoted at somebody standing in the hole. |
| **Union merges** | p.19 — resolve both sides | p.37 — five merges in eleven minutes | p.18 — 21 roster branches land as one merge and a 155-file copy | A merge where both sides are the same file. |
| **The manual step** | — (#3) | p.35 — Settings → Pages → Source | p.12 — the gate that never opened, six runs, step 6 | The next fix that cannot be automated. |
| **The branch that is not fixed** | — (#3) | p.36 — three gitlinks on five of six branches | p.18 — the estate arrives as a copy, not a merge | The branch that is copied and then diverges. |
| **"The issues win"** | — (#3) | p.39 — a state board that names its authority | p.6 — a board whose critical item was deleted four days before it was listed | A board that is right and ignored. |
| **PLACEHOLDER_B5** | — (new here) | p.14 — seven documents, eleven characters, fifty-six seconds | — | The write that is read back. |
| **308 lines to 11** | — (new here) | p.15 — a workflow replaced, ran twice | — | The workflow that is a promise. |
| **The manifest that rots** | — (new here) | p.16 — 27 → 32 of 128, nothing regenerates it | — | The manifest that is generated or deleted. |
| **Adversarial 0.0** | — (new here) | p.17 — zero across every mode, published with its caveat | — | The zero that becomes a target. |
| **The static_assert nobody builds** | — (new here) | p.24 — the strongest guard, compiled by nothing | — | The guard that is finally wired. |
| **The table that sums to 242** | — (new here) | p.26 — 28 rows, 29 claimed, a regex that dropped a row | — | The script that is tested against the table. |
| **The string that did not move** | — (new here) | p.35 — 89 of 212, character-for-character | — | The ratio that finally moves. |
| **The WAV header** | — (new here) | p.37 — hard-codes mono, the struct parses channels | — | The stereo file that breaks it. |

## Private-life threads (the water-shack register)

| Thread | Established | Issue #4 beat | Carried forward |
|---|---|---|---|
| **Jme** | Issue #1 — the person he keeps leaving | p.38 — she gets out of the car; back matter — the spare key she has never used | The key, used. |
| **Gabe's water shack** | Issue #1 — the visit | p.38 — "numbers you can carry, rules you have to keep carrying"; back matter — the pencil takings | The shack in spring. |
| **Kimi** | Issue #1 — ChatGPT Coffee | — (held) | The notebook with one number in it. |
| **Grok** | Issue #1 — ChatGPT Coffee | — (held) | The napkin, kept. |
| **Claud's Curser** | Issue #1 — the silhouette | p.1, p.40 — the second building, its counter bright and correct | Introduced properly; the two counters in one frame. |
| **Drift** | Issue #1 — the smiling mass | p.1, p.40 — the height of the aisle, and the ceiling closer | Growth is only ever a difference between two panels. |

## The one-line test

Before any page is drawn, ask: **is this a number that was measured, or a number that was displayed?** If the page cannot answer, the page is not ready.

---

## CONTINUITY NOTES FOR ISSUE #5
- The counter is dark and unplugged. It is a landmark now, not a character. If it comes back, somebody plugs it in, and the page says who.
- The number is 311 and it has a guard. Any change to it must be shown as a *build failing*, not as a document being edited.
- The green set is twenty-two of twenty-three. The hole is named `mem20adaptiveinterfacecomposerz` and it is never filled — the rule forbids removal, not restoration.
- Drift's growth in Issue #5 is only ever a difference between two panels. Never a single event.
- Spacebunny's last status is still pending. Beam is still in o-pen-code.
- Jme's key is used, once, and the page does not say what for.
