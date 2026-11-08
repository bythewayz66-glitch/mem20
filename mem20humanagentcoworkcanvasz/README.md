# mem20humanagentcoworkcanvasz — Human-Agent Co-work Canvas (RM-032, #325)

**Outcome:** Let humans and agents manipulate the same tasks, files, decisions, and live artifacts.
**Breakthrough:** AI collaboration feels like working beside a capable teammate.

Preserves legacy domain API (**#320 peer dependency**) and CAPABILITY Engine/CLI/10-scenario simulator (`sync` operation kind).

## Legacy domain API (preserved for #320)
`create_canvas(name,participants=None)`, `add_item(canvas,author,content,kind="text")`, `take_turn(canvas,participant)`, `contributions(canvas)`, `canvas_summary(canvas)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Canvas sync role (feeds outcome) |
|---|---|---|
| `mem20realtimeteampresencez` | `set_presence`,`online_users`,`away_users` | participant presence/availability |
| `mem20asynccollaborationcapsulesz` | `create_capsule`,`apply_change`,`merge_capsules`,`capsule_checksum` | async change capture and merge |
| `mem20versioncontrollargeassetandrecoverypipelinez` | `version_asset`,`diff_versions`,`recover` | live artifact versioning/recovery |
| `mem20deterministicconfigurationgraphz` | `add_node`,`add_edge`,`resolve` | deterministic workspace config |
| `mem20semanticobjectgraphz` | `canonical`,`stable_hash`,`words` | artifact/decision identity |
| `mem20relationshipcontextgraphz` | `canonical`,`similarity` | human-agent teammate context |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20humanagentcoworkcanvasz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20humanagentcoworkcanvasz execute '{"name":"mission-canvas","participants":["human","agent"],"items":[{"author":"human","content":"define task","kind":"task"}]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20humanagentcoworkcanvasz serve --port 8805
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20humanagentcoworkcanvasz/tests mem20humanagentcoworkcanvasz/mem20humanagentcoworkcanvasz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20humanagentcoworkcanvasz
```
