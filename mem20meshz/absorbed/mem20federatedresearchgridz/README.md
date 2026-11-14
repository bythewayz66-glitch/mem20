# mem20federatedresearchgridz — Federated Research Grid (RM-043, #313)

**Outcome:** split research across nodes and merge results without centralizing all source data.  
**Breakthrough:** large investigations run privately across distributed machines.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator; enriches `search` with federated grid analysis and 6 **unique** peer integrations (different from #300–#312).

## Legacy domain API (preserved)
`register_node(grid,node)`, `distribute_task(grid,task)`, `aggregate_results(results)`, `grid_health(grid)`, `federated_round(grid,task)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20collectivemodelintelligencez` | `ensemble_predict`,`aggregate_confidence`,`diversity_score` | distributed result aggregation/intelligence |
| `mem20personalcognitivesearchz` | `index`,`query`,`recall` | federated/cognitive search & recall |
| `mem20alternativedatabaseplaygroundz` | `query_plan`,`suggest_index`,`benchmark_query` | research query planning/indexing |
| `mem20crdtcollaborationenginez` | `GCounter.increment/value`,`PNCounter` | CRDT merge primitives for distributed state |
| `mem20prioritycollisionresolverz` | `PriorityCollisionResolver.submit/resolve` | task priority/collision resolution |
| `mem20connectormarketplacez` | `ConnectorMarketplace` (+ method call) | research source/connector discovery |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20federatedresearchgridz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20federatedresearchgridz execute '{"query":"federated research","documents":[{"id":"d1","text":"node task"}],"nodes":[{"id":"n1","status":"ready","load":0,"compute":2}],"task":{"cost":1,"size":3}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20federatedresearchgridz serve --port 8793
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20federatedresearchgridz/tests mem20federatedresearchgridz/mem20federatedresearchgridz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20federatedresearchgridz
```
