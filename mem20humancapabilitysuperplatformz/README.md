# mem20humancapabilitysuperplatformz — Human Capability Super-Platform (RM-220, #326)

**Outcome:** increase what ordinary people can accomplish through capability discovery, assessment, and growth.
**Breakthrough:** FreeStack becomes famous for increasing what ordinary people can accomplish.

Preserves legacy domain API (**#319 peer dependency**) and advanced CAPABILITY Engine/CLI/10-scenario simulator (`search` operation kind, policy guards, replica merge, cancellation, snapshot).

## Legacy domain API (preserved for #319)
`assess(capability,evidence)`, `growth_plan(current,target)`, `capability_matrix(users,skills)`, `team_capability(matrix,skill)`, `learning_recommendation(gaps)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Capability role (feeds search outcome) |
|---|---|---|
| `mem20dynamicskillgraphz` | `add_skill`,`update_proficiency`,`learning_path` | skill/proficiency growth path |
| `mem20capabilitygapmapperz` | `canonical`,`stable_hash`,`words` | capability identity and terms |
| `mem20relationshipcontextgraphz` | `canonical`,`similarity` | human accomplishment context |
| `mem20semanticobjectgraphz` | `canonical`,`stable_hash` | capability/skill semantic objects |
| `mem20pipez` | `version_asset`,`vc_health` | evidence versioning/provenance |
| `mem20deterministicconfigurationgraphz` | `add_node`,`add_edge`,`resolve` | deterministic platform config |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20humancapabilitysuperplatformz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20humancapabilitysuperplatformz execute '{"users":[{"id":"u1","skills":{"execution":3},"evidence":[{"weight":1,"value":0.8}]}],"skills":["execution","collaboration","leadership"]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20humancapabilitysuperplatformz serve --port 8806
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20humancapabilitysuperplatformz/tests mem20humancapabilitysuperplatformz/mem20humancapabilitysuperplatformz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20humancapabilitysuperplatformz
```
