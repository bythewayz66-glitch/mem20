# mem20 desktop — task flows grounded in the shipped views

**Written:** 2026-11-01 · **Owner:** UX research (roster row 20, desktop)
**Baseline:** `main` @ `06fa1220e964f84aabac78127fc18463dfa6798d`
**Companion:** [desktop-personas-2026-11-01.md](./desktop-personas-2026-11-01.md)

---

## 0. How to read this document

Every flow below opens with the **view file and line range it exercises**. If a step cannot be
performed in a file that exists at the baseline commit, it is not in a flow — it is in the
**Surface gap** line at the end of the flow, stated as a gap.

**No flow in this document requires a screen that does not exist.** There is no chat flow, no
onboarding flow, no billing flow, and no mobile flow, because none of those surfaces are in
`web/src/views/**`.

Line numbers were re-derived from the source at `06fa1220` and the view files are byte-identical
on `main` @ `2ea44922`, so every citation holds on either ref.

### 0.1 Flow index

| # | Flow | Persona | Primary view file | Lines |
|---|---|---|---|---|
| F1 | Cold start with a dead door → diagnose → recover | A / D | `Kanban.tsx` | 239–292 |
| F2 | Read the board's health in one glance | A | `Kanban.tsx` | 301–358 |
| F3 | Drag a card into a full column (WIP refusal) | A | `Kanban.tsx` | 136–165 |
| F4 | Move a card with a recorded reason | A | `Kanban.tsx` | 600–777 |
| F5 | Claim a card, then release it | A / B | `Kanban.tsx` | 730–772 |
| F6 | Recover the board after an agent dies mid-claim | A | `Kanban.tsx` | 203–215, 376–410 |
| F7 | Decompose a roadmap phase into a card (Sarge) | A | `Kanban.tsx` | 780–868 |
| F8 | Fix a board whose done column is wrong | A | `Kanban.tsx` | 871–963 |
| F9 | Trace an invariant to the symbol that enforces it | C | `MemoryModel.tsx` | 10–128 |
| F10 | Try to promote a dream without evidence | C | `Dreams.tsx` | 87–130 |
| F11 | Follow a dream's provenance chain | C | `Dreams.tsx` | 132–145 |
| F12 | Falsify a Sales claim end-to-end | E | `Sales.tsx` → `DocsFaq.tsx` | 67–113 → 180–290 |
| F13 | Reach the door from another machine | D | `Connection.tsx` | 44–80 |
| F14 | Compose an agent from the five fields | A | `AgentBuilder.tsx` | 50–215 |
| F15 | Look up who may do what | A / B | `Teamily.tsx` | 53–90 |

---

## F1 — Cold start with a dead door → diagnose → recover

**View:** `web/src/views/Kanban.tsx:239-292` (unreachable branch), `web/src/views/DoorSync.tsx:56-90` (live probe), `web/src/views/Connection.tsx:44-80` (base config)
**Persona:** A Operator, D Remote operator
**Trigger:** the shell boots to `kanban` by default (`App.tsx:55-63`) and `door.healthy()` fails.

### Steps
1. **Boot.** `App.tsx:55-63` reads `window.location.hash`; anything unrecognised falls back to
   `kanban`. There is no welcome screen and no login.
2. **The rail foot reports the door before the page does.** `App.tsx:84-88` polls every 30 s;
   `App.tsx:123-131` renders `door …` / `door up` / `door down` plus the base URL in mono.
3. **Kanban refuses to draw an empty board.** `Kanban.tsx:239-292` — the guard is
   `if (loadErr && !board)` at `:241`; the whole page is replaced by a `Notice tone="bad"`
   (`:250`) whose body carries the key sentence at `:255`:
   > *"The shell will not draw an empty board for a door it cannot reach. An empty board would
   > read as 'no work', which is a different fact from 'no answer'."*
4. **Three diagnostic panels, not one error string.** `Kanban.tsx:259-290`:
   - *What the shell tried* (`:259`) — `GET <base>/api/boards`, `timeout 8000ms`, the raw result.
   - *The one store* (`:270`) — `/opt/mem20/kanban/kanban_3.db`, writer `mem20-kanban.service
     only`, note *"this UI never opens sqlite"*.
   - *Next* (`:280`) — `retry door` at `:282` (primary) and `open Door Sync` at `:285`.
5. **Escalate to Door Sync** if retry fails. `DoorSync.tsx:56-90` runs a real probe and prints
   the raw request line: `GET <base>/api/boards → 200 · N boards · Nms` on success, or
   `→ no answer` on failure. `DoorSync.tsx:65` states that `GET /api/boards` *"is what
   Door.healthy() does — it never fabricates a list"*.
