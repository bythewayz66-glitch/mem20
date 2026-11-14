# mem20loreragcontentgeneratorz — LoRA RAG Content Generator

Retrieval-augmented generation helpers with optional **grounded retrieval** via `memory_engine` (and local keyword fallback). Integrates with mem20 estate modules for conformance.

## Python API

```python
import tempfile
from pathlib import Path
from memory_engine import EngineConfig, MemoryEngine
from mem20loreragcontentgeneratorz.domain import retrieve, retrieve_from_memory, generate, estate_context

# Local corpus
docs = [{"text": "dragons live in caves"}, {"text": "elves love forests"}]
ctx = retrieve(docs, "dragon caves", k=1)
print(generate(ctx, "tell me")["output"])

# Grounded in memory_engine
with tempfile.TemporaryDirectory() as d:
    eng = MemoryEngine(EngineConfig(store_path=Path(d).resolve()))
    eng.remember("lore", "The ancient dragon guards the crystal cave.", epistemic_status="observed")
    grounded = retrieve_from_memory("dragon cave", store_path=d, k=3)
    print(generate(grounded, "describe the guardian")["grounded"])
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20loreragcontentgeneratorz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20loreragcontentgeneratorz/mem20loreragcontentgeneratorz/tests -q
```
