# mem20 - Product Sales-Readiness Evaluation

**Date:** 2026-10-15 - **Evaluator:** Teamily (agent) - **Scope:** `bythewayz66-glitch/mem20` @ `main`
**Method:** full clone; `py_compile` across every surface; real `pytest` runs for `mem20controlz`, `mem20agentz`, `mem20crewz`; import probing; tracked-artifact audit; cross-check against `README.md`, `CANONICAL.md`, the three surface READMEs/PLAN.md, and live GitHub issue/label/milestone state.

> ## STANDING RULE (authoritative for every recommendation here)
> **Features are never removed. They are fixed or completed.** Wherever a gap below could be read as "delete / drop / quarantine", the action is **repair, restore, or complete the implementation**. This rule overrides every earlier audit recommendation.

---

## 1. Verdict

mem20 is a genuinely large, ambitious monorepo: **293 `mem20*z` subsystem packages**, ~9.9k tracked files, and a memory + cognition core (`mcp/`, `memory_engine/`, `cog/`) with a real, working MCP JSON-RPC surface. It is **not yet sellable as a product**. Three surfaces carry demo weight - `mem20controlz` (control plane), `mem20agentz` (agent platform), `mem20crewz` (crew framework) - and **two of the three are currently broken at import/collection time, with no desktop build anywhere in the tree.**

The gap is not ambition or breadth. It is **last-mile shippability**: nothing prevents a syntax-broken commit from landing, two shipped surfaces have live defects that make the demo path fail on a clean machine, and there is no distributable desktop artifact.

### What genuinely works end-to-end today

| Surface / capability | Evidence it works |
|---|---|
| MCP stdio JSON-RPC server (`mcp/`) | Core tree parses clean; documented 4 install channels (pip/Docker/npm/apt) |
| Memory core (`memory_engine/`, `memory.py`) | Grounded/simulated split with store-layer invariants; ledger + vector + BM25 |
| `mem20controlz` package | **Imports clean** (`mem20controlz 0.1.0`); FastAPI app 496 LOC; React build present in `static/` |
| `mem20crewz` package | **Imports clean; 52/52 tests pass** after declaring its own runtime deps |
| `mem20agentz` package | Imports clean after deps; **119/149 tests pass** |
| Git/GitHub automation | `mem20agentz vcs_*` (11 tools), proven live in this engagement |

---

## 2. Gap register

Ranked by **revenue / demo impact**: a **blocker** kills a live demo or a buyer's first 10 minutes; **high** is hit by any serious evaluation; **medium** is hit in week one of a trial; **low** is polish.

### BLOCKERS

| # | Surface | What is missing / broken | Evidence | Sales impact |
|---|---|---|---|---|
| B1 | `mem20agentz` | **`gateway_web.py` does not parse - module unimportable.** An f-string is broken across a raw newline in the dashboard cron-row comprehension. | `mem20agentz/mem20agentz/gateway_web.py:213` -> `SyntaxError: unterminated string literal`; `python3 -m py_compile` fails | The web gateway **and** the office dashboard both import through this module. `desktop.py` (`build_office_factory`) does `from .gateway_web import build_web_factory`, so **the entire agent web/office surface fails to start.** A buyer's first `serve` fails. |
| B2 | `mem20agentz` | **CLI crashes on the `mem20cliz` fallback path.** The fallback decorator references `_exc`, bound only inside the `except` clause, out of scope in the wrapper closure. | `mem20agentz/mem20agentz/cli.py:20-32` -> `NameError: name '_exc' is not defined`; 3 CLI tests fail | Any machine without `mem20cliz` - i.e. **every clean install** - hits this on `profiles`/`sessions`/`status`. The CLI appears fundamentally broken on first use. |
| B3 | repo-wide | **No CI whatsoever.** No `.github/workflows/` on `main`; nothing blocks a broken commit. | `.github/` absent on `main`; 0 registered workflows | There is no green check to show a buyer, no gate on contributions, and no evidence the product builds. This is *why* B1/B2 landed. |

### HIGH

| # | Surface | What is missing / broken | Evidence | Sales impact |
|---|---|---|---|---|
| H1 | `mcp_server_dir/` | **25 of 32 files fail to parse.** A mechanical bulk edit injected `from mcp.server import ...` / `import mcp_types as mt` lines *inside* module docstrings and at wrong indent. | `py_compile` across `mcp_server_dir/` -> **25/32 fail**; referenced as canonical by `CANONICAL.md:23`, `SITEMAP.md:348` | Described as a canonical tree but unusable by any walker. A technical evaluator who lints the repo sees it immediately. **Fix-and-complete, never remove.** |
| H2 | all three surfaces | **Test suites do not run on a clean machine.** `mem20controlz`: 3 test modules error at collection (`ModuleNotFoundError: mem20ops`) and `test_auth_app.py` yields **68 errors**. `mem20agentz`: **30 failed / 119 passed**; `mem20oreo` missing fails `test_oreo.py`, `test_oreditor.py`, `test_graphstore.py`. `mem20crewz`: fails without `aiohttp` because `pyproject.toml` declares `dependencies = []`. | Real `pytest` runs, this engagement | The strongest sales asset - "here are our tests" - is unavailable. Every surface also needs **undeclared** runtime deps (`pyyaml`, `aiohttp`, `httpx`, `fastapi`), so installs are not reproducible. |
| H3 | `mem20controlz` | **Tests cannot collect**: `tests/conftest.py` and the test modules import `mem20ops` (a sibling subsystem) not installed by `mem20controlz`'s own `pyproject.toml`. | `pytest tests` -> 3 collection errors; `from mem20ops import audit, runtime` | The control plane is the primary operational surface; its suite is red on import. |
| H4 | repo-wide (distribution) | **No desktop build exists anywhere.** No Tauri config, no Electron entry, no PyInstaller/pywebview spec, no `.desktop` file, no installer. | `find` for `tauri.conf*` / `electron*` / `*.spec` / `*.desktop` -> **0 results**; `desktop.py` renders **browser HTML**, not a native app | There is nothing a buyer can download and double-click. The desktop surface is a browser page with an office skin. |

