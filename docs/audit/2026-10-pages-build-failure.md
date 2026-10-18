# GitHub Pages build failure — root cause and fix

**Date:** 2026-10-18  
**Issue:** #54  
**Status:** fixed on branch `fix/pages-submodule-checkout` (not merged)

## Symptom

Every GitHub Pages run fails. At the time of diagnosis the workflow had **23
runs, 0 successes**. Pages reports `status: errored`, so the published site never
updates.

| Run | Started | Result |
|---|---|---|
| [38997365571](https://github.com/bythewayz66-glitch/mem20/actions/runs/38997365571) | 2026-10-17 03:04 | failure |
| [38993965502](https://github.com/bythewayz66-glitch/mem20/actions/runs/38993965502) | 2026-10-17 02:11 | failure |
| [38993787131](https://github.com/bythewayz66-glitch/mem20/actions/runs/38993787131) | 2026-10-17 02:09 | failure |
| [38818939768](https://github.com/bythewayz66-glitch/mem20/actions/runs/38818939768) | 2026-10-15 22:42 | failure |
| [38605557497](https://github.com/bythewayz66-glitch/mem20/actions/runs/38605557497) | 2026-10-14 17:18 | failure |

## Exact failure

Job `build` (id `117292749331`), step **Checkout**:

```
2026-10-17T03:04:29.5326491Z ##[group]Fetching submodules
2026-10-17T03:04:29.5326934Z [command]/usr/bin/git submodule sync --recursive
2026-10-17T03:04:29.5556490Z [command]/usr/bin/git -c protocol.version=2 submodule update --init --force --depth=1 --recursive
2026-10-17T03:04:29.5836530Z ##[error]fatal: No url found for submodule path 'kanban-mcp' in .gitmodules
2026-10-17T03:04:29.5860489Z ##[error]The process '/usr/bin/git' failed with exit code 128
```

Step outcomes: `Set up job` success → **`Checkout` failure** → `Upload
artifact` skipped → `deploy` job skipped.

## Root cause

The repository contains three entries with git mode `160000` (gitlinks), added
by a plain `git add` of nested git working trees rather than `git submodule
add`. A gitlink records a commit pointer but writes **no URL**; the URL is only
supplied by `.gitmodules`, which **does not exist** — not at `HEAD`, and not
anywhere in history.

| Path | Pointer SHA | Target repository |
|---|---|---|
| `kanban-mcp` | `834bdb3994942374e1ec9ebe197a6d48442b0ef1` | does not exist (404) |
| `mem20kilnz/engine` | `f28e6597ee23b6a576c8fe53555a889673c52796` | does not exist (404) |
| `mem20oreo` | `c688f7b573c104b0e28abbe4d0381b863aceabb0` | does not exist (404) |

GitHub's legacy Pages builder invokes `actions/checkout` with `submodules:
recursive`, so it fails at the first gitlink. `.github/workflows/ci.yml` uses
`actions/checkout@v4` with no `submodules:` input (default `false`), so CI never
recursed and never surfaced the problem — CI green, Pages red.

## Why every other suspect was ruled out

| Hypothesis | Verdict |
|---|---|
| Missing `pages: write` / `id-token: write` | No — the runner log grants `Pages: write` before the failure |
| Missing concurrency group | No — the run fails before a deploy job exists |
| Wrong `upload-pages-artifact` path | Not reached — the step was skipped |
| Jekyll processing a non-Jekyll site | No — `docs/.nojekyll` is present |
| Missing `index.html` | No — `docs/index.html` exists (40,727 bytes) |
| Base-path / asset 404s | No — `docs/index.html` has 0 absolute-root `href`/`src` refs and no Liquid markers |
| Node version mismatch | N/A — no Node step in this workflow |
| A build step failing before deploy | Partly — the failing step is Checkout, not a build |

## Fix

**1. `docs/audit`-level defect — remove the dangling gitlinks.**

```bash
git rm --cached kanban-mcp mem20oreo mem20kilnz/engine
```

These pointers reference repositories that do not exist, so they carry no
content and no functionality; nothing can ever check them out. This is a broken
pointer being repaired, not a feature being removed. The SHAs above are kept in
the commit message so the original intent is recoverable, and any of these
projects can be re-added properly with `git submodule add` once they exist.
`mem20kilnz/` keeps all 43 of its real files — only the gitlink directory entry
goes.

**2. Decouple Pages from submodule recursion.**

`.github/workflows/pages.yml` publishes `docs/` through the GitHub Actions Pages
source: `checkout` with `submodules: false` → `configure-pages` →
`upload-pages-artifact` (`path: docs`) → `deploy-pages`, with `pages: write` +
`id-token: write` and a `pages` concurrency group. This path does not run Jekyll
at all, so `.nojekyll` becomes belt-and-braces rather than load-bearing.

**3. One-time settings change (manual, cannot be scripted).**

Settings → Pages → Build and deployment → **Source = GitHub Actions**.
Until this is switched, the legacy builder keeps running and keeps failing even
after the gitlinks are gone.

## Acceptance

- [ ] `git ls-files --stage | grep '^160000'` returns nothing
- [ ] Pages source = GitHub Actions
- [ ] `build` → Checkout succeeds, `deploy` runs
- [ ] `https://bythewayz66-glitch.github.io/mem20/` returns 200 with the docs index
- [ ] No application code, package, or feature removed

## Related

- #2 — CI exists but never exercises submodule recursion
- #3 — generated output tracked in the index
