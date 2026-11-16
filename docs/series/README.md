# `docs/series/` — the mem20 narrative series (site + readers)

**Owner:** mem20 Content Creator · **Status:** live site assets

The published narrative layer of the mem20 product site: a series hub, a comic
reader, a chronicles reader, and the shared cookie-free analytics snippet that all
three load. This is **static site content**, not a Python subsystem — nothing here is
imported by the MCP server.

## What lives here

| Path | What it is |
|---|---|
| [`index.html`](./index.html) | Series hub — entry point for both readers. |
| [`comic/`](./comic/) | Comic reader. |
| [`chronicles/`](./chronicles/) | Chronicles reader. |
| [`ANALYTICS.md`](./ANALYTICS.md) | How the shared analytics snippet works and where it is included. |
| [`analytics.js`](./analytics.js) | The one shared, cookie-free analytics file loaded by every page type. |
| [`series.css`](./series.css) | Shared styling for the hub and both readers. |
| [`data/`](./data/) | Series content data consumed by the readers. |

## Analytics

`analytics.js` is loaded by the landing page (`docs/index.html`), the series hub, the
comic reader and the chronicles reader. It is **cookie-free and privacy-respecting** —
see [`ANALYTICS.md`](./ANALYTICS.md) for the per-page script tags and the data it
records.

## Rules

1. **One analytics file.** Every page type loads the same `analytics.js`; do not fork
   it per reader.
2. **Relative paths only.** The readers are served from `docs/series/`, so asset
   references are relative (`../analytics.js` from a reader, `analytics.js` from the
   hub). Absolute `/` paths break the GitHub Pages subpath deployment.
3. **No build step.** These are hand-authored static files; there is no bundler.

## Related

- [`docs/index.html`](../index.html) — the landing page that hosts the series entry.
- [`docs/webdev/`](../webdev/) — deployment targets and frontend drift records.
