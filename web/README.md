# mem20-web

One shell for mem20: one nav, one auth model, one API client.

Built on the `teamz` base and extended into the full product surface:

| surface | state |
|---|---|
| Kanban | **wired to the real door** — `mem20-kanban` REST on `127.0.0.1:8221` |
| Dreams | wired to the `mem20controlz` routes (`/api/dreams`, `/chain`, `/promote`) |
| Agent Builder | five fields (identity · prompt · tools · memory scope · lifecycle) over the **real tool catalog** |
| Teamily | roles/groups from the estate's enforced model; live roster pending a route |
| Docs / FAQ | searchable FAQ + full tool reference |
| Sales | positioning, proof points, pricing, CTA |
| Memory model | the five hard invariants, each with its enforcing symbol |
| Door Sync | the real wire contract + an honest reachability probe |
| Connection | where the two upstreams live |

## The two upstreams

* **Kanban door** — `http://127.0.0.1:8221`. Contract transcribed in
  `src/lib/api.ts` from `mem20kanbanz/mem20kanbanz/door.py`. WIP violations are
  `HTTP 422` and surface as `CapacityFull`. Done is the column flag
  `isDoneColumn`, never a column name.
* **Control plane** — `mem20controlz` (FastAPI). Served same-origin, so the base
  is "wherever this page was loaded from" unless set in Connection.

The shell never opens SQLite. A second writer on the kanban database is a second
source of truth, which is exactly the drift the four-way kanban merge ended.

## The tool catalog is generated, not written

`src/data/tools.json` is produced by AST-parsing the estate's own
`mcp/tools/*.py` and reading every `mt.Tool(name=, title=, description=,
inputSchema=)` registration. `count` in that file is the real number of
registered tools; the UI renders it rather than a remembered figure.

## Honest gaps

* Agent definitions have no write route in the control plane yet, so the builder
  composes but does not save.
* Teamily members / channel activity need a read route and a websocket bridge
  for IRC; the surfaces say so instead of showing invented rows.
* `memory_audit_contamination()` is a store-layer function with no HTTP route —
  the contamination panel will not display a rate it did not measure.

## Run

```sh
npm install
npm run dev        # http://localhost:5180
npm run build      # -> dist/
npm run typecheck
```

Publish the build output to `docs/app/` in the `mem20` repo; the Pages URL is
`https://<owner>.github.io/mem20/app/`.

## Design

Deep navy-slate base · violet-indigo primary · cyan accent. Inter for UI,
JetBrains Mono for ids, cids and tool names.
