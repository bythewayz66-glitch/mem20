# mem20adaptiveforgettingenginez

> **Ebbinghaus forgetting curve with spaced reinforcement scheduling.**

Built under Option C: every clone in this group shared one generic runtime, so
this package could previously do any of its 93 siblings' jobs. It now has a
`domain.py` implementing what its name claims.

## What it actually does

Models per-item retention as `R = exp(-t/S)` with stability `S` widening on
successful review and collapsing on failure, then schedules the next review at
exactly the point retention crosses threshold, and produces a most-lapsed-first
review queue.

## Verify it yourself

```bash
cd /opt/mem20/mem20adaptiveforgettingenginez
python3 -m pytest mem20adaptiveforgettingenginez/tests -q
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
