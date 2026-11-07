# mem20gameplaysystemsdataandbalancepipelinez — Gameplay Systems Data & Balance Pipeline (RM-245, #316)

**Outcome:** represent mechanics, abilities, items, enemies, economy, and progression as validated simulation-ready data.  
**Breakthrough:** designers can change gameplay safely without scattering values through code.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator; enriches progression/execute with pipeline analysis and 6 **unique** peer integrations (different from #300–#315).

## Legacy domain API (preserved)
`collect_telemetry(events)`, `aggregate_metrics(telemetry)`, `balance_tuning(metrics,targets)`, `funnel_analysis(steps)`, `pipeline_report(data)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20sensorymemoryingestz` | `ingest`,`ingest_health` | telemetry/ingest health |
| `mem20selfoptimizingkernelz` | `kernel_health` (+ optimization context) | tuning/optimization kernel health |
| `mem20realitytosoftwarecompilerz` | `validate_spec`,`diff_spec` | validated simulation-ready spec checks |
| `mem20dynamicnarrativeenginez` | `create_story`,`add_node`,`current_text` | gameplay/narrative system signals |
| `mem20businessmodelsimulatorz` | `revenue`,`cost`,`profit`,`margin` | economy/balance modeling |
| `mem20goapagentdesignerz` | `heuristic`,`validate_plan` | AI/system plan validation |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gameplaysystemsdataandbalancepipelinez simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gameplaysystemsdataandbalancepipelinez execute '{"xp":120,"pipeline":true,"events":[{"player":"a","action":"jump"}],"metrics":{"hp":10},"targets":{"hp":15},"data":[{"valid":true}]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gameplaysystemsdataandbalancepipelinez serve --port 8796
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20gameplaysystemsdataandbalancepipelinez/tests mem20gameplaysystemsdataandbalancepipelinez/mem20gameplaysystemsdataandbalancepipelinez/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20gameplaysystemsdataandbalancepipelinez
```
