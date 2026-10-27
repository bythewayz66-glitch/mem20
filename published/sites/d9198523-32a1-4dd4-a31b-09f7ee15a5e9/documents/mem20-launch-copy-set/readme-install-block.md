# README install block + repo header — publish-ready (v3 · canonical-repo-corrected)

**Use:** paste into the canonical repo README (`https://github.com/bythewayz66-glitch/mem20`), under the H1.
**Verified this run:** repo returns HTTP 200, MIT, Python, default branch `main`, `pyproject.toml` version `2.1.0rc2`.
**Supersedes:** v2 (`documents/mem20-assets-refresh/readme-install-block.md`), which pointed at a dead repo and carried an install pin that does not work on this tree.

---

## Why v3 exists (the substantive fix, not a relabel)

v2 told readers to install with a pin that **contradicts the canonical repo**. Two facts from the tree:

| Source | Fact |
|---|---|
| `requirements.txt` | `mcp>=2.1.1` |
| `pyproject.toml` → `[project].dependencies` | `mcp>=2.1.1` |
| README "Installation → 1. pip" | `pip install .` then `mem20-mcp` |

The canonical tree pins **mcp 2.1.1 or newer**. A reader who followed v2's older pin would install an SDK the tree does not use. v3 replaces the pin with `pip install -r requirements.txt` — the command the repo's own README and `install.sh` actually use.

Also corrected: the run command. v2 published a module path from the older, non-canonical `mcp-cognitive-substrate` repo. The canonical entry point is `mcp/mcp_server.py` (and the `mem20-mcp` console script, which wraps it via `launcher.py`).

---

## README H1 + intro

```markdown
# mem20

### Auditable agent memory — the memory layer you can prove.

mem20 is a persistent memory + cognition substrate for AI agents, exposed over the
Model Context Protocol as a JSON-RPC 2.0 service on stdio. It keeps *grounded*
memory (real observations, user statements, events) strictly separate from
*simulated* memory (hypotheticals, counterfactuals, model output), audits
contamination between the two, promotes content only on attached evidence, and
records every operation in an append-only, origin-tagged ledger.

**270 tools across 27 domains.** MIT licensed. Python. Self-hosted. Zero lock-in.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![MCP](https://img.shields.io/badge/MCP-JSON--RPC%202.0%20over%20stdio-informational)
```

> Badge note: these are static status badges. The only *actionable* links (clone URL, install commands, client registration) point at the canonical repo.

---

## Install

````markdown
## Quick Start

mem20 installs from source. It is **not yet published to PyPI**.

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20

# Create venv and install core deps (mcp, pydantic, anyio, numpy, faiss-cpu, sentence-transformers)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run the server (stdio)
MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py
```

A bare registry install is not a valid install path today — the package is not on PyPI.
Use the clone command above.
````

---

## Install as a package (console script)

```bash
pip install .        # builds the wheel and installs the `mem20-mcp` command
mem20-mcp            # starts the MCP server + the :8080 health endpoint
```

`mem20-mcp` is a thin launcher (`launcher.py`) that locates the bundled `mcp/` directory and runs it as a script — so `from mcp.server import Server` resolves to the upstream MCP SDK and is never shadowed by the repo's local `mcp/` directory.

---

## Install as an always-on service (systemd)

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git /opt/mem20
sudo /opt/mem20/install.sh --user $USER --dir /opt/mem20

curl http://localhost:8080/health    # → {"status":"ok", ...}
curl http://localhost:8080/metrics   # → tool counters + contamination_rate
```

What `install.sh` does:

- creates a Python venv at `/opt/mem20/.venv`
- installs core deps from `requirements.txt`
- generates `/etc/systemd/system/mem20.service` from `systemd/mem20.service.template`, then enables and starts it
- default store path `/opt/mem20/store`
- supports `--no-systemd` for a manual run

---

## Other install channels

```bash
# Docker
docker build -t mem20 .
docker run -p 8080:8080 -e MEM20_HEALTH_PORT=8080 -v mem20-store:/data mem20

# apt (.deb)
make deb
sudo dpkg -i packaging/deb/mem20_*.deb
sudo systemctl status mem20
mem20-health
```

---

## Register mem20 with an MCP client

```bash
# Claude Code / Cursor
claude mcp add mem20 -- python3 /path/to/mem20/mcp/mcp_server.py
```

```json
{
  "mcpServers": {
    "mem20": {
      "command": "python3",
      "args": ["/path/to/mem20/mcp/mcp_server.py"],
      "env": { "MEM20_STORE_PATH": "/path/to/store" }
    }
  }
}
```

Or with Hermes:

```bash
hermes config set mcp.servers.mem20 '["python3", "/path/to/mem20/mcp/mcp_server.py"]'
```

---

## Benchmarks section (paste under Install)

```markdown
## Benchmarks

Self-reported, measured on our own internal harness:

| Metric | Result |
|---|---|
| Hit rate — direct | 1.000 |
| Hit rate — multi-hop | 0.800 |
| Hit rate — adversarial | **0.000** |
| Leak rate (clean stores) | 0.000 |

**Read the 0.000 adversarial row honestly:** hard adversarial queries defeat the
retrieval path today. It is a known weakness and it is on the roadmap — not a
smudge. These figures are self-reported on our own harness; they have not been
independently audited and they are not reproducible from a script in this
repository.

We also publish **no LoCoMo/LongMemEval** result comparable to Mem0 or Zep, and
we do not claim one.
```

---

## Provenance / limits section (paste near the bottom)

```markdown
## What "auditable" means here — and what it doesn't

mem20 gives you a grounded/simulated partition enforced at the storage layer,
contamination auditing, evidence-based promotion, and an append-only
origin-tagged ledger.

It is **not** tamper-proof and it is **not** unfakeable. The promotion gate
(`promote_simulated_to_grounded()`) requires `prediction_error_evidence` — a
linked prior prediction resolved in the item's favour, or a registered external
verifier — but that attestation is self-reported rather than cryptographically
enforced. A prior internal audit flagged the gap.

The accurate claim is **evidence-based promotion with an append-only audit
trail**.
```

---

## Guardrail check

- [x] No LoCoMo/LongMemEval claim; explicit disclaimer present
- [x] Adversarial 0.000 disclosed, framed as a known weakness, labelled self-reported
- [x] Promotion described as "evidence-based with an append-only audit trail" — never tamper-proof/unfakeable
- [x] Install commands match the tree (`requirements.txt`, `mcp/mcp_server.py`)
- [x] No bare registry install; canonical repo only
- [x] No retired repo reference
- [x] No stale dependency pin (retired — contradicted by the tree)
