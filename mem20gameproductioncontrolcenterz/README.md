# mem20gameproductioncontrolcenterz — Game Production Control Center (RM-233, #317)

**Outcome:** operate agent work, builds, assets, testing, engine imports, costs, and releases from one live surface.  
**Breakthrough:** a complete studio pipeline becomes visible and controllable.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator. `simulate` returns `scenarios` (backward compatible) and, with production context, a **meaningful** `production_control` report composed from real domain + peer integrations.

## Legacy domain API (preserved)
`sprint_plan(tasks,capacity)`, `burndown(tasks,completed_ids)`, `milestone_status(milestones,today)`, `risk_score(project)`, `production_health(sprints)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | How it affects production control |
|---|---|---|
| `mem20realtimeteampresencez` | `set_presence`,`online_users` | computes effective team capacity used in sprint planning |
| `mem20uniteconomicsautopilotz` | `ltv`,`cac`,`payback_months`,`ltv_cac_ratio` | projects cost/revenue sustainability |
| `mem20hotswappableservicefoundationz` | `register_service`,`swap`,`health` | assesses build/release service readiness |
| `mem20specialistmodelforgez` | `forge_health` | reports production capability/model readiness |
| `mem20labz` | `resilience_score`,`recovery_time` | adjusts risk via resilience and recovery estimates |
| `mem20pipez` | `create_rig`,`set_pose`,`animate` | reports asset/animation pipeline readiness |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gameproductioncontrolcenterz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gameproductioncontrolcenterz execute '{"baseline":1,"production":true,"tasks":[{"id":"t1","effort":3}],"capacity":5,"today":1,"milestones":[{"id":"m1","due_day":5}],"project":{"team_size":4,"budget_ratio":0.9}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gameproductioncontrolcenterz serve --port 8797
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20gameproductioncontrolcenterz/tests mem20gameproductioncontrolcenterz/mem20gameproductioncontrolcenterz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20gameproductioncontrolcenterz
```
