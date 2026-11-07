# mem20selfz — crew runtime

mem20 self-healing, self-tuning, forecasting and optimization runtime.

## Members (16)

Reviewed packages grouped here for joint integration under the
package-review rulings:

- `mem202dand3dartproductionoptimizationpipelinez`
- `mem20aipipelinecostoptimizerz`
- `mem20buildsequenceoptimizerz`
- `mem20datalocalityoptimizerz`
- `mem20demandforecastandcapacitybrainz`
- `mem20milestoneriskpredictorz`
- `mem20qualityriskforecasterz`
- `mem20quantuminspiredoptimizerz`
- `mem20releasereadinesspredictorz`
- `mem20runtimepromptoptimizerz`
- `mem20selfhealingconnectormeshz`
- `mem20selfhealingplansz`
- `mem20selfhealingruntimecivilizationz`
- `mem20selfoptimizingkernelz`
- `mem20selfrepairingtestfactoryz`
- `mem20selftuningresourcegovernorz`

## Status

Skeleton slice: registry, CLI (`--version`, `--members`), hermetic
tests. Member wiring arrives in the integration phase.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20selfz --help
python -m mem20selfz --members
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20selfz/tests -q
```
