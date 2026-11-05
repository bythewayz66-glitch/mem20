# mem20factoryz

Procedural content generation for the mem20 estate: deterministic terrain, BSP dungeons, loot, assets, levels, narrative beats, and lightweight playtesting.

- **Package**: `mem20factoryz`
- **Python**: >= 3.11 (see `pyproject.toml`)
- **Core property**: generation is seed-driven and deterministic for a given config

## Install

From a mem20 checkout:

```bash
python3 -m pip install -e mem20factoryz
```

## CLI

```bash
# Generate a level summary
mem20factoryz generate --seed 7 --width 32 --height 32

# Preview terrain tiles
mem20factoryz terrain --seed 7 --width 16 --height 12

# Write a deterministic texture (PPM) and SFX (WAV)
mem20factoryz texture --seed 7 --resolution 16 --out /tmp/factoryz_texture.ppm
mem20factoryz audio --seed 7 --out /tmp/factoryz_sfx.wav

# Narrative beats
mem20factoryz story --seed 7 --segments 5

# Playtest a generated level
mem20factoryz playtest --seed 7 --runs 2

# Built-in self-test
mem20factoryz test --seed 7
```

## Python API

```python
from mem20factoryz.config import FactoryConfig
from mem20factoryz.generator import TerrainGenerator, BSPDungeonGenerator, LootGenerator
from mem20factoryz.level import LevelBuilder
from mem20factoryz.narrative import NarrativeEngine
from mem20factoryz.assets import AssetSynthesizer, Palette
from mem20factoryz.playtest import Playtester

cfg = FactoryConfig(seed=7, width=32, height=32)

# Heightmap (list[list[float]]) and tile quantization
hmap = TerrainGenerator().generate(cfg)
tiles = TerrainGenerator().to_tiles(hmap, levels=4)

# BSP dungeon: walls/floors, rooms, spawn
dungeon = BSPDungeonGenerator().generate(cfg)
print(len(dungeon["rooms"]), dungeon["spawn"])

# Deterministic loot
loot = LootGenerator().generate(FactoryConfig(items_per_level=5))

# Full level assembly
level = LevelBuilder(cfg).build()
print(level.width, level.height, len(level.objectives))

# Narrative and assets
beats = NarrativeEngine(seed=7).generate(segments=4)
synth = AssetSynthesizer(FactoryConfig(seed=7, asset_resolution=8))
pixels = synth.synthesise_texture(palette=Palette.from_seed(7))
sfx = synth.synthesise_sfx()

# Playtest
results = Playtester(cfg).run(level, runs=2)
print(results[0].summary())
```

## Development

```bash
python3 -m pytest mem20factoryz/mem20factoryz/tests -q
python3 scripts/renovation/conformance.py mem20factoryz
```

## Notes

- Outputs are procedural; keep `seed`/config stable for reproducible results.
- Use the CLI/API for real generation. Do not treat placeholder values as generated assets.
