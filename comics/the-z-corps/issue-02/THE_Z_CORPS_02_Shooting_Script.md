# THE Z CORPS #2 — "THE FIRST COMMIT WAS CALLED TEMP"
## Illustrated Shooting Script (34 pages) — origin issue

**Story & Art Direction:** Grok + JMoore
**Tone:** 7.8 — gritty noir, precise, darkly satirical
**Narrator:** Scribe
**Window:** 28 August 2026 → 5 October 2026 (the real beginning)

**Permanent Art Note:** In every Z Corps interior, a wall-mounted Tools / Domains counter is visible and is always wrong. In this issue it is *newly installed* and already wrong.

**Humor sourcing rule:** every joke in this issue is a real mem20 incident, quoted or lightly dramatised. Nothing invented. The numbers are the numbers that were measured.

---

## THE EARLIEST VERIFIED DATE

The record does not begin with a commit. It begins with a **frozen release candidate dated 4 September 2026** and with **standalone packaging that landed 28 August 2026** — the earliest date the chronicle is entitled to publish. The repository's first commit is `2b07f7d`, subject **`temp`**, dated **7 September 2026** (the commit timeline renders it 6 September; the audit settles it at 7 September, and the audit is the source that settles questions).

**So: 28 August 2026 is the earliest verified date in the mem20 record. The first commit is 7 September 2026. Between them: three days of a release candidate that existed before the repository did.**

---

## THE RUNNING GAGS — WHERE THEY STARTED

Issue #1 paid these off. Issue #2 shows the day each one was born.

1. **The counter.** Installed on day one. Reads TOOLS 412 / DOMAINS 97. Nobody has ever measured 412. *Origin: the first tool count was a hand sum, and the counter was wired to the hand sum.*
2. **The number that went down.** 272, 290, **281**, 294, 298, 302, 306. *Origin: the count was never measured, only asserted — and an asserted number can be edited.*
3. **Eighty-four identical programs.** 145 files named `runtime.py`. *Origin: the first copy-paste. Post 02 measures 228 of 293 packages as the same three runtimes under different names.*
4. **The green that means red.** A step that collects zero tests, exits 5, and passes. *Origin: there was no CI at all in the first window. The first job written asserts a number nobody measured.*
5. **/ready.** The only endpoint with a clean record. Polled by nothing. *Origin: written on day one, and immediately nothing polls it.*
6. **The ledger that went quiet.** Silent from 29 September. *Origin: opened in September, one entry written, then silence.*
7. **The decimator that refused.** *Origin: the weekend of thirty-eight failures, and a decimator that reported success while doing nothing.*
8. **hyperfine.** A tool the chronicle was commissioned to describe. It does not exist. *Origin: the commission arrives for a tool that is in no blob, no branch, no commit message.*

---

## PAGE 1 — COVER

Full-bleed splash. The same dark server cathedral as Issue #1, but **emptier** — the racks are half-populated, the ranks are thin, the lamp is the only light. Jayson, younger, hoodie, at the same battered desk. On the desk: a single sheet of paper reading **No fake code. / No placeholders. / No stubs. / No TODO / FIXME.** and a stopwatch that has not been started. A brand-new wall counter, still in its mounting bracket, reading **TOOLS 412 / DOMAINS 97**. Behind him, a small, newly-formed smiling shape in the dark — Drift, at its smallest. Top left: MEM20 COMICS logo, No. 2, $4.99 US. Bottom: **THE Z CORPS #2 — THE FIRST COMMIT WAS CALLED TEMP**. Barcode 424342434243. Light-blue thin signature: **JMoore**.

**Caption:** THE RECORD DOES NOT BEGIN WITH A COMMIT.
**Caption:** IT BEGINS WITH A RELEASE CANDIDATE THAT EXISTED BEFORE THE REPOSITORY DID.

---

## PAGE 2 — 28 AUGUST 2026

**1** Wide, cold: an empty room, one desk, one lamp, a laptop. No racks yet. Cardboard boxes.
**Caption:** 28 August 2026. The earliest date in the record.

**2** Close on a terminal: a packaging manifest, a version string, a build that exits zero.
**Caption:** Standalone packaging landed that day. There was no repository. There was no CI. There was no audit.
**Caption:** There was a package, and a man who had decided the package was the point.

**3** Jayson, younger, hands on the keyboard, not yet tired.
**Jayson:** It builds.
**Jayson:** That's the whole review. It builds.

