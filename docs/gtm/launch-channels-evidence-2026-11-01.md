# Launch-channel evidence — probe transcripts, 2026-11-01

Raw output behind [`launch-channels-2026-11-01.md`](./launch-channels-2026-11-01.md). Every status
code, byte count and grep result quoted in the plan is reproduced here unedited, so each blocker can be
re-checked without trusting the summary.

**Baseline:** `main` = `2ea4492209dfaae6afb22ca884132a0d1849bfcf` · **Run:** 2026-11-01

---

## 1. Host reachability

```
$ for u in ...; do curl -sS -o /dev/null -w "%{http_code} %{size_download} %{url_effective}" -L "$u"; done

https://mem20.com/                          | 200 33429 https://mem20.com/
https://www.mem20.com/                      | 200 33429 https://mem20.com/
https://mem20.org/                          | 404  9115 https://mem20.org/
https://mem20.store/                        | CURL_EXIT=60  SSL: no alternative certificate subject name matches 'mem20.store'
https://mem20.info/                         | CURL_EXIT=60  SSL: no alternative certificate subject name matches 'mem20.info'
https://www.mem20.org/                      | 404  9115 https://www.mem20.org/
https://www.mem20.store/                    | CURL_EXIT=60  SSL: no alternative certificate subject name matches 'www.mem20.store'
https://www.mem20.info/                     | CURL_EXIT=60  SSL: no alternative certificate subject name matches 'www.mem20.info'
https://bythewayz66-glitch.github.io/mem20/ | 200 33429 http://mem20.com/     <-- note the scheme
https://github.com/bythewayz66-glitch/mem20 | 200 756554 https://github.com/bythewayz66-glitch/mem20
```

### 1a. Why `.store` / `.info` fail at TLS, not at HTTP

```
$ echo | openssl s_client -connect mem20.store:443 -servername mem20.store | openssl x509 -noout -subject -ext subjectAltName
subject=CN = *.github.io
X509v3 Subject Alternative Name:
    DNS:*.github.com, DNS:*.github.io, DNS:*.githubusercontent.com, DNS:github.com, DNS:github.io, DNS:githubusercontent.com
```

GitHub serves its wildcard `*.github.io` certificate for a hostname it has no certificate for. With
`-k` the body is the same 9,115-byte "Site not found":

```
$ curl -ksS -o /dev/null -w "%{http_code} %{size_download}\n" https://mem20.store/
404 9115
$ curl -ksS -o /dev/null -w "%{http_code} %{size_download}\n" https://mem20.info/
404 9115
$ curl -ksS -o /dev/null -w "%{http_code} %{size_download}\n" https://www.mem20.store/
404 9115
$ curl -ksS -o /dev/null -w "%{http_code} %{size_download}\n" https://www.mem20.info/
404 9115
```

**This corrects the directive's §1a**, which records `.store` / `.info` as `404 / 9,115` without noting
the TLS failure that precedes it. The end state is the same; the user-visible failure is worse.

---

## 2. `/sites/` artifacts — 403 with token injection defeated

`/sites/` and `/files/` URLs are access-controlled, and the sandbox shell silently appends `?tk=<token>`
to any complete such URL it sees — including inside heredocs and Python string literals. A naive probe
therefore returns 200 and you wrongly conclude the page is public.

The probe below was written to a file first, with the host and the path split into separate string
literals, so the shell never sees one complete URL:

```python
import urllib.request, urllib.error
host = "https://static." + "teamily" + "." + "ai"
paths = [
  "/" + "sites" + "/ok_0i4LDXJQ25MK/webpages/index.html",
  "/" + "sites" + "/ok_0i4LDXJQ25MK/index.html",
]
for p in paths:
    u = host + p
    print("URL:", u)
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    try:
        r = urllib.request.urlopen(req, timeout=25)
        print("  status", r.status, "final-url-has-tk:", "tk=" in r.geturl(), "bytes", len(r.read()))
    except urllib.error.HTTPError as e:
        print("  HTTPError", e.code, e.read(160))
```

```
$ python3 probe/sites_probe.py
URL: https://static.teamily.ai/sites/ok_0i4LDXJQ25MK/webpages/index.html
  HTTPError 403 b'{"detail":"Forbidden"}'
URL: https://static.teamily.ai/sites/ok_0i4LDXJQ25MK/index.html
  HTTPError 403 b'{"detail":"Forbidden"}'
```

