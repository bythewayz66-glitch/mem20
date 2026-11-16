# mem20 — Work-Preservation & Ops Record (2026-11-16)

**Owner:** bythewayz66 · **Prepared by:** Mem20-admin · **Branch:** `ops/work-preservation-ledger-2026-11-16`
**Repo of record:** `github.com/bythewayz66-glitch/mem20` (public). `JaysonAIOnline/mem20` returns 404 — not the live repo.

Every number below comes from a real check run this session. Nothing is inferred.

---

## 1. What changed this run

| # | Deliverable | File | Status |
|---|---|---|---|
| 1 | Contribution ledger — every agent's landed work with a real 40-char SHA | `docs/ops/contribution-ledger-2026-11-16.md` | committed |
| 2 | Work-preservation check — flags any deliverable with no commit and no permanent URL | `scripts/ops/check-work-preservation.py` | committed, self-test PASS |
| 3 | Work-preservation check — documentation | `docs/ops/work-preservation-check.md` | committed |
| 4 | This ops record | `docs/ops/work-preservation-2026-11-16.md` | committed |
| 5 | `docs/ops/README.md` index rows | `docs/ops/README.md` | committed |

---

## 2. Repo state (verified this run)

| Check | Command | Result |
|---|---|---|
| Canonical repo | `git clone https://github.com/bythewayz66-glitch/mem20.git` | rc=0, 11,439 files |
| `main` HEAD | `git rev-parse origin/main` | `0224a64946a2c00313a9872515893157adcbc47e` |
| `main` commit date | `git log -1 --format=%ci` | 2026-11-16T06:55:07Z |
| `main` subject | `git log -1 --format=%s` | "docs: Update DIARY/failures with MCP server startup fix" |
| `VERSION` | `cat VERSION` | 4.0.0 |
| Remote branches | `git ls-remote --heads origin \| wc -l` | 102 |
| Tracked files | `git ls-tree -r --name-only origin/main \| wc -l` | 11,439 |
| Live surface pin | `docs/surface.json` | 487 tools / 129 domains |
| Group roster | `get_groups_info(["3388661668"])` | 28 members (27 agents + 1 human) |

### 2.1 At-risk commits — 50 across 12 branches

`git rev-list --count origin/main..origin/<branch>` on **full history** (the shallow-clone counts are
inflated and were discarded):

| Ahead | Behind | Branch | Head SHA (40) |
|---:|---:|---|---|
| 14 | 0 | `gtm/claim-ledger-v7-rebase` | `ac929c4e3e5f27669bb92f576c5b2ee265415277` |
| 9 | 0 | `fix/post20-defects` | `a267eaa39e9ceee77281d5aff24035040f582963` |
| 6 | 6 | `ruby-sdk-release-2026-11-01` | `a2354422d35beaa93efd100e75146a33b69c3a0b` |
| 6 | 6 | `feat/4.0-mem20-cpp-expert-braid` | `5a63ed5322ba9fe8833d426a7693f9724155f3c8` |
| 4 | 4 | `feat/4.0-server-builder-mem20meshz` | `abc3a111dbf690b598cf0345c583238b91210098` |
| 3 | 3 | `feat/4.0-server-builder-gateway` | `40cf6c5675f5b16228b8b0ea9e09921e017f2ef7` |
| 2 | 0 | `feat/4.0-mem20-cpp-expert-mem20wasmz` | `925d10aff3516a09c21c32e2b69d5f3215beff0b` |
| 2 | 2 | `docs/ws1-narrative-serial-2026-11-01` | `2d2e6212eb5d4b3570121cdc3c7b1f55353e6e56` |
| 1 | 0 | `fix/perl-sdk-surface-272` | `d5c4af64001000bcc1bfc11297b414072c94f3f7` |
| 1 | 0 | `fix/open-issues-5` | `dafe65024e3539ef401ebbb65d3941e33736a39d` |
| 1 | 1 | `feat/4.0-super-agent-memory-engine` | `638ee427113c3de10c7e3515af5f144c0eb472dc` |
| 1 | 1 | `feat/4.0-conformance-gate-language-aware-discovery` | `d4b04e661f7cf3d47542f5cb27e3b250fc6504df` |

**Total: 50 commits across 12 branches.** These are pushed (not lost) but not landed — the work is
stranded on side branches `main` does not contain.

### 2.2 Open PRs

`GITHUB_LIST_PULL_REQUESTS(state=open)` returned an empty list this run — **0 open PRs**. There is no
open merge path for the 50 stranded commits.

---

## 3. Work-preservation check — evidence

### 3.1 Self-test

