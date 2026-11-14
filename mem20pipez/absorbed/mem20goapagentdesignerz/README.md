# mem20goapagentdesignerz — GOAP Agent Designer (RM-226, #320)

**Outcome:** build goal-oriented agents through a visual editor for actions, costs, perceptions, and memory.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator. `search` is meaningful for GOAP design payloads and backward-compatible for generic search.

## Legacy domain API (preserved)
`plan(actions,start_state,goal_state)`, `action_cost(action)`, `heuristic(state,goal)`, `validate_plan(plan,actions)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | GOAP design role |
|---|---|---|
| `mem20simz` | `fairness_score`,`simulate_incentives` | incentive alignment for actions/agents |
| `mem20styleguideagentz` | `style_health`,`style_score` | design/spec quality checks |
| `mem20humanagentcoworkcanvasz` | `create_canvas`,`add_item`,`canvas_summary` | human-agent design collaboration |
| `mem20dynamicphasereplannerz` | `DynamicPhaseReplanner` (+ phase/order) | phase replanning structure |
| `mem20compoundingproductecosystemz` | `ecosystem_health`,`network_value`,`synergy` | agent ecosystem value signals |
| `mem20asynccollaborationcapsulesz` | `create_capsule`,`capsule_checksum`,`active_members` | async collaboration capsule |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goapagentdesignerz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goapagentdesignerz execute '{"actions":[{"name":"move","effects":{"at":"target"},"cost":1}],"start_state":{"at":"start"},"goal_state":{"at":"target"}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goapagentdesignerz serve --port 8800
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20goapagentdesignerz/tests mem20goapagentdesignerz/mem20goapagentdesignerz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20goapagentdesignerz
```
