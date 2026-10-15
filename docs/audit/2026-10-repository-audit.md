# mem20 — Repository Audit

**Date:** 2026-10-15 · **Auditor:** Teamily (agent) · **Scope:** `bythewayz66-glitch/mem20` @ `main`
**Branch with fixes:** `audit/mem20-2026-10`
**Revised:** 2026-10-15 — feature-removal wording reframed per the standing rule below; expanded with a second, file-by-file pass (see "Expanded findings" at the end).

---

> ## ⚠️ Standing rule (authoritative — supersedes any earlier wording in this report)
> **Existing functionality in mem20 is never removed, deleted, quarantined, or
> dropped. It is fixed or completed.** Any recommendation below that used words
> like "delete", "remove", or "quarantine" about a feature has been reframed to
> a fix-or-complete action. This rule overrides every earlier audit
> recommendation; where this report and the live issue list disagree, **the
> issues win** — and #1 is now a fix-and-complete task.

---

## 1. Method

Full clone at `main`, then:

```bash
python3 -m py_compile    # every tracked *.py outside build/, node_modules/, __pycache__/
git ls-files             # tracked-artifact audit
python3 -m pytest --collect-only   # test collection
grep -rIn 'TODO|FIXME|HACK|XXX|PLACEHOLDER' --include='*.py' .
```

Cross-checked against `README.md`, `docs/`, `CHANGELOG.md`, `pyproject.toml`,
`pytest.ini`, and the live repo settings via the GitHub API.

**Repository size:** ~9,867 files, 1,709 Python modules, 137 `test_*.py` files,
across a large `mem20*z` package estate.

---

## 2. Executive summary

mem20 is a genuinely large, ambitious monorepo. Its core trees (`mcp/`,
`mem20unitiz/`, `mem20runtime/`) are clean and parse correctly. Three things hold
it back, in priority order:

1. **`mcp_server_dir/` fails to parse (25 files).** A bulk edit injected stray
   import lines into docstrings, so the tree cannot be imported, compiled, or
   linted. It is committed to the repo and referenced by `CANONICAL.md` and
   `SITEMAP.md`, so the fix is to **repair it** — the standing rule forbids
   deleting or quarantining it.
2. **There is no CI.** GitHub Actions is not configured at all; nothing prevents a
   syntax-broken commit from landing, which is exactly what happened to
   `mcp_server_dir/`.
3. **Generated output is tracked in git** — `build/` (47 files), `__pycache__/`
   (100 files), `node_modules/` (2,232 files). `.gitignore` already listsd
   `build/`, `__pycache__/`, and `node_modules/`; they were committed anyway.

One isolated production bug (`gateway_web.py`, unterminated f-string) was **fixed
in this branch**. Everything else is recorded as a tracked issue.

---

## 3. Health snapshot

| Area | State | Severity of worst finding |
|---|---|---|
| Source parse integrity | ⛔ 25 files fail `py_compile` | **critical** |
| CI / automated checks | ⛔ none configured | **high** |
| Git hygiene (tracked artefacts) | ⚠️ build/, pycache, node_modules committed | **high** |
| Tests | ⚠️ `pytest` not installable by default; scope unclear | **medium** |
| Documentation | ⚠️ version + tool-count skew | **medium** |
| Robustness / security | ⚠️ broken `try/except`, permissive CORS | **medium** |
| Packaging / runtime paths | ⚠️ stale `mcp/mcp_server.py` refs | **medium** |
| Repo templates / intake | ✅ added in this branch | resolved |

---

## 4. Findings

### A. Build & source integrity

**A1 — `mcp_server_dir/` fails to parse (25 files) · severity: critical**
- **Area:** `mcp_server_dir/**` (25 files), `CANONICAL.md:23`, `SITEMAP.md:348`
- **Description:** every one of `mcp_server_dir/`'s 25 Python files is
  unparseable. The corruption is a mechanical bulk-edit error: the lines
  `from mcp.server import Server` / `from mcp.server.lowlevel.server import ServerRequestContext` /
  `import mcp_types as mt` were injected **inside** module docstrings and at
  arbitrary column offsets. Examples: `search_tools.py` lines 2–4 sit between the
  opening `"""` and the docstring body; `blender_bridge.py:85` is an
  `unexpected indent`.
