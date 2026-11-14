# mem20intentcompilerz — Intent Compiler (RM-051, #329)

**Outcome:** Translate goals into typed executable graphs with resources, constraints, and success conditions.
**Breakthrough:** Users can state goals at a high level and still get reliable execution.

Preserves legacy domain API (**compat critical for 300-308 peer set**) and CAPABILITY Engine/CLI/10-scenario simulator (`compose` operation kind).

## Legacy domain API (preserved)
`parse_intent(text)`, `classify(intent)`, `compile_to_action(intent)`, `validate(intent)`, `intent_confidence(intent,keywords)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Intent compilation role (feeds executable outcome) |
|---|---|---|
| `mem20deterministicconfigurationgraphz` | `add_node`,`add_edge`,`resolve` | typed executable resource/constraint/success graph |
| `mem20dynamicskillgraphz` | `add_skill`,`learning_path` | action/capability execution plan |
| `mem20semanticobjectgraphz` | `canonical`,`stable_hash`,`words` | typed intent/entity identity |
| `mem20relationshipcontextgraphz` | `canonical`,`similarity` | goal executability context |
| `mem20reversibleexecutiongraphz` | `create_graph`,`add_node`,`undo` | reversible execution planning |
| `mem20pipez` | `version_asset`,`vc_health` | intent/plan versioning |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20intentcompilerz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20intentcompilerz execute '{"text":"create deployment pipeline","resources":["ci"],"constraints":["safe rollout"],"success_conditions":["pipeline green"]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20intentcompilerz serve --port 8809
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20intentcompilerz/tests mem20intentcompilerz/mem20intentcompilerz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20intentcompilerz
```
