# mem20outcomesimulationlabz — Outcome Simulation Lab

First-class mem20 subsystem for outcome simulation (simulate_once/monte_carlo/summarize/scenario_compare/risk_of_loss) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20counterfactualmemorysimulatorz`, `mem20realtimebusinesstwinz`, `mem20businessmodelsimulatorz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20outcomesimulationlabz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20outcomesimulationlabz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20outcomesimulationlabz serve --port 8850
```