### 2a. The repo's own `homepage` field, same method

```
$ python3 probe/homepage_probe.py
URL: https://static.teamily.ai/sites/ca954f26-cfef-49bf-92b4-55c652e71f8f/webpages/mem20-site/index.html
  HTTPError 403 b'{"detail":"Forbidden"}'
```

That URL is what `https://api.github.com/repos/bythewayz66-glitch/mem20` returns for `homepage` — the
most-clicked link on the repo, and it is a 403.

### 2b. Control

The control is `https://mem20.com/`, which the identical token-free probe returns `200 / 33,429 bytes`
for (§3). Same probe, same method, one 403 and one 200 — so the 403 is real and the probe is not broken.

---

## 3. What `mem20.com` actually serves

```
$ curl -sS -L https://mem20.com/ -o probe/mem20com.html && wc -c probe/mem20com.html
33429 probe/mem20com.html
```

### 3a. Title and meta

```
$ grep -oiE '<title>[^<]*</title>|<meta[^>]*(description|og:)[^>]*>' probe/mem20com.html

<title>mem20 — Auditable agent memory · 270 tools across 27 domains</title>
<meta name="description" content="Auditable agent memory. 270 tools across 27 domains. Grounded vs simulated, enforced — not hoped for. MIT-licensed MCP server with contamination auditing, an append-only origin-tagged ledger, and published benchmarks that include the row we lose.">
<meta property="og:title" content="mem20 — Auditable agent memory">
<meta property="og:description" content="270 tools across 27 domains. Persistent memory for AI agents — with the audit trail that regulated teams need.">
<meta property="og:type" content="website">
```

### 3b. Version strings — B2

```
$ grep -oE 'v?3\.[0-9]+\.[0-9]+' probe/mem20com.html | sort | uniq -c
      4 v3.0.0
```

```
$ curl -sS https://raw.githubusercontent.com/bythewayz66-glitch/mem20/main/VERSION
3.1.0
```

**The live page is one minor version behind, four times.**

### 3c. Counts are correct

```
$ grep -oE '[0-9]+ (tools|domains|organs|services)' probe/mem20com.html | sort | uniq -c
      8 27 domains
      8 270 tools
```

The surface claim is fine. The version is not.

### 3d. Preview assets — B4

```
$ grep -oiE '<meta[^>]*(og:image|twitter:)[^>]*>|<link[^>]*rel="[^"]*icon[^"]*"[^>]*>' probe/mem20com.html
(no output)
```

**Zero.** No `og:image`, no `twitter:card`, no favicon link. HN, Product Hunt, Reddit, X and Slack all
render a bare grey box, and Product Hunt cannot accept a submission without gallery assets.

### 3e. Analytics — B5

```
$ grep -oiE 'gtag|googletagmanager|plausible|umami|posthog|analytics|segment|matomo|fathom' probe/mem20com.html
(no output)
```

**Zero.** Nothing is measured, so every `utm_*` link in the campaign plan is decorative.

### 3f. Supporting files — B7

```
https://mem20.com/robots.txt   -> 404
https://mem20.com/sitemap.xml  -> 404
https://mem20.com/this-does-not-exist-xyz -> 404 9379
```

---

## 4. The redirect chain — B3

```
$ curl -sS -o /dev/null -D - "https://bythewayz66-glitch.github.io/mem20/?utm_source=hn&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=show_hn"
HTTP/1.1 200 Connection Established
HTTP/2 301
location: http://mem20.com/?utm_source=hn&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=show_hn
```

The query string **is** preserved — UTM survives the hop. The scheme is downgraded to `http://`.

```
$ curl -sS -o /dev/null -D - "https://mem20.com/?utm_source=hn&utm_medium=community&utm_campaign=mem20_launch_2026q4&utm_content=show_hn"
HTTP/2 200
```

### 4a. No HSTS to force the upgrade

```
$ curl -sSI https://mem20.com/ | grep -iE 'strict-transport|server:|content-type:'
server: GitHub.com
content-type: text/html; charset=utf-8
```

No `strict-transport-security` header. Both schemes serve 200:

