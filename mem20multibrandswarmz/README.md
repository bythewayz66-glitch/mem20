# RM-016 — Multi-Brand Swarm (#337)

**Outcome:** Operate multiple focused brands from shared infrastructure while keeping audiences and products distinct.  
**Operation kind:** `analyze`.

## 1st-class implementation
- **Domain:** `create_swarm/add_agent/launch_campaign/cross_promote/swarm_health` (legacy) plus `analyze_swarm` producing brand isolation (distinct audiences/products), shared infrastructure, and portfolio/health.
- **Runtime:** `analyze` wired to domain + 6 peer signals.
- **Ecosystem (6 peers, unique set):** `mem20offerassemblyfabricz`, `mem20compoundingproductecosystemz`, `mem20businessmodelsimulatorz`, `mem20goaleconomyschedulerz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20multibrandswarmz execute '{"brands":["alpha","beta"],"shared_infrastructure":["auth","billing"]}'
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20multibrandswarmz/mem20multibrandswarmz/tests/test_domain.py -q
```
Gateway `SUBSYSTEMS["mem20multibrandswarmz"]`; docs `docs/app/multibrandswarmz/index.html`; target 7/7.
