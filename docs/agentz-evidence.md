# OREO editor (agentZ) — delivery evidence

**Live:** https://mem20.com/agentz/
**PR:** #240 (squash-merged as `a8ede41`)
**Branch:** `feat/oreo-agentz-workspace`

This file exists so the Artifact Evidence Gate has a committed artifact URL
for the change, per the 4.0 renovation rule.

## Artifacts

| Artifact | URL |
|---|---|
| Live site, real LLM reply | https://static.teamily.ai/sites/ca055acc-6302-4fd1-8eda-88bb1c0046d5/documents/03-live/03-live.png |
| Workspace, default view | https://static.teamily.ai/sites/ca055acc-6302-4fd1-8eda-88bb1c0046d5/documents/01-workspace/01-workspace.png |
| Workspace, features populated | https://static.teamily.ai/sites/ca055acc-6302-4fd1-8eda-88bb1c0046d5/documents/02-features/02-features.png |

## Verbatim evidence

- Typecheck: `npx tsc --noEmit` → 0 errors
- Tests: **collected 36 / passed 36 / failed 0** (`Test Files 2 passed (2)`)
- Build: `vite build` → clean; `text.pollinations.ai/openai` present in the bundle
- Pages workflow run 41671387358 → **completed / success**
- Live page: `http://mem20.com/agentz/` → **HTTP 200**
- Live mode pill: **`REAL LLM · OPENAI-FAST`**
- Live LLM round trip, asked *"In one sentence, what is an append-only ledger?"*:

  > An append-only ledger is a tamper-evident record keeping that accepts new
  > entries but never modifies or deletes existing ones, strictly allowing only
  > additions to preserve auditability.

  — Atlas, on the deployed site. Mock boilerplate cannot produce this.

## What changed

`mem20agentz/web` went from a 3-file graph viewer to a multi-agent workspace:

- `src/lib/llm.js` — keyless Pollinations transport, `live` and `mock` modes
  behind `VITE_LLM_MODE`; a failed call throws, never fabricates
- `src/lib/workspace.js` — pure state, unit-testable, no React
- `src/App.jsx` — channels, roster, @mention routing, quoting, attachments,
  task cards with continuation, interval triggers, memory, search
- `src/style.css` — 3→2→1 column responsive layout
- `.github/workflows/pages.yml` — builds the editor into `docs/agentz/` and
  fails the build if the LLM endpoint is missing from the bundle

The OREO graph editor is preserved as a second tab.

## Honest limits

- Triggers fire only while the tab is open; there is no server-side scheduler.
- `localStorage` is per-browser; two tabs overwrite each other.
- The anonymous LLM tier is rate-limited to roughly one reply per 30s and is a
  shared public service — nothing private should be sent to it.
- The OREO graph tab needs the Python backend on `:48022`; on a static deploy it
  shows an explicit "backend not reachable" notice rather than a blank panel.

## Rollback

Revert `a8ede41`, or set `VITE_LLM_MODE=mock` and rebuild.
