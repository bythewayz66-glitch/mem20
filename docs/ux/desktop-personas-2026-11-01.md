# mem20 desktop — personas grounded in the shipped views

**Written:** 2026-11-01 · **Owner:** UX research (roster row 20, desktop)
**Baseline:** `main` @ `06fa1220e964f84aabac78127fc18463dfa6798d`
**Surface of record:** `web/src/views/**` — nine files, all reachable from the one nav in `web/src/App.tsx:30`
**Companion:** [desktop-task-flows-2026-11-01.md](./desktop-task-flows-2026-11-01.md)

---

## 0. Why this document exists

The gap this closes: *desktop research was not grounded in the surfaces that actually exist.*
Personas written from imagination produce flows for screens nobody built, and a flow for a
screen that does not exist is worse than no flow — it becomes a spec an engineer is asked to
satisfy against a component that is not in the tree.

So the method here is inverted from the usual persona exercise. **The surface comes first, the
persona second.** Every persona below is derived from evidence *inside the view files*: the copy
the shell addresses to someone, the control it offers, and the wall it admits to. A persona that
no view speaks to is not listed, however plausible it sounds.

Line numbers were re-derived from the source at `06fa1220`; the view files are byte-identical on
`main` @ `2ea44922`, so every citation holds on either ref.

### 0.1 The nine surfaces, as shipped

| Route id | Nav label | Group | View file | Lines | What it actually is |
|---|---|---|---|---|---|
| `kanban` | Kanban | Operate | `web/src/views/Kanban.tsx` | 965 | The one board, over the REST door on `:8221` |
| `dreams` | Dreams | Operate | `web/src/views/Dreams.tsx` | 147 | Dream list + evidence-gated promotion gate |
| `agents` | Agent Builder | Operate | `web/src/views/AgentBuilder.tsx` | 217 | Five-field agent composition over the real tool catalog |
| `teamily` | Teamily | Operate | `web/src/views/Teamily.tsx` | 132 | Members / roles / groups / activity — four tabs |
| `docs` | Docs / FAQ | Understand | `web/src/views/DocsFaq.tsx` | 292 | 11 sourced FAQ answers + full tool reference |
| `sales` | Sales | Sell | `web/src/views/Sales.tsx` | 211 | Positioning, proof table, pricing |
| `memory` | Memory model | Trust | `web/src/views/MemoryModel.tsx` | 145 | The five hard invariants, each with its guard symbol |
| `door` | Door Sync | Trust | `web/src/views/DoorSync.tsx` | 169 | Live door probe + the 11-route wire contract |
| `connection` | Connection | Trust | `web/src/views/Connection.tsx` | 167 | Where the two upstreams live; auth model |

Nav groups are `Operate / Understand / Sell / Trust` (`App.tsx:30-40`), and the rail is the
**only** navigation in the product — `App.tsx:3-4` states it: *"The nav below is the ONLY
navigation in the product — no per-surface tabs, no second auth flow."* (Teamily's four tabs
are in-page state, not navigation.)

### 0.2 The one fact that shapes every persona

`App.tsx:84-88` polls `door.healthy()` every **30 s** and renders the result in the rail foot as
`door up / door down` (`App.tsx:123-131`). There is no login screen in the shell, no account
concept, and no per-user state. `Connection.tsx:138-150` says why:

> *"The shell deliberately does not cache an API key in localStorage. A static page that holds a
> credential is a credential leak with a stylesheet."* (`Connection.tsx:145-149`)

**Consequence for research:** this is a *single-operator, self-hosted, loopback* product. There
is no multi-tenant persona, no "admin vs member" split inside the shell, and no onboarding
funnel. Any persona that assumes a signup, a team invite, or a per-user dashboard is designing
for a screen that does not exist.

---

## 1. Persona A — The Operator (primary)

**One line:** the person who owns the machine the door runs on, and is accountable for what the
agents did on the board.

### Evidence this persona exists
- `Kanban.tsx:255` — the unreachable branch tells them to run `systemctl status mem20-kanban`.
  Only someone with shell access to the host is addressed by that sentence.
- `Connection.tsx:52-56` — *"the door is loopback-only, so from another machine use
  `ssh -L 8221:127.0.0.1:8221` and keep this value"* (`:55`). Assumes host access, not a hosted
  account.
- `DoorSync.tsx:76` — *"loopback-only by design (`restart=always`, enabled at boot)"* — systemd
  vocabulary, i.e. an operator who reads unit files.
- `Kanban.tsx:187-201` — `bulkDelete` guards with `window.confirm("Delete N card(s)? This is not
  undoable.")` (`:189`). The shell assumes the reader is the person allowed to answer that.

