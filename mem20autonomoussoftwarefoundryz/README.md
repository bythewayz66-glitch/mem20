# mem20autonomoussoftwarefoundryz — Autonomous Software Foundry

Turn specs into tasks, assess code quality, decide deploys, estimate effort, and build artifacts, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20autonomoussoftwarefoundryz.domain import (
    spec_to_tasks, code_quality, deploy_decision, estimate_effort, build_artifact, estate_context,
)

print(spec_to_tasks({"features": ["auth", "api"]}))
print(code_quality({"tests_pass": True, "coverage": 0.9, "lint_clean": True}))
print(deploy_decision(0.8))
print(estimate_effort({"features": ["a", "b", "c"]}))
print(build_artifact({"name": "app"}, "print('hi')\n"))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20autonomoussoftwarefoundryz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20autonomoussoftwarefoundryz/mem20autonomoussoftwarefoundryz/tests -q
```