6. **Door Sync names the cause and the fix.** `DoorSync.tsx:74-80`:
   > *"A browser can only reach the door if it is on the same machine or the door is exposed
   > through a proxy. The door is loopback-only by design (`restart=always`, enabled at boot), so
   > a remote browser will always see this. Use `ssh -L 8221:127.0.0.1:8221` and point Connection
   > at `http://127.0.0.1:8221`."*
   The re-probe control is `probe again` at `DoorSync.tsx:84`.
7. **Set the base.** `Connection.tsx:52-56` explains `DEFAULT_DOOR` and the `ssh -L` tunnel;
   `Connection.tsx:58-68` is `save & test` (persists, re-reads, re-probes, shows `door base saved`
   at `:64`); `Connection.tsx:70-77` is `reset`, which restores `DEFAULT_DOOR`.
8. **Return.** `retry door` on Kanban, or the rail's `Kanban` item (`App.tsx:30-40`).

### What the shell does well
The failure is **diagnosable without a terminal** for the first two steps, and the third step
(`systemctl status mem20-kanban`, `Kanban.tsx:255`) is offered as a sentence, not a dead end.

### Edge cases
- **Door up, board read fails.** `Kanban.tsx:366-371` keeps the last good board and shows
  `Notice tone="warn"` — *"Showing the board as of the previous successful read."* (`:369`). This
  is the correct degraded state: stale, labelled stale.
- **Door down but a board is cached in state.** Same branch — the stale banner, not the
  unreachable page. The unreachable page only fires when there is no board at all (`:241`).

### Surface gap
None. This flow is fully served by three existing views.

---

## F2 — Read the board's health in one glance

**View:** `web/src/views/Kanban.tsx:301-358`
**Persona:** A Operator
**Trigger:** the operator opens the shell to answer "is anything stuck?"

### Steps
1. **Board selector.** `Kanban.tsx:302-310` — a `<select>` of board names from `door.boards()`.
2. **Four stats, computed client-side.** `Kanban.tsx:352-358`:
   `cards` (total), `open` (`/ total`), `claimed`, and **`columns at WIP`**
   (`:357`, `sub={/ lanes.length}`). The last one is the stuck-signal: `Kanban.tsx:233-238`
   counts columns where `wipLimit > 0 && cards in column >= wipLimit`.
3. **Lane headers carry the same fact.** `Kanban.tsx:439` applies `at-cap` and `is-done` classes
   per lane, so a full column is visually distinct from a merely busy one.
4. **Filter without leaving the board.** `Kanban.tsx:311-333` — free-text `filter title or id…`
   (`:312`), `all tags`, `all assignees` (`:325`, with a `__none__` = *unclaimed* option), and a
   `swimlanes` toggle (`:334-339`) that regroups by assignee, rendered by `Swimlanes`
   (`Kanban.tsx:528`).

### What the shell does well
`columns at WIP` is the single most useful number on the page and it is not a vanity metric — it
is the count of places a move will be refused.

### Edge cases
- **Zero boards.** `loadBoards` sets `boards` to `[]`; the select renders empty and the lane area
  renders no columns. The `Empty` component is imported (`Kanban.tsx:29`) but the zero-board case
  is not distinguished from a board with no columns.

### Surface gap
A first-run board (zero boards) has no dedicated empty state. Low severity, but it is the one
state where the operator cannot tell "no boards" from "board failed to load".

---

## F3 — Drag a card into a full column (WIP refusal)

**View:** `web/src/views/Kanban.tsx:136-165` (move + pre-flight), `:439` (lane drop target)
**Persona:** A Operator
**Trigger:** the operator drags a card into a column that is at its WIP limit.

### Steps
1. **Drag starts.** `Kanban.tsx:59-61` holds `dragging` / `dropLane`; the lane under the cursor
   gets the `drop` class at `:439`.
2. **Pre-flight check, local.** `Kanban.tsx:139-149` counts cards already in the target column
   (excluding the dragged one, `:140`) and, if `inCol >= wipLimit`, sets an error status and
   returns **without calling the door** (`:144`):
   > `CapacityFull — "<column>" is at its WIP limit (N/M). Move or finish a card first.`
3. **The door remains the authority.** `Kanban.tsx:150-160` — if the pre-flight passes, the move
   is sent; a `CapacityFull` thrown by the client is rendered at `:156` as
   `HTTP 422 CapacityFull — the door refused the move: <detail>`.
4. **The refusal is shown against the column that refused it.** `Kanban.tsx:360-364` renders the
   status notice above the board; the file's own header states the rule at `:14`:
   *"never swallowed, never retried silently."*

### What the shell does well
Two-layer enforcement with the *local* check explicitly subordinate to the door's 422. The
comment at `Kanban.tsx:137-139` says so: *"The door's 422 remains the authority — this never
replaces it."*