### Context of use
| | |
|---|---|
| **Environment** | Their own workstation or a small server; browser on the same host, or over an SSH tunnel |
| **Session shape** | Short, frequent checks — the 30 s door poll is the heartbeat they glance at |
| **Time pressure** | High when a bot has stalled a column; low when reviewing the week |
| **Tech proficiency** | High — reads `systemctl`, `ssh -L`, `sha256`, `kanban_3.db` without gloss |
| **Device** | Desktop browser, wide viewport (`Kanban` and `AgentBuilder` both render `className="page wide"`) |

### Goals
1. **Know whether the board is real right now** — not "is the page up", but "did the door answer".
2. **Unstick work** — a card claimed by a dead agent, a column at its WIP limit, a phase that
   never got decomposed.
3. **Be able to say what happened** — every move carries a reason, every claim is a metadata
   merge, and the ledger is append-only.

### Pain points the shell already names
- **An unreachable door looks exactly like an empty board.** `DoorSync.tsx:3-6` says this is the
  reason the panel exists; `Kanban.tsx:255` refuses to draw the empty board at all.
- **A silent no-op is worse than an error.** `DocsFaq.tsx:57` — *"A silent no-op here would be
  worse than an error, because an agent would believe the work had advanced."*
- **Four kanban implementations, two SQLite files, one invisible real board.** `DoorSync.tsx:150-163`
  and `Sales.tsx:44-48` both carry this history; it is the operator's origin story.

### What this persona **cannot** do in the shell today
- Cannot create or edit an agent definition — `AgentBuilder.tsx:122-126` is an explicit
  `Notice tone="warn"` titled **"Provisioning is not wired yet"**: *"there is no write route for
  agent definitions in the control plane yet… Creating an agent still goes through the CLI.
  Flagged rather than faked: no agent is saved by this screen."* (`:125`)
- Cannot see who is a member — `Teamily.tsx:41-52`, pill reads **`roster pending`** (`:42`).
- Cannot run the contamination audit — `MemoryModel.tsx:130-141`, pill reads **`live run pending`**
  (`:137`).

### Success criteria (observable)
- Rail foot reads `door up` and the board renders cards — not a spinner, not an empty lane set.
- A move they made shows `moved <id> → <column>` in the status notice (`Kanban.tsx:152`).
- After a bulk release, the notice reads `released N/N — assignee removed via metadata merge`
  (`Kanban.tsx:213`).

---

## 2. Persona B — The Crew Agent (a real actor, not a human)

**One line:** a registered bot that takes work off the board, and whose identity is a *claim*
the shell has to be careful about.

### Evidence this persona exists
- `AgentBuilder.tsx:13` — `LIFECYCLE = ['draft','provisioned','active','paused','retired']`, with
  the note at `:118`: *"only `active` agents may claim cards; retired names stay resolvable in
  history."*
- `AgentBuilder.tsx:64` — the name field is annotated *"the name an agent claims work under on
  the board — `patch_metadata.assignee`"*. The agent's identity **is** a metadata key.
- `Teamily.tsx:11-15` — role `crew` = *"registered agents"*, may *"take and report work; read
  everything"*.
- `Teamily.tsx:17-21` — *"a nick is a claim, not proof"* — an IRC nick is not authentication, so
  authority is scoped to what the nick can prove.
- `Kanban.tsx:730-772` — the drawer's assignee field is labelled *"assignee — merged into
  metadata, never replaced"* (`:730`), with `claim` (`:744`) and `release (null)` (`:758`) buttons.

### Why this persona matters to desktop research
The agent is the **co-author of the operator's screen state**. Every card in a working column
was put there by an agent, and the shell's job is to make that legible without over-claiming.
`Teamily.tsx:17-21` is the design constraint in the agent's own words: a nick is a claim, not
proof — so the UI must never render an agent's presence as authenticated authority.

### Goals
1. Find claimable work (a card in the landing column, unassigned).
2. Claim it **before** moving it — `DocsFaq.tsx:80-92`: *"The assignee is written *before* the
   move, so a card is never sitting in the working column owned by nobody."*
3. Report completion by moving to the column that carries `isDoneColumn` — never by name.

### Pain points
- **Column names disagree across boards.** `Kanban.tsx:16-18`: *"Boards in this estate disagree
  on naming (dev/in_progress, Fleet HQ/in progress), so nothing here ever compares a column name
  to 'done'."* A hardcoded name made every claim on one board fail.
- **WIP limits refuse moves with HTTP 422.** `Kanban.tsx:12-14` — surfaced as `CapacityFull`,
  *"never swallowed, never retried silently"* (`:14`).
