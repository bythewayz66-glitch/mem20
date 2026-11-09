# mem20

**A trusted, auditable memory + world-model layer for agents.**

mem20 gives an agent something it does not otherwise have: a memory that survives the
session, records *why* it believes what it believes, and can be audited after the fact.
It ships as an MCP server (JSON-RPC 2.0 over stdio) plus a large estate of independently
packaged subsystems.

- **Version:** 3.1.2 (`VERSION`)
- **License:** Apache-2.0
- **Python:** >= 3.10
- **Transport:** MCP over stdio, with an HTTP health/metrics endpoint on `:8080`

**Core Edition:** the focused, installable memory substrate lives in
[mem20-ce](https://github.com/bythewayz66-glitch/mem20-ce) (Apache-2.0, `pip install mem20-ce`).

---

## What it actually is

Three layers, in dependency order:

| Layer | Path | What it does |
|---|---|---|
| **Memory engine** | `memory_engine/`, `memory.py` | Global memory, ledger, and vector store. The durable substrate. |
| **MCP server** | `mcp/` | Exposes the engine (and the wider estate) as MCP tools over stdio. |
| **Subsystems** | `mem20*/` | ~300 independently packaged capability modules, each with its own `pyproject.toml`. |

`mcp/` is deliberately **a script directory, not an importable package** — it has no
`__init__.py`, because importing it as `mcp.*` would shadow the upstream `mcp` SDK. That
is why `mcp_server.py` does `from server import main` (script-dir relative) and why the
installed console script `mem20-mcp` routes through `launcher.py`.

---

## Verified numbers

Every figure below was measured against this checkout, not carried over from earlier
documentation. Where an older number was wrong, the correction is noted.

| Metric | Verified value | How measured |
|---|---|---|
| MCP tools | **487** | live JSON-RPC `tools/list` (generated in `docs/surface.json`) |
| MCP tool modules | **44** | `ls mcp/tools/*.py \| wc -l` |
| Subsystems (sitemap) | **340** | `.sitemap/sitemap.json` → `totals.subsystems` |
| Subsystem directories | **297** | `ls -d mem20*/` |
| Source files | **8,497** | `.sitemap/sitemap.json` → `totals.files` |
| Code lines | **384,249** | `.sitemap/sitemap.json` → `totals.code_lines` |
| Total lines | **964,795** | `.sitemap/sitemap.json` → `totals.lines` |
| Packaged subsystems | **288 of 297** | dirs with a `pyproject.toml` at depth 1 or 2 |
| `pyproject.toml` files | **290** | `find . -name pyproject.toml` |
| Test files | **322** | `find . -name "test_*.py" -o -name "*_test.py"` |

### Corrections to previously published numbers

These were wrong in the old README and are corrected here:

| Claim | Old value | **Verified** |
|---|---|---|
| Corpus version | v1 | **v2** (and a v3 exists) |
| Corpus entries | 14 | **2,000** (v2) / **122,178** (v3) |
| Degraded tools | 101 | **169** |
| Unpackaged tools | 142 | **141 in inventory, but only 9 directories actually lack a `pyproject.toml`** |
| Subsystems | 327 | **340** (sitemap) / **297** directories |
| Source files | 8,969 | **8,497** |
| Code lines | 468k | **384,249** |

The corpus is the biggest correction. `benchmarks/corpora/mem20-scale-corpus-v2.manifest.json`
declares `records: 2000` (700 grounded, 1,300 simulated, 250 queries). A newer
`benchmarks/corpora/v3/manifest.json` declares `records: 122178` across 600 probes and
96.41 MiB. **There is no v1 corpus with 14 entries in this repo.**

---

## Install

### From a git checkout (recommended)

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

`requirements.txt` carries the core runtime. It now also declares `httpx`, `PyYAML` and
`stripe`, which several subsystems import at module scope — without them a clean clone
cannot even collect its test suite.

### As a package

```bash
pip install -e .
```

This installs the `memory_engine` package, the repo-root modules (`memory`,
`procedural`, `launcher`, `metrics_collector`, `mem20path`), and three console scripts:

| Script | Purpose |
|---|---|
| `mem20-mcp` | Run the MCP server (equivalent to `python mcp/mcp_server.py`) |
| `mem20-metrics` | Query install metrics, or run the collector dashboard |
| `mem20-path` | Link mem20's console scripts into a default-PATH directory |

### Portable installer (systemd host)

```bash
sudo ./install.sh [--user <user>] [--dir <mem20_dir>] [--venv <venv_path>]
```

Creates a venv, installs `requirements.txt`, generates a systemd unit from
`systemd/mem20.service.template`, and enables + starts the service. Pass `--no-systemd`
to skip the service step.

Blender and Unity are **optional external applications**, not pip packages — see
`requirements-optional.txt`. The server runs without them and reports when a tool needs
one.

---

## Quickstart

### Run the MCP server

```bash
MEM20_STORE_PATH="$HOME/.mem20/store" .venv/bin/python mcp/mcp_server.py
```

Verified on this checkout: the process starts and logs

```
INFO mem20.mcp health endpoint listening on :8080 (/health /ready /metrics)
```

It then serves MCP over stdio. The HTTP endpoint is for liveness and metrics only:

```bash
curl -s localhost:8080/health
curl -s localhost:8080/ready
curl -s localhost:8080/metrics
```

### Point an MCP client at it

```json
{
  "mcpServers": {
    "mem20": {
      "command": "/absolute/path/to/mem20/.venv/bin/python",
      "args": ["/absolute/path/to/mem20/mcp/mcp_server.py"],
      "env": { "MEM20_STORE_PATH": "/home/you/.mem20/store" }
    }
  }
}
```

Or, after `pip install -e .`, use the console script:

```json
{
  "mcpServers": {
    "mem20": { "command": "mem20-mcp" }
  }
}
```

### Use the memory engine directly

```python
from memory_engine import MemoryEngine

engine = MemoryEngine(store_path="~/.mem20/store")
engine.remember("the deploy key rotates on the first Monday", tags=["ops"])
print(engine.recall("when does the deploy key rotate?"))
```

---

## Tests

```bash
python3 -m pytest -q
```

`pytest.ini` sets `--import-mode=importlib` and `testpaths = .`, so a bare `pytest`
collects the whole estate. To narrow:

```bash
python3 -m pytest mem20agentz -q
```

The canonical runner is `mem20verify tests`, which additionally honours per-package
virtualenvs and a per-package timeout.

**Current state:** the suite does not yet run clean end-to-end. A repo-wide run currently
stops at **8 collection errors** (down from 29 after the dependency fix). The remaining
ones are genuine import bugs, tracked in issues #224, #225, #226 and #171–#180. Until
those are closed, `pytest` aborts before executing any test.

---

## Repository layout

```
mem20/
├── memory_engine/        # durable memory: ledger, vectors, API
├── memory.py             # root memory engine (imports procedural.py at module scope)
├── procedural.py         # procedural memory companion to memory.py
├── mcp/                  # MCP server — a SCRIPT DIR, not a package
│   ├── mcp_server.py     # entry point (from server import main)
│   ├── server.py         # JSON-RPC dispatch, health endpoint
│   └── tools/            # 44 modules; 487 tools with the root mixins
├── mem20*/               # ~297 independently packaged subsystems
├── benchmarks/
│   └── corpora/          # v2 (2,000 records) and v3 (122,178 records)
├── toolchest/            # tool inventory + status registry
├── .sitemap/sitemap.json # generated estate map (340 subsystems)
├── braid/                # braid bridge
├── gateway/              # API gateway
├── docs/                 # audits, ops notes, GTM material
├── tests/                # root scratch tests
├── requirements.txt
├── pyproject.toml
└── install.sh
```

---

## Tool inventory and status

`toolchest/` maintains a registry of every tool and subsystem with a `runtime_status`:

| Status | Count | Meaning |
|---|---|---|
| `ok` | 2 | Installed and importable |
| `degraded` | **169** | **Not pip-installed** in the root venv or a local `.venv` |
| `unpackaged` | 141 | No `pyproject.toml` found at inventory time |

Two things worth knowing before trusting these numbers:

1. **`degraded` is an install-state verdict, not a code-quality one.**
   `toolchest/src/toolchest/catalog.py:682` sets `status = "ok" if install_status == "ok"
   else "degraded"`. All 169 share one cause: not pip-installed. See issue #227.
2. **The committed inventory is stale.** `catalog.py:38` hardcodes
   `MEM20_ROOT = Path("/opt/mem20")`, so `toolchest refresh` finds 0 subsystems on any
   other checkout. The 141 "unpackaged" figure predates most subsystems gaining a
   `pyproject.toml` — only 9 directories actually lack one today. See issue #228.

Query the registry:

```bash
cd toolchest && PYTHONPATH=src python3 -m toolchest stats
cd toolchest && PYTHONPATH=src python3 -m toolchest list --category games-3d
cd toolchest && PYTHONPATH=src python3 -m toolchest show mem20agentz
```

---

## Benchmarks

```bash
# v2 — 2,000 records
python benchmarks/v2/run_bench.py

# v3 — 122,178 records, 600 probes
python benchmarks/v3/build_corpus_v3.py --per-category 48000 --out benchmarks/corpora/v3
python benchmarks/v3/validate_corpus_v3.py benchmarks/corpora/v3
python benchmarks/v3/load_corpus_v3.py benchmarks/corpora/v3 --mode ledger --store /tmp/mem20-v3-store --rebuild
```

v2 is designed so every non-control probe has its gold record in the corpus and does not
leak its own answer; the `unanswerable` kind is a control that must score 0.000, and
contamination must stay 0.0.

---

## Contributing

See `CONTRIBUTING.md`. The short version:

```bash
python3 -m compileall -q <touched paths>
python3 -m pytest <package> -q
```

Both must be clean before a PR. Do not commit `build/`, `__pycache__/`, `node_modules/`,
model caches, or runtime state.

---

## License

Apache License 2.0 — see `LICENSE`.

Core Edition (focused product): https://github.com/bythewayz66-glitch/mem20-ce
