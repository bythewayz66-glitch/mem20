# Absolute Truth 113

**Scope:** a full verification pass over `bythewayz66-glitch/mem20` — repository contents, documentation claims, the live MCP surface, every installable package in the tree, the five first-party SDKs, the published-artifact manifest, and the benchmark artifacts.

**Checkout:** `/opt/mem20`, branch `main`. Scan started at `109d06f6c757131bf2e41847bc352e8ae96b7f2c`; final verification was re-run at `b1b9ede7ccbfa8c2aa6b0470a01cee2239a94ad8`. `VERSION` 3.1.2 throughout.
**Date of run:** 2026-11-04.
**Method:** clone the repo, read the code and docs, run the server, run the installers, and compare every claim against a command that can be re-run. Each finding below is backed by a command and its output. Nothing in this file is copied from a prior report.

---

## 0. Post-scan changes (the repo moved during the pass)

The owner pushed six commits while this audit was running. This section records what changed, what it fixed, and what it left broken. **The live surface was 306 tools at scan start and is 311 tools at final verification**, so any sentence below that says 306 is either explicitly dated to `109d06f6` or is describing a document that is now stale.

| Commit | Message | Effect on this report |
|---|---|---|
| `ce36fd69` | Fix docs counts, version skew, architecture stub to match reality | `README.md`, `docs/01`, `docs/02`, `docs/INDEX`, `docs/README`, `docs/TOOL-DOMAINS` moved to **306/39**; `pyproject.toml` moved to 3.1.2; `docs/01-architecture.md` replaced with a 2.8 KB overview (fixes **#245**; partially fixes **#246**). |
| `d382d3f8` | Replace placeholder specs with real specifications | `specs/` grew from 299 B to 2,412 B and lost the literal “placeholder” markers. The content is still outline-level, not a real spec (partially fixes **#247**). |
| `dc4441ac` | Register temporal tools in MCP server | `mcp/server.py` now inherits/calls the temporal module; live `tools/list` rose **306 → 311** with `temporal_doctor`, `temporal_get`, `temporal_ingest`, `temporal_put`, `temporal_slices` (fixes **#244**). |
| `b5c7b45d` | Update diary | Documentation only. |
| `bc0a9a61` | Fix Godot SDK bridge syntax and improve lifecycle methods | 17 insertions / 5 deletions in `mem20-sdk-godot/addons/mem20/mem20_client.gd`. It **does** fix the generated-Python escaping (the emitted bridge now compiles), but it adds `await get_tree()` to a `RefCounted` class, so the addon now fails to parse and `Mem20Client.new()` returns no instance. **#254 is not fixed** — see §5.9. |
| `b1b9ede7` | Update diary | One line added to `DIARY.md`. The live surface was re-checked at this commit: **311**, extractor **311/39**, name sets identical. |

**Verification at `b5c7b45d`:** live `tools/list` = **311**, the extractor = **311 across 39 domains**, and the two name sets are identical (empty symmetric difference). `serverInfo.version` is still the empty string. Re-checked at `bc0a9a61` (Godot-only) and again at `b1b9ede7` (diary-only): **311** each time, `serverInfo.version` still empty, symmetric difference still empty.

**The fix created a new staleness:** the same commit that set the docs to 306 was followed by a commit that made the server 311, so the docs are now wrong by five. No Markdown file in the tree says `311 tools` or `311/39`.

**Issue closures during the pass.** At 06:48:30–06:48:41 UTC — six to seventeen minutes after the verification comments in this report were posted — the owner closed **#244, #245, #246, #247 and #248**. The repository total moved from 48 open / 76 closed to **43 open / 81 closed**. Three of those closures hold up on the evidence: #244 is genuinely fixed by `dc4441ac`, #245’s stub is genuinely replaced, and #247’s literal placeholders are genuinely gone (the content is still outline-level). Two do not: #246 still has no release notes for `v3.1.1`/`v3.1.2` and `CHANGELOG.md` still stops at 3.1.0, and **#248 — “docs advertise a tool count that is not the live one” — was closed while its core claim is still true**, because no Markdown file in the tree says `311` and seven still say `306`. §10 records the state of every issue at the end of the pass rather than trusting its status label.

**Uncommitted owner work at the end of the pass.** Five tracked files carried uncommitted modifications while this audit was finishing: `docs/gtm/claim-ledger-02-facts.md`, `docs/gtm/mem20-launch-copy.md`, `memory_engine/docs/EVIDENCE.md`, `memory_engine/docs/GAP-INVENTORY.md`, and `scripts/check_launch_gate.py`. I did not modify, revert, or commit any of them, and they are **not** part of the `b1b9ede7` snapshot this report grades. Two observations, offered because they are cheap to fix and easy to miss:

- `scripts/check_launch_gate.py` in the working tree sets `RETIRED_VERSIONS = ("v3.0.0", "3.1.2")`. That adds the **current** version to the list of versions that must not appear, so the gate now fails against its own tree: `[FAIL] version served page still carries retired version(s): '3.1.2' x2 (repo VERSION = 3.1.2)`.
- `docs/gtm/mem20-launch-copy.md` now reads `| Version 3.0.0 | pyproject.toml version = "3.1.2"; VERSION file |`, and `memory_engine/docs/GAP-INVENTORY.md` says `pyproject.toml declares version = "3.1.2" while VERSION says 3.1.2 — real drift, 2 releases behind`. Both sentences now contradict themselves after the 3.0.0 → 3.1.2 sweep.

---

## 1. Executive summary

The repository is real, large, and mostly functional, but its public claims about itself are not true. The headline facts:

| Claim surface | What the repo said at scan start | What is actually true at final verification |
|---|---|---|
| MCP tools | `README.md`: 256; `docs/TOOL-DOMAINS.md`: 270; `docs/05-*`: 268; SDKs: 270–272 | **311** on a live `tools/list` at the end of the pass (`b1b9ede7`; **306** at scan start). Docs were corrected to 306 just before the server reached 311, so they are once again five short. |
| MCP domains | 26 (45 md files), 27 (78 md files) | **39** (live list and extractor agree at the end of the pass) |
| Version | `VERSION` 3.1.2 | `pyproject.toml` now 3.1.2; `pip show` still **3.0.0** until reinstall; `CHANGELOG.md` still tops out at **3.1.0**; no release notes for 3.1.1/3.1.2 |
| Architecture doc | “System design, memory model, tool domains, deployment” | **fixed** at `ce36fd69` — 2.8 KB overview, no longer a stub |
| `specs/` | “canonical spec authority” | **partly fixed** — 2,412 B of outlines, no interfaces, schemas, or acceptance criteria |
| Benchmarks | “Nothing here was typed by hand”; adversarial 0.000 is “desired” | `render.py --check` **still refuses the artifact** (exit 3); the named per-query file **still does not exist** |
| Godot SDK | “First-class mem20 MCP client … health probes” | **still cannot make one tool call**. `bc0a9a61` fixed the bridge’s Python escaping but added `await get_tree()` to a `RefCounted` class, so the addon no longer parses (§5.9) |
| `published/MANIFEST.tsv` | integrity record for 128 files | **16 size mismatches, 32 sha256 mismatches, 43 files unlisted** (unchanged) |

Thirteen new issues were filed for the defects that were not already tracked: **#244–#255** and **#257**. (#256 is a separate summary issue opened by the same account while this pass was running; it is not one of the evidence issues below.) Five of the thirteen were **closed** by the owner before the pass ended — #244, #245, #246, #247, #248 — but only the first two were fully resolved; see §0 and §10.

What is genuinely working: the Python server boots, completes a JSON-RPC handshake, registers 311 tools at the end of the pass, and answers `memory_status`; the toolchain installs; the Ruby, Perl and C++ SDKs build and pass their own suites; the TypeScript SDK builds; the MCP server is attached to OpenCode and reports 311 tools there too.

---

## 2. Repository identity and size

```console
$ git rev-parse HEAD                     # at scan start
109d06f6c757131bf2e41847bc352e8ae96b7f2c
$ git rev-parse HEAD                     # at final verification (after owner commits)
b1b9ede7ccbfa8c2aa6b0470a01cee2239a94ad8
$ git branch --show-current
main
$ cat VERSION
3.1.2
$ git status --short        # at scan start: (no output); at the end of the pass:
 M docs/gtm/claim-ledger-02-facts.md
 M docs/gtm/mem20-launch-copy.md
 M memory_engine/docs/EVIDENCE.md
 M memory_engine/docs/GAP-INVENTORY.md
 M scripts/check_launch_gate.py
?? AbsoluteTruth113.md      # this report
$ git tag --sort=-v:refname | head -3
v3.1.2
v3.1.1
v3.1.0
```

| Metric | Value | Command |
|---|---:|---|
| Markdown files | 1,046 (4.64 MB) | `find . -name '*.md' -not -path './.venv/*' -not -path './.git/*'` |
| Subsystems (sitemap) | 340 | `.sitemap/sitemap.json` → `totals.subsystems` |
| Source files (sitemap) | 8,497 | `.sitemap/sitemap.json` → `totals.files` |
| Code lines (sitemap) | 384,249 | `.sitemap/sitemap.json` → `totals.lines`/`code_lines` |
| Package directories | 298 | `ls -d mem20*/` |
| `pyproject.toml` (depth ≤ 2) | 296 | `find . -maxdepth 2 -name pyproject.toml` |
| Working-tree size (excl. `.venv`, `.git`) | 177 MB | `du -sh` |
| Remote branches | 89 | `git branch -r \| wc -l` |
| Issues (at scan start) | 110 = 34 open + 76 closed | `gh issue list --state all` |
| Issues (after this pass filed 13 + one summary issue) | 124 = 43 open + 81 closed at the end of the pass | same |
| Pull requests | 133 | `gh pr list --state all` |

The sitemap says 340 subsystems but only 298 `mem20*/` directories exist, because the sitemap counts organs, services and “other” categories (308 / 16 / 16), not only directories.

---

## 3. The live MCP surface vs. the documented surface

### 3.1 Live server

A real JSON-RPC session against `mcp/mcp_server.py` at scan start, and again at final verification:

```console
# scan start, 109d06f6
$ .venv/bin/python /tmp/opencode/handshake.py
init_seconds 41.3
serverInfo {'name': 'mem20-mcp', 'version': ''}
tools 306

# final verification, b5c7b45d
$ .venv/bin/python - <<'PY'   # initialize, then tools/list in one process
...
{"jsonrpc":"2.0","id":1,"result":{"capabilities":{"tools":{"listChanged":false}},
  "protocolVersion":"2025-06-18","serverInfo":{"name":"mem20-mcp","version":""}}}
PY
tools 311
```

- **311 tools** in `tools/list` at `b5c7b45d` (306 at `109d06f6`).
- `serverInfo.version` is the **empty string** at both commits — the server does not report the version it is.
- Startup is **41.3 s** on this machine, which is why the OpenCode MCP entry needs an explicit startup timeout (`mcp.timeout.startup = 180000`; the default is shorter).
- The extractor reports **311 tools across 39 domains** at `b5c7b45d`, and the live and catalog name sets are **identical** (empty symmetric difference).

### 3.2 What the docs claim

```console
# final verification, b5c7b45d (AbsoluteTruth113.md excluded from its own sweep)
$ for pat in "270 tools" "27 domains" "268 tools" "26 domains" "256 tools" \
             "272 tools" "306 tools" "39 domains" "311 tools"; do
    printf '%-12s ' "$pat"
    grep -rl "$pat" --include='*.md' . | grep -v '.venv' | grep -v AbsoluteTruth113 | wc -l
  done
270 tools    78
27 domains   75
268 tools    25
26 domains   45
256 tools    0
272 tools   11
306 tools    7
39 domains   5
311 tools    0
```

At scan start (`109d06f6`) the same sweep gave 82 / 78 / 25 / 45 / 1 / 11 / **0** / **0**. The owner’s `ce36fd69` commit moved seven files to **306** and five to **39**, which is a real improvement over zero. It did not make the docs true: **no Markdown file says `311`**, and several files still contradict themselves internally.

| File | Claim at final verification | Verdict |
|---|---|---|
| `README.md:41` | `MCP tools \| **306** \| grep -rho "Tool(" mcp/tools/*.py \| wc -l` | Number is stale (live 311); **the measuring command yields 255**, so it cannot support any count. A value pasted next to an unrelated measurement is still an unverified value. |
| `README.md:212` | `# 44 modules, 306 tools` | Module count is correct (`ls mcp/tools/*.py` = 44); tool count is stale by 5. |
| `docs/TOOL-DOMAINS.md:1` | “The 27 MCP domains — authoritative mapping” | Title still says 27; live is 39. |
| `docs/TOOL-DOMAINS.md:3` | “**306 tools across 39 domains.** … generated from the registry itself … cannot drift silently.” | Drifted again. Its own derivation commands now yield **322 sites / 320 distinct / 46 groups**, not the 271 / 270 / 28 written in the body. |
| `docs/TOOL-DOMAINS.md:20-31` | “28 groups − 1 A2A layer = **27 domains** … **270** distinct tools”; then a note claiming “the server exposes **306** tools while the source contains **271** assignments” | Three mutually incompatible counts in one file (27/270, 39/306, 271 sites), none of which is the live 39/311. |
| `docs/02-tools-reference.md:4` | “**306 tools across 39 domains** … agreeing with `README.md`” | Stale by 5; the agreement is with a stale README, not the server. |
| `docs/05-complete-tools-reference.md:3`, `:1350`, `:3181`, `:3324` | “268 tools across 26 domains” | Stale, untouched by the owner’s commit. |
| `toolchest/README.md:10` | “`Mem20MCPServer` (268 real tools)” | Stale; its sibling `toolchest/inventory.json` says `mcp: 306`, which is itself now five behind. |
| `docs/troubleshooting-mcp-server-startup.md:404-518` | `"tools_registered": 270`, `TOOL_COUNT: 270`, “registers **270**” | Stale; the file tells a debugger that 270 is the healthy target. |
| `.github/workflows/mcp-verify.yml:48` | `MEM20_EXPECTED_TOOLS: "306"` | Stale; CI would fail against a 311-tool server. |
| `.github/workflows/finance-model-drift.yml:83` | asserts `(tools, domains) == (270, 27)` | Stale. |
| `verify_mcp.py:5` | default `EXPECTED = 270` | Stale. |

### 3.3 The extractor and the server now agree — but only after the owner fixed the gap

```console
# scan start, 109d06f6
$ .venv/bin/python web/scripts/extract-tools.py --root . --out /tmp/opencode/tools-recheck.json
57 files -> 311 tools across 39 domains

# final verification, b5c7b45d
$ .venv/bin/python web/scripts/extract-tools.py --root . --out /tmp/opencode/tools-recheck2.json
57 files -> 311 tools across 39 domains
```

At scan start the extractor said **311/39** and the live server said **306/39**. The delta was exactly the five `temporal_*` tools. `dc4441ac` added `register_temporal_tools()` to `mcp/server.py`; at `b5c7b45d` the live and catalog name sets are identical and both are **311**. Issue **#244 is fixed**.

The extractor still has a design hazard worth recording: its wiring gate treats any module with **no** `*Mixin` class as wired, which is why the five temporal tools were counted before anything registered them. The same gate currently reports **19 declared-but-unwired tools** across `gateway_*`, `lattice_*`, `memory_engine_*`, and `stream_*`. Those 19 are excluded from the extractor’s 311, so the count is correct today, but the gate would silently absorb another no-mixin module in future.

### 3.4 Three CI checks, three different surfaces

- `.github/workflows/mcp-verify.yml:48` → `MEM20_EXPECTED_TOOLS: "306"` (now stale; live is 311)
- `.github/workflows/finance-model-drift.yml:83` → asserts `(tools, domains) == (270, 27)`
- `verify_mcp.py:5` → `EXPECTED = int(os.environ.get("MEM20_EXPECTED_TOOLS", "270"))`

The owner moved one check closer to reality, but the tree still has three “authoritative” counts and none of them is the live 311. This is issue **#249**.

---

## 4. Installation state

The full suite was installed into `/opt/mem20/.venv` (created with `--system-site-packages` so the system `torch` 2.15.0+cu132 and `numpy` 2.5.4 are reused rather than re-downloaded).

### 4.1 System toolchain

| Tool | Version | Evidence |
|---|---|---|
| OS / arch | Linux 6.1.145, `aarch64` | `uname -a` |
| Python | 3.13.5 | `python3 --version` |
| torch | 2.15.0+cu132 | `import torch` |
| numpy | 2.5.4 | `import numpy` |
| Node | v20.19.2 | `node --version` |
| npm | 9.2.0 | `npm --version` |
| Ruby | 3.3.8 | `ruby --version` |
| Perl | 5.40.1 | `perl -v` |
| CMake | 3.31.6 | `cmake --version` |
| Godot | 4.7.2.stable.official.ed1daf0bf | `godot4 --version` |
| gh | 2.46.0 | `gh --version` |
| git | 2.47.3 | `git --version` |

### 4.2 Python packages

All 296 packages with a `pyproject.toml` were installed editable with `--no-deps --no-build-isolation` (dependencies were installed once, up front, to avoid 296 resolver passes). Only `Pillow`, `openai` and `watchdog` were missing externally; everything else resolved from the system environment.

**Result:** every package installs. The venv holds **404 distributions**, of which **296 are editable installs** — exactly one per `pyproject.toml` in the tree.

```console
$ .venv/bin/python -c "import importlib.metadata as m; ds=list(m.distributions()); \
  print('total', len(ds), 'editable', sum(1 for d in ds if 'editable' in (d.read_text('direct_url.json') or '')))"
total 404 editable 296
```

The 108 non-editable distributions are the shared dependencies (`mcp`, `pydantic`, `anyio`, `faiss-cpu`, `sentence-transformers`, `Pillow`, `openai`, `watchdog`, `pytest`, …) plus tooling. Installs were done in three batches of 61 packages to keep a single pip resolution per batch; each batch took roughly 11–16 minutes on this ARM host.

The installed metadata still reports **3.0.0** because the editable install predates `ce36fd69`’s bump of `pyproject.toml` to 3.1.2; a reinstall would report 3.1.2. The repo’s version sources now agree at 3.1.2 — see issue #246 for the remaining release-notes gap.

**Import check:** every editable package was then imported from its own root in a clean subprocess (`PYTHONPATH=<pkg root>:<pkg root>/src:<repo>`, 45 s timeout). Results are reported in §4.4.

### 4.3 The five SDKs

| SDK | Location | Version | Built / installed | Tests | Live round-trip |
|---|---|---|---|---|---|
| Ruby | `mem20-sdk-ruby/` | 0.2.0 | `gem list mem20-sdk` → `0.2.0` | own suite passes | against a 272-tool surface |
| Perl | `sdk/perl/` | 0.2.0 | `make install`; `Mem20::Version` loads | 103 tests pass | `verify_surface` expects 270 |
| TypeScript | `mem20-sdk-typescript/` | 0.1.0 | `dist/` built, `npm link` resolves | **not run** (see §8) | server baseline 3.0.0 |
| C++ | `sdk/cpp/` | 0.1.0 | `libmem20_sdk.a` in `/usr/local/lib`, headers in `/usr/local/include/mem20` | `ctest` 4/4 pass — but `live_surface` is skipped | `surface_docs` checks hardcoded 272 |
| Godot | `mem20-sdk-godot/` | 0.1.0 | addon directory copies into a project | no tests | **does not compile** at HEAD (`b1b9ede7`) — `get_tree()` on a `RefCounted` (§5.9) |

All five SDKs pin tool counts and/or a server baseline that no longer matches the live 311/39 surface. This is issue **#255**.

### 4.4 Import check

Every editable package was imported from its own root in a clean subprocess. The first pass used a 45 s timeout and four workers:

```console
editable dists 296
import jobs 315 roots 296
{"OK": 298, "FAIL": 7, "TIMEOUT": 10}
```

The 10 timeouts were re-run with a 150 s timeout: **5 import OK** and **5 still failed**. Every genuine failure is in one package — `mem20_mcp`, the package that forwards to the canonical MCP tree. (`mem20_mcp` itself imports; the failures are its forwarding submodules, which call `canonical_root()` at import time.) The affected submodules are:

| Root | Modules that fail | Error |
|---|---|---|
| `mem20_mcp` | `server`, `mcp_server`, `memory_tools`, `cognitive_tools`, `roadmap_tools`, `blender_bridge`, `health`, `install_tracker` | `ImportError: mem20_mcp refused the canonical tree at /opt/mem20/mcp: stub_body: 1 stub body/bodies … first at mcp/tools/integration_tools.py:87 (noop-body)` |

All 296 package roots import, including `mem20_mcp` itself; the eight submodules above do not. The `__init__` row in the raw checker output is an artifact of importing `__init__` as a top-level module, not a package failure. The `mem20_mcp` refusal is a real defect, not an environment artifact: the canonical tree at the documented path fails the package’s own stub gate because `integration_tools.py:87-89` ships a `pass`-body scaffold. This is issue **#257**.

**Caveat on how the check was run.** The checker put the repo root on `PYTHONPATH`, which exposed a separate, standard Python footgun: from `/opt/mem20`, `import mem20kanbanz` resolves the **outer** `mem20kanbanz/` directory as an empty namespace package instead of the installed package one level down. With only the package root on `PYTHONPATH` (the normal installed-import case), both `mem20botz` and `mem20messenger` import correctly. So the initial `mem20botz`/`mem20messenger` failures were an artifact of running from the repo root, not broken packages; the §4.2 install state is sound. It is still worth knowing that `cd /opt/mem20 && python -c "import mem20botz"` gets the namespace, so run imports from the package directory or anywhere outside the repo root.

---

## 5. Verified defects (new issues #244–#255, #257)

Each item below is a defect that was **not** already covered by the 34 open issues at the start of the run. All thirteen were filed as new GitHub issues. The owner fixed or partly fixed #244, #245, #246 and #247 during the pass; each item says so explicitly.

### 5.1 #244 — Five `temporal_*` tools counted as wired but never registered — **FIXED in `dc4441ac`, closed 06:48:30**

At scan start:

- Live `tools/list` = 306; extractor = 311; delta = the five `temporal_*` names.
- `mcp/server.py` had no temporal base class and no `install()` call.
- `temporal_tools.py`’s docstring asserted the opposite.
- The subsystem test called `install(FakeServer())`, so it proved the installer worked, not that it ran.

At final verification (`b5c7b45d`) `mcp/server.py:181` calls `self.register_temporal_tools()`, live `tools/list` is **311**, and the live and catalog name sets are identical. The issue remains open on GitHub but the defect is resolved in `main`.

### 5.2 #245 — `docs/01-architecture.md` was a 142-byte stub — **FIXED in `ce36fd69`, closed 06:48:32**

At scan start:

```console
$ wc -l docs/01-architecture.md
7 docs/01-architecture.md
$ stat -c '%s bytes' docs/01-architecture.md
142 bytes
$ tail -1 docs/01-architecture.md
## What is mem20?
```

`docs/README.md:12` linked it as “System design, memory model, tool domains, deployment”, with no body. At final verification the file is **2,841 bytes** and describes the memory engine, MCP server, subsystem layer, epistemic model, data flow, and design principles. It correctly states 39 domains but its tool count (306) is stale by five. The issue remains open on GitHub but the stub is gone.

### 5.3 #246 — Version skew — **PARTIALLY FIXED in `ce36fd69`, closed 06:48:35 with the release-notes gap still open**

| Source | At scan start | At final verification |
|---|---|---|
| `VERSION` | 3.1.2 | 3.1.2 |
| root `pyproject.toml` | 3.0.0 | **3.1.2** |
| `pip show mem20` | 3.0.0 | 3.0.0 (not reinstalled after the bump) |
| `docs/01-architecture.md` header | 3.0.0 | **3.1.2** |
| `docs/releases/` | only `v3.1.0.md` + index | **unchanged** |
| `CHANGELOG.md` top | `[3.1.0] — 2026-10-31` | **unchanged** |

Tags `v3.1.1` and `v3.1.2` exist and `VERSION` was cut by `48c241a1`, but there are still no release notes for either, and the changelog still stops at 3.1.0. The installed-metadata number is an environment artifact that a reinstall would fix; the missing release notes are a repo defect.

### 5.4 #247 — `specs/` was all placeholders — **PARTIALLY FIXED in `d382d3f8`, closed 06:48:38**

At scan start the five files totalled **299 bytes** and contained literal placeholder text (`# Production package placeholder — replace with real prod.md`, `# VR Office swarm placeholder`, …). At final verification they total **2,412 bytes**:

| File | Size | What it now contains |
|---|---:|---|
| `specs/README.md` | 278 B | A one-paragraph statement that the directory is authoritative, plus a `MEM20_SPEC_SOURCE` override. |
| `specs/prod.md` | 615 B | Six bullet requirements and five deployment bullets — no interfaces, no acceptance tests, no failure modes. |
| `specs/desktop/1/README.md` | 317 B | Five component bullets for a VR office swarm. |
| `specs/desktop/2/README.md` | 338 B | Five component bullets for an MMORPG swarm. |
| `specs/game-maker/20_Essential_Game_Maker_Pipelines.md` | 864 B | Ten one-line pipeline names. |

The literal “placeholder” markers are gone, so the most embarrassing form of the defect is fixed. The files are still outlines: none defines a data format, an API, a compatibility rule, or a test that would tell an implementer whether they had satisfied it. Calling this directory “the canonical spec authority” is still a stretch.

### 5.5 #248 — Tool/domain counts are stale — **closed 06:48:41 while still true**

Covered in §3.2. The owner corrected seven files to 306/39, but the server reached 311 in the next commit, so the new number is already five short, and `docs/TOOL-DOMAINS.md` still contains the old 27/270 derivation in its body. Closed issues #6 and #81 reported the same class of drift at 257/26, so this is a regression that has now happened at least three times. The core problem is structural: the numbers are edited by hand in dozens of files rather than generated once and consumed everywhere.

The issue was closed at 06:48:41, after this report’s verification comment was posted. Re-checked immediately after the close, at `bc0a9a61`: **7 Markdown files still say “306 tools”, 5 say “39 domains”, and 0 say “311”** (`AbsoluteTruth113.md` excluded). `README.md:41` still pairs `306` with a command that returns 255. The defect the issue describes is present at the moment it was closed.

### 5.6 #249 — CI asserts two different surfaces

Covered in §3.4.

### 5.7 #250 — `published/MANIFEST.tsv` is stale

```console
$ wc -l published/MANIFEST.tsv
129 published/MANIFEST.tsv          # 1 header + 128 rows
$ find published -type f | wc -l
171
$ # recompute
size mismatch 16
sha256 mismatch 32
```

Examples:

| Path | Manifest bytes | Actual bytes |
|---|---:|---:|
| `published/README.md` | 4,878 | 4,977 |
| `.../presentations/mem20_repo_v3/slide_01.html` | 5,951 | 3,051 |
| `.../documents/mem20-content-publish/index.html` | 11,021 | 7,170 |
| `.../documents/mem20-launch-copy-set/index.html` | 15,249 | 12,323 |

Many hash mismatches have identical sizes (content changed in place, manifest never regenerated). 43 files in `published/` are absent from the manifest entirely.

### 5.8 #251 — Benchmark report is not reproducible

1. `render.py --check` **refuses** the committed artifact:

   ```console
   $ python3 docs/benchmarks/render.py --check
   artifact failed self-verification:
     - artifact has no per_query rows; cannot verify aggregates
   Refusing to publish. Fix the artifact or the run, not this table.
   EXIT=3
   ```

2. `latest.json` says the rows are committed:

   ```json
   "per_query_note": "1530 per-query rows are committed verbatim in per-query.jsonl.gz next to this file, not omitted."
   ```

   `benchmarks/results/` contains only `latest.json` and `latest.md`. `per-query.jsonl.gz` is not present, not in `git ls-files`, and not ignored.

3. The README’s “generated” tables do not match `latest.json`:

   | Row | README | `latest.json` |
   |---|---:|---:|
   | aggregate `graph` n | 2 | 30 |
   | aggregate `hybrid` n | 13 | 250 |
   | `hybrid` adversarial n | 3 | 60 |
   | `hybrid` adversarial hit rate | 0.000 | 0.1667 |

4. The README still calls adversarial `0.000` the “**desired** result”, while `docs/benchmarks/results-v2.md:9-22` documents that exact 0.000 as a bug: the probes were answer-free and `bench.py` hardcoded `if q.kind == "adversarial": hit, rank = False, None`.

### 5.9 #254 — Godot SDK cannot make a tool call — **regressed by `bc0a9a61`**

Validated with Godot 4.7.2 on a minimal project (`/tmp/opencode/godot-proj`, addon copied fresh from the checkout before each run).

**At `b5c7b45d` the failure was in the generated bridge.** `_stdio_roundtrip()` wrote `"\n"` inside a GDScript triple-quoted string, so GDScript turned it into a real newline and the emitted Python would not parse:

```console
INIT_RAW={"error":"bridge failed","exit_code":1,"output":"... line 10
    init = json.dumps({...})+\"
SyntaxError: unterminated string literal ..."}
START_RESULT=0 PID=-1 INITIALIZED=false
HEALTH=<null>
READY=<null>
TOOL_RESULT={"error":"session failed"}
```

**`bc0a9a61` genuinely fixes that half.** The template now writes `+ "\\n"`, and `bc0a9a61` is the commit that added the extra backslash. To test it in isolation I copied the heredoc into a standalone GDScript, had Godot write the generated file, and compiled it:

```console
$ godot4 --headless --script /tmp/opencode/godot-bridge/extract.gd
WROTE bytes=889
$ python3 -m py_compile /tmp/opencode/godot-bridge/generated_bridge.py
PY_COMPILE_OK
```

**But the same commit introduces a parse error that stops the addon loading at all.** It adds `await get_tree().create_timer(0.1).timeout` at line 201, inside a class declared `extends RefCounted` (line 2). `RefCounted` has no `get_tree()`:

```console
$ godot4 --headless --path /tmp/opencode/godot-proj
SCRIPT ERROR: Parse Error: Function "get_tree()" not found in base self.
          at: GDScript::reload (res://addons/mem20/mem20_client.gd:201)
SCRIPT ERROR: Compile Error: Failed to compile depended scripts.
          at: GDScript::reload (res://validate.gd:0)
ERROR: Failed to load script "res://validate.gd" with error "Compilation failed".
SCRIPT ERROR: Invalid call. Nonexistent function 'new' in base 'GDScript'.
          at: _ready (res://validate.gd:4)
EXIT=124   # the scene never quits, so the 150 s timeout kills it
```

So the client that previously loaded and failed at the bridge now fails to load. `Mem20Client.new()` returns a base `GDScript`, meaning no instance at all.

**Two defects from the original report are untouched:**

1. **`start()` still spawns nothing.** Lines 36–44 build an `env` array, set `_initialized = false`, and `return OK`. `env` is discarded. `close()` (line 106) is a no-op because `_pid` is never set above `-1`.
2. **`server_command` is still ignored.** `_server_cmd` is assigned in `configure()` at line 24 and **never read again**; the embedded Python hardcodes `cmd = ["python3", "mcp/mcp_server.py"]` (line 147) and the host hardcodes `OS.execute("python3", …)` (line 170). A game cannot point the client at a virtualenv interpreter or a different server path, which is exactly what this host needs (`.venv/bin/python`, not `python3`).

There are no tests in `mem20-sdk-godot/`, which is why both a bridge-escaping bug and a base-class mismatch reached `main`.

**Net:** the issue is still valid, and the fix commit made the load failure worse while fixing the bridge. It is a two-line fix (`Engine.get_main_loop()` instead of `get_tree()`, plus routing `_server_cmd` into the bridge), but that is the maintainer’s call.

### 5.10 #252 — `memory_status` reports `OK` for a missing file

```console
$ ls -l /opt/mem20/MEMORY.md
ls: cannot access '/opt/mem20/MEMORY.md': No such file or directory
$ MEM20_STORE_PATH=/tmp/opencode/memtest_store .venv/bin/python -c "...; print(memory.status())"
ledger events : 0
deep entries  : 0
MEMORY.md     : 0/2200 chars OK
USER.md       : 0/1375 chars OK
last event    : none
```

`status()` reads `""` when the file is absent and only checks `len <= cap`, so absence is reported as health. The live MCP tool returns the same string.

### 5.11 #253 — Perl SDK doc says `epistemic_status` is not enforced; the server enforces it

`docs/sdk/perl-release-2026-11-01.md:166-168`:

> **`epistemic_status` is not enforced server-side.** `memory_store {}` silently stores an empty fact…

`mcp/memory_tools.py:921-925` returns an explicit error when the argument is missing, and the schema at line 356 marks it `"required": ["content", "epistemic_status"]`.

### 5.12 #255 — SDK surface constants are stale

| SDK | Constant(s) | Source |
|---|---|---|
| Ruby | `DOMAIN_COUNT = 27`, `DOMAIN_TOOLS = 270`, `TOOL_COUNT = 272`, hard-asserted at `surface.rb:51` | `lib/mem20/surface.rb:37-51` |
| Perl | `$SURFACE_TOOL_COUNT = 270`, `$SERVER_VERSION = '3.0.0'` | `lib/Mem20/Version.pm:10,32` |
| C++ | `kToolCount = 272`, `kDomainCount = 27`, `kServerVersion = 3.1.0` | `include/mem20/surface.hpp:63-75` |
| TypeScript | `SERVER_VERSION = '3.0.0'` | `src/version.ts:4` |
| Godot | server baseline 3.0.0 | `README.md:8` |

Why the tests stay green:

- Ruby’s assertion compares the constant to itself.
- C++ `ctest` 4/4 passes, but `surface_docs` validates the docs against the same `272`; `live_surface` (the only test that would talk to the server) is **skipped** by default, and the C++ SDK has no CI job.
- Perl’s `verify_surface` does compare live `tools/list` to 270, so it reports a mismatch on today’s server.

### 5.13 #257 — `mem20_mcp` refuses the canonical tree because of a `pass`-body scaffold

`mem20_mcp` is the package that forwards to `/opt/mem20/mcp` and refuses a stale or stubbed tree. On the canonical path it refuses the tree:

```console
$ cd /tmp && /opt/mem20/.venv/bin/python -c "import mem20_mcp; mem20_mcp.canonical_root()"
ImportError: mem20_mcp refused the canonical tree at /opt/mem20/mcp:
  stub_body: 1 stub body/bodies under /opt/mem20/mcp/tools,
  first at /opt/mem20/mcp/tools/integration_tools.py:87 (noop-body)
```

The offending code:

```python
    def register_integration_template(self):
        """Scaffold: registers no tools. Implement a real optional integration in its own module."""
        pass
```

Nothing calls it, so its only runtime effect is to break the loader. As a result, eight forwarding modules fail to import (`server`, `mcp_server`, `memory_tools`, `cognitive_tools`, `roadmap_tools`, `blender_bridge`, `health`, `install_tracker`). This is distinct from #171, which was about the canonical root being hardcoded on a non-`/opt/mem20` checkout.

---

## 6. Claims that hold up

Not everything is wrong, and the report should say so:

- The server **does** boot from this checkout after install and complete the MCP handshake (`initialize` → `tools/list`).
- It **does** expose 311 tools at `b5c7b45d` (306 at `109d06f6`), and the count is stable across runs.
- `memory_store` / `memory_recall` work; the store persists to `MEM20_STORE_PATH`.
- The Python packages install editable without build isolation: 296 editable distributions, one per `pyproject.toml`, and **all 296 package roots import**. Eight forwarding submodules of `mem20_mcp` fail on a specific `pass` scaffold that can be deleted (§4.4, #257).
- Ruby, Perl and TypeScript SDKs build; the Perl suite passes 103 tests; the C++ library and headers install and 4/4 tests pass.
- The MCP server is attached to OpenCode (`/root/.config/opencode/opencode.json`) and `opencode mcp list` shows `✓ mem20 connected`. After restoring the startup timeout (`mcp.timeout.startup = 180000`; the CLI `add` command had dropped it) and reconnecting, the Code Mode catalog reports **311** tools, matching the server. The config uses `mcp.servers.mem20` with command `/opt/mem20/.venv/bin/mem20-mcp` and `MEM20_STORE_PATH=/opt/mem20/store`.
- The contamination invariant (`simulated` content never reaches grounded indexes) is implemented as a separate store partition in `memory_engine/memory.py`, not just documented.
- `toolchest/inventory.json`’s MCP count (306) matched the server at scan start but is now stale by five, even though its sibling README says 268.

---

## 7. Claims that are false or unverifiable

| Claim | Verdict |
|---|---|
| “270 tools across 27 domains” (78 + 75 md files at final) | **False.** 311 live at `b5c7b45d` (306 at scan start). |
| “268 tools across 26 domains” (`docs/05-*`) | **False.** |
| “MCP tools: 306” (`README.md:41`, labelled “Verified value”) | **False** (live 311), and the command printed beside it (`grep -rho "Tool(" … \| wc -l`) returns **255**, so it never measured the stated number. |
| “272 tools” (Ruby, C++) | **False.** |
| “The 27 MCP domains — authoritative mapping … cannot drift silently” | **False.** It has drifted, and its own body still says 27/270 while its header says 306/39. |
| “docs/01-architecture.md: system design, memory model, tool domains, deployment” | **Fixed at `ce36fd69`.** The 142-byte stub is now a 2,841-byte overview. |
| “`specs/` … canonical copies of fixed inputs” | **Partly fixed.** The literal placeholders are gone, but the files are still outlines, not specifications. |
| “MCP tools: 306” / “306 tools across 39 domains” in the docs corrected by `ce36fd69` | **False at final verification.** The server reached 311 in `dc4441ac`; no Markdown file says 311. |
| “Every figure below is rendered from a committed artifact … nothing is estimated” | **False.** `render.py --check` exits 3 and the tables show a different run’s numbers. |
| “1530 per-query rows are committed verbatim in per-query.jsonl.gz” | **False.** The file does not exist. |
| “Adversarial 0.000 is the desired result” | **Contradicted** by the repo’s own `results-v2.md`. |
| “`epistemic_status` is not enforced server-side” | **False.** The handler rejects it. |
| Godot “same surface as the Ruby / TypeScript / Perl clients … health probes” | **False.** No call works. |
| `published/MANIFEST.tsv` integrity | **False.** 32 hash mismatches, 16 size mismatches, 43 unlisted files. |
| `memory_status` “OK” | **False** when the file is missing. |
| `mem20_mcp` forwards to the canonical tree | **False.** It refuses the canonical tree because of a `pass` scaffold in it (#257). |

---

## 8. Limitations and what was not verified

Honesty about coverage matters more than a longer green list.

- **Not every test suite in the monorepo was run.** The install check (§4.4) verifies that packages import; it does not run each package’s pytest suite. Existing issues #203–#229 already track package-level conformance failures.
- **`toolchest refresh` did not complete after the full install.** Its subprocess that instantiates `Mem20MCPServer` has a 120 s timeout, and a direct instantiation of the same object took **76 s** on this host (41 s for a bare `tools/list`). Under load the refresh exceeded 120 s and wrote nothing. The checked-in `toolchest/inventory.json` (mcp 306 / cli 122 / subsystem 297 / total 725) was not regenerated by this pass; the earlier fresh run on this host produced mcp 306 / cli 59 / subsystem 297 / total 662. The MCP number matched the server at scan start but is now stale by five; the CLI and total counts are host-dependent and were not independently reconciled.
- **npm/jest for the TypeScript SDK did not run.** A full `npm install` fails in this environment with `ENOENT … rename …/_cacache/tmp/… -> content-v2/…` on the jest/babel tree. `typescript` and `@types/node` were installed into `/tmp/opencode/tsdeps` and copied in, which is enough to build `dist/`, but not enough to run jest. Treat the TypeScript SDK as “builds”, not “tested”.
- **Godot was run headless on 4.7.2 only.** The addon may behave differently in an exported desktop build, but a GDScript parse error and a missing base-class method are host-independent: `RefCounted` has no `get_tree()` in every Godot 4 build.
- **No legal review exists.** `docs/use-cases/LEGAL-REVIEW-REQUEST.md` is still a request; government and clinical production use is explicitly unauthorised. Nothing in this report changes that.
- **GitHub Pages sites were inspected, not exhaustively crawled.** The published-artifact findings come from the checked-in `published/` tree and its manifest, not from live HTTP fetches of every page.
- **The live count moved during the pass.** It was 306 at `109d06f6`, 306 when the owner corrected the docs in `ce36fd69`, and 311 after `dc4441ac`. The report’s final number is 311 at `b1b9ede7`. A future merge can change it; the structural point is that no document in the tree is generated from the server at build time, so the docs trail the code by however many commits it takes someone to notice.
- **Startup time is machine-specific.** 41.3 s here; the timeout is configured at 120 s to leave headroom.

---

## 9. Reproducing this report

```bash
# 1. Clone and identify
git clone https://github.com/bythewayz66-glitch/mem20.git /opt/mem20
cd /opt/mem20
git rev-parse HEAD && cat VERSION

# 2. Environment
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .

# 3. Every package (editable, no resolver churn)
find . -maxdepth 2 -name pyproject.toml -not -path './.venv/*' \
  | xargs -n1 dirname | sort -u > /tmp/pkgs.txt
# install in batches of ~60 with:
#   .venv/bin/pip install --no-deps --no-build-isolation -e ./<pkg>

# 4. Live MCP surface (initialize, then tools/list, in one process)
.venv/bin/python - <<'PY'
import json, subprocess, sys
p = subprocess.Popen([sys.executable, "mcp/mcp_server.py"],
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
def send(o):
    p.stdin.write(json.dumps(o) + "\n"); p.stdin.flush()
send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
      "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                 "clientInfo": {"name": "audit", "version": "1"}}})
print(p.stdout.readline().strip())
send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
tools = json.loads(p.stdout.readline())["result"]["tools"]
print("tools", len(tools))
p.kill()
PY

# 5. Catalog vs live
.venv/bin/python web/scripts/extract-tools.py --root . --out /tmp/tools.json

# 6. Doc drift
for pat in "270 tools" "27 domains" "268 tools" "26 domains" "306 tools" "39 domains" "311 tools"; do
  printf '%-12s ' "$pat"; grep -rl "$pat" --include='*.md' . | grep -v '.venv' | wc -l
done

# 7. Manifest and benchmarks
python3 - <<'PY'
import csv, os, hashlib
rows = list(csv.reader(open('published/MANIFEST.tsv'), delimiter='\t'))
for p, size, digest in (r for r in rows[1:] if len(r) >= 3):
    if not os.path.isfile(p): continue
    if str(os.path.getsize(p)) != size: print('SIZE', p)
    if hashlib.sha256(open(p,'rb').read()).hexdigest() != digest: print('SHA', p)
PY
python3 docs/benchmarks/render.py --check; echo "exit=$?"

# 8. Godot client (§5.9)
mkdir -p /tmp/godot-proj/addons
cp -r mem20-sdk-godot/addons/mem20 /tmp/godot-proj/addons/mem20
printf 'config_version=5\n\n[application]\nconfig/name="mem20 check"\nconfig/features=PackedStringArray("4.7")\nrun/main_scene="res://main.tscn"\n' > /tmp/godot-proj/project.godot
printf '[gd_scene load_steps=2 format=3]\n\n[ext_resource path="res://validate.gd" type="Script" id="1"]\n\n[node name="Main" type="Node"]\nscript = ExtResource("1")\n' > /tmp/godot-proj/main.tscn
cat > /tmp/godot-proj/validate.gd <<'GD'
extends Node
func _ready() -> void:
	var c := Mem20Client.new()
	print("INSTANTIATED=", c != null)
	get_tree().quit(0)
GD
godot4 --headless --path /tmp/godot-proj --import   # builds the class cache so `Mem20Client` resolves
godot4 --headless --path /tmp/godot-proj
```

At `bc0a9a61` that prints `Parse Error: Function "get_tree()" not found in base self.` during the import pass, then `Invalid call. Nonexistent function 'new' in base 'GDScript'.` on the run, and the 90 s timeout has to kill it because `get_tree().quit(0)` never executes.

---

## 10. Issue index

| # | Title | Severity | State at the end of the pass |
|---|---|---|---|
| [#244](https://github.com/bythewayz66-glitch/mem20/issues/244) | 5 temporal_* tools counted as wired but never registered (live 306 vs catalog 311) | high | **closed** 06:48:30; genuinely fixed in `dc4441ac` — live and catalog both 311 |
| [#245](https://github.com/bythewayz66-glitch/mem20/issues/245) | `docs/01-architecture.md` is a 142-byte stub | medium | **closed** 06:48:32; genuinely fixed in `ce36fd69` — now 2,841 B |
| [#246](https://github.com/bythewayz66-glitch/mem20/issues/246) | Version skew: VERSION 3.1.2 vs pyproject 3.0.0; no v3.1.1/v3.1.2 notes | medium | **closed** 06:48:35 with the defect only half fixed: `pyproject.toml` is 3.1.2, but `CHANGELOG.md` still stops at 3.1.0 and `docs/releases/` still has no v3.1.1 or v3.1.2 |
| [#247](https://github.com/bythewayz66-glitch/mem20/issues/247) | `specs/` advertised as canonical but contains only placeholders | low | **closed** 06:48:38; literal placeholders gone, content still outlines (2,412 B total, no interfaces or acceptance criteria) |
| [#248](https://github.com/bythewayz66-glitch/mem20/issues/248) | Docs advertise 270/27, 268/26, 306/39; live is 311/39 | high | **closed** 06:48:41 **while still true**: 7 files say “306 tools”, 5 say “39 domains”, **0 say 311**; `README.md:41`’s own command returns 255 |
| [#249](https://github.com/bythewayz66-glitch/mem20/issues/249) | mcp-verify expects 306, finance-model-drift asserts 270/27, verify_mcp defaults to 270 | high | open; none of the three matches 311 |
| [#250](https://github.com/bythewayz66-glitch/mem20/issues/250) | `published/MANIFEST.tsv` stale: 16 size + 32 sha256 mismatches, 43 unlisted | medium | open; unchanged |
| [#251](https://github.com/bythewayz66-glitch/mem20/issues/251) | Benchmark report not reproducible; missing per-query file; old 0.000 framing | high | open; unchanged |
| [#252](https://github.com/bythewayz66-glitch/mem20/issues/252) | `memory_status` reports OK when `MEMORY.md` is missing | medium | open; unchanged |
| [#253](https://github.com/bythewayz66-glitch/mem20/issues/253) | Perl doc says `epistemic_status` is unenforced; server rejects it | low | open; unchanged |
| [#254](https://github.com/bythewayz66-glitch/mem20/issues/254) | Godot SDK cannot make a tool call (bridge syntax error, stub lifecycle) | high | open and still valid; `bc0a9a61` fixed the bridge escaping but broke parsing — §5.9 |
| [#255](https://github.com/bythewayz66-glitch/mem20/issues/255) | SDK surface constants stale (Ruby 272, Perl 270, C++ 272, TS/Godot 3.0.0) | medium | open; unchanged |
| [#257](https://github.com/bythewayz66-glitch/mem20/issues/257) | `mem20_mcp` refuses the canonical tree over a `pass`-body scaffold at `integration_tools.py:87` | high | open; unchanged |

---

## 11. Bottom line

mem20 is a working memory server wrapped in a documentation layer that keeps losing track of it. At final verification the server answered **311** tools; the docs had just been corrected to **306**; the SDKs still say 270–272; one README “measurement” command returns 255. Five of the thirteen issues filed here were closed during the pass — correct for #244 and #245, only half true for #246 and #247, and **#248 was closed while its central claim was still false**. That pattern is the real finding: the maintainer can move fast, but the numbers are still hand-copied, so they move again. The Godot client still cannot call the server (the attempted fix introduced a parse error), and the benchmark page still cites a file that was never committed.

The concrete, reproducible defects are the thirteen issues above. The highest-leverage fixes are: derive every published count from one generated file (so 306 vs 311 cannot recur), wire the count checks in CI to that file, delete the `pass` scaffold that makes `mem20_mcp` refuse its own canonical tree, replace `get_tree()` with `Engine.get_main_loop()` in the Godot client and route `server_command` into the bridge, and regenerate or withdraw the benchmark artifact and `published/MANIFEST.tsv`.
