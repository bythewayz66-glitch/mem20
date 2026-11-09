# mem20hardwareawareinferencecompilerz — Hardware-Aware Inference Compiler (RM-065, #322)

**Outcome:** compile model graphs for the exact CPU, GPU, NPU, memory, and latency budget available.

Preserves legacy domain API (**#314 peer dependency**) and CAPABILITY Engine/CLI/10-scenario simulator. `search` is meaningful for compile payloads and backward-compatible for generic search.

## Legacy domain API (preserved)
`fuse_ops(ops)`, `quantize(weights,bits=8)`, `schedule(ops,device)`, `memory_estimate(ops,dtype_bytes=4)`, `optimize_graph(graph)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Compile role |
|---|---|---|
| `mem20edgefleetbrainz` | `Node`,`Workload`,`estimate_energy_wh`,`estimate_cost`,`score_placement` | hardware target energy/cost/placement |
| `mem20modalitybridgez` | `supported_modalities`,`encode_text`,`bridge` | model/modality context |
| `mem20modelgenomelabz` | `create_genome`,`fitness`,`mutate` | model variant evaluation |
| `mem20personalmodelevolutionz` | `create_model`,`adapt`,`predict` | device/user adaptation signal |
| `mem20pipez` | `pathfind`,`validate_level` | graph traversal/validation |
| `mem20pipez` | `parse_dialogue`,`validate_dialogue`,`export_script` | artifact spec validation/export |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwareawareinferencecompilerz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwareawareinferencecompilerz execute '{"compile":true,"ops":[{"type":"matmul","size":10,"priority":1},{"type":"relu","size":10}],"weights":[0.0,0.5,1.0],"device":{"id":"cpu"}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwareawareinferencecompilerz serve --port 8802
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20hardwareawareinferencecompilerz/tests mem20hardwareawareinferencecompilerz/mem20hardwareawareinferencecompilerz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20hardwareawareinferencecompilerz
```
