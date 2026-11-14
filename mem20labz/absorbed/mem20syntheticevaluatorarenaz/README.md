# mem20syntheticevaluatorarenaz — Synthetic Evaluator Arena

First-class mem20 subsystem for synthetic evaluation arena (create_arena/evaluate/leaderboard/arena_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20collectivemodelintelligencez`, `mem20simz`, `mem20agentoutputcompilerz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20syntheticevaluatorarenaz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20syntheticevaluatorarenaz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20syntheticevaluatorarenaz serve --port 8839
```