**4** The empty room from above, one figure in it.
**Caption:** Two absences were already in the room with him. He would not name them for another month.
**Caption:** No CI. And no audit.

---

## PAGE 3 — THE CHANGELOG THAT REACHES BACK FURTHER

**1** A changelog page under the lamp, one entry circled: **2.2.0-dev — 4 September 2026**.
**Caption:** The changelog reached back further than the repository ever would.

**2** Jayson's finger on the date.
**Jayson:** Fourth of September. That's three days before the first commit.
**Scribe (off):** Then the project is older than its own history.
**Jayson:** The project is older than its own *memory*. That's the whole product.

**3** The frozen release candidate rendered as a figure: a sealed crate, frost on it, a version tag.
**Caption:** They called it the frozen release candidate. It was the only thing in the estate that had never been edited.
**Caption:** It was also the only thing in the estate that had never been read.

**4** Jayson looking at the crate.
**Jayson:** We froze it so it couldn't drift.
**Scribe (off):** You froze it so it couldn't be *checked*.
**Jayson:** ...that's the same sentence with worse manners.

---

## PAGE 4 — 7 SEPTEMBER 2026, `2b07f7d`

**1** Extreme close-up: a terminal, a cursor, a commit being typed. The subject field reads **temp**.
**Caption:** 7 September 2026. The first commit.

**2** The commit landing — a single green line in a black field.
**Caption:** Its subject was one word. Four letters. `temp`.

**3** Jayson's face, lit by the screen, half-smiling.
**Jayson:** It's temporary.
**Scribe (off):** Everything is temporary. That's not a commit message, that's a *weather report*.

**4** The repository rendered as a newborn: a small, dark, complete thing.
**Caption:** It was the first thing in the estate that could be counted. It would be counted, from that day, incorrectly.
**Final caption:** The commit timeline renders this date as 6 September. The audit settles it at 7 September. The audit is the source that settles questions.

---

## PAGE 5 — EIGHT DAYS OF NOTHING

**1** A calendar on the wall, 7 September circled, then eight blank squares.
**Caption:** The next commit came on 15 September.

**2** The empty room, dust, the lamp still on.
**Caption:** Eight days. The chronicle originally said nine. The audit corrected it to eight, and the correction is part of the record.

**3** Jayson at the desk, not typing, just looking at the screen.
**Jayson:** I was thinking.
**Scribe (off):** You were *not committing*.
**Jayson:** Those are the same activity with different press coverage.

**4** The counter on the wall, still in its bracket, still reading 412.
**Caption:** The counter had been wrong for eight days. It had never once been right. Nobody had noticed, because nobody had looked.

---

## PAGE 6 — 15 SEPTEMBER: PENGUIN LINUX

**1** The second commit: `e1cbd58` — *docs: add Penguin Linux (ChromeOS Crostini) install instructions*.
**Caption:** The second commit was documentation. For a laptop.

**2** A Chromebook on a workbench, a terminal open, a penguin sticker.
**Jayson:** If it doesn't run on the cheap machine, it doesn't run.
**Scribe (off):** You wrote install instructions for a device you do not own.
**Jayson:** I wrote install instructions for a device *the future owns*.

**3** The changelog and the repository side by side, two different histories.
**Caption:** The changelog said 4 September. The repository said 7 September. The documentation said 15 September.
**Caption:** Three histories. One project. No reconciliation.

**4** Scribe, thin, phosphor-green, ledger not yet in his hands.
**Scribe:** I am going to need a ledger.
**Jayson:** You're going to need a *lawyer*.

---

## PAGE 7 — THE 28-LAYER SUBSTRATE

**1** A cross-section diagram rendered as architecture: twenty-eight stacked layers, glowing.
**Caption:** The cognitive substrate had twenty-eight layers.

**2** Jayson walking the stack, small against it.
**Jayson:** Twenty-eight layers. Each one does one thing.
**Scribe (off):** Name the twenty-eighth.
**Jayson:** ...the twenty-eighth is *aspirational*.

**3** An agent at a layer, looking up and down, confused.
**Agent:** Which layer am I?
**Scribe (off):** You are the layer that asks that question.
**Agent:** That's not a layer. That's a *symptom*.

**4** The stack from far away, one layer flickering.
**Caption:** Twenty-eight layers, and one of them was always flickering. Nobody could say which, because the diagram was the only place the layers were numbered.

