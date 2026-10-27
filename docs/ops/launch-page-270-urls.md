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

## 2. What changed

- **Surface band** added to the hero: 270 tools / 27 domains, with the provenance list (registry 889,
  MCP tools 270, CLI surfaces 318, subsystems 303, retired surface 257 / 26) and the source of truth
  for each figure.
- **Version badge** corrected `v2.1.0rc2` → `v3.0.0` in all four places it appeared (hero badge,
  comparison table, install meta row, footer).
- **Benchmark table** broken out per retrieval mode — `graph`, `hybrid`, `keyword`, `semantic` — so the
  adversarial column is visible per mode instead of aggregated away. `graph` is marked *not scored*
  for direct and adversarial (it ran the multi-hop class only, n=2), not shown as passing.
- **Caveat block** states the adversarial 0.000 limitation across all three scored modes and repeats
  that there is no LoCoMo / LongMemEval parity claim.
- **Dashboard** gained section 07 (tool surface with sources of truth) and section 08.

## 3. Reachability — the `/sites/` finding

Every `/sites/` artifact URL returns **403 Forbidden** to an anonymous visitor. Verified with
`python-urllib` and a Chrome UA, both token-free. A plain `curl` returns 200 only because the sandbox
shell injects an access token into the request — that 200 is not evidence of public reachability.

**Canonical public host: `https://mem20.com/`** (GitHub Pages, `docs/` on `main`).
`https://bythewayz66-glitch.github.io/mem20/` 301-redirects to it.

No `/sites/` URL is presented as a public link anywhere in the rebuilt pages.

## 4. Quality gate

| Check | Result |
|---|---|
| CSS brace balance | 133/133 launch · 116/116 dashboard |
| Unclosed tags | none |
| Inline JS syntax (`node --check`) | pass (1 block launch, 2 dashboard) |
| Stale strings (`v2.1.0rc2`, `257 tools`, `26 domains`) | 0 |
| `270` occurrences | 10 launch · 10 dashboard |
| `/sites/` links presented as public | 0 |
| Headless Chromium render | clean, no JS errors |
| Horizontal overflow @ 390×844 and 1280×900 | none |

## 5. Outstanding

The public site picks up the v3.0.0 badge only when this branch merges to `main`. No public post
should go out before that merge.
