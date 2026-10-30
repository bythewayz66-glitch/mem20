# mem20adapz — Unified Adaptive Systems Runtime

**Version 1.0.0** · First-class implementations · No generic templates

Single runtime absorbing every former `mem20adaptive*` organ with real domain logic.

| Short | Former package | What it does |
|-------|----------------|--------------|
| achievement | mem20adaptiveachievementenginez | Tiered goals, adaptive targets, reward signals |
| dispatch | mem20adaptivedispatchenginez | Capability / load / trust / urgency assignment |
| forgetting | mem20adaptiveforgettingenginez | Ebbinghaus R=exp(-t/S) + spaced review queue |
| inference | mem20adaptiveinferencemarketplacez | Double-auction inference capacity matching |
| interface | mem20adaptiveinterfacecomposerz | Capability → interface plan composition |
| personality | mem20adaptivepersonalityruntimez | Context-aware style profile |
| pricing | mem20adaptivepricingbrainz | Log-log elasticity → revenue/margin price |

```bash
pip install -e ".[dev]"
mem20adapz --demo
python -m pytest tests -q
```

```python
from mem20adapz import AdaptiveRuntime
rt = AdaptiveRuntime()
rt.forgetting.add("k", "v")
rt.pricing.observe(10, 100)
print(rt.health())
```

After merge, remove old roots:
```bash
bash mem20adapz/DELETE_ORIGINALS.sh
```
