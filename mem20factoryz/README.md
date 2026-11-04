# mem20factoryz

Deterministic, hermetic game-factory primitives for the mem20 estate: a seeded
PRNG and value noise, terrain and BSP-dungeon generators, texture and audio
synthesis, level assembly, narrative beats, and playtest simulation.

Everything is reproducible from a seed. No network, no wall clock, and no
external asset files are involved.

## Install

```bash
cd mem20factoryz
python3 -m pip install -e .
```

## CLI

The top-level `--seed` must come before the subcommand.

```bash
# Build a 32x32 level and print its summary
python3 -m mem20factoryz --seed 7 generate --width 32 --height 32

# Emit the same level as JSON
python3 -m mem20factoryz --seed 7 generate --width 32 --height 32 --json

# Synthesize a texture and an SFX file
python3 -m mem20factoryz --seed 7 texture --resolution 16 --out /tmp/factoryz.ppm
python3 -m mem20factoryz --seed 7 audio --out /tmp/factoryz.wav

# Preview terrain tiles and simulate five playthroughs
python3 -m mem20factoryz --seed 7 terrain --width 16 --height 8
python3 -m mem20factoryz --seed 7 playtest --runs 5
```

The installed console script is equivalent:

```bash
mem20factoryz --seed 7 generate --width 32 --height 32
```

## Python API

```python
from mem20factoryz.config import FactoryConfig
from mem20factoryz.level import LevelBuilder

cfg = FactoryConfig(seed=7, width=32, height=32)
level = LevelBuilder(cfg).build()

assert (level.width, level.height) == (32, 32)
print(len(level.entities), len(level.objectives), level.spawn)
```

`Generator` is an abstract base class: concrete generators implement
`generate(config)` and return their artifact (a heightmap, a dungeon dict, or a
loot table).

## Guarantees

- The same seed produces byte-identical output (`DeterministicPRNG`).
- Level, texture, audio, narrative, and playtest paths are all seeded.
- Failure is explicit: an incomplete `Generator` subclass cannot be
  instantiated.

## Test

```bash
python3 -m pytest -q mem20factoryz/mem20factoryz/tests
```
