# mem20hardwaremarketplacez — Hardware Marketplace (RM-048, #323)

**Outcome:** Match workloads to volunteered, owned, or rented compute under explicit limits.
**Breakthrough:** Users can monetize or share spare compute without surrendering control.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator (`match` operation kind). `match` is meaningful for marketplace payloads (`listings`/`workloads`) and backward-compatible for generic demand/supply matching.

## Legacy domain API (preserved)
`list_hardware(seller,hw,price)`, `search(listings,query)`, `price_estimate(hw)`, `transaction(listing,buyer)`, `marketplace_health(listings)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Marketplace role (feeds match outcome) |
|---|---|---|
| `mem20causalroutingbrainz` | `Node`,`Workload`,`estimate_energy_wh`,`estimate_cost`,`score_placement` | placement/energy/cost fit per listing |
| `mem20devicecapabilitycompilerz` | `compile_for_device`,`compatibility`,`feature_flags` | capability + explicit limits enforcement |
| `mem20datalocalityoptimizerz` | `optimal_placement`,`migration_cost`,`placement_score`,`locality_report` | locality and migration-cost fit |
| `mem20energyawarecomputemigrationz` | `ComputeNode`,`Workload`,`greenest_node`,`carbon_footprint`,`energy_cost` | carbon/energy-aware selection |
| `mem20zerotouchnodeswarmz` | `register_node`,`discover`,`assign_task`,`load_distribution`,`heal` | volunteered pool availability/load |
| `mem20roamingworkloadschedulerz` | `schedule`,`migrate`,`node_load`,`scheduler_health` | workload scheduling/migration fit |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwaremarketplacez simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwaremarketplacez execute '{"listings":[{"seller":"gpu-a","hardware_spec":{"cores":8,"memory_gb":16,"gpu":true},"price":40,"available":true}],"workloads":[{"id":"train","cpu":2,"memory_gb":4,"gpu":1}]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwaremarketplacez serve --port 8803
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20hardwaremarketplacez/tests mem20hardwaremarketplacez/mem20hardwaremarketplacez/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20hardwaremarketplacez
```