```
http://mem20.com/  -> 200 final=http://mem20.com/
https://mem20.com/ -> 200 final=https://mem20.com/
```

So all 12 tracked links in `docs/gtm/mem20-campaign-plan.md` begin with a plaintext hop, with nothing to
force an upgrade.

---

## 5. Install path — verified, and it is honest

```
$ for p in mem20 mem20-ai mem20-mcp mem20-sdk mem20api; do curl -sS -o /dev/null -w "%{http_code}" https://pypi.org/pypi/$p/json; done
mem20 -> 404
mem20-ai -> 404
mem20-mcp -> 404
mem20-sdk -> 404
mem20api -> 404

$ for p in mem20 mem20-sdk; do curl -sS -o /dev/null -w "%{http_code}" https://registry.npmjs.org/$p; done
mem20 -> 404
mem20-sdk -> 404
```

The live page already says this correctly — *"not yet on PyPI, so install is from source"* — and gives a
`git clone` → `venv` → `pip install -r requirements.txt` → `mcp/mcp_server.py` sequence. This is a
strength, not a gap.

---

## 6. Repo state

```
$ curl -sS https://api.github.com/repos/bythewayz66-glitch/mem20 | python3 -c "..."
homepage: 'https://static.teamily.ai/sites/ca954f26-cfef-49bf-92b4-55c652e71f8f/webpages/mem20-site/index.html'
has_issues: True has_discussions: False
stars: 1 forks: 0 watchers: 0 open_issues: 0
license: MIT
pushed_at: 2026-11-01T17:22:57Z
```

`has_discussions: false` — "open an issue" is a valid CTA, "join the discussion" is not.

---

## 7. Gate output

```
$ python3 scripts/check_launch_gate.py

mem20 launch gate
  site   : https://mem20.com/
  pages  : https://bythewayz66-glitch.github.io/mem20/

  [PASS] anonymous       https://mem20.com/ returned 200, 33429 bytes, no access token
  [FAIL] version         served page never mentions current version 3.1.0; served page still carries retired version(s): 'v3.0.0' x4, '3.0.0' x4 (repo VERSION = 3.1.0)
  [FAIL] social_preview  no og:image on the served page -> HN/PH/Reddit/X render a bare grey box (twitter:card=absent, favicon=absent)
  [FAIL] https_hop       canonical link hops through plaintext: 301 -> http://mem20.com/
  [FAIL] crawlable       robots.txt returned 404 (want 200)
  [FAIL] analytics       no analytics snippet on the served page -> every utm_* link is decorative and the Day-7 channel readout is a guess (pass --waive-analytics to accept this in writing)
  [FAIL] repo_homepage   repo homepage https://static.teamily.ai/sites/ca954f26-cfef-49bf-92b4-55c652e71f8f/webpages/mem20-site/index.html returned 403 - this is a /sites/ artifact, which is project-member-only and always 403s

LAUNCH GATE: BLOCKED - 6 of 7 gates failed, 1 passed.
Do not post to Show HN, Product Hunt or Reddit until every gate passes.
See docs/gtm/launch-channels-2026-11-01.md section 3.1 for the minimum unblock.
```

Exit code `1`.

```
$ python3 scripts/check_launch_gate.py --waive-analytics

  [PASS] analytics       owner waiver recorded (--waive-analytics): launch runs without on-page attribution
LAUNCH GATE: BLOCKED - 5 of 7 gates failed, 2 passed.
```

### 7a. A bug the gate found in itself

The first version of the checker reported `https_hop` as **PASS**. Cause: `urllib.request.urlopen`
follows redirects by default, so the 301 to `http://` was silently chased to a 200 and the plaintext hop
was invisible. Fixed with a `HTTPRedirectHandler` subclass whose `redirect_request` returns `None`, which
makes urllib raise `HTTPError` for the 3xx so the status and `Location` are observable. The gate now
reports `301 -> http://mem20.com/` and fails, as it should.

This is why the gate is run against the live site rather than reasoned about: the first version would
have passed a launch onto a plaintext link.

---

*All output above was produced in this run against `main` = `2ea4492209dfaae6afb22ca884132a0d1849bfcf`.
This is a go-to-market plan, not investment advice.*
