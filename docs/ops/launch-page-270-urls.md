# Launch page + dashboard — 270 tools / 27 domains rebuild (2026-10-27)

**Owner:** Webpage Developer · **Branch:** `feat/ws2-launch-page-270`
**Baseline:** `main` = `1264076698a00878acc3adacf7bf1d51eea315cc` (verified at 08:44 UTC, matches the roster)
**Branch head:** rebased onto `main` `b44eff6f12d4b6869f6c66f71cf1a1d1ef485a11` (2026-10-27, `docs(ops): verify the 21 roster branches`).
The branch was originally cut from `b9de9aa84b04341ac873689875a9bf8dd1cc3b7c`; `main` advanced 7 commits during the run
(`fix(ci): restore the full 308-line ci.yml` #117, `fix(copy): docs/index.html 268/26 -> 270/27 and source-only install block` a6a0734,
and the convergence merges). The rebase was clean — no conflict markers. The page's `verified on main @` stamp reads
`45445f4` (the roster-dispatch commit the tool surface was counted against); `main` has since advanced to `b44eff6`
with ops-only commits that do not touch the tool surface, so the count still holds.
**Roster row:** #3 in `docs/ops/workload-roster-2026-10-27.md` @ `05da8465c607ee0fa12982d50268bdbf35f88067`

This file is the permanent-URL record for the rebuilt launch page and dashboard. The branch SHA is
recorded here by commit; the live URLs and the reachability verdict below were each fetched, not assumed.

---

## 1. What was stale

| Artifact | Before | Problem |
|---|---|---|
| `docs/index.html` (public site) | `main` carries 270/27; live host was serving a pre-270 build (sha `9bce8f7a…`) | The live `mem20.com` build lagged the repo — GitHub Pages had not rebuilt from `main` at audit time |
| `docs/index.html` version badge | `v2.1.0rc2` ×6 | `VERSION` on `main` is **3.0.0**; the badge understated the release |
| `docs/index.html` benchmark table | 4 aggregate rows | aggregated the adversarial class, hiding that it is 0.000 in **every** scored mode |
| `docs/dashboard.html` | no tool surface anywhere | a launch dashboard that could not state the surface it was launching |
| `/sites/` launch copies | several at 257/26, one 270/27 at `0325f63d…` → **404** | the only correct copy was unreachable |

## 2. What was rebuilt

Both files were rebuilt against the surface `main` actually serves. Every number below is copied
from a file on `main`, not re-derived:

| Figure | Value | Source on `main` |
|---|---|---|
| Tools | **270** | `README.md` L161/L184/L242, `docs/index.html`, `docs/finance/inputs.json` `tool_surface.tools`, `CHANGELOG.md` L16 |
| Domains | **27** | same set; `docs/finance/inputs.json` `tool_surface.domains` |
| Capability registry | 889 (270 MCP tools + 318 CLIs + 303 subsystems) | `README.md` L171 |
| Retired surface | 257 / 26 | `docs/finance/inputs.json` `tool_surface.previous_tools` / `previous_domains` |
| Version | 3.0.0 | `VERSION` |
| Benchmark corpus | `mem20-agent-kb-v1`, 14 facts / 3 simulated / 13 queries | `benchmarks/results/latest.json` |

`docs/dashboard.html` gains a section `07 — Tool surface`, naming each source of truth and stating
that **27 is a grouping of 37 raw tool prefixes**, not a contraction of the surface (several prefixes
share a domain, e.g. `cog_*` / `tot_*`, `cloud_*` / `cloudstorage_*`, `self_model_*`). That grouping
choice was previously undocumented next to the number.

## 3. Adversarial row — kept honest, and made more specific

The task required the adversarial result stay visible. It is now **harder to misread**, because the
page breaks the benchmark out by retrieval mode instead of aggregating it:

| Retrieval mode | Direct | Multi-hop | Adversarial | p50 |
|---|---|---|---|---|
| `graph` | not scored | 1.000 | not scored | 0.6 ms |
| `hybrid` | 1.000 | 0.800 | **0.000** | 103.5 ms |
| `keyword` | 1.000 | 0.800 | **0.000** | 105.0 ms |
| `semantic` | 1.000 | 0.800 | **0.000** | 12.2 ms |
| Leak rate (clean stores) | 0.000 | 0.000 | 0.000 | — |

- The page states **hybrid 0.000 · keyword 0.000 · semantic 0.000** in a sentence directly under the table.
- `graph` is marked *not scored* for the direct and adversarial classes rather than being left blank or
  allowed to read as a pass — it ran the multi-hop class only (n=2).
- The caveat says the weakness is **not confined to one mode**, and that three latency profiles
  (0.6 / 12.2 / ~104 ms) do not buy adversarial robustness.