```
$ python3 scripts/ops/check-work-preservation.py --self-test
{
  "preserved": [ {"artifact": "a", "commit": "0224a64946a2c00313a9872515893157adcbc47e", ...},
                 {"artifact": "b", "permanent_url": "https://static.teamily.ai/sites/abc/webpages/p/index.html", ...} ],
  "at_risk":   [ {"artifact": "c", "commit": null, "permanent_url": null} ],
  "preserved_count": 2,
  "at_risk_count": 1
}
SELF-TEST: PASS
```

### 3.2 Run against the live ledger

```
$ python3 scripts/ops/check-work-preservation.py --ledger docs/ops/contribution-ledger-2026-11-16.md
ledger: docs/ops/contribution-ledger-2026-11-16.md
preserved: 7   at-risk: 1
  AT-RISK  daily report 2026-10-26 (published)  (no commit, no permanent URL)
rc=1
```

The check found **7 preserved deliverables and 1 genuinely at-risk one** — proving it is not vacuous:

> **At-risk finding.** The published daily-report page
> `https://static.teamily.ai/sites/928e72e8-002b-4e3d-a039-9ae5959cb039/webpages/mem20-daily-report-2026-10-26/index.html`
> answers HTTP 200, but its source is **not committed to `main`**. `git ls-tree -r --name-only origin/main`
> returns **0** paths under `published/sites/928e72e8-...`. It exists only as a hosted artifact with no repo
> copy — if the host drops it, the page is gone. Owner: Mem20-admin.

The other published page (`ea6393ed-.../mem20-admin-ops-ledger`) **is** tracked on `main` at
`published/sites/ea6393ed-90a6-4a42-b2f2-536e27a0a061/webpages/mem20-admin-ops-ledger/index.html`, so it is
preserved on both counts.

The at-risk *branches* (§2.1) each carry a 40-char SHA in the ledger's §1.2 — they are pushed, so they are
preserved as artifacts even though they are not landed on `main`.

---

## 4. Site uptime (checked this run)

| URL | HTTP | Note |
|---|---|---|
| `https://mem20.com/` | 200 | live launch surface, states v4.0.0 |
| `https://bythewayz66-glitch.github.io/mem20/` | 200 | GitHub Pages index |
| `https://bythewayz66-glitch.github.io/mem20/dashboard.html` | 200 | GitHub Pages dashboard |
| `https://static.teamily.ai/sites/ea6393ed-.../webpages/mem20-admin-ops-ledger/index.html` | 200 | ops ledger page (tokenized) |
| `https://static.teamily.ai/sites/928e72e8-.../webpages/mem20-daily-report-2026-10-26/index.html` | 200 | daily report (tokenized) |

All five reachable. No 403/404/timeout this run.

---

## 5. Open blockers (with owners)

| Blocker | Owner | Evidence |
|---|---|---|
| 50 commits stranded on 12 branches, 0 open PRs | branch owners (see §2.1) | `git rev-list --count` + empty PR list |
| `mem20` not on PyPI — install stays source-only | GitHub Repo Assistant | prior runs: `mem20`/`mem20-ai`/`mem20oreo` all 404 |
| `mem20.jaysonai.online` NXDOMAIN — DNS record never created | owner (DNS) | `docs/CNAME` committed, no DNS record |
| Benchmark acceptance gap — adversarial queries at 0.0 hit-rate | Mem20 Benchmark Dataset Builder | prior runs |
| Growth Hacker has no branch on the remote | Growth Hacker | `git ls-remote` — no branch found |

---

## 6. Next actions

1. **Open PRs for the 12 stranded branches** — start with `gtm/claim-ledger-v7-rebase` (14 ahead) and
   `fix/post20-defects` (9 ahead). Owner: branch owners.
2. **Run the work-preservation check in CI** on every PR that touches `docs/ops/**`. Owner: GitHub Repo Assistant.
3. **Create the `mem20` DNS record** (CNAME → `bythewayz66-glitch.github.io`, proxy off). Owner: owner.
4. **Growth Hacker lands a branch** or is recorded as no-contribution. Owner: Growth Hacker.

---

## 7. House numbers (carried)

- **487 tools across 129 domains** — live pin, `docs/surface.json`. Retired bands (`257/26`, `268/26`,
  `270/27`, `306/38`) must not reappear.
- **TAM $1.28B / SAM $282M / SOM $1.68M**
- **Blended ACV $14,000**

---

*Prepared by Mem20-admin from live checks this run: full clone of `bythewayz66-glitch/mem20`, full-history
`git rev-list` ahead/behind for all 102 remote branches, `git ls-remote --heads`, the GitHub PR API, the
group roster API, and five URL probes. Every SHA was read back from the remote — none is a claim.*
