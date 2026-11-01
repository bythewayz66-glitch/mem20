# Retired infra purge — allowlist and verification (G8)

**Task:** purge retired `Sidney` / `gabe` / `jaysonai` references from `main`, and verify no live
service or systemd unit still points at them.
**Owner directive:** `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220e964f84aabac78127fc18463dfa6798d`, row 5 (Server Builder, gap G8).
**Baseline:** `main` = `48c241a1` (`v3.1.2`).
**Branch:** `chore/g8-purge-retired-infra-2026-11-01`.

## 1. Two different things share the name "retired" — do not treat them alike

| Identity | What it is | State (verified 2026-11-01) | Action |
|---|---|---|---|
| `jaysonai.online` **zone** and the hosts in it (`mem20.`, `shop.`, `control.`, `docs.`, `jnet1.`, apex, `www`) | the retired **infrastructure**: a DNS zone plus the boxes behind it | `jaysonai.online` → **NXDOMAIN**; `mem20.jaysonai.online` → **NXDOMAIN** (Cloudflare + Google DoH, per directive §1) | **purged** from live code and live docs |
| the retired **publish host** (`216.198.115.91`) and its **publish gate** | the SSH/rsync target and the gate that routed to it | host unreachable: `2222` → `No route to host`, `22` → timeout, `80` → timeout; `sidney` and `gabe` do not resolve | **purged** from live code and live docs |
| `JaysonAIOnline` **GitHub org** | a *different, live* thing: the upstream org still serving `JaysonAIOnline/oreo` (**HTTP 200**), a pinned dependency of `mem20agentz` | **live** | **kept** — attribution and a dependency source, not retired infra |

`mem20.jaysonai.online` is **not** recreated by this change. It is NXDOMAIN on both resolvers and
`jaysonai.online` is delegated to Cloudflare NS; the directive says to leave it dead. Nothing in
this branch creates a DNS record, a host, or a tunnel.

## 2. What was purged

Live code paths — the ones that could actually *act* on a retired name:

| File | Before | After |
|---|---|---|
| `mem20controlz/mem20controlz/websites.py` | `FLEET_SITES` shipped **8 retired hostnames** as the panel's fleet inventory, each rendered by the Websites tab | `FLEET_SITES = []`; the planned-vs-observed drift mechanism and its tests are unchanged |
| `mem20controlz/.../web/src/tabs/Websites.jsx` | comment named the retired zone | comment describes the state without naming it |
| `tools/gen_completion_audit.py` | comment named the retired zone | comment describes the state without naming it |
| `packaging/deb/build-deb.sh` | `Maintainer: JaysonAI <noreply@jayson.ai>` — shipped in **every `.deb`** | `Maintainer: mem20 maintainers <bythewayz66@gmail.com>` |
| `mem20-sdk-ruby/lib/mem20/version.rb` | comment tied `SERVER_VERSION` to the retired host | states the validated server release only |

Live docs — served or read as current guidance:

| File | Why it mattered |
|---|---|
| `docs/dashboard.html` | **served on GitHub Pages.** A whole panel titled *"Publish path — Sidney via gabe"* told readers the canonical publish target *is* the retired server. Replaced with the real rule: GitHub is the only publication channel. |
| `CANONICAL.md` | the canonical-designation document; named the host and gate |
| `CHANGELOG.md`, `docs/releases/v3.1.0.md` | release records naming the host and gate |
| `mem20-sdk-ruby/README.md`, `docs/EVIDENCE.md`, `docs/API.md`, `docs/INSTALL.md` | SDK docs naming the host as the verification/publication surface |
| `docs/ops/corrections-2026-10-26.md` | said "GitHub is the delivery surface **until Sidney is back**" — an instruction to wait for a host that will never return. Now a dated historical record. |

## 3. Allowlist — the only places the tokens may remain

`git grep -ciE 'sidney|gabe'` on this branch returns hits in the files below and nowhere else. Each
entry is a *reason the token cannot be removed without destroying evidence or breaking a real
path*, not a convenience exemption.