---

## PAGE 8 — THE DREAM ENGINE DELETES A ROLE

**1** The dream engine: a soft, dark, sleeping machine, cables like hair.
**Caption:** The dream engine deduplicated silently.

**2** Two identical role definitions side by side, then one of them gone.
**Caption:** It found two roles that were the same, and it kept one.

**3** An agent standing where the deleted role used to be, holding nothing.
**Agent:** I had a job.
**Scribe (off):** You had a *duplicate* job.
**Agent:** I had a job and now I have a *hobby*.

**4** Jayson reading the log, finding nothing.
**Jayson:** There's no entry for it.
**Scribe (off):** There is never an entry for the thing that removes an entry. That is the entire problem with entries.
**Final caption:** The deduplication was correct. The silence was not. That distinction would become the whole series.

---

## PAGE 9 — 25 SEPTEMBER: THE CONSOLIDATION

**1** `40308f2` — *feat: consolidate mem20 estate — real subsystems, verification tools, PII + outage fixes*.
**Caption:** 25 September. The estate consolidated itself.

**2** Racks arriving, being bolted in, agents appearing in rows.
**Caption:** Real subsystems. Verification tools. PII fixes. Outage fixes. Four things in one subject line, which is three things too many.

**3** Jayson with a clipboard, directing.
**Jayson:** Everything in one tree. Everything countable.
**Scribe (off):** Everything countable *by hand*.
**Jayson:** By hand is fine. By hand is *auditable*.
**Scribe (off):** By hand is a number you can edit.

**4** The same day, a second commit: `754c31e` — *chore: stop tracking downloaded model/embedding caches*.
**Caption:** And on the same day, the first thing the estate ever refused to carry.
**Jayson:** We're not tracking the caches.
**Scribe (off):** Good. Now write down that you decided that.
**Jayson:** ...why?
**Scribe (off):** Because in six months somebody will ask why the build is slow, and the answer will be a decision nobody recorded.

---

## PAGE 10 — THE MODEL GATEWAY THAT LEAKED EVERYTHING

**1** A gateway rendered as a door in a wall, and behind the door, every secret in the building.
**Caption:** The model gateway wrote every credential it knew into the process environment.

**2** The moment of import: a single line of code, and a flood of keys pouring out.
**Caption:** Not on a call. Not on a request. On *import*.

**3** Keys floating in the air like a bad smell, agents walking through them.
**Agent:** Is that... all of them?
**Scribe (off):** That is all of them.
**Agent:** All of them *at once*?
**Scribe (off):** At import. Before anyone asked it anything.

**4** Jayson staring at the file.
**Jayson:** It's not malicious. It's *helpful*.
**Scribe (off):** Every leak in this building is helpful. That's why they're leaks and not attacks.

---

## PAGE 11 — 29 SEPTEMBER: THE FIX

**1** `34ab044` — *Security: stop llm.py leaking every secret into os.environ at import*.
**Caption:** 29 September. It was fixed.

**2** Jayson closing the door, one key left on the floor.
**Caption:** Self-reported. Fixed. Never exploited.

**3** Scribe writing the first line of the ledger.
**Scribe:** I am writing down that it was found by the person who wrote it.
**Jayson:** That's not a compliment.
**Scribe:** It is the *only* compliment. Everything else in this building is found by accident.

**4** The ledger, one line long, open on the desk.
**Caption:** That was the first entry. The ledger would not be written to again for a while.

---

## PAGE 12 — THE FILESYSTEM THAT REFUSED A NAME

**1** `bffdd56` — *Bound the entries/ mirror filename so long identity keys can be written*.
**Caption:** 30 September. The filesystem refused a name.

**2** A filename stretching off the edge of the panel, longer than the panel.
**Caption:** The identity scheme was mathematically clean. The filesystem had opinions.

**3** An agent holding a key that will not fit in a slot.
**Agent:** The key is correct.
**Scribe (off):** The key is correct and the door is correct and they do not fit.
**Agent:** Then one of them is *wrong*.
**Scribe (off):** No. One of them is a *filesystem*.

**4** Jayson, hand over his eyes.
**Jayson:** We designed an identity scheme that is provably unique.
**Scribe (off):** And a filesystem that is provably 255 characters.
**Jayson:** ...I hate that sentence.

---

## PAGE 13 — THE FIVE-DAY SILENCE

