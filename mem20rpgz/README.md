# mem20rpgz

RPG generation subsystem for mem20 - converts story outlines into playable RPGs using multi-agent studio approach.

## Features
- Elemental Tetrad multi-agent studio (Narrative, Scene, Gameplay agents)
- Deterministic seeded generation
- Optional live LLM mode
- Character creation, combat, inventory, quests
- CLI interface

## Usage
```python
from mem20rpgz import create_game
game = create_game(seed=12345)
```
