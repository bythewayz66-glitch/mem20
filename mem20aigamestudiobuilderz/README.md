# mem20aigamestudiobuilderz — AI Game Studio Builder

Scaffold game projects, plan asset pipelines, generate build configs, estimate size, and validate projects, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20aigamestudiobuilderz.domain import (
    scaffold_project, asset_pipeline, build_config, estimate_size, validate_project, estate_context,
)

proj = scaffold_project("my-game", genre="rpg", engine="unity")
print(proj["folders"])
print(asset_pipeline([{"id": "tex1", "type": "texture", "format": "png"}]))
print(build_config(proj, platform="mobile"))
print(estimate_size([{"size_mb": 10}, {"size_mb": 5}]))
print(validate_project(proj))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20aigamestudiobuilderz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20aigamestudiobuilderz/mem20aigamestudiobuilderz/tests -q
```