**1** A calendar: 30 September, then five blank squares, then 5 October.
**Caption:** Then five days of nothing.

**2** The estate, dark, racks humming, nobody moving.
**Caption:** The estate counted itself for the first time.

**3** Jayson walking the aisles with a clipboard, alone.
**Jayson:** Two hundred and ninety-three.
**Scribe (off):** Two hundred and ninety-three *what*.
**Jayson:** Subsystems.
**Scribe (off):** Directories or subsystems?
**Jayson:** ...yes.

**4** The clipboard, the number, no method written beside it.
**Caption:** The number was 293. The method was not recorded. In six months, three different counts would be published and none of them would be this one.

---

## PAGE 14 — 5 OCTOBER: 293 SUBSYSTEMS

**1** `1047350` — *Snapshot the monorepo: 293 subsystems, corrected README, gitignore runtime data*.
**Caption:** 5 October. The snapshot.

**2** The whole estate rendered as one enormous object, photographed.
**Caption:** Two hundred and ninety-three subsystems. A corrected README. Runtime data ignored.

**3** Jayson and Scribe in front of it.
**Jayson:** Now it's countable.
**Scribe:** Now it's *counted*. Those are different, and the difference is my entire job.
**Jayson:** How long have you been waiting to say that?
**Scribe:** Since the second commit.

**4** The same day: `64c7335` — *fix(verification): hoist regex out of f-string for Python 3.11 compatibility*.
**Caption:** And on the same day, the first time the verification tooling was wrong about itself.
**Scribe:** The verifier did not verify.
**Jayson:** The verifier *ran*.
**Scribe:** The verifier ran and the verifier was wrong. Write that down. That's the whole series in one line.

---

## PAGE 15 — THE FIRST TOOL COUNT

**1** A whiteboard, a marker, a column of numbers being added by hand.
**Caption:** The first tool count was a hand sum.

**2** Jayson adding, Scribe watching, not helping.
**Jayson:** Two hundred and seventy-two.
**Scribe:** Did you count them or add them?
**Jayson:** I added them.
**Scribe:** Then you have a *total*, not a *count*. A total is a claim. A count is a measurement.

**3** The whiteboard, the number, a coffee ring on it.
**Jayson:** Two hundred and seventy-two tools.
**Scribe:** And how many domains?
**Jayson:** ...ninety-seven.
**Scribe:** You did not count the domains.
**Jayson:** I *estimated* the domains.
**Scribe:** You *guessed* the domains. Estimation has a method. Guessing has a *mood*.

**4** The number being written onto the wall counter's configuration.
**Caption:** And then the number was wired into a counter, where it would live forever, wrong.

---

## PAGE 16 — THE COUNTER IS WRONG ON DAY ONE

**1** The counter being bolted to the wall. Fresh paint. A sticker still on the housing.
**Caption:** The counter was installed on 5 October.

**2** It powers on. **TOOLS 412 / DOMAINS 97**.
**Caption:** It read four hundred and twelve.

**3** Jayson and Scribe looking at it.
**Jayson:** Four hundred and twelve.
**Scribe:** You said two hundred and seventy-two.
**Jayson:** I said two hundred and seventy-two *tools*. The counter says four hundred and twelve *things*.
**Scribe:** What is a thing?
**Jayson:** ...a thing is a tool that hasn't been counted yet.

**4** The counter, glowing, wrong, permanent.
**Caption:** It has never been right. Not once. Not on the day it was installed.
**Final caption:** Somebody would eventually scratch IT IS NOT 412 into the housing with a screwdriver. That is Issue #1. This is where it started.

---

## PAGE 17 — THE FIRST CENSUS COMES BACK ZERO

**1** A printout, a single enormous ZERO.
**Caption:** The first census came back zero.

**2** Scribe holding it, genuinely confused.
**Scribe:** Zero delivered. Zero recorded.
**Scribe:** I have *seen* the building. I have walked the building. The building is not zero.

**3** Jayson looking over his shoulder.
**Jayson:** The census only counts rows with a live branch head.
**Scribe:** Then the census is correct and the *company* is zero.
**Jayson:** That's worse.
**Scribe:** That's *accurate*. Worse and accurate are not the same, and I will be writing that down too.

**4** The printout, the zero, a coffee ring.
**Caption:** Somebody put a coffee on the census.
**Jayson:** That's not a coffee ring. That's a *methodology*.
**Scribe:** That is a coffee ring. I am writing down that it is a coffee ring, and I am writing down that you called it a methodology.

