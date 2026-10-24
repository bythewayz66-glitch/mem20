---
applyTo: "web/**,dashboard/**"
---

# Frontend rules (`web/`, `dashboard/`)

Two separate Vite apps — do not merge or cross-import them.

| App | React | Notes |
| --- | --- | --- |
| `web/` | React 18 | The unified shell. TypeScript, `tsc --noEmit` typechecks. |
| `dashboard/` | React 19 | Standalone dashboard for the MCP server. |

## `web/src/data/tools.json` is GENERATED

Never hand-edit it. It is AST-extracted from `mcp/tools/*.py` by
`web/scripts/extract-tools.py` inside `.github/workflows/mem20-web.yml`, then
rebuilt and published to `docs/app/` for GitHub Pages. To change the catalog,
change the Python tool signatures and let CI regenerate.

## Commands

```bash
cd web && npm install && npm run typecheck && npm run build
cd dashboard && npm install && npm run build
```

`npm run typecheck` is part of the CI gate — a PR that fails it does not build.

## Conventions

- `web/src/lib/api.ts` is the single API client; route new calls through it
  rather than adding `fetch` calls in views.
- Views live in `web/src/views/`, shared UI in `web/src/components/ui.tsx`,
  styles in `web/src/styles.css`.
- Do not commit `dist/` or `node_modules/`.
