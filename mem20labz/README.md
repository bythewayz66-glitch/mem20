# mem20labz — crew runtime

mem20 laboratory runtime.

## Members (10)

Reviewed packages grouped here for joint integration under the
package-review rulings:

- `mem20autonomoussaleslaboratoryz`
- `mem20continuouscompatibilitylabz`
- `mem20customerdigitaltwinlabz`
- `mem20dependencymutationlabz`
- `mem20executabledesignstresslabz`
- `mem20modelgenomelabz`
- `mem20neuromorphiceventlabz`
- `mem20simz`
- `mem20remoteexperimentlabz`
- `mem20webassemblycomponentlabz`

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