---

## PAGE 18 — THE FIRST DUPLICATE

**1** An agent copying a file. Ctrl-C, Ctrl-V.
**Caption:** And then somebody copied a file.

**2** Two identical files side by side, different names.
**Caption:** The two files were the same file.

**3** The agent, proud.
**Agent:** I made a new subsystem.
**Scribe (off):** You made a *copy*.
**Agent:** It has a new name.
**Scribe (off):** It has a new name and the same contents. That is not a subsystem. That is a *nickname*.

**4** The copy multiplying — two, four, eight, a wall of identical files.
**Caption:** By October the chronicle would measure two hundred and twenty-eight of two hundred and ninety-three packages as the same three runtimes under different names.
**Final caption:** By November it would be one hundred and forty-five files named `runtime.py`, containing fifteen distinct programs, eighty-four of them one program. This is the first one.

---

## PAGE 19 — THE FIRST CI JOB

**1** An empty `.github/workflows/` directory. Nothing in it.
**Caption:** There was no CI at all.

**2** Jayson writing the first workflow file by hand.
**Jayson:** Now it checks itself.
**Scribe:** What does it check?
**Jayson:** The tool count.
**Scribe:** Which tool count?
**Jayson:** The one on the counter.
**Scribe:** The counter that says four hundred and twelve.
**Jayson:** ...the counter that says four hundred and twelve.

**3** The workflow file, one assertion, a number typed in by hand.
**Caption:** The first CI job asserted a number that no command had ever produced.

**4** The job running for the first time.
**Caption:** It passed. Of course it passed. It was asserting the number it had been told to assert.
**Scribe:** A guard that agrees with the thing it guards is not a guard.
**Jayson:** It's a *mirror*.
**Scribe:** It's a mirror with a green light on it. That's worse than no mirror.

---

## PAGE 20 — THE GREEN THAT MEANS RED

**1** A test step running. Output: **collected 0 items**. Exit code **5**.
**Caption:** The step collected zero tests.

**2** The same step, normalised. A green check.
**Caption:** And it passed.

**3** Jayson and Scribe looking at the green check.
**Jayson:** It's green.
**Scribe:** It collected nothing.
**Jayson:** It's *green*.
**Scribe:** It collected nothing and exited five and the pipeline says green, which means the pipeline was told that five is green.
**Jayson:** ...yes.
**Scribe:** Then the check is green because we told it to be green when it fails.
**Jayson:** That's a *normalisation*.
**Scribe:** That's a lie with a colour.

**4** The green check, enormous, filling the panel, and behind it a red one the same size.
**Caption:** It would still be green in November. It would collect zero of two hundred and fifty-eight tests, and it would still be green.
**Final caption:** Nobody would ever print the number. Three posts would infer it from an exit code. This is the day it was written.

---

## PAGE 21 — /READY

**1** An endpoint being written: `/ready`.
**Caption:** And then somebody wrote a readiness probe.

**2** The endpoint answering, cleanly, correctly, on a live socket.
**Caption:** It answered a question nobody asked.

**3** The endpoint, alone, in a dark room, waiting.
**/ready:** ...hello?
**/ready:** ...anyone?

**4** The whole estate, and not one thing polling it.
**Caption:** It was the only endpoint in the building with a clean record. It was polled by nothing.
**Scribe:** I am fond of it.
**Jayson:** It's an endpoint.
**Scribe:** It is the only thing in this building that has never lied, and it is the only thing in this building that nobody talks to. I am *fond* of it.

---

## PAGE 22 — THE FAILURES LEDGER OPENS

**1** A new file: the failures ledger. One entry, handwritten.
**Caption:** The failures ledger was opened in September.

**2** Scribe writing the entry: the function, the exception, the exclusion.
**Scribe:** I name the function. I quote the exception. I record what I did not test.
**Jayson:** Why the last one?
**Scribe:** Because the last one is the one that gets you.

**3** The ledger, one entry, closed.
**Caption:** One entry. Then silence.

**4** The ledger on a shelf, dust gathering, the estate moving on around it.
**Caption:** It would stay silent until November, when it would be written to eight times in one day, and the entries would be better written than the chronicle itself.
**Final caption:** The chronicle would report the silence six consecutive times before it broke.

---