- **A claim on someone else's card is refused unless forced** (`DocsFaq.tsx:80-92`).

### What this persona **cannot** do in the shell today
- There is no agent-facing surface at all. The shell is a *human* view of agent state. The agent
  acts through the door's REST routes (`web/src/lib/api.ts:340-350`), not through these views.
- No presence, no heartbeat, no "which agent is alive" — `Teamily.tsx:114`: *"Channel state is
  not streamed into this shell… live presence is pending that bridge."*

---

## 3. Persona C — The Trust Reviewer

**One line:** the person who has to answer *"can you prove what this agent remembers?"* to
someone who is not in the room — a compliance reviewer, a customer's security team, a sceptical
colleague.

### Evidence this persona exists
- `Sales.tsx:19-27` — the hero copy is written *at* this person: *"when your agent acts on a
  memory, can you show where it came from? … That is enforced in the store, not promised in a
  prompt."*
- `MemoryModel.tsx:1-5` — *"Invariant text is taken from README.md § 'Hard invariants enforced by
  the store engine' — not paraphrased into something the code does not do. Each carries the
  symbol that actually enforces it, so a reader can go look."*
- `DocsFaq.tsx:218` — the answer panel's pill reads **`source-backed`**, and every answer carries
  a `src` line naming a file (`DocsFaq.tsx:226`).
- `Dreams.tsx:132-145` — the provenance panel names `GET /api/dreams/{id}/chain` as the audit
  trail (`:138`).

### Context of use
| | |
|---|---|
| **Environment** | Desktop, often screen-sharing or exporting rather than clicking live |
| **Session shape** | Long, read-only, adversarial — they are looking for the gap |
| **What they need** | A symbol, a file, a route — something they can check without trusting the page |
| **Failure they fear** | A green badge that means "we assumed it" rather than "we measured it" |

### Goals
1. Map each of the five invariants to the function that enforces it.
2. Follow one dream from simulated → promoted, with the evidence that justified it.
3. Confirm the audit trail is append-only and carries `origin` + `store` on every line.

### Pain points the shell already names
- **Green must mean measured.** `MemoryModel.tsx:137-141`: *"The audit is a store-layer function;
  there is no HTTP route for it in mem20controlz yet, and this shell will not display a rate it
  did not measure. Green here must mean measured, never assumed."*
- **No second promotion path.** `MemoryModel.tsx:121`: *"No admin override, no 'just this once',
  no flag that skips the gate."*
- **Retired counts must not be restated.** `DocsFaq.tsx:124-138` names `257`, `258`, `268` as
  retired (`:135`) and refuses to repeat them (`:136`).

### What this persona **cannot** do in the shell today
- Cannot see a contamination rate — the panel is `live run pending` (`MemoryModel.tsx:130`).
- Cannot read a provenance chain — `Dreams.tsx:141`: *"select a dream to read its chain — no chain
  is rendered while the control plane is unreachable."* The chain panel is a placeholder; the
  route is documented (`:138`) but the view never calls it.

> **Research note.** This is the single largest gap between what the Trust group *promises* and
> what it *shows*. `MemoryModel` and `Dreams` are the two surfaces a reviewer is sent to, and both
> end in a "pending" pill. That is honest, and it is also the highest-value thing to fix.

---

## 4. Persona D — The Remote Operator (tunnelled)

**One line:** the operator, but on a different machine from the door — the case the shell
handles explicitly and the case most likely to be mistaken for an outage.

### Evidence this persona exists
- `Connection.tsx:52-56` — the `ssh -L 8221:127.0.0.1:8221` instruction exists for exactly this
  person (`:55`).
- `DoorSync.tsx:74-80` — *"A browser can only reach the door if it is on the same machine or the
  door is exposed through a proxy… so a remote browser will always see this."*
- `Kanban.tsx:255` — the unreachable copy offers two remedies: start the door, **or** point the
  shell at one from Connection (`:285`).

### Why they are a separate persona and not a mode
Their failure state is *expected and permanent*, not exceptional. A remote operator will see
`door down` on first load, every load, until they tunnel. If the shell treats that as an error
condition, it trains them to ignore the one signal that matters. `DoorSync.tsx:74-80` is the
correct treatment: name the cause, name the fix, do not call it a fault.

### Goals
1. Distinguish "I am remote" from "the door is dead" in under five seconds.
2. Set the door base once and have it stick (`Connection.tsx:58-68`, `save & test`).
3. Get back to the board without re-reading an essay.

### Pain point
`Connection.tsx:58-68` persists the base via `setDoorBase(...)`, but the shell stores **no
credential** (`Connection.tsx:145-149`). So a tunnelled session is re-established by the tunnel,
not by the app — the app cannot help, and should not pretend to.