| # | Path | Category | Why it must stay |
|---|---|---|---|
| A1 | `published/**` (94 files) | **immutable archive** | `published/` is the GitHub-side permanent copy of every delivered artifact, integrity-pinned by `published/MANIFEST.tsv` (per-file sha-256). Editing a preserved file breaks the manifest and destroys the record of what was actually shipped. `published/README.md` rule 3: *"never edit a preserved file in place."* Many of these files *are* the deploy scripts and publish reports that named the retired host — rewriting them would falsify the delivery record. |
| A2 | `.sitemap/sitemap.json` (2) | **generated snapshot** | a point-in-time index (`root: /opt/mem20`, `generated_at: 2026-10-28T23:54:00-0600`) of README text, including `published/README.md` verbatim. `sitemap build` regenerates it wholesale; hand-editing would desynchronise the index from the tree it describes and would not survive the next build. |
| A3 | `docs/ops/branch-inventory-2026-10-31.md` (8) | **dated audit record** | names the git branch `chore/retire-jaysonai-sidney-gabe`. A branch name is a git ref, not infrastructure; rewriting it would falsify the inventory. This document is also what *records* G8. |
| A4 | `docs/ops/branch-disposition-2026-10-31.md` (10) | **dated audit record** | same branch name, plus the dated retirement finding. |
| A5 | `docs/ops/owner-directive-2026-11-01.md` (5) | **the directive itself** | quotes the gap statement and the verified DNS/host findings. It is the authorising document; it cannot be edited to hide what it authorises. |
| A6 | `docs/ops/tag-audit-2026-10-31.md` (1) | **dated audit record** | already states *"Sidney and gabe are retired and are not used by this audit"* — a correct retirement statement, not a live reference. |
| A7 | `docs/ops/roster-verification-2026-10-27.md` (1) | **dated audit record** | same: records the retired host as dark. |
| A8 | `docs/gtm/claim-ledger.md` (1) | **verbatim commit subject** | quotes the subject of `f1672473` — *"chore(infra): purge retired jaysonai.online / Sidney / gabe references (#145)"*. Altering it would make the ledger cite a commit message that does not exist. |
| A9 | `docs/market/market-claims-consistency-2026-10-31.md` (4) | **real on-disk path** | cites `published/sites/54ed398d-…/documents/mem20-market-research-v3/gabe-bundle/`, a directory that **exists** in the archive. The path is the citation. |
| A10 | `docs/pricing/RECONCILIATION_NOTE.md` (2) | **real on-disk path** | same `gabe-bundle` directory. |
| A11 | `scripts/sweep-tool-counts.py` (2) | **real on-disk path** | its `ROWS_PAGES` / `PASS2_FILES` sets must name the file they rewrite; that file lives under `gabe-bundle/`. Removing the entry would silently stop the sweep from correcting that page. |
| A12 | `docs/ops/retired-infra-allowlist-2026-11-01.md` | **this document** | it must be able to name what it allows. |
| A13 | `scripts/verify-retired-infra-purge.sh` | **the gate** | it must be able to name the pattern it enforces. |

**Not allowlisted, and therefore purged:** every other tracked file. In particular the previously
offending `docs/dashboard.html` (3 hits), `CANONICAL.md` (4), `CHANGELOG.md` (2),
`docs/releases/v3.1.0.md` (2), `mem20-sdk-ruby/**` (6), `mem20controlz/**` (2),
`docs/ops/corrections-2026-10-26.md` (3), `packaging/deb/build-deb.sh` (1) and
`tools/gen_completion_audit.py` (1) now return **0**.

### `jaysonai` — a separate question

`git grep -ciE 'jaysonai'` is **not** the acceptance gate (the directive's gate is `sidney|gabe`).
For completeness, the surviving `jaysonai` hits fall into three classes and all three are kept:

1. **`JaysonAIOnline` GitHub org** — `CANONICAL.md`, `README.md`, `docs/README.md`,
   `docs/sdk/cpp/source-ledger.md`, `docs/hygiene/oreo-gitlink.md`, `mem20agentz/pyproject.toml`.
   Live org (HTTP 200), pinned dependency, deliberate attribution.
2. **Dated audit records / branch names** — `docs/ops/*-2026-10-3*.md`, `docs/gtm/claim-ledger.md`,
   `CHANGELOG.md` (the `JaysonAIOnline/mem20` → `bythewayz66-glitch/mem20` URL migration note).
3. **Product/brand strings** — `mem20gamez` `companyName`, `mem20officez` harvested dashboard,
   `mem20botz/identity.py` operator profile, `entries/project.md`, `roadmaps/*`. The operator's own
   name and branding, not the retired DNS zone. Removing a person's name from their own product is
   not this task.

The retired **zone** `jaysonai.online` now appears only in `CHANGELOG.md` and
`docs/releases/v3.1.0.md` as the dated retirement record, plus the A1/A2 archive.

## 4. No live service or systemd unit points at them

| Check | Command | Result |
|---|---|---|
| Remote-host directives in any unit | `git grep -nE 'Host=\|HostName\|ssh \|rsync\|sftp\|scp \|StrictHostKey' -- '*service*' '*timer*' ':!published/'` | **no matches** |
| Shipped unit template | `systemd/mem20.service.template` | clean — local venv path, no remote target |
| Deployed unit generator | `packaging/deb/build-deb.sh` | clean — rewrites `ExecStart` to `/opt/mem20/venv/bin/mem20-mcp` |
| Unit health probe list | `mem20controlz/.../websites.py` `UNIT_CANDIDATES` | 5 local units (`mcp-server`, `mem20controlz`, `mem20cviz`, `mem20ucgz`, `mem20sensorz`) — none remote |
| CI workflows | `git grep -nE 'sidney\|gabe\|jaysonai\|216\.198' -- '.github/*'` | **no matches** |
| Archived units | `published/.../mem20-sync.service`, `mem20-sync.timer`, `mem20.service` | archive only (A1). `ExecStart` is local; the only host mention is a comment in the timer. Not installed from this repo. |
| Host reachability | `curl` + `/dev/tcp` to `216.198.115.91` | `2222` → `No route to host`; `22` → timeout; `80` → timeout |
| Name resolution | `getent hosts sidney` / `gabe` | both **NXDOMAIN** |

## 5. Acceptance

```bash
bash scripts/verify-retired-infra-purge.sh
```

The gate greps the branch, subtracts exactly the allowlist above, and exits non-zero if anything
else matches. It also re-runs the `mem20controlz` suite, because the `FLEET_SITES` change touches
tested code.

## 6. What this does not do

- Does not delete or rewrite the `published/` archive or its manifest.
- Does not touch DNS. `mem20.jaysonai.online` stays NXDOMAIN; no record is created.
- Does not remove the `JaysonAIOnline` org attribution or the pinned `oreo` dependency.
- Does not close the `chore/retire-jaysonai-sidney-gabe` branch — that is GitHub Repo Assistant's
  row (directive §3 row 1 / `branch-disposition` §8).
