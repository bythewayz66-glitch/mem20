# mem20studioz — crew runtime

mem20 studio runtime.

## Members (5)

Reviewed packages grouped here for joint integration under the
package-review rulings:

- `mem20aigamestudiobuilderz`
- `mem20aiproductionstudiooperatingsystemz`
- `mem20assetremixstudioz`
- `mem20protocolinventionstudioz`
- `mem20webgpucomputestudioz`

## Status

Skeleton slice: registry, CLI (`--version`, `--members`), hermetic
tests. Member wiring arrives in the integration phase.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20studioz --help
python -m mem20studioz --members
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20studioz/tests -q
```
