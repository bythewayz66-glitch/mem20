# mem20adapz — Unified Adaptive Systems Runtime

**Version 1.0.0** · First-class implementations · No generic templates

This package is the single runtime that absorbs every former top-level
`mem20adaptive*` organ. Each capability is a real, tested implementation —
not a thin wrapper around a shared generic core.

## Absorbed organs

| Short id     | Former package                         | What it actually does                                      |
|--------------|----------------------------------------|------------------------------------------------------------|
| achievement  | mem20adaptiveachievementenginez        | Tiered goals, adaptive targets, reward signals             |
| dispatch     | mem20adaptivedispatchenginez           | Capability / load / trust / urgency mission assignment     |
| forgetting   | mem20adaptiveforgettingenginez         | Ebbinghaus R=exp(-t/S) + spaced review queue               |
| inference    | mem20adaptiveinferencemarketplacez     | Double-auction price-time matching for inference capacity  |
| interface    | mem20adaptiveinterfacecomposerz        | Capability → interface plan composition (RM-003 lineage)   |
| personality  | mem20adaptivepersonalityruntimez       | Context-aware style (formality, warmth, initiative, …)     |
| pricing      | mem20adaptivepricingbrainz             | Log-log elasticity fit + revenue/margin price recommendation |

## Install

```bash
cd mem20adapz
python -m pip install -e ".[dev]"
```

## Quick start

```python
from mem20adapz import AdaptiveRuntime
from mem20adapz.dispatch import Agent, Mission
from mem20adapz.interface import Capability, UserIntent

rt = AdaptiveRuntime()

# Spaced repetition
rt.forgetting.add("fact-1", "Paris is the capital of France", stability_days=2.0)
print(rt.forgetting.queue())

# Adaptive pricing
rt.pricing.observe(10.0, 120)
rt.pricing.observe(14.0, 70)
print(rt.pricing.recommend())

# Inference marketplace
rt.inference.bid(0.02, 10, agent="buyer")
rt.inference.ask(0.015, 8, agent="seller")
print(rt.inference.clear())

# Mission dispatch
rt.dispatch.register(Agent(id="a1", capabilities={"code", "review"}, load=0.2, trust=0.9))
print(rt.dispatch.assign(Mission(id="m1", required_capabilities={"code", "review"}, urgency=0.8)))

# Personality
print(rt.personality.style_for(task_type="support", urgency=0.8, emotional_valence=-0.3))

# Achievements
rt.achievement.add_goal("ship", "Ship features", target=10)
print(rt.achievement.record("ship", 4))

# Interface composition
rt.interface.register(Capability(id="search", name="Semantic Search", tags=["search"]))
print(rt.interface.compose(UserIntent(text="search deployment notes", preferred_tags=["search"])))

print(rt.health())
```

## CLI

```bash
mem20adapz --version
mem20adapz --members
mem20adapz --health
mem20adapz --demo
```

## Tests

```bash
python -m pytest tests -q
```

## Removing the old packages

After this package is merged into the mem20 monorepo, the former root
directories must be deleted:

```bash
bash DELETE_ORIGINALS.sh
```

See `DELETE_ORIGINALS.sh` for the exact list.
