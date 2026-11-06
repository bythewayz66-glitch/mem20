# mem20assistz — crew runtime

mem20 companion, coach and assistant runtime.

## Members (9)

Reviewed packages grouped here for joint integration under the
package-review rulings:

- `mem20ambientdevicecompanionz`
- `mem20conflictdeescalationassistantz`
- `mem20contextawarelearningcoachz`
- `mem20conversationalactiondesktopz`
- `mem20humancapabilityacceleratorz`
- `mem20humancapabilitysuperplatformz`
- `mem20personalautomationcanvasz`
- `mem20personalintelligencecompanionz`
- `mem20universalcompaniondevicesdkz`

## Python API

```python
import tempfile
import mem20assistz
from mem20assistz.domain import estate_context

print(mem20assistz.__version__)
print(len(mem20assistz.MEMBERS))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
mem20assistz --version
mem20assistz --members
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20assistz/tests -q
```
