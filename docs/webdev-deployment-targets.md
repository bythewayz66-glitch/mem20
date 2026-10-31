# Webdev deployment targets — verified inventory

> **RETIRED 2026-10-31.** The legacy zone this inventory was measured in is
> retired. `mem20.com` is the only canonical public host (`docs/CNAME`), and no
> DNS record in the retired zone is to be created or restored. Hostnames below
> are written as `<retired-zone>` so the retired name is not cited anywhere in
> `docs/`. The measurements are kept as the record of what was probed on
> 2026-10-03, plus a 2026-10-31 re-probe of the same names.

Board card `c3b19dd2` "Configure Webdev deployment targets" (Fleet HQ).
Measured 2026-10-03. Every row below was probed, not inferred.

Reproduce any row with the command in its `verify` cell. Secrets come from
`/opt/mem20/secrets/.env` only; no value here is a secret.

## Summary

| # | Target | Mechanism | Reaches | Status 2026-10-03 | Re-probe 2026-10-31 |
|---|---|---|---|---|---|
| 1 | `control.<retired-zone>` | Cloudflare tunnel `mem20-control` | `127.0.0.1:8890` | live, HTTP 200 | **HTTP 530** (tunnel down) |
| 2 | `shop.<retired-zone>` | Cloudflare tunnel `mem20-control` | `127.0.0.1:8891` | live, HTTP 200 | **HTTP 530** (tunnel down) |
| 3 | `mem20.pages.dev` | Cloudflare Pages project `mem20` | Pages build | live, last deploy 2026-09-04 | not re-probed |
| 4 | `rewardforge.pages.dev` | Cloudflare Pages project `rewardforge` | Pages build | live, last deploy 2026-08-13 | not re-probed |
| 5 | `jnet1.<retired-zone>` | bare A record to this box's public IP | nothing | was 502 — record deleted 2026-10-03 | **502 / no listener** (record still answers) |

The 2026-10-31 re-probe is why this file is marked retired rather than merely
historical: the two tunnel hostnames no longer serve, so nothing in the retired
zone is a live deployment target. `mem20.com` is.

## 1–2. Tunnel-routed control plane and shop

Tunnel id `82f029bf-249d-4a57-92f6-027727c5c719`, name `mem20-control`,
status `healthy` as measured on 2026-10-03. Unit
`cloudflared-mem20-control.service` (active at that time).

Ingress is defined **locally** in `/etc/cloudflared/config.yml`, not in the
Cloudflare-side config — the remote config legitimately reports 0 ingress rules.
That is not a defect; do not "fix" it.

```
control.<retired-zone> -> http://127.0.0.1:8890
shop.<retired-zone>    -> http://127.0.0.1:8891
catch-all              -> http_status:404
```

The catch-all refusing unrouted hostnames is deliberate and correct.

- **verify:** `curl -s -o /dev/null -w '%{http_code}' https://control.<retired-zone>/` → `200` on 2026-10-03, **`530` on 2026-10-31**
- **verify:** `ss -ltnp | grep -E ':8890|:8891'` → both bound to `127.0.0.1` only

Both are loopback-only. Nothing but those two hostnames reaches them.

## 3–4. Cloudflare Pages

Two projects exist, both on their default `*.pages.dev` domains. Neither is
attached to a custom hostname — the zone's only CNAMEs were the two tunnel
hostnames above.

- **verify:** `python -m mem20ops pages-inspect`

| project | hostname | last deploy |
|---|---|---|
| `mem20` | `mem20.pages.dev` | 2026-09-04T18:12:20Z |
| `rewardforge` | `rewardforge.pages.dev` | 2026-08-13T05:36:39Z |

## 5. `jnet1.<retired-zone>` — RESOLVED: record deleted

```
A  jnet1.<retired-zone>  ->  74.254.4.61   proxied=false  ttl=60
```

`74.254.4.61` is this box's own public IP (confirmed against `api.ipify.org`),
so the record pointed at us. But **nothing listens on port 80 or 443 here**:

```
ss -ltnp | grep -E ':80 |:443 '     -> no matches
curl http://127.0.0.1:80/           -> HTTP 000 (no listener)
curl http://127.0.0.1:443/          -> HTTP 000 (no listener)
curl http://jnet1.<retired-zone>/   -> HTTP 502
```

So the hostname was advertised in public DNS and answered 502. It was not
proxied, so Cloudflare was not involved — this was the bare path failing. There
was no nginx or caddy on the box and no systemd unit referencing the name.

**Decision (Jayson, 2026-10-03): delete the record.** It advertised a host that
serves nothing, and nothing in the estate was waiting on it — the only code
reference was `mem20controlz/websites.py` listing it as "box origin / live",
which was never true in any serving sense.

**2026-10-31 re-probe:** the name still resolves and still fails to connect
(`CONNECT tunnel failed, response 502`). The delete recorded below did not take
effect, or the record was recreated. **Do not restore it** — the zone is
retired; this is recorded so the state is not mistaken for a regression to fix.

### Recovery

The deleted record, recorded so the delete is reversible:

| field | value |
|---|---|
| id | `914593e7e2eb7879ad1d532f5798bfcd` |
| type | `A` |
| name | `jnet1.<retired-zone>` |
| content | `74.254.4.61` |
| proxied | `false` |
| ttl | `60` |
| zone id | `2bf677eac422dabc2b7ca8a285a0975c` |

To restore it, POST the same shape back to the zone's `dns_records`. Nothing else
on the box needs changing, because nothing was serving it. **Superseded
2026-10-31: the zone is retired — do not restore.**

## Non-web DNS in the same zone

For completeness, so the 8 records are accounted for: 3 MX
(`route1/2/3.mx.cloudflare.net`, Cloudflare email routing), SPF TXT
(`v=spf1 include:_spf.mx.cloudflare.net ~all`), and a DKIM TXT
(`cf2024-1._domainkey`). None of these are deployment targets.

## Standing rule

`/opt/mem20/secrets/.env` is the only place Cloudflare credentials live. DNS
records are user-authored state: detection and audit never rewrite them.

## Canonical host

`mem20.com` — registered in `docs/CNAME`, resolves to the GitHub Pages
A-records, returns 200. Verified 2026-10-31: `sha256` of the served
`index.html` is `ae533ac5…` and of `dashboard.html` is `6a89a725…`, both
identical to the committed files on `main`.
