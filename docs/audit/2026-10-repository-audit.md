# mem20 — Repository Audit

**Date:** 2026-10-15 · **Auditor:** Teamily (agent) · **Scope:** `bythewayz66-glitch/mem20` @ `main`
**Branch with fixes:** `audit/mem20-2026-10`

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

1. **`mcp_server_dir/` is a corrupt duplicate of `mcp/`.** 25 of its Python files
   fail to parse — a bulk edit injected stray import lines into docstrings. It is
   committed to the repo and referenced by `CANONICAL.md` and `SITEMAP.md`.
2. **There is no CI.** GitHub Actions is not configured at all; nothing prevents a
   syntax-broken commit from landing, which is exactly what happened to
   `mcp_server_dir/`.
3. **Generated output is tracked in git** — `build/` (47 files), `__pycache__/`
   (100 files), `node_modules/` (2,232 files). `.gitignore` already lists
d   `build/`, `__pycache__/`, and `node_modules/`; they were committed anyway.

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

**A1 — `mcp_server_dir/` is a corrupt duplicate of `mcp/` · severity: critical**
- **Area:** `mcp_server_dir/**` (25 files), `CANONICAL.md:23`, `SITEMAP.md:348`
- **Description:** `mcp_server_dir/` duplicates `mcp/` but every one of its 25
  Python files is unparseable. The corruption is a mechanical bulk-edit error:
  the lines
  `from mcp.server import Server` / `from mcp.server.lowlevel.server import ServerRequestContext` /
  `import mcp_types as mt` were injected **inside** module docstrings and at
  arbitrary column offsets. Examples: `search_tools.py` lines 2–4 sit between the
  opening `"""` and the docstring body; `blender_bridge.py:85` is an
  `unexpected indent`.
- **Impact:** The tree cannot be imported, compiled, or linted by any tool that
  walks it; it inflates clone size and defeats repo-wide tooling.
- **Suggested fix (needs a decision):** Determine whether anything still runs
  `mcp_server_dir/` — `CANONICAL.md` and `SITEMAP.md` name it, but `README.md` and
  the systemd/`ExecStart` references point at `mcp/mcp_server.py`. If dead, delete
  it (one commit) and update the two docs; if live, regenerate it from `mcp/`.
  Do **not** hand-fix 25 files.

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
  branch (`.github/workflows/ci.yml`), scoped to the non-quarantined tree, plus an
  advisory test job. Follow-up: make the test job required once the tree is green.

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
| 1 | **Decide the fate of `mcp_server_dir/`** — delete or regenerate | critical | human + OpenCode | 25 unparseable files poison every repo-wide tool and hide real errors |
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

Everything else is **flagged, not applied** — per the protocol, destructive or
structural changes need the owner's decision.

---

## 7. Recommended next steps

1. Review and merge `audit/mem20-2026-10` (or cherry-pick the `gateway_web.py` fix if you want that immediately).
2. Decide #1 in the action plan — it is the single highest-leverage call.
3. Adopt `docs/handoff/AGENT-OPERATING-PROTOCOL.md` as the working agreement and have Hermes and OpenCode read it before their next session.
4. Move the created issues onto the **Repo hygiene & CI — 2026-10 audit** milestone and assign owners.

> When this report and the live issue list disagree, **the issues win** — they
> are the moving source of truth.
