# Corrections register — 2026-10-26

Three claims circulating in the team were wrong. Each was re-tested from this
sandbox; the commands and raw results are below so anyone can repeat them.

## 1. The launch pages do not exist — this is a rebuild, not a republish

`mem20-launch_v2` and `mem20-launch-dashboard_v3` both return **404** under the
project id, with and without an access token. They are not stale, unpublishable
or awaiting a re-deploy; there is nothing there to republish.

```bash
curl -s -o /dev/null -w '%{http_code}\n' \
  https://static.teamily.ai/sites/6f82e258-87dc-4f42-b201-f6e344b6184b/webpages/mem20-launch_v2/index.html
# 404
curl -s -o /dev/null -w '%{http_code}\n' \
  https://static.teamily.ai/sites/6f82e258-87dc-4f42-b201-f6e344b6184b/webpages/mem20-launch-dashboard_v3/index.html
# 404
```

**Consequence:** the launch page job is scoped as a **rebuild from current
`docs/index.html`**, not a re-publish of an existing build. Anyone planning
around a quick republish is planning around a file that is not there.

## 2. Sidney (216.198.115.91) is dark — nobody may report the gateway as up

All four ports fail, from this sandbox, on 2026-10-26:

| Port | Result |
|---:|---|
| 2222 | `connect: No route to host` |
| 9900 | `connect: No route to host` |
| 22 | timeout |
| 80 | timeout |

Two distinct failure modes — `EHOSTUNREACH` on the app ports, timeout on the
standard ports — which is what a host that is off the network looks like, not
what a firewall drop on a live host looks like.

```bash
for p in 2222 9900 22 80; do
  timeout 6 bash -c "cat < /dev/null > /dev/tcp/216.198.115.91/$p" \
    && echo "$p OPEN" || echo "$p fail"
done
```

**Consequence:** no status report may describe the gateway as reachable today,
and no artifact may be delivered by pointing at Sidney. GitHub is the delivery
surface until Sidney is back.

## 3. mem20 is not on PyPI — no doc may claim `pip install`

| package | PyPI JSON API |
|---|---|
| `mem20` | 404 |
| `mem20-ai` | 404 |
| `mem20oreo` | 404 |

```bash
for p in mem20 mem20-ai mem20oreo; do
  printf "%-12s %s\n" "$p" \
    "$(curl -s -o /dev/null -w '%{http_code}' https://pypi.org/pypi/$p/json)"
done
```

**Consequence:** any README, launch page, deck or SDK doc that shows
`pip install mem20` is documenting a package that cannot be installed. The
install path is from source (`git clone` + `pip install -e .`) or the MCP
stdio entry point. This is a copy fix across every surface, tracked separately.

---

# DNS — the answer for the owner

> **RETIRED 2026-10-31.** The mem20 hostname in the `<retired-zone>` zone is
> retired. `docs/CNAME` names **`mem20.com`**, which resolves and returns 200,
> and that is the canonical public host. The CNAME branch below is obsolete —
> no DNS record is to be created. This section is kept only as the record of
> what was measured on 2026-10-26.

The mem20 hostname in the `<retired-zone>` zone had **no record**. This was not
propagation lag.

Evidence: both Cloudflare and Google DoH return **NXDOMAIN (Status 3)** for the
name, and the authority section in that answer is the zone's *own* SOA — the
nameservers that host `<retired-zone>` are themselves saying the name does not
exist. An apex query on the same zone returns **NOERROR (Status 0)**, so the
zone is live and answering; only this one name is missing.

```bash
curl -s "https://dns.google/resolve?name=mem20.com&type=A" | head -c 200
# {"Status":0,...}   <- resolves (the retired hostname returned Status 3)
curl -s "https://dns.google/resolve?name=<retired-zone>&type=A" | head -c 120
# {"Status":0,...}   <- apex resolves
curl -s "https://dns.google/resolve?name=<retired-zone>&type=NS"
# quentin.ns.cloudflare.com, ainsley.ns.cloudflare.com
```

## The record that was proposed — and is now obsolete

A DNS-only `CNAME` from `mem20` in the `<retired-zone>` zone to
`bythewayz66-glitch.github.io` was the proposed fix on 2026-10-26. **It is not
to be created.** The owner retired the `<retired-zone>` hostname on 2026-10-31
and `mem20.com` now serves the site, so the record would point a retired name at
a site that already has a canonical host.

`docs/CNAME` in the repo names **`mem20.com`** — the repo half is done and
correct, and no DNS change is outstanding.

## What replaced it

`mem20.com` is the canonical public host: it resolves to the GitHub Pages
A-records and returns **200** with bytes identical to the committed
`docs/index.html`. Nothing needs to be pointed anywhere else.
