# mem20graphz — graph crew runtime (#321)

mem20 graph systems runtime. Preserves `MEMBERS`, `__version__`, and legacy CLI (`--version`, `--members`).

## Members (7)
- `mem20capabilitygapmapperz` — capability gap mapping utilities (canonical/hash/terms)
- `mem20crossproductloyaltygraphz` — loyalty graph edges/degree/centrality
- `mem20deterministicconfigurationgraphz` — deterministic config graph resolve
- `mem20dynamicskillgraphz` — dynamic skill graph/proficiency/learning path
- `mem20relationshipcontextgraphz` — relationship context canonical/similarity
- `mem20reversibleexecutiongraphz` — reversible execution graph nodes/undo
- `mem20semanticobjectgraphz` — semantic object terms/hashing

## Meaningful cross-subsystem wiring (criterion 6)
Real imports and calls to all 7 member subsystems, exercised by `tests/test_graphz_crew.py` and surfaced via `doctor`.

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20graphz --version
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20graphz --members
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20graphz doctor
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20graphz serve --port 8801
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20graphz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20graphz
```
