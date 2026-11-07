# mem20simz — crew runtime

mem20 simulator runtime.

## Members (8)

Reviewed packages grouped here for joint integration under the
package-review rulings:

- `mem20audiencereactionsimulatorz`
- `mem20businessmodelsimulatorz`
- `mem20counterfactualmemorysimulatorz`
- `mem20ethicalincentivesimulatorz`
- `mem20gamebalancesimulatorz`
- `mem20lifescenariosimulatorz`
- `mem20productledgrowthsimulatorz`
- `mem20useracceptancesimulatorz`

## Status

Skeleton slice: registry, CLI (`--version`, `--members`), hermetic
tests. Member wiring arrives in the integration phase.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20simz --help
python -m mem20simz --members
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20simz/tests -q
```
