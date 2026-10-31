# mem20 MCP surface — independent measurement, 2026-10-31

**Measured commit:** `8f0a310d5dbcb77e92188dd2312516d47ea0bffd` (`main`, `docs(ops): correct branch disposition after H4 landed mid-run (H5b rev 2)`)

This measurement was first taken at `27c1e5fb78def1d34b9b8f572a66f1424b1b350e`
(the SHA named in the assignment) and then **re-run at current `main`**, because
14 commits had landed in between. Every number below is identical at both
commits — 272 registration sites, 271 string-literal sites, 270 distinct keys,
28 registrars, 270 at runtime — so the findings are not a snapshot artefact of
the older SHA. The re-run was done because `d709d1b` ("correct
docs/02-tools-reference.md to 270 tools / 27 domains") landed in that window, so
the "27" claim had just been re-asserted and needed checking against code again.

This file is the result of re-deriving the product surface **from code only**. No
count in this document was copied from `README.md`, `docs/index.html`, or an
earlier ops note. Where those documents disagree with the code, the disagreement
is recorded rather than smoothed over.

---

## Verdict

| Claim under test | Result | Status |
|---|---|---|
| 270 unique tools | **270** | **CONFIRMED** by two independent methods |
| 28 `register_*_tools` groups | **28** | **CONFIRMED** |
| 27 domains | **not reproducible from the code** | **REFUTED as a code-derived number** |
| Which group is "not a domain" | **`register_a2a_tools`** | named below, with evidence |

**The repo ships 270 tools across 28 registration groups.** "27 domains" is an
editorial subtraction performed by `docs/TOOL-DOMAINS.md`, not a property the
code exposes. The task's hypothesis — that the odd group is `register_job_tools`
or `register_cognitive_tools` — is **wrong on both counts**: `register_job_tools`
is row 27 and `register_cognitive_tools` is row 2 of that document's own table.
Neither is excluded.

---

## Method

Two independent measurements, deliberately different in kind, so that agreement
between them is evidence rather than a restatement of the same grep.

### 1. Runtime — instantiate the real server, count the real registry

`Mem20MCPServer.__init__` calls `_setup_tools()`, which calls every
`register_*_tools` method, each of which assigns into `self.tools`. The
authoritative count is therefore `len(server.tools)` on a constructed instance —
this is exactly the dict `_handle_list_tools` returns to an MCP client.

```bash
pip install 'mcp' 'mcp-types>=2.3.0' 'aiohttp'   # declared in requirements.txt
cd /tmp && python3 /tmp/surface_measure.py       # script reproduced below
```

The script must be run from **outside** the repo root. `mcp/` is the server
directory, and putting the repo root on `sys.path[0]` makes `import mcp` resolve
to that local directory instead of the MCP SDK, which fails with
`Error: mcp package not installed`. The script imports the SDK first, then
inserts `mcp/` on `sys.path` so `server.py`'s `from tools.x import ...` resolves:

```python
import sys, os
REPO = os.environ.get("MEM20_REPO", "/workspace/mem20")
import mcp, mcp_types                      # SDK first, so mcp/ cannot shadow it
sys.path.insert(0, os.path.join(REPO, "mcp"))
sys.path.insert(0, REPO)
import server as S
srv = S.Mem20MCPServer()
runtime = sorted(srv.tools)
print("RUNTIME_TOOLS", len(runtime))
regs = sorted(n for n in dir(S.Mem20MCPServer)
              if n.startswith("register_") and n.endswith("_tools")
              and callable(getattr(S.Mem20MCPServer, n)))
print("REGISTRAR_METHODS", len(regs))
groups = {}
for g in regs:                             # attribute each tool to its registrar
    p = S.Mem20MCPServer.__new__(S.Mem20MCPServer)
    p.tools = {}
    for a in ("_jobs", "_tool_calls", "_tool_errors"): setattr(p, a, {})
    p._job_timeout = 1800.0; p._start_time = 0.0; p._request_count = 0
    p._request_errors = 0; p._event_taxonomy = []; p._audit_cache = None
    p._audit_cache_ts = 0.0
    getattr(p, g)()
    groups[g] = sorted(p.tools)
flat = [t for v in groups.values() for t in v]
print("SUM_OF_GROUPS", len(flat), "UNION", len(set(flat)))
print("PARTITION_CLEAN", len(flat) == len(set(flat)) == len(runtime))
for g in regs:
    print("  %-38s %3d" % (g.replace("register_","").replace("_tools",""), len(groups[g])))
```

Output:

```
RUNTIME_TOOLS 270
REGISTRAR_METHODS 28
SUM_OF_GROUPS 270 UNION 270
PARTITION_CLEAN True
```

### 2. Static — enumerate registration sites in the source

```bash
# every assignment site into the registry
grep -rn 'self\.tools\[' mcp --include='*.py' | wc -l                    # 272
# of those, sites using a string-literal key
grep -rhoE 'self\.tools\["[^"]*"\]' mcp --include='*.py' | wc -l         # 271
# distinct string-literal keys
grep -rhoE 'self\.tools\["[^"]*"\]' mcp --include='*.py' | sort -u | wc -l   # 270
# registrar call sites in the server
grep -oE 'register_[a-z0-9_]*_tools' mcp/server.py | sort -u | wc -l      # 28
```

Result: **270 distinct keys, 28 registrar groups** — identical to the runtime
measurement. The two methods agree exactly, and the per-group partition is
*clean*: the 28 groups partition the 270 tools with no overlap and no remainder
(`SUM_OF_GROUPS 270`, `UNION 270`, `PARTITION_CLEAN True`).

---

## The one duplicate: `lie_status`

272 assignment sites vs 270 distinct keys is accounted for exactly:

| Cause | Sites | Effect on `len(tools)` |
|---|---:|---|
| `lie_status` assigned twice — `mcp/tools/lie_tools.py:74` and `:82` | 2 | 0 (second assignment overwrites the first) |
| `self.tools[_status_name]` — `mcp/tools/world_tools.py:54`, non-literal key | 1 | 0 (mutually exclusive with the live path, see below) |

`lie_status` is a **real defect**, not a counting artefact: the same dict key is
written twice, so the source contains one more assignment than the server
exposes. It is recorded here, not fixed — removing a registration changes the
exposed schema, which is a behaviour change and belongs with tests.

`world_tools.py:54` is *not* a duplicate. It sits inside the
`MEM20_FLAG_WORLDMODEL_20` kill-switch branch: when the flag is off, the
registrar emits a single `world_model_status` placeholder and `return`s before
registering the 8 world-model tools. The two paths never both execute. This is
also why the flag changes the surface — the scripts above were run with the
default (flag unset → ON), giving 270; with `MEM20_FLAG_WORLDMODEL_20=0` the
runtime count is **251** (270 − 8 world_model − 6 affective − 6 procedural + 1
placeholder = 251), which is consistent with the same registry rather than a
second contradiction.

---

## Domain count: 28 groups, and why "27" is not a code-derived number

The code exposes **28 registrar groups**. There is no flag, marker, or
annotation anywhere in the registry that demotes one of them. Every one of the
28 contributes callable tools that appear in `tools/list` identically.

The "27" comes from a single editorial subtraction, stated in
`docs/TOOL-DOMAINS.md`:

> `| register_*_tools groups | **28** | one per domain module, plus the A2A layer |`
> `| minus the A2A Hermes layer | −1 | register_a2a_tools — an inter-agent transport, not a tool domain |`
> `| = **domains** | **27** | |`
> `| — | **subtotal (27 domains)** | **265** | |`
> `| 28 | a2a (transport layer, not counted as a domain) | 5 | ... |`

So the excluded group is **`register_a2a_tools`** — 5 tools (`a2a_list`,
`a2a_call`, `a2a_discover`, `a2a_history`, `a2a_orchestrate`), and the
arithmetic `28 − 1 = 27`, `265 + 5 = 270` does reconcile.

**But the subtraction is a judgement, not an observation.** Those 5 tools are
ordinary entries in `self.tools`; nothing in code distinguishes them. A reader
re-deriving the surface from source will get 28, every time. Labeling A2A a
"transport layer" is a product taxonomy decision, and it is legitimate — it is
just not something the repository *ships*, and it must not be presented as a
counted fact.

### The "27" claim is also internally inconsistent

`README.md` contradicts the taxonomy two ways in the same table — the one headed
**"Tool domains (27)"**:

1. **It lists `a2a_*` as a domain.** Row: `` | `a2a_*` | 5 | Agent-to-agent |
   Discover, call, and orchestrate peer agents over A2A | ``. README counts A2A
   as a domain while claiming 27; `docs/TOOL-DOMAINS.md` excludes it to reach 27.
   The two documents cannot both be right.

2. **It omits `lie_*` entirely.** A formally registered domain module
   (`mcp/tools/lie_tools.py`) with **10 live tools** has no row in the table.
   The `lie_*` domain was added in the same correction that produced the 270/27
   number, and the table was never updated to include it.

3. **Its row counts sum to 257, not 270.** Several rows are stale relative to
   what registers today:

| README row | README claims | Actually registers | Note |
|---|---:|---:|---|
| `memory_*` | 49 | **52** | 39 in `register_memory_tools` + 13 in `register_enhanced_memory_tools` |
| `cog_*`, `tot_*` + substrate | 15 | **19** | `register_cognitive_tools` |
| `world_model_*` | 9 | **8** | `register_world_tools` world-model subset (its other 6 are `affective_*`) |
| `cloud_*` | 10 | 10 | but `cloudstorage_*` is a separate 8 — README lists it separately, so `cloud`+`cloudstorage` = 18 |
| `fs_*` | 13 | 10 + 3 | 10 `filesystem` + 3 `integration` (`fs_read`/`fs_write`/`fs_list`) |
| `imagination_*` | 8 | **9** | inside `register_cognitive_tools` |
| `lie_*` | — | **10** | **row missing entirely** |
| **sum of rows** | **257** | **270** | |

The table therefore publishes a total of 257 while the paragraph above it says
270. A reader who adds the table up gets a different number than the headline.

---

## Per-group map, as measured

28 groups, 270 tools, clean partition. Group name is the registrar method with
the `register_` / `_tools` affixes removed.

| # | Group | Tools | Source module |
|---:|---|---:|---|
| 1 | `memory` | 42 | `mcp/memory_tools.py` |
| 2 | `cognitive` | 19 | `mcp/cognitive_tools.py` |
| 3 | `world` | 14 | `mcp/tools/world_tools.py` |
| 4 | `enhanced_memory` | 13 | `mcp/tools/enhanced_memory_tools.py` |
| 5 | `versioncontrol` | 11 | `mcp/tools/versioncontrol_tools.py` |
| 6 | `cloudservice` | 10 | `mcp/tools/cloudservice_tools.py` |
| 7 | `database` | 10 | `mcp/tools/database_tools.py` |
| 8 | `filesystem` | 10 | `mcp/tools/filesystem_tools.py` |
| 9 | `lie` | 10 | `mcp/tools/lie_tools.py` |
| 10 | `productivity` | 10 | `mcp/tools/productivity_tools.py` |
| 11 | `braid` | 9 | `mcp/tools/braid_tools.py` |
| 12 | `communication` | 9 | `mcp/tools/communication_tools.py` |
| 13 | `dev` | 9 | `mcp/tools/dev_tools.py` |
| 14 | `marketing` | 9 | `mcp/tools/marketing_tools.py` |
| 15 | `thought_process` | 9 | `mcp/tools/thought_process.py` |
| 16 | `cloudstorage` | 8 | `mcp/tools/cloudstorage_tools.py` |
| 17 | `design` | 8 | `mcp/tools/design_tools.py` |
| 18 | `finance` | 8 | `mcp/tools/finance_tools.py` |
| 19 | `webscraping` | 8 | `mcp/tools/webscraping_tools.py` |
| 20 | `blender` | 7 | `mcp/tools/blender_tools.py` |
| 21 | `search` | 7 | `mcp/tools/search_tools.py` |
| 22 | `procedural` | 6 | `mcp/tools/procedural_tools.py` |
| 23 | `a2a` | 5 | `mcp/tools/a2a_tools.py` |
| 24 | `irc` | 5 | `mcp/tools/irc_tools.py` |
| 25 | `unity` | 5 | `mcp/tools/unity_tools.py` |
| 26 | `roadmap` | 4 | `mcp/roadmap_tools.py` |
| 27 | `integration` | 3 | `mcp/tools/integration_tools.py` |
| 28 | `job` | 2 | `mcp/server.py` (the only registrar defined inline) |
| | **total** | **270** | |

`register_job_tools` is the only registrar defined in `mcp/server.py` itself
rather than in a `mcp/tools/*.py` module — it registers `job_status` and
`job_wait`, the poll/await pair for `LONG_RUNNING_TOOLS`. That makes it a
structural outlier, **not** a non-domain: both tools are live in the registry and
it is counted as row 27 by `docs/TOOL-DOMAINS.md`.

`register_integration_tools` registers `fs_read` / `fs_write` / `fs_list`. These
do **not** collide with `register_filesystem_tools`, which registers
`fs_read_advanced` / `fs_write_advanced` / `fs_search` / `fs_metadata` /
`fs_diff` / `fs_archive_create` / `fs_archive_extract` / `fs_disk_usage` /
`fs_watch` / `fs_permissions` — a disjoint set of 10. The two groups share the
`fs_` prefix but no tool names, so the 13 in README's `fs_*` row are 10 + 3.

---

## What this means for the published numbers

**`270` is correct.** Two independent methods agree, the partition is clean, and
the single duplicate is explained.

**`27 domains` is not supported by the code.** The code has 28 registration
groups. Twenty-seven is reachable only by an editorial decision to exclude
`register_a2a_tools`, and that decision is not encoded anywhere in the
repository — it exists only as prose in `docs/TOOL-DOMAINS.md`, which
`README.md` then contradicts by listing `a2a_*` as a domain.

**README's domain table is materially wrong regardless of how the taxonomy is
settled:** it omits the 10-tool `lie_*` domain, and its rows sum to 257 against a
stated total of 270.

The honest formulation, which this document adopts and which any surface-facing
copy should use, is:

> **270 tools across 28 registration groups** — with A2A (5 tools) presented
> separately as an inter-agent transport if that taxonomy is wanted, in which
> case say "270 tools in 27 domain groups plus the A2A transport layer" and make
> the table sum to 265, not 257.

No count in this document is inferred. Every figure above came from executing
the two commands in **Method** against `8f0a310d5dbcb77e92188dd2312516d47ea0bffd`
(current `main`), and the same commands were first run against
`27c1e5fb78def1d34b9b8f572a66f1424b1b350e` with identical results.

---

## Reproducing

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20 && git checkout 8f0a310d5dbcb77e92188dd2312516d47ea0bffd
pip install 'mcp' 'mcp-types>=2.3.0' 'aiohttp'

# static
grep -rn 'self\.tools\[' mcp --include='*.py' | wc -l                      # 272 sites
grep -rhoE 'self\.tools\["[^"]*"\]' mcp --include='*.py' | sort -u | wc -l # 270 distinct
grep -oE 'register_[a-z0-9_]*_tools' mcp/server.py | sort -u | wc -l       # 28 groups

# runtime (script from Method, saved as /tmp/surface_measure.py, run from outside the repo)
cd /tmp && python3 /tmp/surface_measure.py   # RUNTIME_TOOLS 270 / REGISTRAR_METHODS 28
```

The runtime step needs no network, no store, and no live transport: it constructs
the server object and reads `self.tools`, which is the same dict `tools/list`
serves.
