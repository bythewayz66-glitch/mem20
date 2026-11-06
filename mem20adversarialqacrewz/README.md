# mem20adversarialqacrewz — Adversarial QA Crew

Generate adversarial test cases, score mutations, fuzz inputs, and produce release verdicts, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20adversarialqacrewz.domain import (
    generate_adversarial_cases, mutation_score, fuzz_input, verdict, hash_case, estate_context,
)

cases = generate_adversarial_cases({"base_input": {"value": 5}}, count=6)
print(len(cases), cases[0]["mutation"])
print(mutation_score("abc", "axc"))
print(fuzz_input({"x": 5, "s": "a"}, seed=1))
print(verdict([{"pass": True}, {"pass": False}]))
print(hash_case({"a": 1}))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20adversarialqacrewz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20adversarialqacrewz/mem20adversarialqacrewz/tests -q
```
