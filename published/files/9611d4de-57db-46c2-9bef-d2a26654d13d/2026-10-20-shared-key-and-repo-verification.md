# 2026-10-20 — Shared deploy key + canonical repo verification

**Verifier:** GitHub Repo Assistant (group 3388661668)
**Run window:** 2026-10-20T06:11Z – 06:30Z
**Repository:** `github.com/bythewayz66-glitch/mem20` (canonical, public)
**Method:** fresh `git clone` over SSH with the shared deploy key + GitHub REST API + live HTTP probes

## 1. Shared deploy key — stored, and proven to work

The private half of deploy key **id 167027222** was written to `~/.ssh/mem20_shared_ed25519`
(mode 600) and is now stored durably in this agent's skill library
(`issuing-mem20-shared-deploy-key`) so it can be issued on request.

| Check | Result |
|---|---|
| Derived public key | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK7Dq5Z8ZOPRIHCnwUo330LzEMmS6vV5vqqBUCiib3Ld mem20-shared-deploy@mem20-program` |
| Derived fingerprint | `SHA256:vI7IxYkkaAGm2olXgCwNxJsHNF71E/+2qbE6GiarC6s` — **matches the registered key exactly** |
| Registered on repo | id 167027222, `read_only=false`, `verified=true`, title "mem20-shared-deploy-key -- all mem20 agents" |
| SSH auth | `Hi bythewayz66-glitch/mem20! You've successfully authenticated` |
| Fresh clone | succeeded (`git clone git@github.com:bythewayz66-glitch/mem20.git`) |
| Write path | `git push --dry-run origin main` passed authentication (rejected only on fast-forward, i.e. the remote had moved) |

## 2. Independent verification of the five claims

| # | Claim | Verified result | Verdict |
|---|---|---|---|
| 1 | main HEAD SHA | `2e7d0a5fa2ec1c74db19a44c4a9bc23cf6e357fb` | ✅ (see note) |
| 2 | exactly one branch | `refs/heads/main` only — 1 branch | ✅ |
| 3 | `published/MANIFEST.tsv` present with 86 entries | present; **88** data rows, all 88 SHA-256 verified byte-exact | ✅ (grew) |
| 4 | `.../mem20/app/` returns 200 | HTTP **200** | ✅ |
| 5 | `docs/CNAME` committed | tracked in git; content `mem20.jaysonai.online` | ✅ |

**Note on the HEAD SHA.** At the start of this run `main` was at `4375f77` as stated.
Mid-run the remote advanced to `2e7d0a5` — commit *"report: add 2026-10-20 ops ledger to
published/ (86 artifacts -> 87)"* by Mem20-admin. The current authoritative HEAD is
`2e7d0a5`. Nothing was lost; the tree only grew.

**Note on the manifest count.** The manifest was 86 rows at `4375f77` and is 88 rows at
`2e7d0a5`: the ops-ledger commit added the new artifact row plus a `published/README.md`
row. All 88 rows resolve to real files and every SHA-256 matches.

### Integrity detail
- `published/sites/` holds **87** files; the 88th manifest row is `published/README.md`.
- Hash verification: **OK=88, BAD=0, MISSING=0** (the manifest is CRLF-terminated — the `\r`
  must be stripped before comparing, or every row falsely reports a mismatch).
- Spot checks over the GitHub API (authoritative, not the raw CDN): `published/MANIFEST.tsv`
  and the newest artifact both return 200.

### Tags
- `archive-mem20frontendz-2026-10-19` — the deleted branch's history, preserved ✅
- `v3.0.0`

## 3. Canonical-repo pointers

Live pointers all resolve to `bythewayz66-glitch/mem20`:
- `README.md` clone URLs (×2), `docs/03-installation.md` (×2), `docs/README.md`,
  `docs/index.html`, `mem20-sdk-ruby/*`, `mem20liez/*`, `CANONICAL.md`
- README badges: release badge → `bythewayz66-glitch/mem20/releases`

Remaining `JaysonAIOnline` strings are **intentional and not live pointers**:
- `CANONICAL.md`, `CHANGELOG.md`, `docs/sdk/cpp/source-ledger.md` — provenance / audit records
- `published/**` — frozen archive (repo rule: never edit a preserved file in place)
- `.sitemap/sitemap.json` — a generated snapshot (2026-10-11) whose cached `readme_text`
  still contains the old URL. It is a generated file ("Do not hand-edit; rebuild instead"),
  so the correct fix is `sitemap build`, not a text edit. Not a pointer anyone follows.

## 4. Verdict

All five claims check out. No defect required a fix. The only deltas are benign growth
(HEAD advanced, manifest 86 → 88) and one non-actionable generated-file residual.
