# mem20secretslessworkloadidentityz — Secrets-less Workload Identity

First-class mem20 subsystem for secrets-less workload identity (issue/verify/rotate identities, health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`, `mem20faultcontainmentcellsz`, `mem20selfhealingplansz`, `mem20deterministicconfigurationgraphz`.

## Python API (runnable)
```python
from mem20secretslessworkloadidentityz.domain import issue_identity, verify, rotate, identity_report, probe
i=issue_identity("svc"); print(verify(i)["valid"])  # True
print(rotate(i)["workload"])  # svc
r=identity_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20secretslessworkloadidentityz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20secretslessworkloadidentityz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20secretslessworkloadidentityz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20secretslessworkloadidentityz serve --port 8823
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/secretslessworkloadidentityz/index.html` (no Vite edits).

## MCP & registration
`SecretslessWorkloadIdentityToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20secretslessworkloadidentityz/mem20secretslessworkloadidentityz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20secretslessworkloadidentityz
```
Target **7/7**.
