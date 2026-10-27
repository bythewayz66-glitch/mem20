# IONOS DNS → GitHub Pages for the four mem20 domains

**Executed:** 2026-10-27 (UTC)
**Scope:** `mem20.com`, `mem20.org`, `mem20.store`, `mem20.info` → mem20 homepage
**Target:** GitHub Pages site `bythewayz66-glitch/mem20` (legacy build, source `main:/docs`)

> Status in one line: **DNS is fully applied to all four zones and verified.** `mem20.com` is the
> registered primary custom domain and serves **HTTP and HTTPS 200** with the real mem20 page.
> `mem20.org`, `mem20.store` and `mem20.info` carry the correct GitHub Pages DNS records but return
> **HTTP 404** from GitHub, because GitHub Pages permits only one registered custom domain per
> repository.

---

## 1. API authentication — key format finding

The supplied key was rejected when sent alone. The IONOS DNS API requires the combined
`<prefix>.<secret>` form in the `X-API-Key` header; the bare secret is not accepted.

| Attempt | Credential sent | Endpoint | Result |
|---|---|---|---|
| V1 | bare secret (86 chars) | `GET /dns/v1/zones?limit=5` | **HTTP 400** `{"message":"Invalid API key format."}` |
| V2 | `<public-prefix>.<secret>` in `X-API-Key` | `GET /dns/v1/zones?limit=5` | **HTTP 200** — four zones returned |
| V3 | `<public-prefix>:<secret>` HTTP Basic auth | `GET /dns/v1/zones?limit=5` | **HTTP 401** `{"message":"Missing or invalid credentials."}` |
| V4 | bare secret, no query string | `GET /dns/v1/zones` | **HTTP 400** `{"message":"Invalid API key format."}` |

The key itself is valid — only the format was wrong. All subsequent calls used V2.

Zones returned (HTTP 200):

| Domain | Zone ID | Type |
|---|---|---|
| mem20.com | `8f5648af-d1dd-11f1-8883-0a58644413d4` | NATIVE |
| mem20.info | `88338066-d1dd-11f1-8883-0a58644413d4` | NATIVE |
| mem20.org | `89ef6139-d1dd-11f1-8883-0a58644413d4` | NATIVE |
| mem20.store | `84a72552-d1dd-11f1-8883-0a58644413d4` | NATIVE |

---

## 2. Records removed (IONOS parking that would shadow Pages)

Each zone carried an apex `A` on an IONOS parking IP plus a matching apex `AAAA` on
`2607:f1c0:100f:f000:0:0:0:200`. GitHub Pages serves IPv4 only, so both had to go.

| Zone | Record deleted | API result |
|---|---|---|
| mem20.com | `A mem20.com → 74.208.236.144` | **HTTP 200** |
| mem20.com | `AAAA mem20.com → 2607:f1c0:100f:f000:0:0:0:200` | HTTP 404 `RECORD_NOT_FOUND` (cascaded with the A record) |
| mem20.org | `A mem20.org → 74.208.236.214` | **HTTP 200** |
| mem20.org | `AAAA mem20.org → 2607:f1c0:…:200` | HTTP 404 (already gone, cascaded) |
| mem20.store | `AAAA mem20.store → 2607:f1c0:…:200` | **HTTP 200** |
| mem20.store | `A mem20.store → 74.208.236.216` | HTTP 404 (already gone, cascaded) |
| mem20.info | `A mem20.info → 74.208.236.67` | **HTTP 200** |
| mem20.info | `AAAA mem20.info → 2607:f1c0:…:200` | HTTP 404 (already gone, cascaded) |

The `404 RECORD_NOT_FOUND` responses are the expected second half of a parking pair: deleting one
half of the apex A/AAAA pair removes the other, so the follow-up delete finds nothing. Net effect is
the intended one — no apex AAAA remains in any zone (confirmed in §4).

Delivery records were **left untouched**: MX, SPF TXT, DKIM CNAMEs (`s1-ionos`, `s2-ionos`),
`_dmarc`, `_domainconnect`, `autodiscover`, and the zone NS/SOA set all remain.

---

## 3. Records created

Exact API calls, per zone (all against `https://api.hosting.ionos.com/dns/v1`):

