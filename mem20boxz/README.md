# mem20boxz — crew runtime

mem20 sandbox runtime.

## Members (4)

Reviewed packages grouped here for joint integration under the
package-review rulings:

- `mem20simz`
- `mem20multiworldsandboxz`
- `mem20scopemutationsandboxz`
- `mem20spatialcomputingsandboxz`

## Status

Skeleton slice: registry, CLI (`--version`, `--members`), hermetic
tests. Member wiring arrives in the integration phase.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20boxz.mem20boxz --version
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20boxz.mem20boxz --members
```