- The adversarial figure also stays in the hero number strip, the comparison table, and
  `What we don't claim`, plus the dashboard's hero chip and benchmark block.

## 4. URLs

| Surface | URL | Status |
|---|---|---|
| **Public launch page (canonical)** | https://mem20.com/ | **200**, 36,627 bytes — this is the shippable link |
| Public launch page (GitHub alias) | https://bythewayz66-glitch.github.io/mem20/ | 301 → `http://mem20.com/` (`docs/CNAME` pins the custom domain), then **200** |
| Launch page mirror (this rebuild) | https://static.teamily.ai/sites/6aacb84a-cf8f-448f-bcd1-8bac8c850dc6/webpages/mem20-launch-v5/index.html | 200 with token, **403 to anonymous** — not public |
| Dashboard (this rebuild) | https://static.teamily.ai/sites/6aacb84a-cf8f-448f-bcd1-8bac8c850dc6/webpages/mem20-launch-dashboard-v4/index.html | 200 with token, **403 to anonymous** |

`docs/CNAME` pins the Pages host to **mem20.com**, so the GitHub Pages hostname is an alias, not the
canonical link. Every campaign URL should use `https://mem20.com/`.

### What the live site serves today vs what this branch contains

Measured by `curl` on `https://mem20.com/` at 09:12 UTC, **before** this branch merges:

| Claim | Live `mem20.com` (main) | This branch |
|---|---|---|
| Tool count | 270 tools / 27 domains — already correct | 270 tools / 27 domains |
| Version badge | `2.1.0rc2` ×6 — stale | `v3.0.0` (`VERSION` on main is 3.0.0) |
| Benchmark table | 4 aggregate rows — the adversarial class is aggregated | 5 rows, per retrieval mode, adversarial 0.000 named in three modes |
| Tool-surface band | absent | present (270 / 27, registry 889, retired 257/26) |

So the surface claim on the live site is **already correct**; what this branch actually fixes is the
**version badge** and the **benchmark table shape**. The premise that the published page was stale
"against the 270/27 surface" is not what the measurement shows — `main`'s `docs/index.html` carries 270/27.
Recorded here rather than reported as a fix that was not needed.

### Reachability caveat (measured, not assumed)

Every `/sites/` artifact returns **403 Forbidden** to a token-free request, under both a bare
`python-urllib` client and a Chrome UA string. A plain `curl` of a `/sites/` URL returns **200** only
because the sandbox shell appends an access token — that is a content fetch, not proof of a public
page. So:

- campaign / HN / Product Hunt / Reddit links **must** point at `https://mem20.com/`, never `/sites/`;
- the dashboard's blocker card B2 now states exactly this, replacing the old card whose `src` line
  cited a launch path that no longer exists.

## 5. Quality gate

Run against the committed bytes:

| Check | Launch page | Dashboard |
|---|---|---|
| CSS `{` = `}` | 133 / 133 | 116 / 116 |
| Unclosed HTML tags (script/style/comments stripped) | 0 | 0 |
| Tag mismatches | 0 | 0 |
| Inline JS `node --check` | PASS | PASS |
| Stale strings (`257 tools`, `268 tools`, `111 tools`, `15 domains`, `26 domains`, `2.1.0rc2`) | 0 | 0 (257/26 retained once, as an explicitly labelled retired prior) |
| `270` occurrences | 10 | 10 |
| Horizontal-overflow guards | `body{overflow-x:hidden}`, `pre{overflow-x:auto}`, `.table-scroll` | `.tablewrap{overflow-x:auto}`, `.bcell{flex:1 1 150px}`, `.notes{auto-fit minmax(280px,1fr)}` |
| Section numbering | nav anchors resolve | `00`–`09`, unique |
| Mobile | `@media(max-width:900px)` + `(max-width:640px)`; surface band 3→2→1 col; strip 4→2 col; table min-width 560px inside a scroll container | `@media(max-width:640px)`; new panel is 4 flex cells that wrap, table inside `.tablewrap` |

Rendered/mobile measurement (headless Chromium, viewport 390×844 and 1280×900):

| Page | 390px | 1280px |
|---|---|---|
| launch | `scrollWidth` 390 = `clientWidth` 390 → **no overflow** | 1280 = 1280 → no overflow |
| dashboard | 390 = 390 → **no overflow** | 1280 = 1280 → no overflow |

Wide `<table>` elements do exceed the viewport, but each sits inside its own scroll container
(`.table-scroll` / `.tablewrap`), which is the intended behaviour and does not scroll the document.

## 6. Non-claims held intact

No LoCoMo or LongMemEval parity claim; vendor figures presented as claimed, not confirmed; no
superlatives; promotion described as auditable and explicitly **not** unfakeable or cryptographic.
