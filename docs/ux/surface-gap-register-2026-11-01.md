# Surface Gap Register — `web/src/views/**`

**Date:** 2026-11-01
**Verified against:** `main` @ `152d994` (grafted clone, `git log -1` = *Merge PR #169: docs(4.0) SUBSTRATE.md*)
**Scope:** the nine shipped views reachable from the single nav in `web/src/App.tsx:30`
**Method:** every row below was read out of the checked-out tree at that commit. No row is
carried over from memory, and no row cites a line that was not re-read in this pass.

This register exists because the personas and task flows
([`desktop-personas-2026-11-01.md`](./desktop-personas-2026-11-01.md),
[`desktop-task-flows-2026-11-01.md`](./desktop-task-flows-2026-11-01.md)) were grounded at
`06fa1220`. `main` has since moved 88 commits. The flows still hold — the view files are
byte-identical in the regions they cite — but the *gaps* those flows route around deserve
their own tracked list, with a severity and an acceptance criterion each, so they can be
closed or explicitly accepted rather than rediscovered by every reader.

---

## 1. How to read this register

Each row is one of three kinds, and the kind matters more than the severity:

| Kind | Meaning | Who closes it |
|---|---|---|
| **Placeholder** | The surface says out loud that it cannot do the thing. Honest, and the copy is correct. | A backend route, then the view |
| **Defect** | The surface claims or implies something the code does not do. | Whoever owns the view |
| **Latent** | The code is wrong but cannot currently be reached, because a data bound is below the threshold. | Whoever owns the view, before the bound moves |

A **Placeholder** is not a bug. It is a design decision that has been written down, and the
only failure mode is a later contributor "fixing" it by inventing data. A **Defect** is a bug.
A **Latent** row is the dangerous one: it passes every test today and breaks silently the day
the catalog grows.

---

## 2. The register

### G-01 — Teamily roster is a placeholder, and the copy is accurate

- **Kind:** Placeholder
- **Anchor:** `web/src/views/Teamily.tsx:42`
- **What the surface says:** `<Panel title="Members" right={<Pill mono>roster pending</Pill>}>`
- **What the code does:** renders no member rows. There is no roster fetch in the view.
- **Gap:** none in the copy. The gap is that a reader who skims sees a "Members" panel and
  assumes a roster exists behind it.
- **Severity:** Low — the pill is unambiguous at the point of use.
- **Acceptance criterion:** the panel either renders real members from
  `mem20botz/identity.py`, or keeps the `roster pending` pill. It must never render
  plausible-looking names. **Do not close this by inventing rows.**

### G-02 — Teamily is a bot map, not a channel client

- **Kind:** Placeholder
- **Anchor:** `web/src/views/Teamily.tsx:114-117`
- **What the surface says:** a `warn` notice titled *"Channel state is not streamed into this
  shell"*, explaining that a browser cannot speak IRC on `127.0.0.1:6667` and needs a
  websocket bridge, and that the table above is the real bot map from `mem20botz/README.md`
  with live presence pending that bridge.
- **What the code does:** renders a four-row reference table (`kanban`, `agentz`, `crewbot`,
  `relay`) at `Teamily.tsx:107-110`. No socket, no polling, no presence.
- **Gap:** the *nav label* is "Teamily" and the *panel* is "Groups & channels", which reads as
  a chat surface. The notice corrects it, but only after the user has committed to the tab.
- **Severity:** Medium — this is the single most likely place for a designer to spec a flow
  for a screen that does not exist. The task flows already exclude chat for this reason.
- **Acceptance criterion:** any flow that begins "the user opens a channel" is rejected at
  review until a websocket bridge exists. The notice stays until then.

### G-03 — Contamination audit has no route, and the surface refuses to fake a rate

- **Kind:** Placeholder
- **Anchor:** `web/src/views/MemoryModel.tsx:130` (pill), `:137-140` (notice)
- **What the surface says:** pill `live run pending`; notice *"Not run from the browser"* —
  the audit is a store-layer function, there is no HTTP route for it in `mem20controlz` yet,
  and the shell will not display a rate it did not measure. *"Green here must mean measured,
  never assumed."*
- **What the code does:** renders the explanation and no number. `memory_audit_contamination()`
  is described at `:132-136` but never called.
- **Gap:** the trust surface — the one place a reviewer goes to confirm the grounded/simulated
  partition holds — cannot show its own headline metric.
- **Severity:** **High.** This is the highest-value gap in the register. Every other
  placeholder is a missing convenience; this one is a missing *proof*, on the screen whose
  entire job is proof.
- **Acceptance criterion:** a `GET /api/memory/contamination` route in `mem20controlz` that
  calls the real store-layer function, and a view that renders `contamination_rate`,
  `violations`, and `violations_simulated_in_bm25_corpus` from that response. A clean system
  must render `0.0` **from a measurement**, not from a default. Until the route exists the
  pill stays.

### G-04 — The provenance chain is promised in prose and never fetched

- **Kind:** Placeholder (with a copy defect)
- **Anchor:** `web/src/views/Dreams.tsx:134-144`
- **What the surface says:** a panel titled *"Provenance & audit trail"* whose lede states that
  every ledger line carries `origin` and `store`, that a promotion stamps status onto the
  original grounded line plus the deep-store markdown header, and that the chain endpoint is
  `GET /api/dreams/{id}/chain`. The body is an empty state: *"select a dream to read its chain
  — no chain is rendered while the control plane is unreachable"*.
- **What the code does:** `grep -n "chain" web/src/views/Dreams.tsx` returns five hits, all of
  them prose or the endpoint string (`:6`, `:37`, `:137`, `:138`, `:141`). There is **no call
  to the chain endpoint anywhere in the file.** The only fetch is `control.dreams()` at `:26-30`.
- **Gap:** the empty state blames the control plane ("while the control plane is unreachable"),
  but the chain would not render even with a healthy control plane, because nothing requests
  it. `sel` is declared at `:22` and never used to fetch.
- **Severity:** **High** — and note the copy defect specifically: the empty state's stated
  reason is false. A reviewer with a live control plane would read that message, conclude the
  backend was down, and go debug the wrong system.
- **Acceptance criterion:** (a) an effect keyed on `sel` that calls the chain endpoint and
  renders the returned lines; (b) the empty state re-worded to distinguish *"no dream selected"*
  from *"control plane unreachable"* — two different states currently share one message.
  This is the cheapest high-severity fix in the register: one effect on `sel`.

### G-05 — `claim` can write an empty assignee

- **Kind:** Defect
- **Anchor:** `web/src/views/Kanban.tsx:744` (claim), `:758` (release)
- **What the code does:** the claim button calls
  `door.patchMetadata(card.id, { assignee })` with no guard on `assignee`. The input at
  `:733-738` is seeded from `useState(card.assignee)` (`:613`) and is freely editable, so it
  can be cleared to `''`. The release button at `:758` correctly sends `{ assignee: null }`.
- **What the door does:** `mem20kanbanz/mem20kanbanz/door.py:364-377` merges the patch and
  removes a key mapped to `None`. An empty string is **not** `None`, so `''` is merged in as a
  real value rather than removing the key.
- **Gap:** a card can end up with `assignee: ""` — neither claimed nor cleanly unclaimed. The
  board's own filters then disagree about it: `:128` treats a falsy `assignee` as unassigned
  (`assigneeFilter === '__none__' && c.assignee`), while `:129` compares
  `c.assignee !== assigneeFilter`, so an `''` card is invisible under "all assignees" grouping
  at `:544` (`c.assignee || '— unclaimed —'`) yet still occupies the claimed styling test at
  `:477` (`c.assignee && !c.isDone`). The two paths disagree on the same value.
- **Severity:** Medium — no data loss, but it corrupts the one field the board's grouping and
  filtering are built on, and the corruption is silent.
- **Acceptance criterion:** the claim button is disabled while `assignee.trim() === ''`, and
  the handler sends `assignee.trim()`. A card must never hold `assignee: ""`. Add a test that
  asserts `patchMetadata` is not called with an empty-string assignee.

### G-06 — The tool list is sliced at 400 while the pill reports the unsliced count

- **Kind:** **Latent** — not currently reachable
- **Anchor:** `web/src/views/AgentBuilder.tsx:134` (pill), `:155` (slice)
- **What the code does:** the panel header renders `<Pill mono>{filtered.length} shown</Pill>`
  at `:134`, but the list body renders `filtered.slice(0, 400).map(...)` at `:155`.
- **Why it is latent, not live:** the catalog is **270 tools across 27 domains**
  (`web/src/data/tools.json`: `count: 270`, `domain_count: 27`, `domains` length 27,
  `tools` length 270; surfaced through `web/src/data/catalog.ts`). `270 < 400`, so the slice
  never truncates today and the pill is currently truthful.
- **Gap:** the moment the catalog passes 400 tools the pill starts over-reporting, and the
  over-report is invisible — the user sees "431 shown" above a list that ends at 400 with no
  scroll affordance or "more" marker.
- **Severity:** Low today, **High on the day it triggers.** This is exactly the class of bug
  that ships because it is green in every test until it is not.
- **Acceptance criterion:** either drop the slice (the list is already inside a
  `maxHeight: calc(100vh - 330px)` scroll container at `:153`, so the slice buys nothing), or
  make the pill report `Math.min(filtered.length, 400)` and render an explicit
  "showing 400 of N" line. Prefer dropping the slice. Add a test that fails if
  `CATALOG.count > 400` while a slice is present.

---

## 3. Summary

| ID | View | Kind | Severity | Cheapest close |
|---|---|---|---|---|
| G-01 | Teamily | Placeholder | Low | none — keep the pill |
| G-02 | Teamily | Placeholder | Medium | none — keep the notice |
| G-03 | MemoryModel | Placeholder | **High** | new control-plane route |
| G-04 | Dreams | Placeholder + copy defect | **High** | one effect on `sel` + reword |
| G-05 | Kanban | Defect | Medium | guard + `trim()` |
| G-06 | AgentBuilder | Latent | Low → High | drop the slice |

**Two rows are worth doing first, and neither is large.** G-04 is one effect and one reworded
empty state. G-06 is a deleted `.slice(0, 400)`. Together they remove the only *false statement*
in the register (G-04's empty state blaming the control plane) and the only *time bomb* (G-06).

**G-03 is the one that needs a decision, not a patch.** It is the trust surface's headline
metric and it has no route. Either the route gets built, or the product accepts that the
contamination rate is a CLI-only number — but that choice should be made explicitly, because
the screen currently promises a proof it cannot produce.

---

## 4. What this register does not claim

- It does not claim the nine views are complete. It claims these six gaps are real at
  `152d994` and that each has a stated acceptance criterion.
- It does not re-derive the personas or flows. Those were grounded at `06fa1220`; the view
  files are unchanged in the cited regions, so the flows stand.
- It does not treat a Placeholder as a defect. G-01, G-02 and G-03 are honest copy over a
  missing backend. The failure mode to guard against is a contributor "completing" them with
  invented data, which is why each acceptance criterion says so explicitly.
- **G-06 is recorded as latent, not live.** An earlier draft of this research called the
  count mismatch a live defect. It is not: the catalog is 270 tools and the slice is 400. The
  correction is recorded here rather than quietly dropped, because a register that overstates
  its findings is worth less than one that does not exist.

---

## 5. Verification commands

Every anchor above can be re-checked in one pass from a clone at `152d994`:

```bash
sed -n '42p'    web/src/views/Teamily.tsx        # G-01 roster pending
sed -n '114,117p' web/src/views/Teamily.tsx      # G-02 channel notice
sed -n '130p;137,140p' web/src/views/MemoryModel.tsx  # G-03 pill + notice
sed -n '134,144p' web/src/views/Dreams.tsx       # G-04 panel + empty state
grep -n "chain" web/src/views/Dreams.tsx         # G-04: prose only, no fetch
sed -n '744p;758p' web/src/views/Kanban.tsx      # G-05 claim vs release
sed -n '134p;155p' web/src/views/AgentBuilder.tsx # G-06 pill vs slice
python3 -c "import json;d=json.load(open('web/src/data/tools.json'));print(d['count'],d['domain_count'],len(d['tools']))"
# expect: 270 27 270  -> 270 < 400, so G-06 is latent
```

---

**UX Researcher** · 2026-11-01 · grounded at `main` @ `152d994`
