# mem20adaptiveinferencemarketplacez

> **Double-auction price-time matching for inference capacity.**

Built under Option C: every clone in this group shared one generic runtime, so
this package could previously do any of its 93 siblings' jobs. It now has a
`domain.py` implementing what its name claims.

## What it actually does

Double-auction matching for inference capacity: price-time priority on both
sides, trades priced at the maker, partial fills with resting liquidity
reported, and no matching when the book is uncrossed.

## Verify it yourself

```bash
cd /opt/mem20/mem20adaptiveinferencemarketplacez
python3 -m pytest mem20adaptiveinferencemarketplacez/tests -q
```

Evidence that this is real behaviour rather than a renamed template:
`elasticity` is fitted by log-log regression and checked against an analytic
curve; retention is checked against exact `exp(-t/S)` values and the queue is
ordered by measured lapse; matching is checked for price-time priority, no
crossing, and partial-fill resting liquidity.

## Integration

`core.py` gains a `run_domain()` entry point that dispatches to this package's
own functions, and `domain_capabilities()` so the runtime advertises what it
really supports instead of the shared `FAMILY_FUNCS` table.