- **Impact:** The tree cannot be imported, compiled, or linted by any tool that
  walks it, so its functionality is invisible to repo-wide tooling and to CI.
- **Suggested fix (fix and complete — never remove):** `mcp_server_dir/` is
  existing functionality and must be **repaired**, not deleted or quarantined.
  Repair the injected lines — move them out of the docstrings back to their
  correct module-level position, or drop the accidental duplication where they
  already exist — and fix the indentation at each site; script the repair where
  the corruption is mechanical. Then settle the tree's relationship with `mcp/`:
  either make `mcp_server_dir/` canonical, or maintain it as a mirror regenerated
  from `mcp/`; either way the result must **build and run**. Update `CANONICAL.md`
  and `SITEMAP.md` to describe the tree's role, and drop the temporary
  `mcp_server_dir/` exclusion from the CI syntax gate once it parses.

**A2 — `install_tracker.py`: commented-out `try:` leaves a code path without its handler · severity: medium**
- **Area:** `mcp_server_dir/install_tracker.py` (also present under `mcp/`)
- **Description:** The `try:` keyword is commented out (`# try:`) while the
  `except Exception:` block remains live, producing an `IndentationError`. The
  same pattern appears in `mcp_server_dir/mcp_server.py`. It looks like a
  deliberate "disable telemetry" edit that was never completed.
- **Suggested fix:** Restore `try:` (or delete the `except` with it) in one small
  commit. Low risk; it is telemetry only.

**A3 — `mem20agentz/gateway_web.py`: unterminated f-string in the dashboard · severity: high · ✅ FIXED**
- **Area:** `mem20agentz/mem20agentz/gateway_web.py` (~line 213)
- **Description:** The cron-row comprehension built an f-string across a raw
  newline (`f"<li>{...}"` then a new line continuing the expression), producing
  `SyntaxError: unterminated string literal`. Because the module is the web
  gateway's dashboard renderer, **the whole module — and therefore the gateway —
  failed to import.**
- **Fix applied (this branch):** Extracted the conditional into a small local
  `_cron_row(j)` helper that builds the label first and returns the `<li>…</li>`.
  Behaviour is identical; `py_compile` now passes.
- **Note:** This is the value of A2 of the action plan — a syntax gate would have
  caught it before merge.

### B. CI & automated checks

**B1 — No CI is configured · severity: high**
- **Area:** repo settings / `.github/workflows/`
- **Description:** The repository has no workflows. `GITHUB_LIST_REPOSITORY_WORKFLOWS`
  returns empty. Nothing runs `compileall`, tests, or lint on push or PR.
- **Impact:** Syntax-broken code merged (`mcp_server_dir/`, `gateway_web.py`), and
  will again.