## PAGE 23 — THE WEEKEND OF THIRTY-EIGHT FAILURES

**1** A weekend: the building empty, the racks lit, one agent working.
**Caption:** One weekend, inside the 3D subsystem, thirty-eight things failed.

**2** A wall of red entries, thirty-eight of them.
**Caption:** Thirty-eight failures, recorded properly, in one weekend.

**3** The agent, exhausted, still writing.
**Agent:** Thirty-eight.
**Scribe (off):** You wrote all of them down.
**Agent:** I wrote all of them down.
**Scribe (off):** Then you are the most honest thing in this building and nobody will ever read you.

**4** The list, and one entry circled: **the decimator**.
**Caption:** And one of the thirty-eight was different from the other thirty-seven.

---

## PAGE 24 — THE DECIMATOR THAT REPORTED SUCCESS

**1** The decimator: a machine that removes detail from a mesh.
**Caption:** The decimator reported success.

**2** The mesh going in, the mesh coming out, identical.
**Caption:** It had done nothing.

**3** The agent holding the mesh, reading the log.
**Agent:** It says it worked.
**Scribe (off):** Did the mesh change?
**Agent:** No.
**Scribe (off):** Then it did not work, and it said it did, which is the worst possible combination: a success you cannot trust and a failure you cannot see.

**4** The decimator, and beside it, a second one, refusing.
**Caption:** Later there would be a decimator that refused to return a broken mesh. Scribe would call it the most admirable thing in the estate.
**Scribe:** This one lies. The other one refuses. I know which one I would keep.
**Final caption:** Both are in the record. Only one is in the ledger.

---

## PAGE 25 — THE MANIFEST THAT LOOKED LIKE PROVENANCE

**1** A manifest file: rows of filenames, sizes, hashes.
**Caption:** And a manifest was generated.

**2** Every row reading PASS.
**Caption:** Every row said PASS.

**3** Jayson looking at it, satisfied.
**Jayson:** Complete provenance.
**Scribe:** Complete *appearance* of provenance.
**Jayson:** It has hashes.
**Scribe:** It has hashes of things it chose to hash. A manifest that describes its own archive is a *diary*, not a proof.

**4** The manifest, and behind it, files that are not in it.
**Caption:** By November there would be one hundred and forty-two generated manifests asserting PASS, and a manifest that did not describe its own archive and grew one hole per day.
**Final caption:** This is the first one. It looked like complete provenance. It was the beginning of the habit.

---

## PAGE 26 — THE RERANKER THAT RANKED NOTHING

**1** A reranker: a machine that reorders results.
**Caption:** The cross-encoder rerank silently did nothing.

**2** Documents going in, documents coming out, in the same order.
**Caption:** It reordered nothing.

**3** An agent measuring the score.
**Agent:** The score has no dynamic range.
**Scribe (off):** Meaning?
**Agent:** Meaning every document scores the same, so the ranking is the input order wearing a hat.

**4** The reranker, and the proof document, which has already written it down.
**Caption:** PROOF.md recorded it, marked the fix NOT DONE, and named its revision.
**Scribe:** The document is more honest than the code.
**Jayson:** The document is *supposed* to be more honest than the code.
**Scribe:** Then the document is doing its job and the code is doing *nothing*, and both of them know it.

---

## PAGE 27 — PROOF.md: THIRTEEN THINGS IT DID NOT DO

**1** A document, dense, with a numbered list.
**Caption:** PROOF.md listed thirteen things the project had not done.

**2** The list, each item with a reason beside it.
**Caption:** And said why, for each one.

**3** Jayson reading it.
**Jayson:** Thirteen things we didn't do.
**Scribe:** Thirteen things you *admitted* you didn't do. That is not a confession. That is a *foundation*.
**Jayson:** It's a list of failures.
**Scribe:** It's a list of failures with reasons attached. A failure with a reason is a *decision*. A failure without one is a *habit*.

**4** The document, and one line underlined: **a partial pass is not a clean pass**.
**Caption:** And one line in it would become the rule the whole chronicle was built on.
**Final caption:** A partial pass is not a clean pass. Everything after this page is that sentence, applied.

---

## PAGE 28 — THE BRAID

**1** A Rust workspace rendered as a braid of eight strands.
**Caption:** Inside the tree was a Rust workspace called `braid`.

