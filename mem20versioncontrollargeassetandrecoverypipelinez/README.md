# RM-239 — Version Control, Large-Asset and Recovery Pipeline

**Outcome:** Manage code, scenes, models, media, branches, locking, replication, and recovery as one system

**Breakthrough:** Large creative projects gain software-grade traceability and resilience

This package is the machine-executable local implementation derived from the supplied Off Record Lab roadmap. It includes versioned typed state, SQLite WAL persistence, event history/snapshots, SDK CRUD/subscription, resumable idempotent jobs, cancellation, retries/timeouts/quotas/backpressure, deterministic replica reconciliation, local/hybrid/cloud placement/failover, roadmap-specific `heal` logic, decision confidence/explanations, feedback, CLI, HTTP console/API, safety guards, simulator, benchmark/metrics, and rollback-capable installer.

Named live product surfaces, real provider/device credentials, production traffic, and governed FreeStack deployment remain target-environment integration and are not claimed complete.

## Install

mem20 is **not on PyPI**. Install from source:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
```

## Run the CLI

```bash
cd mem20/mem20versioncontrollargeassetandrecoverypipelinez
python3 -m mem20versioncontrollargeassetandrecoverypipelinez simulate
```

## Runnable example: audit an asset release

`audit_asset_release()` versions an asset and audits it against the rest of the
estate — credential screening (`mem20secretz`), asset budget (`mem20kilnz`),
grounded ledger write + read-back (`memory_engine`), store round-trip
(`mem20verify`), estate registration (`toolchest`), and the fleet registry
(`gateway`).

```python
import json
import sys

# run from the mem20 repo root
sys.path.insert(0, "mem20versioncontrollargeassetandrecoverypipelinez")

from mem20versioncontrollargeassetandrecoverypipelinez.integration import (
    audit_asset_release,
)

report = audit_asset_release(
    asset_id="hero_sword",
    content="blade-v1",
    family="weapon",
    triangles=3000,
    metadata={"artist": "kim"},
)

print(json.dumps(report, indent=2, sort_keys=True))
print("release ok:", report["ok"])
```

Real output from that script:

```text
{
  "asset_id": "hero_sword",
  "budget": {
    "family": "weapon",
    "ok": true,
    "reason": "within standard 3000-8000",
    "tier": "standard",
    "triangles": 3000
  },
  "fleet": {
    "agents": 0
  },
  "integrity": {
    "checked": 11,
    "error": "",
    "ok": true,
    "roundtrip_ok": 11
  },
  "inventory": {
    "entries": 312,
    "path": "/workspace/mem20/toolchest/inventory.json",
    "subsystem_registered": true
  },
  "ledger": {
    "ok": true,
    "rows": 5,
    "topic": "asset.hero_sword"
  },
  "ok": true,
  "secrets": [],
  "version": {
    "asset_id": "hero_sword",
    "hash": "995da62c28952302d83466091e512f65fb584525fac051476d62882a47c942f6",
    "size": 8,
    "ts": 1793560377.4827988,
    "version": "995da62c"
  }
}
release ok: True
```

A manifest carrying a credential is refused (`ok: false`, `secrets[0].severity == "critical"`),
and an asset outside its triangle budget is refused with the budget reason.

## MCP surface

The pipeline is registered with the mem20 MCP server as the tool
`vcs_asset_release_audit` (`mcp/tools/versioncontrol_tools.py`), so an agent can
audit a release without shelling out:

```json
{"asset_id": "hero_sword", "content": "blade-v1", "family": "weapon", "triangles": 3000}
```

## Tests

```bash
python3 -m pytest mem20versioncontrollargeassetandrecoverypipelinez -q
```
