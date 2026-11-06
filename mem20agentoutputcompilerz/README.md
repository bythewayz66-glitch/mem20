# mem20agentoutputcompilerz — Agent Output Compiler

Merge, deduplicate, compile, validate, and summarize multi-agent outputs, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20agentoutputcompilerz.domain import (
    merge_outputs, dedupe, compile_report, validate_output, summarize, estate_context,
)

outputs = [
    {"agent": "planner", "items": [{"id": 1, "task": "a"}]},
    {"agent": "coder", "items": [{"id": 1, "task": "a"}, {"id": 2, "task": "b"}]},
]
print(merge_outputs(outputs)["sources"])
print(dedupe([{"id": 1}, {"id": 1}, {"id": 2}]))
print(compile_report(outputs))
print(validate_output({"items": []}))
print(summarize(outputs))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20agentoutputcompilerz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20agentoutputcompilerz/mem20agentoutputcompilerz/tests -q
```
