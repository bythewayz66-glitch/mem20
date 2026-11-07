# mem20executiondigitaltwinz — Execution Digital Twin (RM-059, #310)

**Outcome:** mirror every live workflow in a predictive simulation updated from telemetry.  
**Breakthrough:** the system sees likely bottlenecks and failures before they happen.

First-class `forecast` operation (CAPABILITY/Engine preserved) enriched with real digital twin analysis (`create_twin`, `sync_twin`, `simulate`, `predict_outcome`, `drift`) and, for explicit twin requests, 6 **unique** peer integrations (different from #300–#309). Legacy domain API is preserved (used as a peer by #307).

## Legacy domain API (preserved)
`create_twin(process)`, `sync_twin(twin, real_state)`, `simulate(twin, actions)`, `predict_outcome(twin, action)`, `drift(twin, real_state)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20personalworkflowtwinz` | `create_twin`,`observe`,`suggest_improvements`,`efficiency_score`,`twin_health` | workflow twin observation/improvement |
| `mem20integrationdigitaltwinz` | `create_twin`,`sync`,`simulate`,`drift`,`health` | integration/system twin sync & simulation |
| `mem20memorytimemachinez` | `rewind`,`replay`,`diff`,`timeline`,`checkpoint_series` | snapshot/time-machine replay & diff |
| `mem20counterfactualmemorysimulatorz` | `branch`,`counterfactual`,`compare`,`outcome_probability` | counterfactual branches/outcomes |
| `mem20customerdigitaltwinlabz` | `build_twin`,`simulate_behavior`,`predict_churn`,`recommend_action` | behavior/churn/recommendation twin |
| `mem20crossruntimeeventlatticez` | `emit`,`order_events`,`causal_link`,`lattice_merge`,`filter_by_type` | causal event lattice/ordering |

## Runnable example (verified)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20executiondigitaltwinz simulate
```

Observed: 10 Engine simulator scenarios `ok=true`.

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20executiondigitaltwinz execute '{"process":{"id":"wf","state":{"progress":1},"metrics":{"success_rate":0.7}},"real_state":{"progress":2},"actions":[{"name":"advance","effect":{"progress":1},"impact":0.05}],"series":[1,2,3],"steps":2}'
```

Returns `slope/forecast/confidence` plus twin analysis (`twin`,`simulation`,`predicted_outcome`,`drift`) and 6 peer `signals` (all `ok:true`) for explicit twin requests.

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20executiondigitaltwinz serve --port 8790
```

HTTP: `/health`, `/spec`, `/metrics`, `/events`, `/objects`, `/doctor` (peer probe), `/execute`, `/feedback`, `/replica/merge`, `/jobs/<id>/cancel`, cockpit at `/`.

## Tests / conformance

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20executiondigitaltwinz/tests mem20executiondigitaltwinz/mem20executiondigitaltwinz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20executiondigitaltwinz
```

