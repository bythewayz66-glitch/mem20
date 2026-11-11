# mem20 site analytics

Cookie-free, privacy-respecting page analytics for the mem20 product site and both series.

**Snippet:** [`docs/series/analytics.js`](analytics.js) — one shared file, loaded by every page type.

## Where it is included

| Page | Path | Script tag |
|---|---|---|
| Landing page | `docs/index.html` | `<script src="series/analytics.js" defer></script>` |
| Series hub | `docs/series/index.html` | `<script src="analytics.js" defer></script>` |
| Comic reader | `docs/series/comic/index.html` | `<script src="../analytics.js" defer></script>` |
| Chronicles reader | `docs/series/chronicles/index.html` | `<script src="../analytics.js" defer></script>` |

All four load the **same** file, so an event means the same thing on every page and the
numbers are directly comparable across the product site and the series.

## What is collected

| Event `e` | Fires when | Fields |
|---|---|---|
| `pageview` | page load (once) | `p` path, `t` title, `r` referrer host |
| `outbound` | click to an external site | `d` destination (`github` / `pypi` / `external`), `u` full URL, `p`, `t` |
| `nav` | click on a nav/footer link | `n` target (`product` / `series` / `comic` / `chronicles`), `u`, `p`, `t` |
| `series` | click on a series or issue link | `series` (`hub` / `comic` / `chronicles`), `i` issue number, `u`, `p`, `t` |

Every event also carries `ts` (epoch ms) and `site` (site label, `mem20.com`).

Issue blocks on the comic page are tracked even before their art exists: the issue rows are
not anchors yet, so a click anywhere inside an `.issue` block emits a `series` event with
that issue's number. That is what makes "which issue did they open" answerable while the
series is still in production.

## What is **not** collected

- **No cookies.** Nothing is written to `document.cookie`, `localStorage` or `sessionStorage`.
- **No personal data.** No IP is stored by the snippet, no user ID, no fingerprint, no
  device or browser string, no session ID, no cross-visit identifier.
- **No cross-site tracking.** No third-party script, no pixel, no shared ID. Referrer is
  reduced to a **hostname only** and same-site referrers are dropped.
- **No query strings or fragments.** `p` is `location.pathname` only, so search terms and
  anchors never leave the page.
- **No Do-Not-Track traffic.** If the browser sends `DNT: 1`, `Sec-GPC: 1`, or
  `navigator.globalPrivacyControl === true`, the snippet sends **nothing at all** — not even
  the pageview — and exposes `window.mem20Analytics.disabled === 'dnt'`.

## Where it goes

The destination is configured in **one place**: the `CFG.endpoint` constant at the top of
`analytics.js`.

```js
var CFG = {
  endpoint: '',            // e.g. 'https://collector.example.com/e' — empty = local only
  site: 'mem20.com',
  respectDNT: true,
  trackOutbound: true,
  trackNav: true,
  trackSeries: true
};
```

- **`endpoint: ''` (current default)** — nothing leaves the browser. Events are still
  emitted, but only to the page itself (see below). This is the safe default: the
  instrumentation is live and verifiable without shipping data anywhere.
- **Set `endpoint`** to a collector URL to start shipping. Events are POSTed as JSON with
  `credentials: 'omit'` (cookies are never attached) via `navigator.sendBeacon`, falling
  back to `fetch(..., {keepalive: true})`. The collector must send CORS headers allowing
  the site origin.

### Reading events in the browser

Every event is dispatched as a `mem20:analytics` CustomEvent on `document`, and appended to
`window.mem20Analytics.queue`. To watch live traffic:

```js
document.addEventListener('mem20:analytics', e => console.log(e.detail));
// or, after the fact:
window.mem20Analytics.queue
```

To emit a custom event from page code:

```js
window.mem20Analytics.track('cta_click', { where: 'hero' });
```

## How to read the numbers

Once an endpoint is set, the useful ratios are:

- **Series discovery rate** = `nav` where `n=series` ÷ `pageview` on `/`. How many landing
  visitors find the series at all.
- **Series depth** = `pageview` on `/series/comic/` + `/series/chronicles/` ÷ `pageview` on
  `/series/`. Whether the hub converts to a reader.
- **Issue engagement** = `series` events with a non-empty `i` ÷ `pageview` on the comic page.
  Which issues people actually click.
- **Install intent** = `outbound` where `d=pypi` ÷ `pageview`. The closest thing to a
  conversion signal the site has.
- **Repo intent** = `outbound` where `d=github` ÷ `pageview`.
- **Referrer mix** = distribution of `r` on `pageview`. Where readers come from.

Because DNT traffic is dropped entirely, absolute counts under-report. Treat these as
**ratios**, not censuses.

## Size and performance

The snippet is a single ~4 KB uncompressed file, loaded with `defer` so it never blocks
rendering, with no dependencies and no network request when `endpoint` is empty. It adds no
layout, no font and no image.

## Changing the destination

1. Edit `CFG.endpoint` in `docs/series/analytics.js`.
2. Commit. All four pages pick it up — there is nothing else to change.
3. To disable analytics entirely, set `respectDNT: true` and leave `endpoint: ''`, or
   remove the four `<script>` tags.
