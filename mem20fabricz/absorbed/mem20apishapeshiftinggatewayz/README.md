# mem20apishapeshiftinggatewayz — API Shape-Shifting Gateway

Adapt payloads, route versions, diff schemas, and transform responses, with mem20 estate integration and governance wiring.

## Python API

```python
import tempfile
from mem20apishapeshiftinggatewayz.domain import transform_payload, version_route, schema_diff, adapt_response, estate_context

print(transform_payload({"old_name": 1}, {"old_name": "new_name"}))
print(version_route("/items", 2))
print(schema_diff({"properties": {"a": {}}}, {"properties": {"a": {}, "b": {}}}))
print(adapt_response({"ok": True}, target_version=3))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20apishapeshiftinggatewayz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20apishapeshiftinggatewayz/mem20apishapeshiftinggatewayz/tests mem20apishapeshiftinggatewayz/tests -q
```
