# A7 — Pages scheme downgrade: before-state capture

**Captured:** 2026-10-31T22:49:50Z (UTC)
**Item:** sweep §09 #7 — "Fix the Pages redirect to https so the canonical URL is not downgraded on the first hop"
**Status:** OBSERVED, NOT FIXED. The fix is the repository setting **Settings → Pages → Enforce HTTPS**, which only the repository owner can change. No repository setting was touched by this capture.

## Observation

Request to the GitHub Pages project URL:

```
GET https://bythewayz66-glitch.github.io/mem20/
```

Response headers (verbatim, first hop):

```
HTTP/2 301
server: GitHub.com
content-type: text/html
location: http://mem20.com/
x-github-request-id: CC0E:1A6DF7:463F0D:4DC077:6AE66C10
x-github-edge-region: sea
accept-ranges: bytes
age: 1150
date: Sat, 31 Oct 2026 22:49:50 GMT
via: 1.1 varnish
x-served-by: cache-lax-kwhp1940108-LAX
x-cache: HIT
x-cache-hits: 0
x-timer: S1793486991.668724,VS0,VE2
vary: Accept-Encoding
x-fastly-request-id: 7db43f7576cac3b7c0308681ce17b08673648dc4
content-length: 162
```

**The exact `Location` header is `http://mem20.com/` — scheme `http`, not `https`.**

Followed chain:

```
final_url = http://mem20.com/
code      = 200
redirects = 1
```

## Why this matters

The canonical host is `mem20.com` and it serves correctly over TLS (`https://mem20.com/` → `200`). But the first hop from the Pages project URL lands the visitor on the **plaintext** origin. That is a downgrade on the first request: the initial navigation is unencrypted, and any HSTS-less client stays on `http` for that page load.

## Fix (owner-only)

Repository **Settings → Pages → Enforce HTTPS** → enable. Once enabled, the 301 `Location` should become `https://mem20.com/` and the downgrade disappears.

This document records the before-state only. An after-state capture should be taken once the owner flips the toggle.

## Canonical host integrity (checked in the same run)

`https://mem20.com/` returns `200`, and its bytes are sha256-identical to `main:docs/index.html` and `main:docs/dashboard.html`:

| Surface | sha256 | Bytes |
|---|---|---|
| `https://mem20.com/` (live) | `ae533ac58697a4b8da566cff8485b1e801a2d0c772cefe4ac9805d8b05fc08cc` | 33,429 |
| `main:docs/index.html` | `ae533ac58697a4b8da566cff8485b1e801a2d0c772cefe4ac9805d8b05fc08cc` | 33,429 |
| `https://mem20.com/dashboard.html` (live) | `6a89a72524595b77b4dd92aef704e2a609338fe94ddc459c6cfb6c901e7c3c10` | 61,488 |
| `main:docs/dashboard.html` | `6a89a72524595b77b4dd92aef704e2a609338fe94ddc459c6cfb6c901e7c3c10` | 61,488 |

**No drift.**
