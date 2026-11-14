# mem20memorytimemachinez — Memory Time Machine

Snapshot, rewind, replay, diff, and timeline utilities for memory/state evolution, integrated with mem20’s memory engine.

## Features
- Deterministic in-memory snapshots (`snapshot`, `checkpoint_series`)
- `rewind`, `replay`, `diff`, `timeline`
- Optional engine-backed snapshot metadata via `memory_engine` (`EngineConfig`, `MemoryEngine.index_health`)
- `estate_context()` integrates real sibling modules (`mem20path`, `toolchest`, `mem20webhooksupernetworkz`, `mem20mixedinitiativefocusenginez`)

## CLI

```bash
# Domain CLI (snapshot/context)
python -m mem20memorytimemachinez.domain snapshot --label demo --state '{"counter": 1}'
python -m mem20memorytimemachinez.domain context
```

## Python API

```python
import tempfile
from mem20memorytimemachinez.domain import snapshot, checkpoint_series, diff, rewind, estate_context

snaps = checkpoint_series({"x": 0}, [{"x": 1}, {"y": 2}])
print(len(snaps), rewind(snaps, 0))
print(diff({"a": 1}, {"a": 2}))

with tempfile.TemporaryDirectory() as d:
    s = snapshot({"k": "v"}, label="with-engine", store_path=d)
    print("engine_health" in s)
    print(estate_context(d)["engine_status_checked"])
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20memorytimemachinez/mem20memorytimemachinez/tests -q
```
