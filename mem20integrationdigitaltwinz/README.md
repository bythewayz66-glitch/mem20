# mem20integrationdigitaltwinz — Integration Digital Twin (RM-076, #328)

**Outcome:** Simulate external services, rate limits, failures, and future API changes.
**Breakthrough:** Integration work becomes predictable before production traffic hits it.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator (`route` operation kind).

## Legacy domain API (preserved)
`create_twin(system)`, `sync(twin,real_state)`, `simulate(twin,scenario)`, `drift(twin,real_state)`, `health(twin)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Twin/routing role (feeds outcome) |
|---|---|---|
| `mem20deterministicconfigurationgraphz` | `add_node`,`add_edge`,`resolve` | external service/config resolution |
| `mem20versioncontrollargeassetandrecoverypipelinez` | `version_asset`,`diff_versions` | twin state versioning/snapshots |
| `mem20reversibleexecutiongraphz` | `create_graph`,`add_node`,`undo` | reversible scenario simulation |
| `mem20semanticobjectgraphz` | `canonical`,`stable_hash`,`words` | service/API semantic identity |
| `mem20relationshipcontextgraphz` | `canonical`,`similarity` | integration/failure/API-change context |
| `mem20dynamicskillgraphz` | `add_skill`,`learning_path` | route/failover/simulate capability path |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20integrationdigitaltwinz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20integrationdigitaltwinz execute '{"system":{"id":"payments-api","state":{"status":"ok"}},"scenario":[{"name":"rate_limit","effect":{"status":"throttled"}}]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20integrationdigitaltwinz serve --port 8808
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20integrationdigitaltwinz/tests mem20integrationdigitaltwinz/mem20integrationdigitaltwinz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20integrationdigitaltwinz
```
