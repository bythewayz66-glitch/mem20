# mem20labz — crew runtime (unified lab subsystem)

Unified lab subsystem consolidating experimental/lab runtimes under `mem20labz/labs/`.

mem20 laboratory runtime.

## Members (10)

Reviewed packages grouped here for joint integration under the
package-review rulings:

- `mem20autonomoussaleslaboratoryz`
- `mem20labz`
- `mem20twinz`
- `mem20labz`
- `mem20labz`
- `mem20labz`
- `mem20labz`
- `mem20simz`
- `mem20labz`
- `mem20labz`

## Status

Skeleton slice: registry, CLI (`--version`, `--members`), hermetic
tests. Member wiring arrives in the integration phase.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20labz --version
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20labz --members
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20labz status
```
