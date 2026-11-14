# mem20goaleconomyschedulerz — Goal Economy Scheduler (RM-056, #319)

**Outcome:** allocate scarce compute, money, time, and attention among competing goals.  
**Breakthrough:** resources flow toward the highest-value achievable outcomes.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator. `schedule` is meaningful for goal-economy payloads and backward-compatible for generic node placement.

## Legacy domain API (preserved)
`schedule_goals(goals,budget)`, `goal_value(goal)`, `rebalance(goals,new_budget)`, `progress(goals,completed_ids)`, `priority_queue(goals)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Scheduling role |
|---|---|---|
| `mem20selfhealingplansz` | `create_plan`,`plan_status`,`heal_plan` | plan resilience/health |
| `mem20opportunityradarz` | `score_opportunity`,`rank`,`scan` | opportunity/value prioritization |
| `mem20revenueleakhunterz` | `detect_leaks`,`recoverable`,`hunter_health` | budget/money leak risk |
| `mem20milestoneriskpredictorz` | `MilestoneRiskPredictor.add_point/velocity/forecast` | milestone schedule forecast |
| `mem20humancapabilitysuperplatformz` | `capability_matrix`,`team_capability` | attention/execution capacity |
| `mem20facez` | `compose_plan`,`probe_members` | control interface composition |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goaleconomyschedulerz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goaleconomyschedulerz execute '{"goals":[{"id":"g1","value":10,"cost":3},{"id":"g2","value":8,"cost":2}],"budget":4}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goaleconomyschedulerz serve --port 8799
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20goaleconomyschedulerz/tests mem20goaleconomyschedulerz/mem20goaleconomyschedulerz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20goaleconomyschedulerz
```