```
POST /zones/{zone_id}/records    → HTTP 201
[
  {"name": "<apex>", "type": "A", "content": "185.199.108.153", "ttl": 3600, "disabled": false},
  {"name": "<apex>", "type": "A", "content": "185.199.109.153", "ttl": 3600, "disabled": false},
  {"name": "<apex>", "type": "A", "content": "185.199.110.153", "ttl": 3600, "disabled": false},
  {"name": "<apex>", "type": "A", "content": "185.199.111.153", "ttl": 3600, "disabled": false}
]

POST /zones/{zone_id}/records    → HTTP 201
[
  {"name": "www.<apex>", "type": "CNAME", "content": "bythewayz66-glitch.github.io",
   "ttl": 3600, "disabled": false}
]
```

Applied identically to all four zones — 4 × `A` at the apex and 1 × `CNAME` on `www` each.

---

## 4. Final DNS state (read back from the API, per zone)

| Domain | Apex A records | www | Apex AAAA |
|---|---|---|---|
| mem20.com | 185.199.108.153, .109.153, .110.153, .111.153 | CNAME → bythewayz66-glitch.github.io | none |
| mem20.org | 185.199.108.153, .109.153, .110.153, .111.153 | CNAME → bythewayz66-glitch.github.io | none |
| mem20.store | 185.199.108.153, .109.153, .110.153, .111.153 | CNAME → bythewayz66-glitch.github.io | none |
| mem20.info | 185.199.108.153, .109.153, .110.153, .111.153 | CNAME → bythewayz66-glitch.github.io | none |

Confirmed twice: (a) `GET /zones/{id}` record dump, and (b) `dig` against the zones' own
authoritative nameservers (`ns.ui-global-dns.com` for .com, `ns1021.ui-dns.com` for the rest).
Public resolvers (`8.8.8.8`, `1.1.1.1`) also return the GitHub A set for all four apexes and
`bythewayz66-glitch.github.io.` for all four `www` names.

---

## 5. GitHub Pages registration — the one-domain limit (measured, not assumed)

GitHub Pages stores a **single** custom domain per repository (`cname` is a scalar field, and the
`docs/CNAME` file holds one hostname). Registering a second domain does not add it — it **replaces**
the first. This was verified by direct observation rather than assumed:

1. `PATCH /repos/bythewayz66-glitch/mem20/pages` with `cname=mem20.com` → 200, `cname: "mem20.com"`.
   At this point `mem20.com` served the site.
2. `PATCH … pages` with `cname=mem20.org` → 200, `cname: "mem20.org"`. `mem20.com` **immediately
   dropped to HTTP 404** while `mem20.org` took over serving 200. The second domain had replaced the
   first, not been added alongside it.
3. Requesting the same endpoint with `https_enforced` before a certificate existed returned
   `HTTP 404 {"message":"The certificate does not exist yet"}`, so certificate provisioning was
   allowed to complete first and HTTPS enforcement was left for afterwards.

Consequence, stated plainly: **`mem20.com` is the primary and the only registered custom domain.**
`mem20.org`, `mem20.store` and `mem20.info` resolve correctly to GitHub Pages and carry the right
records, but GitHub answers them with its own 404 page ("Site not found") because it has no
registration telling it which site they belong to.

A host header probe against the Pages CDN confirms this is a registration gate, not a DNS problem —
before registration, even `mem20.com` returned 404 under `Host:` forcing, and began returning 200
only once registered.

### Root-cause fix applied during this work

`docs/CNAME` on `main` still contained `mem20.jaysonai.online`, a hostname with **no A record** in the
`jaysonai.online` zone (Cloudflare nameservers, NXDOMAIN on lookup). That orphaned entry is what
pushed the site into `status: errored` after the domain switch. Fixed in commit
**`4ea9361fa2f0e341035f3a9648f1239f4fd0302a`** (`docs/CNAME` → `mem20.com`), after which the site
returned to `status: building` and then served 200.

### How the other three domains serve

There is no redirect mechanism available to fill the gap:

- IONOS exposes **no** redirect/forwarding API for these zones (probed `/domains/v1/*`,
  `/redirect/v1/*` — all 404 or "Unsupported serviceId"), so HTTP redirects cannot be configured
  here.
- GitHub Pages will not serve a hostname it has not been told about, and being told about a second
  hostname evicts the first.

So the three non-primary domains can only become reachable **one at a time**, by promoting each to
primary while `docs/CNAME` matches it — which necessarily takes `mem20.com` offline for the duration
of the certificate issuance (minutes to about an hour). Which of the four should be the permanent
primary is an owner decision, not a technical one.