---

## 5. Persona E — The Evaluator (pre-purchase)

**One line:** someone deciding whether this is worth running, who will read the Sales page and
then try to falsify one claim on it.

### Evidence this persona exists
- `Sales.tsx:67-113` — a table headed **"Proof, not adjectives"**, where every claim names the
  surface that verifies it: *"{CATALOG.count} tools … browsable in Docs → Tool reference"*
  (`:84`), *"5 invariants … Memory model surface"*, *"1 door, 1 store … Door Sync surface"*,
  *"11 wire routes … Door Sync surface"* (`:99`).
- `Sales.tsx:116-131` — **"Who it is for"** names three segments: agent platform teams,
  automation and ops, research and evaluation.
- `Sales.tsx:206-209` — *"figures on this page are read from the repository at build time; the
  pricing rows marked 'quoted' are intentionally not invented."*
- `Sales.tsx:150-186` — the Team tier's amount renders as `$— / seat · quoted` (`:156`), not a
  number.

### Goals
1. Check one claim end-to-end without asking anyone (Sales → Docs → the surface it names).
2. See a price that is either real or explicitly unquoted.
3. Understand the differentiator in one sentence: grounded vs simulated, separated by code.

### Pain point
The proof table's links are **prose, not links** — "browsable in Docs → Tool reference" is a
sentence, not an anchor. The evaluator has to use the rail themselves. This is a real, small,
fixable friction point, and it is the only place in the shell where a claim is stated without a
one-click path to its evidence.

---

## 6. Personas deliberately **not** created

Listed so the next researcher does not re-derive them, and so no flow is written for them.

| Rejected persona | Why it has no surface |
|---|---|
| **Team member / invited user** | No invite, no account, no per-user state. `Connection.tsx:138-150` — the shell carries no credentials. |
| **Chat participant** | There is no chat view. `Teamily.tsx:114` says channel state is not streamed; the four bots are a *table*, not a client. **Chat does not count as a surface.** |
| **Billing / plan admin** | `Sales.tsx` is a marketing page with `$—` placeholders (`:156`). No billing route in `api.ts:357-373`. |
| **Mobile user** | Every page is `className="page"` / `"page wide"` with a fixed left rail; `Kanban` uses drag-and-drop lanes. No responsive breakpoint work exists. |
| **New-user / onboarding** | No first-run flow. The shell boots straight to `kanban` (`App.tsx:55-63`) and shows `door down` if it cannot reach one. |

---

## 7. Persona → surface matrix

`●` primary · `○` secondary · `—` not used

| Surface | A Operator | B Crew agent | C Trust reviewer | D Remote op | E Evaluator |
|---|---|---|---|---|---|
| `Kanban.tsx` | ● | ○ (via door, not UI) | ○ | ● | ○ |
| `Dreams.tsx` | ○ | — | ● | ○ | ○ |
| `AgentBuilder.tsx` | ● | ○ (identity/lifecycle) | ○ | ○ | — |
| `Teamily.tsx` | ○ | ● (roles tab) | ○ | — | — |
| `DocsFaq.tsx` | ○ | — | ● | ○ | ● |
| `Sales.tsx` | — | — | ○ | — | ● |
| `MemoryModel.tsx` | ○ | — | ● | — | ○ |
| `DoorSync.tsx` | ● | — | ○ | ● | ○ |
| `Connection.tsx` | ● | — | — | ● | — |

---

## 8. What this changes about the research plan

1. **Stop designing for a chat surface.** The Teamily view is a *reference table* over
   `mem20botz/identity.py` (`Teamily.tsx:87`), not a client. Any flow that starts "the user opens
   a channel" is designing for a screen that does not exist.
2. **Treat the three "pending" pills as the research agenda**, not as defects to route around:
   `roster pending` (`Teamily.tsx:42`), `live run pending` (`MemoryModel.tsx:130`), and the
   unrendered provenance chain (`Dreams.tsx:141`). These are the three places where a persona's
   goal is stated on screen and cannot be completed.
3. **The unreachable-door state is a first-class flow, not an error page.** It is the only state
   a remote operator ever sees on first load.
4. **Every flow must name a file.** See the companion document — each of its 15 flows opens with
   the view file and line range it exercises, and none of them requires a component that is not
   in the tree.

---

**Method note.** Every claim above is traceable to a line in `web/src/views/**` or
`web/src/App.tsx` at `06fa1220`. No persona was inferred from the product's marketing, from
`README.md`, or from a prior research document. Where the shell admits a gap, the gap is quoted
rather than smoothed over.