- **Suggested fix:** ✅ A minimal **syntax gate** workflow is included in this
  branch (`.github/workflows/ci.yml`), scoped for now to the trees that currently
  parse — `mcp_server_dir/` is temporarily excluded **until its repair lands
  (#1)**, not quarantined — plus an advisory test job. Follow-up: make the test
  job required once the tree is green, and drop the temporary exclusion so the
  gate covers the whole repo.

### C. Repository hygiene (tracked artefacts)

**C1 — `build/` is committed · severity: high**
- **Area:** `build/` (47 tracked files)
- **Description:** A built copy of the package is in the tree, including its own
  copies of the syntax-broken modules (e.g. `build/lib/.../a2a_tools.py`).
  `.gitignore` lists `build/`, so this was added before the rule or with `-f`.
- **Impact:** Confuses tools that glob `**/*.py`, ships dead code, and doubles the
  surface for the corruption in A1.
- **Suggested fix:** `git rm -r --cached build` in a docs-free hygiene commit;
  confirm `.gitignore` covers it (it does).

**C2 — `__pycache__/` (100 files) and `node_modules/` (2,232 files) are tracked · severity: high**
- **Area:** repo-wide
- **Description:** Compiled bytecode and an entire Node dependency tree are
  committed, despite both being in `.gitignore`.
- **Impact:** Thousands of files of noise in every clone and every `git status`.
- **Suggested fix:** `git rm -r --cached` both; add a CI step that fails if either
  reappears.

### D. Tests

**D1 — `pytest` is not installed by default · severity: medium**
- **Area:** `pyproject.toml` (`[project.optional-dependencies] dev = ["pytest>=7"]`)
- **Description:** A plain `python3 -m pytest` on a fresh checkout fails with
  `No module named pytest`. The test suite is only reachable after
  `pip install -e '.[dev]'`, which the README does not state as a prerequisite
  for running tests.
- **Suggested fix:** Document the dev install in `CONTRIBUTING.md` (done) and in
  the README testing section; suggest `pip install -e '.[dev]'`.

**D2 — Test scope depends on the developer's installed set · severity: medium**
- **Area:** `pytest.ini` (top-level `addopts = --import-mode=importlib`)
- **Description:** The comment in `pytest.ini` itself records that a bare `pytest`
  once "ran 132 tests and reported green while 1,400+ tests in the other packages
  never executed". The default now collects `.`, but the suite still depends on
  optional runtime deps (embedding models, blender) being present, so a green run
  locally does not imply a green run in CI — or vice versa.
- **Suggested fix:** Split tests into `unit` (deps-free, must pass everywhere) and
  `integration` (optional deps) via `pytest` markers, and gate only `unit` in CI.

### E. Documentation

**E1 — Version skew across docs · severity: medium**
- **Area:** `pyproject.toml` vs `README.md`, `docs/`, `CHANGELOG.md`
- **Description:** `pyproject.toml` declares `version = "2.1.0rc2"`. The docs
  simultaneously carry `2.1-rc2`, `2.1.0-rc2`, `2.1.0`, `2.0.0`, `2.13.4`, and a
  `2.2.0-dev` roadmap reference. There is no single authoritative version marker
  the reader can trust.
- **Suggested fix:** Treat `pyproject.toml` (+ the `VERSION` file) as the source of
  truth; sweep the docs to reference it, and add a release checklist step.

**E2 — README tool-count claims do not match the tree · severity: medium**
- **Area:** `README.md` (~L24, L52), `docs/01-architecture.md` (~L24, L110)
- **Description:** The docs assert **"257 tools · 26 domains"**. The actual
  `mcp/tools/` directory holds **24** modules; even `mcp_server_dir/tools/` holds
  only 22. The number is presented as a headline fact and is not derivable from
  the code.
- **Suggested fix:** Generate the count from the registry (`mcp/tools/__init__.py`)
  and paste it in, or replace the hard number with "see `docs/05-complete-tools-reference.md`".
  Add a CI check that fails on drift.

**E3 — No index link path from the new collaboration docs · severity: low**
- **Area:** `INDEX.md`
- **Description:** `docs/handoff/AGENT-OPERATING-PROTOCOL.md` is not yet linked from
  `INDEX.md`, so an agent that lands on the repo root may miss it.
- **Suggested fix:** Add one line to `INDEX.md` pointing at the protocol.
  *(Pending in this branch — flagged, not applied, since INDEX.md needs a human
  pass.)*

### F. Robustness & security

**F1 — Swallowed exceptions hide real failures · severity: medium**
- **Area:** `mem20agentz/gateway_web.py` (`except Exception: cron_rows = "<li>(sealed)</li>"`),
  and the `except Exception` around `_track_first_run`.
- **Description:** Several `except Exception` blocks collapse any error into a
  placeholder string. A broken cron backend is indistinguishable from an empty
  one. Startup telemetry failures are silent by design (acceptable), but the
  dashboard's silent "sealed" is not.
- **Suggested fix:** Log the exception (with the module's existing stderr pattern)
  before falling back, so failures are visible in the service log.

**F2 — `DefaultErrorHandler` must be registered · severity: low**
- **Area:** `mcp_server_dir/tools/search_tools.py` (docstring references it)
- **Description:** The search mixin's summary claims it registers a
  `DefaultErrorHandler` for 429/402/403 rate-limit cases. Confirm this is actually
  wired in the live `mcp/` implementation or the claim is misleading.
- **Suggested fix:** Verify and, if missing, implement or correct the docstring.

**F3 — Secrets posture is good, keep it that way · severity: info**
- **Area:** `.gitignore`, `secrets/`
- **Description:** `secrets/`, `.env`, `*.key`, `*.pem` are correctly ignored, and
  no secrets were found committed in the audit. No action; noted so a future
  change does not regress it. Enable secret scanning at the repo level as
  defence-in-depth (see issue).

### G. Packaging & runtime paths

**G1 — Stale entry-point references · severity: medium**
- **Area:** `2.0_roadmap/adr/0001-…md`, `2.0_roadmap/step_10.md`, `2.0_roadmap/human_package/steps/step_10.md`
- **Description:** These reference `mcp/mcp_server.py` as a ~4,848-line file and the
  `From systemd ExecStart path (mcp/mcp_server.py)`. The actual
  `mcp/mcp_server.py` is now a small shim; `README.md:67` correctly explains the
  decomposition, but the roadmap docs still describe the pre-decomposition state
  as current.
- **Suggested fix:** Mark the roadmap entries as historical, or update them to
  point at `mcp/server.py` + the mixins.

---

## 5. Prioritized action plan

Priority = severity, then effort-to-unblock. "Why now" is the reason it sits at
this rank.

### P0 — do first (blocks everything else)

| # | Action | Sev | Layer | Why now |
|---|---|---|---|---|
| 1 | **Fix and complete `mcp_server_dir/`** — make all 25 files parse and run | critical | human + OpenCode | 25 unparseable files poison every repo-wide tool and hide the tree's real functionality |
| 2 | **Land the syntax gate** (`.github/workflows/ci.yml`, in this branch) | high | Teamily | Prevents the class of bug that produced #1 |
| 3 | **Untrack `build/`, `__pycache__/`, `node_modules/`** | high | Teamily | Removes ~2,400 files of noise and trims the corruption surface |

### P1 — next

| # | Action | Sev | Layer | Why now |
|---|---|---|---|---|
| 4 | Restore the `try:` in `install_tracker.py` | medium | OpenCode | One-line fix; leaves a broken idiom in the tree |
| 5 | Mark unit vs integration tests; gate `unit` in CI | medium | OpenCode | Makes "green" mean something |
| 6 | Fix README/docs version + tool-count skew | medium | Teamily | The docs are the product's front door and currently misstate the product |
| 7 | Update stale roadmap entry-point references | medium | Teamily | Cheap; stops misleading new readers |

### P2 — when the tree is stable

| # | Action | Sev | Layer |
|---|---|---|---|
| 8 | Log swallowed exceptions in the dashboard path | medium | OpenCode |
| 9 | Verify/implement the search rate-limit handler | low | OpenCode |
| 10 | Add `docs/handoff/` to `INDEX.md`; enable secret scanning | low | Teamily |

---

## 6. Applied in this branch

| Change | File |
|---|---|
| Fixed unterminated f-string (module now imports) | `mem20agentz/mem20agentz/gateway_web.py` |
| Bug + enhancement issue forms | `.github/ISSUE_TEMPLATE/` |
| PR template, CODEOWNERS, template config | `.github/` |
| Syntax-gate CI + advisory tests | `.github/workflows/ci.yml` |
| CONTRIBUTING / SECURITY / CODE_OF_CONDUCT | repo root |
| Agent operating protocol, state board, handoff template | `docs/handoff/` |

Everything else is **flagged, not applied** — per the protocol, structural
changes need the owner's decision. Note the standing rule above: fixing or
completing a feature is always in scope; **removing one never is**.

---

## 7. Recommended next steps

1. Review and merge `audit/mem20-2026-10` (or cherry-pick the `gateway_web.py` fix if you want that immediately).
2. Fix and complete #1 in the action plan (repair `mcp_server_dir/`; never remove it) — it is the single highest-leverage call.
3. Adopt `docs/handoff/AGENT-OPERATING-PROTOCOL.md` as the working agreement and have Hermes and OpenCode read it before their next session.
4. Move the created issues onto the **Repo hygiene & CI — 2026-10 audit** milestone and assign owners.

> When this report and the live issue list disagree, **the issues win** — they
> are the moving source of truth.

---
---

# Expanded findings — second pass (2026-10-15)

A deeper, file-by-file pass across all source languages, CI, tests, docs, TODO
markers, secrets, hardcoded paths, and dependencies surfaced **13 additional
findings**, filed as issues **#13–#25**. All are additive; the standing rule
(**fix or complete — never remove**) applies unchanged.

## Raw scan totals

| Signal | Count |
|---|---|
| TODO markers (genuine, excluding risk-scorer/detector literals) | 8 |
| FIXME / HACK / XXX | 0 |
| PLACEHOLDER (all benign — template tokens) | 8 |
| Bare `except:` clauses | **316** |
| `eval(` / `exec(` in non-test source | 17 |
| `/home/jayson` occurrences (all text types) | **169** |
| Rust `.rs` files (`braid/` + `braid_python/`) | 63 |
| C++ `.cpp` files | 2 |
| JS files (1,400 of them inside `node_modules/`) | 1,428 |
| TS files (107 inside `node_modules/`) | 518 |
| `test_*.py` tracked | 139 |
| `conftest.py` tracked | 33 |
| Top-level `mem20*z` package directories | 292 |
| Byte-identical package `core.py` files (sha1 `3342189f…`) | **100** |
| Tracked `.pyc` (cpython-311 / cpython-314) | 12 / 84 |
| Tracked `.env`-named files (both `.env.example`, safe) | 2 |

## New issues

| # | Finding | Area | Sev |
|---|---|---|---|
| #13 | 316 bare `except:` clauses swallow errors across the Python estate | robustness | high |
| #14 | Untrack non-existent `/home/jayson` "spec authority" directories — commit a canonical copy | portability | high |
| #15 | 169 hardcoded `/home/jayson` paths make the repo non-portable | portability | medium |
| #16 | Generated state tracked in git — 4.3 MB harness entries, `chroma.sqlite3`, `ledger.jsonl` | hygiene | high |
| #17 | Estate-wide duplication — 100 byte-identical package `core.py` files (and `mcp/` vs `mcp_server_dir/`) | duplication | high |
| #18 | `test/` scratch directory breaks a plain `pytest` collection (conftest copy + basename collisions) | tests | medium |
| #19 | Add Dependabot + a dependency-audit CI job (supply-chain posture) | supply chain | medium |
| #20 | No Python lockfile; `braid*/Cargo.lock` gitignored — builds are not reproducible | reproducibility | medium |
| #21 | CI covers Python only — the Rust `braid` workspace has no build/test gate | CI | low |
| #22 | Tracked `.pyc` bytecode mixes Python 3.11 (12) and 3.14 (84) | hygiene | low |
| #23 | Add pre-commit hooks (whitespace, large-file, secret scan) to cut churn | tooling | low |
| #24 | Vendored sub-project committed wholesale: `mem20officez/src_harvest/` brings its own CI, lockfile, and dependency tree | vendoring | medium |
| #25 | Two `.cpp` files and a root `Makefile`, but no C++ build config — the SDK example is never compiled | tooling | low |

## Notes on the new pass

- **Dependency drift is assessed from the files only** (no registry lookups):
  `requirements.txt` is floor-pinned, `requirements-optional.txt` lists external
  *applications* (Blender, Unity — correctly not pip packages), and no lockfile is
  tracked. `Cargo.lock` is absent for the `braid` workspace.
- **Secrets:** no committed secrets were found. The only tracked `.env`-named
  files are two `.env.example` templates (safe). Tracked absolute paths are
  **leakage of the author's environment**, not credentials.
- **`test/test_suite_upgraded.py`** is a stale copy of `conftest.py` with no tests
  — a duplicate, not a feature; the standing rule does not protect a copy.
- **Duplication (#17) is the root cause behind #1**: the corruption reached one
  copy of the shared code and not the other. De-duplicating removes the whole
  class of bug, so it is ranked P0 alongside #1.

## Updated prioritized action plan (supersedes §5)

The original P0/P1/P2 ranks hold; the new issues slot in as follows.

### P0 — first

1. **#1** Fix and complete `mcp_server_dir/` — make all 25 files parse and run
2. **#2** Land the CI syntax gate (in this branch)
3. **#3 / #16 / #22** Untrack generated output, state data, and `.pyc`
4. **#17** De-duplicate the estate `core.py` (root cause of #1's class of bug)

### P1 — next

5. **#13** Replace bare `except:` with logged `except Exception:`
6. **#15 / #14** Make the repo portable (paths + committed spec inputs)
7. **#5 / #18** Fix the test layout; split unit vs integration
8. **#6 / #7** Close the documentation-skew gaps
9. **#19 / #20** Supply chain + reproducibility (Dependabot, lockfiles)

### P2 — when the tree is stable

10. **#8 / #9 / #10** Smaller robustness + docs items
11. **#21 / #23 / #24 / #25** Rust CI, pre-commit, vendoring decision, C++ build target

> Standing rule unchanged: **fix or complete — never remove.** The live issue
> list remains the source of truth wherever this report and the list disagree.
