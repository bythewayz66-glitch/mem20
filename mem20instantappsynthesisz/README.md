# mem20instantappsynthesisz — Instant App Synthesis (RM-010, #327)

**Outcome:** Compile a plain-language objective into a working composition of existing FreeStack capabilities.
**Breakthrough:** Users describe an outcome and receive a usable app in minutes.

Preserves legacy domain API (**#318 peer dependency**) and CAPABILITY Engine/CLI/10-scenario simulator (`compose` operation kind).

## Legacy domain API (preserved for #318)
`synthesize(spec)`, `scaffold(app)`, `estimate_size(app)`, `validate_spec(spec)`, `deploy_config(app,target="vercel")`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Synthesis role (feeds composition outcome) |
|---|---|---|
| `mem20deterministicconfigurationgraphz` | `add_node`,`add_edge`,`resolve` | app/page config graph resolution |
| `mem20semanticobjectgraphz` | `canonical`,`stable_hash`,`words` | spec/component semantic identity |
| `mem20versioncontrollargeassetandrecoverypipelinez` | `version_asset`,`vc_health` | synthesized artifact versioning |
| `mem20dynamicskillgraphz` | `add_skill`,`learning_path` | capability composition path |
| `mem20relationshipcontextgraphz` | `canonical`,`similarity` | objective-to-composition intent context |
| `mem20capabilitygapmapperz` | `canonical`,`stable_hash` | capability gap/coverage check |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20instantappsynthesisz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20instantappsynthesisz execute '{"objective":"build a todo app","spec":{"name":"todo","pages":["home"],"components":["list","form"]}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20instantappsynthesisz serve --port 8807
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20instantappsynthesisz/tests mem20instantappsynthesisz/mem20instantappsynthesisz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20instantappsynthesisz
```