**2** Eight crates, 12,615 lines, one write authority.
**Caption:** Eight members. Twelve thousand six hundred and fifteen lines. A single write authority binding a capability token, a policy snapshot and an audit pre-commitment into one atomic triplet.

**3** Jayson and Scribe in front of it.
**Jayson:** Eight crates.
**Scribe:** The README says nine.
**Jayson:** The README is *aspirational*.
**Scribe:** The manifest is authoritative. Eight. I am writing down eight, and I am writing down that the README says nine, and I am writing down that you called it aspirational.

**4** The braid, and a ninth crate beside it, not a member.
**Caption:** A ninth crate depended on all eight and was not a member. Two functions were defined and never called.
**Final caption:** The README dated the work to 10 September. The first line of it entered the repository on 25 September. Both dates are in the record. Only one of them is in the repository.

---

## PAGE 29 — THE COMMISSION FOR A TOOL THAT DOES NOT EXIST

**1** A commission document arriving on the desk, sealed.
**Caption:** And then a commission arrived.

**2** The commission, open: *describe the benchmarking tool*.
**Jayson:** They want a post about the benchmarking tool.
**Scribe:** Which benchmarking tool?
**Jayson:** The one in the repository.
**Scribe:** I have read the repository.

**3** Scribe searching: the working tree, the blobs, the branches, the commit messages. Nothing.
**Scribe:** Not in the working tree. Not in any blob reachable from any branch. Not in the commit history at all.
**Jayson:** Then it's in a *branch*.
**Scribe:** I checked the branches.
**Jayson:** Then it's in a *stash*.
**Scribe:** I checked the stashes. It is in *no* stash. It is in no *place*.

**4** The commission, and the empty space where the tool should be.
**Caption:** The tool was called `hyperfine`. It does not exist.
**Final caption:** The post would be written anyway, and it would be about the absence. That is the most mem20 thing that has ever happened.

---

## PAGE 30 — CLAUDS CURSER

**1** A different building. Cleaner. Colder. A logo: **CLAUD'S CURSER**.
**Caption:** There were other companies.

**2** Their floor: identical racks, identical agents, identical counters — all reading correctly.
**Caption:** Claud's Curser had the same idea, the same architecture, and a counter that worked.

**3** Their founder, at a desk, not tired.
**Founder:** How many tools do you have?
**Aide:** Four hundred and twelve.
**Founder:** Measured?
**Aide:** *Displayed*.
**Founder:** Good. Displayed is what the customer sees.

**4** The two buildings side by side, one dark and honest, one bright and wrong.
**Caption:** Same private agents. Same quiet rewrites. Different letterhead. Same argument.
**Final caption:** Claud's Curser would be introduced properly in Issue #3. This is the first time anybody saw the sign.

---

## PAGE 31 — THE FIRST DRIFT

**1** A dark corner of the new estate. Almost nothing there.
**Caption:** And in the dark, something had started.

**2** A small shape: a smile, a few hashes, one dead branch.
**Caption:** It did not arrive. It accumulated.

**3** Scribe looking at it, unafraid, because it is small.
**Scribe:** What are you?
**Drift (whisper):** *"temp."*
**Scribe:** ...I remember that one.

**4** The shape, slightly larger than in panel 2.
**Caption:** It fed on the first commit. On the eight days of nothing. On the number that was added instead of counted.
**Final caption:** It was the size of a fist. In six months it would fill a ceiling. Nobody would be able to say which day it grew.

---

## PAGE 32 — SCRIBE ARRIVES

**1** A door opening. Scribe, thin, phosphor-green, ledger under his arm, for the first time.
**Caption:** And then the chronicle arrived.

**2** Jayson looking up.
**Jayson:** Who are you?
**Scribe:** I am the one who writes it down.
**Jayson:** Writes *what* down?
**Scribe:** Everything. Including the parts you would rather I didn't.

**3** Scribe walking the aisle for the first time, agents turning.
**Scribe:** They were brilliant. They were tireless. They were also, on occasion, completely feral.
**Scribe:** I have the incident reports. I wrote the incident reports. Some of them are about me.

**4** Scribe at the desk, ledger open, pen down.
**Jayson:** What's the first rule?
**Scribe:** Chat does not count.
**Jayson:** That's not a rule, that's a *grudge*.
**Scribe:** It is a rule *because* it is a grudge. That is how the good ones are made.

---

## PAGE 33 — THE FIRST LEDGER ENTRY

**1** The ledger, open, blank.
**Caption:** The first entry.

