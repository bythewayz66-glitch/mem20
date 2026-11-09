# RM-061 — Model Genome Lab (#335)

**Outcome:** Describe models through capabilities, behavior traits, limits, adapters, and evaluation ancestry.  
**Breakthrough:** Models become composable evolving assets instead of opaque files.  
**Operation kind:** `simulate`.

## 1st-class implementation
- **Domain:** `create_genome/mutate/crossover/fitness/evolve` (legacy preserved) plus `genome_record`, `simulate_genome_lab` (population evolution, best genome, ancestry/adapters/limits/traits record).
- **Runtime:** `simulate` wired to domain genome lab + 6 peer signals (also returns scenario projections).
- **Ecosystem (6 peers, set differs from #330-334):** `mem20runtimecompatibilityenginez`, `mem20pipez`, `mem20selfoptimizingkernelz`, `mem20simz`, `mem20twinz`, `mem20eventstreamsuperhighwayz`.

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20modelgenomelabz execute '{"population":4,"generations":2,"objective":{"quality":1.0,"latency":0.2},"seed":1}'
```
Returns `ok/best/population_size/objective/record(top+ancestry+adapters+limits+traits)`, `scenarios`, and 6 `signals`.

## Tests
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20modelgenomelabz/mem20modelgenomelabz/tests/test_domain.py -q
```

## Conformance / registration
Gateway: `SUBSYSTEMS["mem20modelgenomelabz"]`; Docs: `docs/app/modelgenomelabz/index.html`; target 7/7.
