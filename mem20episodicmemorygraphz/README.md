# mem20episodicmemorygraphz — Episodic Memory Graph (RM-021, #306)

**Outcome:** store experiences as linked people, places, goals, actions, outcomes, and time.  
**Breakthrough:** memory becomes navigable experience rather than a pile of text chunks.

First-class implementation: legacy-compatible episode API plus graph navigation/query/timeline/entity indexing, durable SQLite WAL state, CLI + JSON HTTP API + cockpit, `docs/app` monitor, and 6 **unique** peer integrations (different from #300-#305).

## Legacy-compatible API
`create_episode(title,events=None)`, `add_event(ep,event)`, `link_episodes(episodes,a,b,relation='follows')`, `recall(episodes,query)`, `episode_graph(episodes)`, `forget(episodes,older_than)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20dynamicskillgraphz` | `add_skill`,`update_proficiency`,`learning_path`,`skill_gap`,`graph_stats` | skill/proficiency graph over episode actions/outcomes |
| `mem20reversibleexecutiongraphz` | `create_graph`,`add_node`,`undo`,`redo`,`graph_health` | reversible episode/replay graph |
| `mem20mixedinitiativefocusenginez` | `focus_score`,`suggest`,`take_over`,`blend`,`focus_health` | focus/attention for recall lens |
| `mem20spatialcommanduniversez` | `create_region`,`add_entity`,`distance`,`in_region`,`spatial_health` | spatial/place indexing |
| `mem20crossproductloyaltygraphz` | `add_edge`,`degree`,`centrality`,`recommend_products`,`loyalty_score` | relationship centrality/recommendations |
| `mem20deterministicconfigurationgraphz` | `add_node`,`add_edge`,`resolve`,`validate`,`diff_configs` | deterministic relationship/config resolution |

## Runnable example (verified)

```bash
cd /opt/mem20
DB=/tmp/emg-demo.sqlite3
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20episodicmemorygraphz --db "$DB" create --title "ship fix"
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20episodicmemorygraphz --db "$DB" recall fix
```

Observed (key fields): `create` returns `ok=true`, episode id/title/events, and peer signals (`focus_recall`, `spatial_places` all `ok:true`). `recall` returns matching episodes and `focus_recall` signal.

```bash
python -m mem20episodicmemorygraphz status
python -m mem20episodicmemorygraphz doctor
python -m mem20episodicmemorygraphz simulate
python -m mem20episodicmemorygraphz serve --port 8786
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20episodicmemorygraphz/tests -q
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20episodicmemorygraphz
```