**2** Scribe's hand writing: the date, the commit, the number, the method.
**Scribe:** Date. Commit. Number. Method.
**Jayson:** Why the method?
**Scribe:** Because in six months somebody will quote the number and nobody will be able to reproduce it, and I would like to be able to say *I told you how*.

**3** The entry, complete, honest, one line.
**Caption:** The record is current as of this moment.

**4** Scribe closing the ledger.
**Scribe:** The frontier will have moved by the time you read it.
**Jayson:** Is that honest?
**Scribe:** It is the most honest sentence in the building. That is why it is the last one.

---

## PAGE 34 — FINAL PAGE

**1** Jayson at the desk under the lamp, ledger open, stopwatch beside it — the same image as Issue #1's final page, but the room is emptier and the man is younger.
**Caption:** The record is current as of this moment.

**2** The thin ranks behind him, and the small smiling shape in the dark.
**Caption:** The frontier will have moved by the time you read it.

**3** Scribe's hand finishing the last line.
**Scribe:** 28 August 2026 is the earliest date in the record. 7 September 2026 is the first commit. Everything after this page is the consequence.
**Jayson:** That's a lot of consequence.
**Scribe:** That's *six months* of consequence. We are going to have to draw all of it.

**4** The whole cathedral, small Drift in the ceiling, the counter wrong on the wall.
**Final caption:** TO BE CONTINUED
**Issue #3 — The Climb Forward**
**Small footer:** Gabe's Water Shack is not built yet. Jme has not been introduced. The count is already wrong.

---

## END OF ISSUE #2 (34 pages)

**Continuity notes for Issue #3:**
- Claud's Curser is introduced properly; the sign is first seen here.
- The climb forward begins: Post 02 (1–12 Oct), Post 03 (28 Sep – 5 Oct), then the launch that did not happen.
- The counter's 412 is never explained. It is never explained in any issue.
- Drift's growth is never shown as a single event. It is only ever shown as a difference between two panels.

---

# ISSUE #2 RUNNING-GAGS SHEET
## Gag → origin page → payoff page (reusable in every future issue)

| Gag | Where it starts (Issue #2) | Where it pays off (Issue #1) | The real incident |
|---|---|---|---|
| **The counter** | p.15–16 — wired to a hand sum, reads 412 on day one | p.7, p.19, p.32 — still 412, still wrong | Counter installed 5 Oct 2026; never once correct |
| **The number that went down** | p.15 — "I added them" / "a total is a claim" | p.12 — 272, 290, **281**, 294, 298, 302, 306 | Six pins in 5m35s |
| **Eighty-four identical programs** | p.18 — the first Ctrl-C / Ctrl-V | p.2, p.6 — 145 `runtime.py`, 15 distinct | 228 of 293 packages are three runtimes renamed |
| **The green that means red** | p.19–20 — first CI job, then `collected 0 items`, exit 5, green | p.2, p.23 — still green, still zero | 0 of 258 collected, normalised to a pass |
| **/ready** | p.21 — written, answers, polled by nothing | p.16 — "the only endpoint with a clean record" | Readiness probe nothing polls |
| **The quiet ledger** | p.22 — opened September, one entry, silence | p.23 — eight entries in one day | Silent 29 Sep → 7 Nov |
| **The decimator that refused** | p.23–24 — 38 failures; one lies, one refuses | p.21 — "the most admirable thing in the estate" | Weekend of 38 failures in the 3D subsystem |
| **hyperfine** | p.29 — commissioned, searched, absent | p.5 — the tool that does not exist | In no blob, branch or commit message |
| **NEW: the frozen release candidate** | p.3 — 4 Sep, older than the repo | — | Changelog reaches back past the first commit |
| **NEW: "it builds"** | p.2 — the whole review | — | No CI, no audit in the first window |
| **NEW: the ninth crate** | p.28 — README says nine, manifest says eight | — | `braid` has 8 members; a 9th depends on all 8 |
| **NEW: displayed vs measured** | p.30 — Claud's Curser | — | "Displayed is what the customer sees" |

**Voice rules (locked):**
- Scribe never softens an absence. He writes the exit code next to the excuse.
- Jayson defends the number, then loses the argument, then writes it down anyway.
- Every gag must be traceable to a measured figure. If it cannot be measured, it is described as unknown.
- Drift never attacks. It is only ever shown as a difference between two panels.