### MEDIUM

| # | Surface | What is missing / broken | Evidence | Sales impact |
|---|---|---|---|---|
| M1 | git hygiene | **Generated output is tracked**: `build/` (47 files), `__pycache__/` (5 files). `.gitignore` lists them but they were committed anyway. | `git ls-files build __pycache__` | Bloat, noisy diffs, and stale copies of source that confuse anyone reading the tree. **Stop tracking** - do not delete the working tree. |
| M2 | repo-wide | **Subsystem packaging is incomplete**: 293 `mem20*z` dirs, only **151** carry a `pyproject.toml`; **142 are unpackaged**. | `ls -d mem20*z` vs `[ -f $d/pyproject.toml ]` | "293 subsystems" reads as breadth until a buyer tries to install one and finds no packaging. |
| M3 | docs | **Advertised capability counts drift from the tree.** README claims "326 subsystems, 632/875 capabilities ok, 101 degraded, 142 unpackaged" - numbers that no longer agree with the measured 293/151. `TODO.md` still heads a `mem30` workspace path. | `README.md` repository-layout section; `TODO.md:1` | Overstated/undersynced numbers are the fastest way to lose a technical buyer's trust. |
| M4 | `mem20crewz` | **Runtime dependencies undeclared.** `pyproject.toml` has `dependencies = []` yet `a2a.py:28` imports `yaml` and `a2a.py:254` imports `aiohttp`. | Failed suite -> `ModuleNotFoundError: No module named 'yaml'` / `'aiohttp'`; passes only after manual install | A clean `pip install mem20crewz` yields a framework that fails on first A2A call. |
| M5 | `mem20agentz` | **ORE-O integration is not installable.** 8 test failures trace to `ModuleNotFoundError: No module named 'mem20oreo'`; the package ships but is not on the path for its own consumer tests. | `pytest mem20agentz/tests` -> 8 x `mem20oreo` | The "NL -> graph -> runnable app" story is the most demo-able feature in the repo and is currently dark. **Complete the integration** - do not drop it. |
| M6 | `mem20agentz` | **`desktop.py` hardcodes absolute paths** at import time: `CREWZ_ROOT = "/opt/mem20/mem20crewz"`, `GAMEZ_ROOT = "/opt/mem20/mem20gamez"`. | `desktop.py:33-34` | Works only on the author's host. On a buyer's machine the office surface silently degrades. |

### LOW

| # | Surface | What is missing / broken | Evidence | Sales impact |
|---|---|---|---|---|
| L1 | `mem20agentz` | **Silent exception swallowing** in dashboard builders: `except Exception: ... = "<li>(sealed)</li>"`. A failure is rendered as an empty panel. | `gateway_web.py:215-218` | A degraded panel is indistinguishable from an empty one - exactly the quiet lie the repo's own honesty rules forbid. |
| L2 | `mem20crewz` | **`Brain` base methods raise bare `NotImplementedError`** (5 sites) and the class is not an `abc.ABC`, so a subclass that forgets a method fails at call time rather than instantiation. | `mem20crewz/neural.py:33,37,40,43,53` | Ergonomic paper cut for anyone extending the framework. |
| L3 | repo | **Dead/retired artifacts committed**: `memory.py.broken`, `backups/retired-units/searxng.service.bak`. | `find -name '*.broken' -o -name '*.bak'` | Cosmetic; **keep the artifacts**, record them rather than removing. |
| L4 | `mem20controlz` | `README.md` documents a **165-test suite**; the tree holds 4 test modules and 0 that collect without the sibling dep. | `mem20controlz/README.md` | Documentation promises a green suite that cannot be produced. |

---

## 3. Ranked summary

| Rank | Count | Items |
|---|---:|---|
| Blocker | 3 | B1 gateway_web syntax - B2 CLI NameError - B3 no CI |
| High | 4 | H1 mcp_server_dir 25/32 - H2 suites don't run + undeclared deps - H3 controlz collection - H4 no desktop build |
| Medium | 6 | M1 tracked build output - M2 142 unpackaged subsystems - M3 doc/count drift - M4 crewz deps - M5 mem20oreo dark - M6 hardcoded paths |
| Low | 4 | L1 silent excepts - L2 Brain ABC - L3 committed dead artifacts - L4 README test-count |

**Fix order that unblocks the most demo value per unit of work:** **B1 -> B2 -> B3 -> H2 -> H1 -> H4** - the first two restore the two shipped surfaces, the third installs the gate that stops regression, and H2/H1/H4 convert a repo into a product.

---

## 4. Demo-path hazards (what a live demo would actually hit)

1. `mem20agentz gateway serve` / office dashboard -> **`SyntaxError` at import** (B1).
2. `python -m mem20agentz profiles list` on a clean host -> **`NameError`** (B2).
3. `pytest` anywhere in the three surfaces -> red or collection error (H2).
4. `find` for a desktop binary -> **nothing** (H4).
5. "293 subsystems" -> 142 of them have no packaging (M2).

Each of these is closed by a tracked issue filed alongside this report; none requires removing a feature.

---

_Endpoints, live data and verdicts were gathered in a single reproducible session against `main`; each finding cites the exact file and command._
