# mem20hotswappableservicefoundationz — Hot-Swappable Service Foundation (RM-091, #324)

**Outcome:** Replace running service implementations without stopping unrelated capabilities.
**Breakthrough:** The platform upgrades continuously with near-zero disruption.

Preserves legacy domain API (**#317 peer dependency**) and CAPABILITY Engine/CLI/10-scenario simulator (`analyze` operation kind). `analyze` is meaningful for service/swap payloads and backward-compatible for generic analyze.

## Legacy domain API (preserved for #317)
`register_service(registry,name,impl)`, `swap(registry,name,new_impl)`, `health(registry)`, `rollback(registry,name)`, `list_services(registry)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Hot-swap role (feeds analysis outcome) |
|---|---|---|
| `mem20pipez` | `version_asset`,`diff_versions`,`recover`,`vc_health` | impl versioning and recovery readiness |
| `mem20deterministicconfigurationgraphz` | `add_node`,`add_edge`,`resolve` | deterministic service/config resolution |
| `mem20reversibleexecutiongraphz` | `create_graph`,`add_node`,`undo` | reversible swap/rollback safety model |
| `mem20semanticobjectgraphz` | `words`,`stable_hash`,`canonical` | service identity and semantic hashing |
| `mem20relationshipcontextgraphz` | `canonical`,`similarity` | dependency/continuity context |
| `mem20dynamicskillgraphz` | `add_skill`,`update_proficiency`,`learning_path` | swap/rollback capability readiness path |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hotswappableservicefoundationz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hotswappableservicefoundationz execute '{"service":"api","op":"swap","current_impl":"v1","impl":"v2","config":{"deps":["runtime"]}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hotswappableservicefoundationz serve --port 8804
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20hotswappableservicefoundationz/tests mem20hotswappableservicefoundationz/mem20hotswappableservicefoundationz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20hotswappableservicefoundationz
```
