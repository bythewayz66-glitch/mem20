# mem20energyawarefoundationz — Energy-Aware Foundation

Power monitoring, thresholds, budgets, and optimization actions with durable state and 6 unique cross-subsystem peers (different set from #300-#303). Preserves legacy domain API: `power_reading`, `threshold_check`, `energy_budget`, `optimize_power`, `daily_energy`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20selftuningresourcegovernorz` | `govern`,`adjust_quota`,`governor_health` | power/budget quota governance |
| `mem20realtimebusinesstwinz` | `create_twin`,`update_kpi`,`check_alerts`,`twin_health` | KPI threshold alerts/twin health |
| `mem20freestackambientcomputingfabricz` | `pool_resources`,`allocate`,`fabric_health` | resource pool/allocation view |
| `mem20pipez` | `collect_telemetry`,`aggregate_metrics`,`pipeline_report` | telemetry aggregation/reporting |
| `mem20pipez` | `create_plan`,`orchestrate`,`pipeline_health` | optimization action orchestration |
| `mem20autonomousworkcellsz` | `create_cell`,`enqueue`,`assign_workers`,`process_next`,`cell_health`,`throughput` | action execution work cells |

## Runnable example (verified)
```bash
cd /opt/mem20
DB=/tmp/eaf-demo.sqlite3
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20energyawarefoundationz --db "$DB" device add --id meter-1 --power 120 >/dev/null
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20energyawarefoundationz --db "$DB" policy --id default --budget 150 --threshold 100 >/dev/null
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20energyawarefoundationz --db "$DB" evaluate
```
Observed (key fields): `ok=false` when budget/threshold exceeded; `result.threshold_checks` show overage; `result.actions` propose reductions; `signals.resource_governor/business_twin/ambient_fabric/orchestration/workcell` all `ok:true`.

```bash
python -m mem20energyawarefoundationz status
python -m mem20energyawarefoundationz doctor
python -m mem20energyawarefoundationz simulate
python -m mem20energyawarefoundationz serve --port 8784
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20energyawarefoundationz/tests -q
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20energyawarefoundationz
```
