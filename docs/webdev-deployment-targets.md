# Webdev deployment targets — RETIRED

**Status: OBSOLETE as of 2026-10-31.**

This document was a verified inventory (measured 2026-10-03) of the `jaysonai.online`
fleet: `control.jaysonai.online`, `shop.jaysonai.online`, `jnet1.jaysonai.online`, the
`mem20-control` Cloudflare tunnel, and two `pages.dev` projects.

**`jaysonai.online` is retired.** The zone, its hosts, the tunnel and the origin box no
longer exist. Nothing in this repository targets them, and no action item should be
opened against them.

## What replaced it

| Surface | Where it lives now |
|---|---|
| Product website | GitHub Pages, built from `docs/` on `main`, custom domain `mem20.com` (`docs/CNAME`) |
| Canonical source | `github.com/bythewayz66-glitch/mem20` |
| Publish path | GitHub only — no server, no tunnel, no external publish authority |

See `docs/webdev/ionos-dns-mem20.md` for the live DNS record set for `mem20.com`,
`mem20.org`, `mem20.store` and `mem20.info`.

## Why this file still exists

It is kept as a tombstone so that a reader who finds an old link learns the target is
gone, rather than following a runbook for infrastructure that cannot be reached. The
original content is in git history at the commit before this rewrite.
