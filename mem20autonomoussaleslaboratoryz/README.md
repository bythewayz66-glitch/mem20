# mem20autonomoussaleslaboratoryz — Autonomous Sales Laboratory

Score leads, generate outreach, estimate conversion, value pipelines, and segment leads, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20autonomoussaleslaboratoryz.domain import (
    lead_score, outreach_message, conversion_probability, pipeline_value, segment_leads, estate_context,
)

lead = {"name": "Bob", "email": "b@x.com", "budget": 2000, "authority": True, "need": True, "timeline_days": 10, "deal_value": 1000}
print(lead_score(lead))
print(outreach_message(lead, {"subject": "Hi {name}", "body": "Hello {name}"}))
print(conversion_probability(lead, touches=3))
print(pipeline_value([lead]))
print(segment_leads([lead]))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20autonomoussaleslaboratoryz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20autonomoussaleslaboratoryz/mem20autonomoussaleslaboratoryz/tests -q
```