### Edge cases
- **`wipLimit === 0`** means unlimited — the pre-flight is skipped (`Kanban.tsx:141`).
- **Bulk move into a full column.** `Kanban.tsx:167-185` moves cards one at a time and reports
  `bulk move → <col>: N/M moved · refused: capacity` — partial success is reported as partial,
  not as failure.

### Surface gap
None.

---

## F4 — Move a card with a recorded reason

**View:** `web/src/views/Kanban.tsx:600-777` (`CardDrawer`)
**Persona:** A Operator
**Trigger:** the operator needs the move to be auditable, not just done.

### Steps
1. **Open the card.** `Kanban.tsx:217-226` fetches the authoritative card (`GET /api/tasks/:id`);
   a 404 renders `no such card: <id>`. The drawer is mounted at `:521`.
2. **Read the facts.** `Kanban.tsx:648-666` — `id` (`:652`), `column`, `assignee`, `tags`, and
   **`isDoneColumn`** as a literal `true`/`false` (`:660`). The drawer shows the flag, not a guess
   from the column name.
3. **Pick a target.** `Kanban.tsx:691-721` renders one button per other column
   (`:695` filters out the card's current column), each annotated `wip N` when the column has a
   limit (`:716`).
4. **The reason is mandatory.** `Kanban.tsx:700-705` — the note state is `:612`; clicking a
   target with an empty reason field sets an error at `:703`:
   > `a move needs a reason — the door records update_reason on every move`
   and **does not call the door**.
5. **Move.** `Kanban.tsx:707` sends `moveToColumnId(card.id, c.id, note)`; on success the drawer
   closes and the board refreshes.

### What the shell does well
The reason field is not optional decoration — it is a gate, and the gate's copy explains *why*
(`update_reason` is recorded on the card). This is the audit trail being enforced at the UI.

### Edge cases
- **422 on the drawer path.** `Kanban.tsx:711` renders `HTTP 422 CapacityFull — <detail>` inline
  in the drawer, so the operator does not lose their typed reason.
- **Card moved by an agent while the drawer is open.** The move will still be attempted; the door
  decides. The drawer does not re-read before writing — a known race, low impact because the door
  is the single writer.

### Surface gap
None.

---

## F5 — Claim a card, then release it

**View:** `web/src/views/Kanban.tsx:730-772`
**Persona:** A Operator, B Crew agent (the same metadata key)
**Trigger:** work needs an owner, or an owner needs to be removed.

### Steps
1. **The field is labelled with its semantics.** `Kanban.tsx:730`:
   *"assignee — merged into metadata, never replaced"*.
2. **Claim.** `Kanban.tsx:738-746` — type a name (`agent name` placeholder at `:738`), press
   `claim`; sends `patchMetadata(card.id, { assignee })` (`:744`).
3. **Release.** `Kanban.tsx:756-766` — `release (null)` (`:766`) sends `{ assignee: null }`
   (`:758`). Per `api.ts:348`, *"a key set to null is removed (this is how a claim is released)"*.
4. **Why merge matters.** `DocsFaq.tsx:80-92` (the claim answer): *"recording an assignee never
   erases tags"* — a `PATCH` that replaced metadata would silently drop the card's tags.

### What the shell does well
The two buttons are the two halves of one contract, and the label states the contract. An
operator who reads only the label still cannot corrupt the card.

### Edge cases
- **Claiming someone else's card.** The door refuses unless forced (`DocsFaq.tsx:80-92`). The
  drawer surfaces the error via `setErr(errMsg(e))` (`Kanban.tsx:745`).
- **Empty assignee string.** `claim` with an empty field sends `{ assignee: "" }`, which is a
  *set*, not a removal. The correct release path is the `release (null)` button. This is a real
  trap: two adjacent buttons where one is a no-op-looking set and the other is the removal.

### Surface gap
`claim` is not disabled when the field is empty (`Kanban.tsx:742-746`). A disabled state (or
coercing `""` → `null`) would remove the trap. Small, contained.

---

## F6 — Recover the board after an agent dies mid-claim

**View:** `web/src/views/Kanban.tsx:203-215` (`bulkRelease`), `:376-410` (bulk bar)
**Persona:** A Operator
**Trigger:** cards sit in a working column assigned to an agent that is no longer running.

### Steps
1. **Find them.** `Kanban.tsx:325` — the assignee filter (with `unclaimed`), or `swimlanes`
   (`:334-339`) to see one agent's cards as a row.
2. **Select.** `Kanban.tsx:490` — per-card selection populates `selected`.
3. **The bulk bar appears.** `Kanban.tsx:376-410` — `N selected`, then
   `release (drop assignee)`, a `move to…` select, `delete`, `clear`.
4. **Release.** `Kanban.tsx:203-215` — loops `patchMetadata(id, { assignee: null })` per card and
   reports at `:213`: `released N/M — assignee removed via metadata merge`.
5. **Then move.** `Kanban.tsx:167-185` via the `move to…` select, which reports partial success
   explicitly.

### What the shell does well
Release is separated from move, and release is non-destructive. The operator can free the cards
first and decide where they go second — which is the correct order when the destination is
itself at WIP.

### Edge cases
- **Delete is guarded.** `Kanban.tsx:189` — `window.confirm("Delete N card(s)? This is not
  undoable.")`. The only destructive action in the shell has a confirm.
- **Partial failure on release.** `Kanban.tsx:203-215` swallows per-card errors and counts by
  omission, then reports `released N/M`. The failures are not itemised — the operator knows *how
  many* failed but not *which*.

### Surface gap
`bulkRelease` reports a count, not the failing ids (`Kanban.tsx:203-215`). For a board with many
cards this forces a manual re-scan. Low severity, real friction.

---

## F7 — Decompose a roadmap phase into a card (Sarge)

**View:** `web/src/views/Kanban.tsx:780-868` (`SargePanel`)
**Persona:** A Operator
**Trigger:** a roadmap phase needs to become board work.

### Steps
1. **Open Sarge.** `Kanban.tsx:344` — the `Sarge` button in the board bar toggles `sargeOpen`;
   the panel renders above the board at `:410`.
2. **Read what Sarge is.** `Kanban.tsx:804-814` — the panel title is
   *"Sarge — decomposer, writes a real card back to the door"*, and the lede explains the
   `jobid` contract (`:810`, `:813`): Sarge writes the card id back into the phase as `jobid`,
   *"which is what stops the same phase being decomposed twice on the next pass."*
3. **Fill the card.** `Kanban.tsx:816-830` — `card title (required)` (`:816`), `content / brief`,
   `assignee`, `tags, comma separated`, and a landing-column select defaulting to the column
   flagged `isLanding` (`:797`), rendered at `:828`.
4. **Create.** `Kanban.tsx:831-856` — `create card` is **disabled until the title is non-empty**
   (`:837`), then `door.addCard(boardName, title, {...})` (`:838`). Success clears the form and
   shows `card created on "<board>"`.
5. **The honest caveat.** `Kanban.tsx:810-814`:
   > *"This panel creates the card through the same REST door every other tool uses — it does not
   > shell out to the roadmap files, so a card made here carries no `jobid` until Sarge sees the
   > phase."*

### What the shell does well
The panel does not pretend to be Sarge. It is a card-creation form that shares Sarge's landing
column, and it says so. That distinction is the difference between a useful shortcut and a
duplicate-work generator.

### Edge cases
- **422 on create.** `Kanban.tsx:854` — `HTTP 422 CapacityFull — <detail>` if the landing column
  is full. The form retains its content.
- **No landing column flagged.** `Kanban.tsx:797` falls back to `lanes[0]`.

### Surface gap
None. (The `jobid` write-back is Sarge's job, not this panel's, and the panel says so.)

---

## F8 — Fix a board whose done column is wrong

**View:** `web/src/views/Kanban.tsx:871-963` (`BoardControl`)
**Persona:** A Operator
**Trigger:** cards never register as done, because the flag sits on the wrong column.

### Steps
1. **Open board control.** `Kanban.tsx:342` — the `board control` button; the panel is titled at
   `:887`.
2. **See the current flag.** `Kanban.tsx:880` computes `doneCols`; `:922` renders
   `Current: <names>` or **`none — nothing can be completed`**.
3. **Pick and set.** `Kanban.tsx:897-921` — a select of all columns plus `set done column`
   (`:918`), which calls `door.setDoneColumn(board.name, pick)`. Per `api.ts:344`, this *"moves
   the flag, never adds a second one."*
4. **Verify against the table.** `Kanban.tsx:943-958` — a per-column table with `name`, `pos`,
   `wip`, `done`, `landing`, `id`. The `done` and `landing` cells are `Pill` badges, so the
   operator can confirm exactly one column carries each flag.
5. **Read the goal.** `Kanban.tsx:960` — `board goal — <goal>` or *"the door reported no goal for
   this board"*.

### What the shell does well
`none — nothing can be completed` is the single most valuable string in this view. It converts a
silent "cards never finish" bug into a named, fixable state.

### Edge cases
- **Door answers without success.** `Kanban.tsx:910` throws
  `door answered without success — did the board have that column?` rather than reporting a
  false success.

### Surface gap
None.

---

## F9 — Trace an invariant to the symbol that enforces it

**View:** `web/src/views/MemoryModel.tsx:10-128`
**Persona:** C Trust reviewer
**Trigger:** someone asks "how do you know a dream never gets retrieved as fact?"

### Steps
1. **The framing.** `MemoryModel.tsx:52-58` — grounded vs simulated, *"separated by code, not by
   convention."*
2. **Four stats.** `MemoryModel.tsx:60-65` — `hard invariants 5`, `guarded index writes 2`
   (vector + bm25), `promotion paths 1` (evidence only), and `clean contamination rate 0.0`
   (`:64`) whose sub-label is **`target`** — not a measurement.
3. **The five invariants, each with its guard.** `MemoryModel.tsx:10-41` defines them; `:69` is
   the section head; `:80-88` renders each as number + title + body + a `tag` carrying the guard
   symbol: `_assert_grounded()`, `_allow_simulated=False`, `_validate_partition_tags()`,
   `prediction_error_evidence`, `set_epistemic_status()`.
4. **The store layout.** `MemoryModel.tsx:43-49` defines it; `:95-104` renders it —
   `ledger.jsonl`, `embeddings.npy / index`, `bm25_corpus.json`, `records/<id>.md`, and
   `simulated/` with the note *"simulated partition — never indexed"*.
5. **The gate, drawn.** `MemoryModel.tsx:108-128` — simulated → `↓ requires
   prediction_error_evidence` → grounded, plus `Notice tone="warn"` titled **"There is no second
   path"** (`:121`): *"No admin override, no 'just this once', no flag that skips the gate."*

### What the shell does well
Every invariant names a symbol the reviewer can grep, and `MemoryModel.tsx:1-5` states that the
text is taken from `README.md` rather than paraphrased. This is the strongest surface in the
product for the Trust persona, and it is entirely static — it needs no backend.

### Edge cases
- **The `0.0` stat.** `MemoryModel.tsx:64` renders `clean contamination rate 0.0` with sub
  `target`. It is labelled as a target, not a result — consistent with the audit panel below it
  being `live run pending`.

### Surface gap
The contamination audit panel (`MemoryModel.tsx:130-141`) is a placeholder: *"there is no HTTP
route for it in mem20controlz yet, and this shell will not display a rate it did not measure"*
(`:137-141`). The reviewer's third goal cannot be completed here.

---

## F10 — Try to promote a dream without evidence

**View:** `web/src/views/Dreams.tsx:87-130`
**Persona:** C Trust reviewer
**Trigger:** the reviewer wants to see the gate actually refuse.

### Steps
1. **Read the list.** `Dreams.tsx:50-84` — `title`, `status`, `epistemic` (green `grounded` /
   amber `simulated`), and `evidence` as `present` / `absent`.
2. **Click a row.** `Dreams.tsx:64` — `onClick={() => setSel(d.id)}` populates the dream id field
   in the promotion panel (`:96`).
3. **Try to promote with no evidence.** The button is `disabled={!sel.trim() || !evidence.trim()}`
   (`Dreams.tsx:110`), and the helper text at `:124-126` reads:
   > *"disabled on purpose — there is no promotion without evidence"* (`:125`)
4. **Supply evidence.** `Dreams.tsx:102-109` — a textarea whose placeholder shows the shape:
   `prediction_error_evidence — e.g. {"prediction_id":"pred_…","resolved_in_favour":true}`.
5. **Promote.** `Dreams.tsx:111-121` — `JSON.parse` (`:113`) then `control.promote(id, parsed)`
   (`:114`); success shows `promote accepted by the control plane` (`:115`), a parse or HTTP
   error shows the message.

### What the shell does well
The gate is enforced **client-side before the request**, so the reviewer sees the rule rather
than a server 4xx. The file's header (`Dreams.tsx:1-12`) states the intent: *"the promote button
REFUSES to fire without it rather than letting the server 4xx later."*

### Edge cases
- **Malformed JSON.** `JSON.parse` (`:113`) throws inside the `try`, so the message is the parse
  error — readable, but not labelled as a JSON problem.
- **Control plane unreachable.** `Dreams.tsx:38-46` renders `Notice tone="warn"` — *"A statically
  hosted shell has no FastAPI behind it… No dream rows are shown rather than inventing them"*
  (`:45`).

### Surface gap
None for the gate itself. The gate is the best-implemented interaction in the Trust group.

---

## F11 — Follow a dream's provenance chain

**View:** `web/src/views/Dreams.tsx:132-145`
**Persona:** C Trust reviewer
**Trigger:** the reviewer has promoted a dream and wants the audit trail.

### Steps
1. **Read the promise.** `Dreams.tsx:134-139` — *"Every ledger line carries `origin` and
   `store`, and a promotion stamps the status onto the original grounded line plus the deep-store
   markdown header. The chain endpoint is `GET /api/dreams/{id}/chain`."* (`:138`)
2. **Look for the chain.** `Dreams.tsx:141` — the panel body is a static `div.empty`:
   > *"select a dream to read its chain — no chain is rendered while the control plane is
   > unreachable"*

### What the shell does
It names the route and refuses to fabricate a chain. That is the honest choice.

### Surface gap — **the largest in the product**
The route is documented (`Dreams.tsx:5`, `:138`), the copy promises it, and **the view never calls
it**. Selecting a row sets `sel`, but the only consumer of `sel` is the *promotion* panel
(`Dreams.tsx:96`) — nothing fetches the chain. A reviewer following the Trust path arrives at a
placeholder at the exact moment they need evidence.

**This is the flow to build next.** It is one effect on `sel` plus a render of the returned
chain — no new backend contract, no new screen.

---

## F12 — Falsify a Sales claim end-to-end

**View:** `web/src/views/Sales.tsx:67-113` → `web/src/views/DocsFaq.tsx:180-290`
**Persona:** E Evaluator
**Trigger:** the evaluator reads a claim and wants to check it without asking anyone.

### Steps
1. **Read the proof table.** `Sales.tsx:67-113` — five rows, each `claim` → `where it is
   verifiable`:
   - `{CATALOG.count} tools` → *"every `mt.Tool(…)` registration in `mcp/tools/*.py`, across N
     domains — browsable in Docs → Tool reference"* (`:84`)
   - `5 invariants` → *"numbered and paired with the symbol that enforces each — Memory model surface"*
   - `1 door, 1 store` → *"`mem20-kanban.service` on `127.0.0.1:8221`, sole writer of
     `kanban_3.db` — Door Sync surface"*
   - `11 wire routes` → *"transcribed from `mem20kanbanz/door.py`, including the 422 WIP refusal
     — Door Sync surface"* (`:99`)
   - `audit trail` → *"append-only `ledger.jsonl` with origin/store on every line, plus
     per-record provenance — Dreams surface"*
2. **Navigate by hand.** The rail (`App.tsx:30-40`) — `Docs / FAQ` under *Understand*.
3. **Check the tool count.** `DocsFaq.tsx:185-190` — the `Tool reference` tab is labelled with
   `CATALOG.count` (`:188`); `:194` searches name/title/description/domain; `:241` lists hits;
   `:259-280` shows the selected tool's `title`, `domain · mcp/tools/<domain>_tools.py`,
   description, and `inputSchema properties` (`:271`); `:283` is the pre-selection empty state.
4. **Check the retired counts are not restated.** `DocsFaq.tsx:124-138` — the count answer says
   the number *"is the number this UI stands behind"* (`:134`) and names `257`, `258`, `268` as
   retired counts that *"are not restated here"* (`:135-136`).
5. **Check a claim's source.** `DocsFaq.tsx:218-232` — every answer panel carries a
   `source-backed` pill (`:218`) and a `src` line naming a file (`:226`), plus tag chips
   (`:229`). Example: `README.md § Hard invariant 4 · mcp/memory_tools.py § _memory_promote`.

### What the shell does well
The proof table is unusually honest: it names the *surface*, not just the file, and the pricing
rows that are not real render as `$— / seat · quoted` (`Sales.tsx:156`) with a footnote at
`Sales.tsx:206-209`.

### Edge cases
- **The evaluator cannot click through.** The proof table's "where it is verifiable" cells are
  **prose, not anchors**. There is no `<a>` or `onClick` in `Sales.tsx:67-113` — the evaluator
  must use the rail and re-find the surface themselves.

### Surface gap
The proof table should link to its named surface. `Sales.tsx` already receives `onOpenApp`
(`Sales.tsx:14`, used at `:32`, `:148`, `:164`, `:177`, `:199`), and `App.tsx:71` already exposes
`go(route)` — wiring a route callback into the proof table is the only missing piece.

---

## F13 — Reach the door from another machine

**View:** `web/src/views/Connection.tsx:44-80`
**Persona:** D Remote operator
**Trigger:** the operator is on a laptop; the door is on the host.

### Steps
1. **Read the constraint.** `Connection.tsx:52-56` — *"default `DEFAULT_DOOR` — the door is
   loopback-only, so from another machine use `ssh -L 8221:127.0.0.1:8221` and keep this value"*
   (`:55`). The panel's pill starts at `checking` (`:49`).
2. **Establish the tunnel** (outside the shell — the shell cannot do this).
3. **Confirm the base.** `Connection.tsx:48-51` — the input is pre-filled from `getDoorBase()`.
4. **`save & test`.** `Connection.tsx:58-68` (`:67`) — persists, re-reads, re-probes, shows
   `door base saved` (`:64`). `reset` at `:70-77` restores `DEFAULT_DOOR`.
5. **Read the auth model while here.** `Connection.tsx:138-150` — pill `one model` (`:138`) and
   three `proof` cells: `door` = *"no auth — loopback only, so the network boundary is the
   control"* (`:140`); `control` = *"`/api/auth/login` sets the session; every other route is
   behind it"*; `shell` = *"carries no credentials of its own and stores no token"* (`:142`).
   The reasoning follows at `:145-149`: *"The shell deliberately does not cache an API key in
   localStorage. A static page that holds a credential is a credential leak with a stylesheet."*

### What the shell does well
It tells the truth about a limitation it cannot fix, and it does not offer a fake "connect"
button.

### Edge cases
- **Tunnel up, door still down.** The pill reads `down` and `ctl.detail` prints the raw error in
  mono (`Connection.tsx:120-124`, `:124`).
- **Empty control base.** `Connection.tsx:88-96` (`:91`) — empty means *"wherever this page was
  loaded from"*, which is the correct default for a same-origin shell.

### Surface gap
None. This is the best-served flow for the remote persona.

---

## F14 — Compose an agent from the five fields

**View:** `web/src/views/AgentBuilder.tsx:50-215`
**Persona:** A Operator
**Trigger:** the operator wants to define a new agent.

### Steps
1. **Read the frame.** `AgentBuilder.tsx:50-56` — *"Five fields decide what an agent is: identity,
   prompt, tools, memory scope, lifecycle"*, plus the real count (`:53`).
2. **Identity.** `AgentBuilder.tsx:60-68` — name input (`:62`) annotated
   *"the name an agent claims work under on the board — `patch_metadata.assignee`"* (`:64`).
3. **Prompt.** `AgentBuilder.tsx:69-77` — textarea (`:73`) with placeholder *"system prompt —
   what this agent is for, and what it must refuse"*.
4. **Memory scope.** `AgentBuilder.tsx:79-103` — four radios from `SCOPES` (`:14-19`):
   `user` (*durable facts about the operator*), `project` (*state of the work in flight*),
   `session` (*this conversation only*), `none` (*no recall — tools only*). Default `project`.
5. **Lifecycle.** `AgentBuilder.tsx:105-121` — five buttons from `LIFECYCLE` (`:13`), with the
   note at `:118`: *"only `active` agents may claim cards; retired names stay resolvable in
   history."*
6. **Tools.** `AgentBuilder.tsx:130-215` — search (`:139`) and a domain filter (`:141`) over
   `CATALOG.tools`, a `N selected` / `N shown` pill pair (`:133-134`), per-tool `params` tags
   (`:196`), and a `clear` button.
7. **Hit the wall.** `AgentBuilder.tsx:122-126` — `Notice tone="warn"` titled
   **"Provisioning is not wired yet"**:
   > *"This panel composes the five fields and shows the real tool catalog, but there is no write
   > route for agent definitions in the control plane yet — `app.py` exposes dreams, websites and
   > registry reads only. Creating an agent still goes through the CLI. Flagged rather than
   > faked: no agent is saved by this screen."* (`:125`)

### What the shell does well
The tool list is real — `AgentBuilder.tsx:1-8` documents that `src/data/tools.json` was produced
by AST-parsing `mcp/tools/*.py` for every `mt.Tool(...)` call. The panel is a *design surface*
over real data, and it says it cannot save.

### Edge cases
- **No tool matches.** `AgentBuilder.tsx:211` — `no tool matches "<q>"`.
- **400-tool render cap.** `AgentBuilder.tsx:155` — `filtered.slice(0, 400)`. With a catalog
  larger than 400 the list silently truncates; the `N shown` pill reports `filtered.length`
  (`:134`), not the rendered count, so the two disagree.

### Surface gap
Two, both stated by the view itself:
1. **No write route** — the five fields cannot be saved (`AgentBuilder.tsx:122-126`).
2. **`N shown` vs rendered** — `AgentBuilder.tsx:155` vs `:134`. Cosmetic, but it is a count that
   does not match what is on screen, which is exactly the class of error this product exists to
   avoid.

---

## F15 — Look up who may do what

**View:** `web/src/views/Teamily.tsx:53-90`
**Persona:** A Operator, B Crew agent
**Trigger:** "can a guest claim a card?" / "who is allowed to run a privileged command?"

### Steps
1. **Open Teamily → `roles`.** `Teamily.tsx:34-39` — four in-page tabs; `roles` is the second.
   The `roles` branch begins at `:53`.
2. **Read the authority table.** `Teamily.tsx:64` renders `ROLES` (defined `:11-15`) — three roles:
   - `operator` / `jayson` / *"everything, privileged commands included — by direct message only"*
   - `crew` / *"registered agents"* / *"take and report work; read everything"*
   - `guest` / *"anyone else"* / *"read-only self-description"*
3. **Read the three rules.** `Teamily.tsx:79` renders `RULES` (defined `:17-21`):
   - *"a guest cannot take work"* — *"a stranger should not be able to claim the operator's board."*
   - *"a privileged command is refused in the channel"* — *"even from the operator — the
     transcript is readable by everyone in it, so an instruction sent there could be replayed by
     a guest."*
   - *"a nick is a claim, not proof"* — *"an IRC nick is not authentication, so authority is
     scoped to match what the nick can prove."*
4. **Check the source.** `Teamily.tsx:87` — `source: mem20botz/identity.py`.

### What the shell does well
This is a **reference table over a real authority model**, not a member list. The three rules are
the design constraints the rest of the product obeys — particularly "a nick is a claim, not
proof", which is why `Kanban`'s assignee is a metadata key and not an identity.

### Edge cases
- **`members` tab.** `Teamily.tsx:41-52` — the `Pill` reads **`roster pending`** (`:42`) and the
  body is a `Notice tone="warn"` titled **"No member read route yet"** (`:43`): *"Listing invented
  members would be the exact failure the kanban merge was done to kill, so the table stays empty
  until a real route exists."* The empty body names the missing route at `:48`.
- **`groups` tab.** `Teamily.tsx:92-120` — a real bot map (`kanban`, `agentz`, `crewbot`, `relay`)
  with a `Notice` at `:114` that *"Channel state is not streamed into this shell"* — a browser
  cannot speak IRC on `127.0.0.1:6667`.
- **`activity` tab.** `Teamily.tsx:122-130` — `Notice` at `:124`: *"No activity feed to read…
  this surface shows nothing rather than a plausible-looking stream."*

### Surface gap
Three of four tabs are honest placeholders. **The `roles` tab is the only one that carries
information**, and it is the one a flow should be written against. Any flow that starts on
`members` is designing for a screen that does not exist.

---

## 9. Cross-flow findings

### 9.1 The three dead ends, ranked by cost to a persona

| Rank | Dead end | File:line | Persona blocked | Cost |
|---|---|---|---|---|
| 1 | Provenance chain never fetched | `Dreams.tsx:132-145` | C Trust reviewer | The Trust path ends at a placeholder at the moment evidence is needed |
| 2 | Contamination audit has no route | `MemoryModel.tsx:130-141` | C Trust reviewer | The `0.0` stat can never be confirmed as measured |
| 3 | Agent definitions cannot be saved | `AgentBuilder.tsx:122-126` | A Operator | Five fields compose, nothing persists |

All three are **stated by the view**, not inferred. That is the product's discipline working —
and it is also the research agenda.

### 9.2 The patterns the shell gets right (do not redesign these)

1. **Refuse to render a false empty state.** `Kanban.tsx:255`, `Dreams.tsx:38-46`,
   `Teamily.tsx:41-52`, `MemoryModel.tsx:137-141` — four independent instances of the same rule.
2. **Name the cause and the fix, not just the error.** `DoorSync.tsx:74-80`,
   `Kanban.tsx:259-290`, `Connection.tsx:52-56`.
3. **Gate the action, don't 4xx later.** `Dreams.tsx:110-126` (evidence), `Kanban.tsx:700-705`
   (reason), `Kanban.tsx:837` (title).
4. **Label stale as stale.** `Kanban.tsx:366-371` — *"Showing the board as of the previous
   successful read."*
5. **Every claim carries a source.** `DocsFaq.tsx:218-232`, `MemoryModel.tsx:1-5`,
   `Sales.tsx:67-113`.

### 9.3 What is *not* in the tree, and therefore not in any flow

- No chat / channel client — `Teamily.tsx:114-118` (a table, not a client).
- No login screen — `Connection.tsx:138-150` (the shell holds no credential).
- No member roster — `Teamily.tsx:41-52`.
- No activity feed — `Teamily.tsx:122-130`.
- No billing — `Sales.tsx:150-186` (`$—` placeholders).
- No mobile layout — every page is `page` / `page wide` with a fixed rail.
- No onboarding — `App.tsx:55-63` boots straight to `kanban`.

---

**Method note.** Every flow above was written by reading the view file at
`06fa1220e964f84aabac78127fc18463dfa6798d` and following its actual state transitions. Line
numbers were re-derived from the source (`grep -n` against the checked-out tree) rather than
estimated. Where a step could not be performed, it is recorded as a **Surface gap** rather than
written as if it worked.