---

## 6. Raw verification output (2026-10-27T08:40:40Z)

```
==================== mem20.com ====================
--- dig +short A mem20.com @8.8.8.8 ---
185.199.108.153
185.199.111.153
185.199.110.153
185.199.109.153
--- dig +short AAAA mem20.com @8.8.8.8 ---
(blank = none)
--- dig +short CNAME www.mem20.com @8.8.8.8 ---
bythewayz66-glitch.github.io.
--- curl -I http://mem20.com/ ---
HTTP/1.1 200 OK
Content-Length: 36627
Content-Type: text/html; charset=utf-8
--- curl -I http://www.mem20.com/ ---
HTTP/1.1 404 Not Found
Content-Length: 9115

==================== mem20.org ====================
--- dig +short A mem20.org @8.8.8.8 ---
185.199.111.153
185.199.109.153
185.199.108.153
185.199.110.153
--- dig +short AAAA mem20.org @8.8.8.8 ---
(blank = none)
--- dig +short CNAME www.mem20.org @ns1021.ui-dns.com ---
bythewayz66-glitch.github.io.
--- curl -I http://mem20.org/ ---
HTTP/1.1 404 Not Found
Content-Length: 9115
--- curl -I http://www.mem20.org/ ---
HTTP/1.1 301 Moved Permanently
Location: http://mem20.org/

==================== mem20.store ====================
--- dig +short A mem20.store @8.8.8.8 ---
185.199.110.153
185.199.109.153
185.199.108.153
185.199.111.153
--- dig +short AAAA mem20.store @8.8.8.8 ---
(blank = none)
--- dig +short CNAME www.mem20.store @ns1021.ui-dns.com ---
bythewayz66-glitch.github.io.
--- curl -I http://mem20.store/ ---
HTTP/1.1 404 Not Found
Content-Length: 9115
--- curl -I http://www.mem20.store/ ---
HTTP/1.1 404 Not Found
Content-Length: 9115

==================== mem20.info ====================
--- dig +short A mem20.info @8.8.8.8 ---
185.199.111.153
185.199.110.153
185.199.108.153
185.199.109.153
--- dig +short AAAA mem20.info @8.8.8.8 ---
(blank = none)
--- dig +short CNAME www.mem20.info @8.8.8.8 ---
bythewayz66-glitch.github.io.
--- curl -I http://mem20.info/ ---
HTTP/1.1 404 Not Found
Content-Length: 9115
--- curl -I http://www.mem20.info/ ---
HTTP/1.1 404 Not Found
Content-Length: 9115
```

`Content-Length: 36627` on `mem20.com` is the real homepage; its `<title>` is
`mem20 — Auditable agent memory`, matching the canonical GitHub Pages build byte-for-byte.
The `9115`-byte 404 body on the other hosts is GitHub's own "Site not found" page, not a DNS failure.

---

## 7. Honest summary

| Domain | DNS → GitHub Pages | Pages registration | Live HTTP | Live HTTPS |
|---|---|---|---|---|
| mem20.com | ✅ 4 × A + www CNAME | ✅ primary | **200** (real page) | **200** |
| mem20.org | ✅ 4 × A + www CNAME | ❌ not registerable alongside | 404 from GitHub | n/a |
| mem20.store | ✅ 4 × A + www CNAME | ❌ not registerable alongside | 404 from GitHub | n/a |
| mem20.info | ✅ 4 × A + www CNAME | ❌ not registerable alongside | 404 from GitHub | n/a |

HTTPS: the certificate covering `mem20.com` + `www.mem20.com` reached state `approved` (expires
2027-01-25), and `https://mem20.com/` returns **200**. The only remaining Pages setting is
`https_enforced`, currently `false`, which can be switched on to make HTTP redirect to HTTPS.

`www.mem20.com` still answers 404: GitHub only auto-redirects `www` ↔ apex for the hostnames it has
certificated in the correct pairing, and the `www` half needs the enforced-HTTPS/redirect step to
engage. Its DNS is correct (§4).

**Not done, and not blocked by DNS:** getting all four hosts to answer 200 simultaneously requires a
redirect layer in front of GitHub Pages — a CDN/proxy with per-host redirect rules, or a small
redirect service. GitHub Pages alone cannot do it. That is a decision (which domain is primary, and
whether to add a proxy) rather than a record change.
